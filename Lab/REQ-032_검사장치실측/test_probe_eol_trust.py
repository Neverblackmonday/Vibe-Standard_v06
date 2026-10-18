"""REQ-032 실험 단계(개발부) 실측 스크립트.

실험 파일이며 정규 경로로 복사하거나 옮기지 않는다(Workflow/03 11.2절 5항).
`python -m pytest Lab/REQ-032_검사장치실측/test_probe_eol_trust.py -s -q -p no:cacheprovider`로
실행하고, 출력 원문을 실험 기록에 옮긴다. 결과 파일을 만들지 않는다.

- E2: 줄바꿈 기본 규칙(.gitattributes)과 core.autocrlf 조합이 인수 시험 해시 대조
  (`git diff --no-index --full-index /dev/null <파일>`의 index 줄 해시)에 주는 영향.
  임시 Git 저장소는 pytest tmp_path 아래에만 만든다.
- E2r: 이 저장소의 줄바꿈 현황(읽기 전용 조회: git config --get, git ls-files --eol).
- E3: Claude Code 폴더 신뢰 상태와 훅 경로를 읽기만으로 점검할 수 있는지.
  사용자 파일은 읽기 모드로만 열고, 값은 신뢰 여부(불리언)와 키 이름만 출력한다.
"""
import hashlib
import json
import pathlib
import subprocess
import sys

# 콘솔 기본 인코딩(cp949)으로 한글 출력이 깨지지 않게 UTF-8로 고정한다
sys.stdout.reconfigure(encoding="utf-8")

REPO = pathlib.Path(__file__).resolve().parents[2]
TEST_REL = "test_sample.py"
LF_BYTES = b"def test_a():\n    assert 1 + 1 == 2\n"
CRLF_BYTES = LF_BYTES.replace(b"\n", b"\r\n")
ATTRS = {
    "none": None,
    "text=auto": b"* text=auto\n",
    "text=auto eol=lf": b"* text=auto eol=lf\n",
}
AUTOCRLF = ["true", "false", "input"]


def git(args, cwd, check=True):
    # 실패를 숨기지 않기 위해 check=True이면 명령과 stderr를 담아 실패시킨다
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and r.returncode != 0:
        raise AssertionError(f"git {args} 실패: {r.stderr.decode('utf-8', 'replace')}")
    return r


def no_index_hash(cwd, rel):
    # 인수 시험 해시 대조와 같은 명령(Workflow/03 12절 4항). 차이가 있으면 종료 코드 1이 정상이다
    r = git(["diff", "--no-index", "--full-index", "/dev/null", rel], cwd, check=False)
    for line in r.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith("index "):
            return line.split("..")[1].split()[0], r.stderr.decode("utf-8", "replace").strip()
    raise AssertionError(f"index 줄 없음: {r.stdout!r} {r.stderr!r}")


def raw_hash(cwd, rel):
    return git(["hash-object", "--no-filters", rel], cwd).stdout.decode().strip()


def eol_of(path):
    data = path.read_bytes()
    return "CRLF" if b"\r\n" in data else "LF"


def make_repo(root, autocrlf, attr):
    root.mkdir()
    git(["init", "-q"], root)
    git(["config", "user.name", "probe"], root)
    git(["config", "user.email", "probe@example.invalid"], root)
    git(["config", "core.autocrlf", autocrlf], root)
    if attr is not None:
        (root / ".gitattributes").write_bytes(attr)
        git(["add", ".gitattributes"], root)
        git(["commit", "-q", "-m", "attr"], root)
    return root


def run_case(tmp, autocrlf, attr_name, content_name, content):
    a = make_repo(tmp / f"a_{autocrlf}_{attr_name.replace(' ', '_').replace('=', '-')}_{content_name}",
                  autocrlf, ATTRS[attr_name])
    (a / TEST_REL).write_bytes(content)
    h_written, warn_diff = no_index_hash(a, TEST_REL)
    add = git(["add", TEST_REL], a)
    git(["commit", "-q", "-m", "test"], a)
    h_after_commit, _ = no_index_hash(a, TEST_REL)
    status_a = git(["status", "--porcelain"], a).stdout.decode().strip()
    b = a.parent / (a.name + "_clone")
    git(["clone", "-q", "-c", f"core.autocrlf={autocrlf}", str(a), str(b)], a.parent)
    h_clone, _ = no_index_hash(b, TEST_REL)
    return {
        "autocrlf": autocrlf,
        "attr": attr_name,
        "written": content_name,
        "raw_hash_written": raw_hash(a, TEST_REL)[:12],
        "h_written": h_written[:12],
        "h_after_commit": h_after_commit[:12],
        "clone_eol": eol_of(b / TEST_REL),
        "h_clone": h_clone[:12],
        "match_written_clone": h_written == h_clone,
        "status_after_commit": status_a or "(clean)",
        "add_warning": "yes" if add.stderr.strip() else "no",
        "diff_warning": "yes" if warn_diff else "no",
    }


def test_e2_eol_hash_matrix(tmp_path):
    rows = []
    for autocrlf in AUTOCRLF:
        for attr_name in ATTRS:
            for content_name, content in (("LF", LF_BYTES), ("CRLF", CRLF_BYTES)):
                rows.append(run_case(tmp_path, autocrlf, attr_name, content_name, content))
    keys = list(rows[0])
    print("\n[E2] " + " | ".join(keys))
    for r in rows:
        print("[E2] " + " | ".join(str(r[k]) for k in keys))
    assert len(rows) == len(AUTOCRLF) * len(ATTRS) * 2


def test_e2x_cross_config(tmp_path):
    # 해시를 기록한 PC(autocrlf=true)와 다시 구하는 환경의 설정이 다를 때(autocrlf=false·input)를 흉내 낸다.
    # 기록 쪽: LF로 쓴 파일의 no-index 해시. 재계산 쪽: autocrlf=true로 복제한 작업 트리(CRLF)에서 설정만 바꿔 계산
    print("\n[E2x] attr | 기록 해시 | 재계산 autocrlf | 작업 트리 | 재계산 해시 | 같음")
    for attr_name in ATTRS:
        a = make_repo(tmp_path / f"x_{len(attr_name)}_{attr_name.replace(' ', '_').replace('=', '-')}",
                      "true", ATTRS[attr_name])
        (a / TEST_REL).write_bytes(LF_BYTES)
        h_rec, _ = no_index_hash(a, TEST_REL)
        git(["add", TEST_REL], a)
        git(["commit", "-q", "-m", "test"], a)
        b = a.parent / (a.name + "_clone")
        git(["clone", "-q", "-c", "core.autocrlf=true", str(a), str(b)], a.parent)
        for other in ("false", "input"):
            git(["config", "core.autocrlf", other], b)
            h_re, _ = no_index_hash(b, TEST_REL)
            print(f"[E2x] {attr_name} | {h_rec[:12]} | {other} | {eol_of(b / TEST_REL)} | {h_re[:12]} | {h_rec == h_re}")


def test_e2n_add_default_rule_to_existing(tmp_path):
    # 이미 autocrlf=true로 받아 작업 트리가 CRLF인 저장소에 기본 규칙을 더했을 때 변경으로 잡히는지
    print("\n[E2n] 더한 규칙 | 규칙만 더한 뒤 status | add --renormalize 뒤 status(규칙 파일 제외)")
    for attr_name in ("text=auto", "text=auto eol=lf"):
        a = make_repo(tmp_path / f"n_{attr_name.replace(' ', '_').replace('=', '-')}", "true", None)
        (a / "doc.md").write_bytes(b"line1\nline2\n")
        (a / "tool.cmd").write_bytes(b"@echo off\r\necho hi\r\n")
        (a / "hook").write_bytes(b"#!/bin/sh\nexit 0\n")
        (a / ".gitattributes").write_bytes(b"*.cmd text eol=crlf\nhook text eol=lf\n")
        git(["add", "."], a)
        git(["commit", "-q", "-m", "base"], a)
        b = a.parent / (a.name + "_clone")
        git(["clone", "-q", "-c", "core.autocrlf=true", str(a), str(b)], a.parent)
        attrs = b"* " + ATTRS[attr_name][2:] + b"*.cmd text eol=crlf\nhook text eol=lf\n"
        (b / ".gitattributes").write_bytes(attrs)
        st1 = git(["status", "--porcelain"], b).stdout.decode().strip().replace("\n", ", ")
        git(["add", "--renormalize", "."], b)
        st2 = git(["status", "--porcelain"], b).stdout.decode().strip().replace("\n", ", ")
        print(f"[E2n] {attr_name} | {st1} | {st2}")


def test_e2r_repo_eol_state():
    # 이 저장소에 대한 읽기 전용 조회만 한다
    for key in ("core.autocrlf", "core.eol", "core.safecrlf"):
        r = git(["config", "--get", key], REPO, check=False)
        origin = git(["config", "--show-origin", "--get", key], REPO, check=False)
        print(f"\n[E2r] {key} = {r.stdout.decode().strip() or '(설정 없음)'} "
              f"origin={origin.stdout.decode().strip().split(chr(9))[0] or '-'}")
    out = git(["ls-files", "--eol"], REPO).stdout.decode("utf-8", "replace").splitlines()
    counts = {}
    crlf_index = []
    for line in out:
        parts = line.split(None, 3)
        i_eol, w_eol = parts[0], parts[1]
        counts[(i_eol, w_eol)] = counts.get((i_eol, w_eol), 0) + 1
        if i_eol in ("i/crlf", "i/mixed"):
            crlf_index.append(line.split("\t")[-1])
    print(f"[E2r] 추적 파일 {len(out)}개")
    for k in sorted(counts):
        print(f"[E2r] {k[0]:8} {k[1]:8} {counts[k]}")
    print(f"[E2r] index가 CRLF·mixed인 파일 {len(crlf_index)}개")
    for p in crlf_index:
        print(f"[E2r]   {p}")
    # 커밋된 인수 시험 파일: index blob 해시와 작업 트리 기준 no-index 해시 비교
    staged = git(["ls-files", "-s", "--", "Departments/Quality/assets/acceptance"], REPO).stdout.decode(
        "utf-8", "replace").splitlines()
    same = diff = 0
    diffs = []
    for line in staged:
        meta, path = line.split("\t", 1)
        blob = meta.split()[1]
        if not path.endswith(".py"):
            continue
        h, _ = no_index_hash(REPO, path)
        if h == blob:
            same += 1
        else:
            diff += 1
            diffs.append(path)
    print(f"[E2r] 추적 중인 인수 시험 .py: index blob 해시 = no-index 해시 {same}개, 다름 {diff}개")
    for p in diffs:
        print(f"[E2r]   다름: {p}")
    assert out


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.exists() else "(없음)"


def test_e3_trust_readonly():
    home = pathlib.Path.home()
    cfg = home / ".claude.json"
    print(f"\n[E3] 사용자 상태 파일 존재: {cfg.exists()}")
    if cfg.exists():
        before = sha256(cfg)
        with cfg.open("r", encoding="utf-8") as f:  # 읽기 모드로만 연다
            data = json.load(f)
        after = sha256(cfg)
        print(f"[E3] 읽기 전후 sha256 앞 16자리: {before} / {after} (같음={before == after})")
        projects = data.get("projects", {})
        print(f"[E3] projects 항목 수: {len(projects)}")
        want = str(REPO).replace("\\", "/").lower()
        hits = [k for k in projects if k.replace("\\", "/").lower() == want]
        print(f"[E3] 이 저장소 경로와 맞는 항목 키: {hits}")
        for k in hits:
            entry = projects[k]
            print(f"[E3]   hasTrustDialogAccepted = {entry.get('hasTrustDialogAccepted', '(키 없음)')}")
            print(f"[E3]   항목 키 이름: {sorted(entry)}")
        sibling = [k for k in projects if "vibe standard" in k.lower()]
        for k in sibling:
            print(f"[E3]   유사 경로 {k}: hasTrustDialogAccepted="
                  f"{projects[k].get('hasTrustDialogAccepted', '(키 없음)')}")
    for p in (REPO / ".claude" / "settings.local.json", home / ".claude" / "settings.json",
              home / ".claude" / "settings.local.json"):
        line = f"[E3] {p}: 존재={p.exists()}"
        if p.exists():
            with p.open("r", encoding="utf-8") as f:
                s = json.load(f)
            perms = s.get("permissions", {})
            line += f" 최상위 키={sorted(s)} permissions 키별 개수=" + str(
                {k: (len(v) if isinstance(v, list) else type(v).__name__) for k, v in perms.items()})
        print(line)
    hooks = git(["config", "--get", "core.hooksPath"], REPO, check=False)
    print(f"[E3] core.hooksPath = {hooks.stdout.decode().strip() or '(설정 없음)'} (종료 코드 {hooks.returncode})")
