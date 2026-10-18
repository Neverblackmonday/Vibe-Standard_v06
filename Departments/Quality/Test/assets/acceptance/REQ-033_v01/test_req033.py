# -*- coding: utf-8 -*-
"""REQ-033 인수 시험: 프로세스 맵, 모델 매트릭스와 CEO 설정 규칙, 작업 큐.

작성 기준은 Workflow/03_라이프사이클 「시험실」, 절차서는 Departments/Quality/Test/results/ACC-033_v01.md다.

- 시험은 저장소 파일을 만들거나 고치지 않는다. 임시 파일과 시험 저장소는 모두 pytest tmp_path 아래에 만든다.
- 「적용본」은 설계·개발 적용본 폴더(REQ-033_적용본_vNN)의 가장 높은 버전이며, 「현행 거버넌스 파일」은
  Workflow/·.claude/·스크립트 폴더에서 적용본이 있는 파일은 적용본, 없는 파일은 원본이다(REQ-033_v04 5절 머리 안내).
- 「반영 뒤 상태」는 이 저장소를 tmp 아래로 복제하고, 적용본(설계 → 개발 순서)을 원본 경로에 덮어 쓴 복제본이다.
  유효 값 계산(resolve_model.py)은 저장소의 Workflow/data/를 읽으므로 반영 뒤 상태에서만 실행할 수 있다.
- 기대값(시험용 맵의 결함, 모델 매트릭스 칸의 규칙, 유효 값)은 승인된 EC-033_v02 3.3~3.6절과 설계 적용본
  04 1.1~1.4절에서 옮긴 것이며, 개발부 스크립트의 구현과 독립된 기대값으로 쓴다.
"""

import copy
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------- 기본값

SCRIPTS = "Departments/Development/Implementation/assets/scripts"
GOV_PREFIXES = ("Workflow/", ".claude/", SCRIPTS + "/")
INBOX = "Departments/Secretariat/Secretary/assets/inbox"
CLASSES = ("Critical", "Major", "Minor")
NO_CLASS = "분류 없음"
NA = "해당 없음"
MODEL_VALUES = {"고급", "중급", "중급(시범)", "제한 없음", "활성 때 정함", NA}
EFFORT_VALUES = {"low", "medium", "high", "xhigh", "max", "정하지 않음", NA}
EFFORT_MEANS = {"호출 인자", "실행 단위", "정하지 않음"}
SAVED_AT = "2026-10-20T09:00:00+09:00"
CONFIRMED_AT = "2026-10-20T09:05:00+09:00"


# ---------------------------------------------------------------- 실행 도구

def _env():
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        env.pop(key, None)
    env.update({
        "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "acc-test", "GIT_AUTHOR_EMAIL": "acc-test@example.invalid",
        "GIT_COMMITTER_NAME": "acc-test", "GIT_COMMITTER_EMAIL": "acc-test@example.invalid",
    })
    return env


def run(args, cwd, timeout=900):
    res = subprocess.run([str(a) for a in args], cwd=str(cwd), capture_output=True, env=_env(), timeout=timeout)
    return res.returncode, (res.stdout + res.stderr).decode("utf-8", "replace")


def git_ok(cwd, *args):
    code, out = run(["git", "-c", "core.quotepath=false", *args], cwd)
    assert code == 0, f"git {' '.join(map(str, args))} 실패(종료 코드 {code}):\n{out}"
    return out


def git_z(cwd, *args):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(cwd), capture_output=True, env=_env())
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    return [p for p in res.stdout.decode("utf-8").split("\0") if p]


def py(script, *args, cwd):
    # -B: 적용본 폴더 안에 __pycache__를 만들지 않는다. -I는 스크립트 폴더를 sys.path에서 빼 check_standard 가져오기를 막으므로 쓰지 않는다
    return run([sys.executable, "-B", script, *args], cwd)


def tail(text, n=60):
    return "\n".join(text.splitlines()[-n:])


def _toplevel():
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(Path(__file__).resolve().parent),
                         capture_output=True, env=_env())
    assert res.returncode == 0, "저장소 루트를 찾을 수 없습니다"
    return Path(res.stdout.decode("utf-8").strip())


REPO = _toplevel()


# ---------------------------------------------------------------- 적용본 찾기

def _highest(folder, pattern):
    folder = REPO / folder
    best = None
    if folder.is_dir():
        for p in folder.iterdir():
            m = re.fullmatch(pattern, p.name)
            if m and p.is_dir() and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), p)
    return best[1] if best else None


def design_dir(config):
    opt = config.getoption("--acc-design-dir")
    if opt:
        return (REPO / opt).resolve()
    return _highest("Departments/Design/Spec/workspace", r"REQ-033_적용본_v(\d{2})")


def dev_dir(config):
    opt = config.getoption("--acc-dev-dir")
    if opt:
        return (REPO / opt).resolve()
    return _highest("Departments/Development/Implementation/workspace", r"REQ-033_적용본_v(\d{2})")


def design_wf(config):
    d = design_dir(config)
    assert d is not None, "설계 적용본 폴더(REQ-033_적용본_vNN)가 없습니다(명세 단계 산출물)"
    p = d / "Workflow.적용본"
    assert p.is_dir(), f"설계 적용본에 Workflow.적용본/이 없습니다: {p}"
    return p


def dev_scripts(config):
    d = dev_dir(config)
    assert d is not None, "개발 적용본 폴더(REQ-033_적용본_vNN)가 없습니다(구현 단계 산출물)"
    p = d / (SCRIPTS + ".적용본")
    assert p.is_dir(), f"개발 적용본에 스크립트 폴더가 없습니다: {p}"
    return p


def dev_script(config, name):
    p = dev_scripts(config) / name
    assert p.is_file(), f"개발 적용본에 {name}이 없습니다: {p}"
    return p


def applied_files(base):
    """적용본 폴더의 파일을 (원본 경로, 적용본 파일)로 돌려준다. 첫 「.적용본」 경로 조각에서 접미어를 뗀다."""
    out = []
    if base is None:
        return out
    for p in sorted(base.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts:
            continue
        parts = list(p.relative_to(base).parts)
        for i, part in enumerate(parts):
            if part.endswith(".적용본"):
                parts[i] = part[: -len(".적용본")]
                break
        else:
            continue
        out.append(("/".join(parts), p))
    return out


def current_gov(config):
    """현행 거버넌스 파일: {원본 경로: 읽을 파일}. 개발 적용본이 설계 적용본보다, 적용본이 원본보다 앞선다."""
    files = {rel: REPO / rel for rel in git_z(REPO, "ls-files", "-z", "--", *[p.rstrip("/") for p in GOV_PREFIXES])}
    originals = set(files)
    for base in (design_dir(config), dev_dir(config)):
        for rel, p in applied_files(base):
            if rel.startswith(GOV_PREFIXES):
                files[rel] = p
    return files, originals


# ---------------------------------------------------------------- 문서 읽기

def heading_section(text, keyword):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and keyword in m.group(2):
            level = len(m.group(1))
            out = [line]
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6}) ", nxt)
                if h and len(h.group(1)) <= level:
                    break
                out.append(nxt)
            return "\n".join(out)
    return ""


def table_rows(sec):
    rows = []
    for line in sec.splitlines():
        s = line.strip()
        if not s.startswith("|") or re.fullmatch(r"\|[\s:|-]+\|", s):
            continue
        rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def glossary_rows(config):
    files, _ = current_gov(config)
    text = files["Workflow/01_표준_개요.md"].read_text(encoding="utf-8")
    sec = heading_section(text, "용어")
    assert sec, "01 「용어」 절이 없습니다"
    return {r[0]: r for r in table_rows(sec)[1:]}


def org_table(wf_dir):
    text = (wf_dir / "02_부서_구조_및_작업구역.md").read_text(encoding="utf-8")
    sec = heading_section(text, "조직 표")
    rows = table_rows(sec)
    head = rows[0]
    ci, si = head.index("코드"), head.index("상태")
    return {r[ci]: r[si] for r in rows[1:]}


def model_ids(wf_dir):
    """04 1.1절 표의 등급 → 기본 모델 ID."""
    text = (wf_dir / "04_모델_운용.md").read_text(encoding="utf-8")
    sec = heading_section(text, "모델 등급과 기본 모델")
    ids = {}
    for r in table_rows(sec)[1:]:
        m = re.search(r"`([^`]+)`", r[-1])
        if m:
            ids[r[0]] = m.group(1)
    assert "고급" in ids and "중급" in ids, f"04 1.1절 표에서 기본 모델 ID를 읽지 못했습니다: {ids}"
    return ids


def scan_lines(rel, path):
    """옛 용어 확인 대상 줄(개정 이력 표와 01 「용어」 표의 「쓰지 않는 말」 칸 제외)."""
    data = path.read_bytes()
    if b"\0" in data:
        return []
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    out = []
    in_glossary = False
    for no, line in enumerate(text.splitlines(), 1):
        if rel.endswith(".md") and re.match(r"^#{1,6} .*개정 이력", line):
            break
        if rel == "Workflow/01_표준_개요.md":
            h = re.match(r"^(#{1,6}) (.*)$", line)
            if h:
                in_glossary = "용어" in h.group(2) and len(h.group(1)) == 2
            if in_glossary and line.strip().startswith("|"):
                line = line.strip().rstrip("|").rsplit("|", 1)[0]
        out.append((no, line))
    return out


def old_term_hits(config, pattern, allow=None):
    files, _ = current_gov(config)
    hits = []
    for rel in sorted(files):
        for no, line in scan_lines(rel, files[rel]):
            for m in re.finditer(pattern, line):
                if allow and allow(line, m):
                    continue
                hits.append(f"{rel}:{no}: {line.strip()[:160]}")
    return hits


def new_file_names(config):
    _, originals = current_gov(config)
    names = []
    for base in (design_dir(config), dev_dir(config)):
        for rel, _ in applied_files(base):
            if rel not in originals:
                names.append(rel)
    return names


# ---------------------------------------------------------------- 프로세스 맵·모델 매트릭스

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def broken_link(pm):
    """시작 단계가 아니고 앞 단계가 있는 단계 하나를 골라 그 단계로 들어오는 next를 모두 지운다."""
    pm = copy.deepcopy(pm)
    starts = {s for t in pm["tracks"] for s in t["starts"]}
    incoming = {}
    for st in pm["steps"]:
        for n in st.get("next", []):
            incoming.setdefault(n, []).append(st["id"])
    target = next(st["id"] for st in pm["steps"] if st["id"] not in starts and incoming.get(st["id"]))
    for st in pm["steps"]:
        if target in st.get("next", []):
            st["next"] = [n for n in st["next"] if n != target]
            if not st["next"]:
                st["end"] = True
    return pm, target


def removed_part(pm, part="Q07", replacement="Q01"):
    """활성 파트 하나를 모든 단계의 parts에서 다른 파트로 바꿔 그 파트가 어느 단계에도 없게 한다."""
    pm = copy.deepcopy(pm)
    found = False
    for st in pm["steps"]:
        if part in st.get("parts", []):
            found = True
            st["parts"] = [replacement if p == part else p for p in st["parts"]]
    assert found, f"설계 적용본 프로세스 맵에 {part}가 없습니다"
    return pm


def class_sets(pm):
    sets = {}
    for st in pm["steps"]:
        for part in st.get("parts", []):
            sets.setdefault((part, st.get("role")), set()).update(st.get("classes", []))
    return sets


def mutated_wf(config, tmp_path, pm=None, mm=None):
    """설계 적용본 Workflow를 tmp로 복사하고 데이터 파일 하나를 바꾼다(--workflow-dir 시험용)."""
    dst = tmp_path / "wf"
    shutil.copytree(design_wf(config), dst)
    if pm is not None:
        write_json(dst / "data" / "process_map.json", pm)
    if mm is not None:
        write_json(dst / "data" / "model_matrix.json", mm)
    return dst


def check_map(config, wf_dir):
    return py(dev_script(config, "check_process_map.py"), "--workflow-dir", wf_dir, cwd=REPO)


# ---------------------------------------------------------------- 반영 뒤 상태(복제본)

@pytest.fixture(scope="session")
def reflected(request, tmp_path_factory):
    """이 저장소의 복제본에 적용본(설계 → 개발)을 원본 경로로 덮어 쓰고 커밋한 상태.

    비서팀·PM팀의 미추적 기록(승인된 REQ-033_v04와 그 승인 기록 등)을 함께 복사해, 복제본에서 Workflow/ 변경이
    승인된 REQ의 scope 안에 들게 한다. 그 밖의 미추적 파일은 복사하지 않는다(커밋 전 검사의 다른 순서가
    이 시험과 관계없는 파일로 달라지지 않게 하기 위해서다).
    """
    config = request.config
    dev_scripts(config)  # 개발 적용본이 없으면 여기서 실패한다(구현 전)
    root = tmp_path_factory.mktemp("reflected")
    repo = root / "repo"
    git_ok(root, "clone", "-q", "--no-hardlinks", str(REPO), str(repo))
    for rel in git_z(REPO, "ls-files", "--others", "--exclude-standard", "-z", "--", "Departments/Secretariat"):
        dst = repo / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, dst)
    for base in (design_dir(config), dev_dir(config)):
        for rel, p in applied_files(base):
            dst = repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst)
    hooks = root / "nohooks"
    hooks.mkdir()
    git_ok(repo, "add", "-A")
    git_ok(repo, "-c", f"core.hooksPath={hooks}", "commit", "-q", "-m", "acc: reflected base")
    return repo


# ================================================================ 체크리스트 4

def test_c4_3_current_map_no_errors(request):
    """4 ③: 연결·누락 검사를 현행(설계 적용본) 프로세스 맵에 실행하면 오류 0건."""
    code, out = check_map(request.config, design_wf(request.config))
    assert code == 0, f"현행 프로세스 맵에서 종료 코드 {code}:\n{tail(out)}"
    assert "[PASS]" in out and "[FAIL]" not in out, tail(out)


def test_c4_3_broken_link_detected(request, tmp_path):
    """4 ③: 단계 하나의 연결을 끊은 시험용 프로세스 맵에서 P2 오류."""
    pm, target = broken_link(load_json(design_wf(request.config) / "data" / "process_map.json"))
    code, out = check_map(request.config, mutated_wf(request.config, tmp_path, pm=pm))
    assert code == 1, f"끊은 맵({target})에서 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert any(line.startswith("[FAIL] P2") for line in out.splitlines()), tail(out)


def test_c4_3_missing_active_part_detected(request, tmp_path):
    """4 ③: 활성 파트 하나(Q07)를 뺀 시험용 프로세스 맵에서 P4 누락 오류."""
    assert org_table(design_wf(request.config)).get("Q07") == "활성", "Q07이 02 조직 표의 활성 파트가 아닙니다"
    pm = removed_part(load_json(design_wf(request.config) / "data" / "process_map.json"))
    code, out = check_map(request.config, mutated_wf(request.config, tmp_path, pm=pm))
    assert code == 1, f"파트를 뺀 맵에서 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert any(line.startswith("[FAIL] P4") and "Q07" in line for line in out.splitlines()), tail(out)


@pytest.mark.parametrize("case", ["broken_link", "removed_part"])
def test_c4_3_staged_warn_not_blocking(reflected, case):
    """4 ③(D5 대안 (가)): 끊긴 맵을 스테이징한 커밋 전 검사가 [WARN]과 오류 건수를 출력하고,
    종료 코드는 정상 맵을 스테이징했을 때와 같다(그 검사 때문에 실패하지 않음)."""
    rel = "Workflow/data/process_map.json"
    target = reflected / rel
    original = target.read_bytes()
    pm = json.loads(original.decode("utf-8"))
    checker = f"{SCRIPTS}/check_standard.py"
    results = {}
    try:
        for kind in ("valid", case):
            if kind == "valid":
                obj = pm  # 내용은 같고 들여쓰기만 다른 정상 맵
                text = json.dumps(obj, ensure_ascii=False, indent=1) + "\n"
            else:
                obj = broken_link(pm)[0] if case == "broken_link" else removed_part(pm)
                text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
            target.write_text(text, encoding="utf-8", newline="\n")
            git_ok(reflected, "add", "--", rel)
            results[kind] = py(checker, "--staged", cwd=reflected)
            git_ok(reflected, "reset", "-q", "--", rel)
            target.write_bytes(original)
    finally:
        target.write_bytes(original)
    v_code, v_out = results["valid"]
    b_code, b_out = results[case]
    assert not re.search(r"프로세스 맵 검사 오류 [1-9]\d*건", v_out), f"정상 맵에서 오류 건수 출력:\n{tail(v_out)}"
    m = re.search(r"프로세스 맵 검사 오류 (\d+)건\(커밋을 막지 않음", b_out)
    assert m and int(m.group(1)) >= 1, f"끊긴 맵에서 오류 건수 줄이 없습니다:\n{tail(b_out)}"
    rule = "P2" if case == "broken_link" else "P4"
    assert any(line.startswith("[WARN]") and rule in line for line in b_out.splitlines()), tail(b_out)
    assert not any(re.match(r"^\[FAIL\] P[1-6]\b", line) for line in b_out.splitlines()), \
        f"프로세스 맵 오류가 [FAIL]로 출력되었습니다:\n{tail(b_out)}"
    assert b_code == v_code, (f"끊긴 맵의 종료 코드 {b_code}가 정상 맵의 {v_code}와 다릅니다"
                              f"\n--- 정상\n{tail(v_out, 30)}\n--- 끊김\n{tail(b_out, 30)}")


def test_c4_6_glossary_and_old_term(request):
    """4 ⑥: 「프로세스 맵」 행과 그 「쓰지 않는 말」의 「공정 지도」, 옛 용어 확인 대상에 「공정 지도」 없음."""
    rows = glossary_rows(request.config)
    assert "프로세스 맵" in rows, "01 「용어」 표에 「프로세스 맵」 행이 없습니다"
    assert "공정 지도" in rows["프로세스 맵"][-1], rows["프로세스 맵"]
    hits = old_term_hits(request.config, r"공정\s*지도")
    assert not hits, "옛 용어 「공정 지도」:\n" + "\n".join(hits)
    bad = [n for n in new_file_names(request.config) if re.search(r"공정|지도|원장|대장|대표님", n)]
    assert not bad, f"새 파일 이름의 옛 용어: {bad}"


# ================================================================ 체크리스트 8

def test_c8_1_matrix_cells_match_process_map(request):
    """8 ①: 모델 매트릭스 칸이 프로세스 맵의 (파트, 역할)·분류 집합과 같다(시험이 직접 대조한 기대값)."""
    wf = design_wf(request.config)
    text04 = (wf / "04_모델_운용.md").read_text(encoding="utf-8")
    assert "Workflow/data/model_matrix.json" in heading_section(text04, "단계별 모델"), "04 1.2절이 모델 매트릭스를 가리키지 않습니다"
    pm = load_json(wf / "data" / "process_map.json")
    mm = load_json(wf / "data" / "model_matrix.json")
    sets = class_sets(pm)
    cells = {(c["part"], c["role"]): c for c in mm["cells"]}
    assert len(cells) == len(mm["cells"]), "모델 매트릭스에 겹친 칸이 있습니다"
    assert set(cells) == set(sets), (f"빠진 칸 {sorted(set(sets) - set(cells))}, "
                                     f"남는 칸 {sorted(set(cells) - set(sets))}")
    active = {c for c, s in org_table(wf).items() if s == "활성"}
    assert active <= {p for p, _ in cells}, f"칸이 없는 활성 파트: {sorted(active - {p for p, _ in cells})}"
    problems = []
    for key, cell in cells.items():
        cs = sets[key]
        if cell.get("effort_means") not in EFFORT_MEANS:
            problems.append(f"{key} effort_means {cell.get('effort_means')}")
        if (NO_CLASS in cell) != (NO_CLASS in cs):
            problems.append(f"{key} 「분류 없음」 키 {'있음' if NO_CLASS in cell else '없음'}, 분류 집합 {sorted(cs)}")
        for cls in CLASSES + ((NO_CLASS,) if NO_CLASS in cell else ()):
            val = cell.get(cls)
            if not isinstance(val, dict):
                problems.append(f"{key} {cls} 키 없음")
                continue
            if val.get("model") not in MODEL_VALUES or val.get("effort") not in EFFORT_VALUES:
                problems.append(f"{key} {cls} 허용 밖 값 {val}")
            na = val.get("model") == NA and val.get("effort") == NA
            if cls in cs and (val.get("model") == NA or val.get("effort") == NA):
                problems.append(f"{key} {cls}: 실행되는 분류인데 「해당 없음」")
            if cls not in cs and not na:
                problems.append(f"{key} {cls}: 실행되지 않는 분류인데 값 {val}")
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("case", ["cell_removed", "na_violated", "no_class_key_added"])
def test_c8_1_checker_detects_matrix_mismatch(request, tmp_path, case):
    """8 ①: 프로세스 맵과 모델 매트릭스를 대조하는 검사(P6)가 칸 결함을 오류로 낸다."""
    wf = design_wf(request.config)
    mm = load_json(wf / "data" / "model_matrix.json")
    if case == "cell_removed":
        mm["cells"] = [c for c in mm["cells"] if c["part"] != "Q07"]
    elif case == "na_violated":
        cell = next(c for c in mm["cells"] if c["part"] == "Q03")
        assert cell["Minor"]["model"] == NA, "Q03 Minor가 「해당 없음」이 아닙니다(EC 3.5절 3번 표)"
        cell["Minor"] = {"model": "고급", "effort": "medium"}
    else:
        cell = next(c for c in mm["cells"] if c["part"] == "P01")
        assert NO_CLASS not in cell
        cell[NO_CLASS] = {"model": "고급", "effort": "medium"}
    code, out = check_map(request.config, mutated_wf(request.config, tmp_path, mm=mm))
    assert code == 1, f"{case}에서 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert any(line.startswith("[FAIL] P6") for line in out.splitlines()), tail(out)


def _settings(tmp_path, cells, saved_at=SAVED_AT, raw=None):
    p = tmp_path / "model_settings.json"
    if raw is not None:
        p.write_text(raw, encoding="utf-8")
    else:
        p.write_text(json.dumps({"saved_at": saved_at, "cells": cells}, ensure_ascii=False), encoding="utf-8")
    return p


def resolve(reflected, *args, settings):
    return py(f"{SCRIPTS}/resolve_model.py", *args, "--settings", settings, cwd=reflected)


def has_line(out, part, role, cls, grade, mid, effort, source, confirmed=None):
    pat = (rf"^\[INFO\] {re.escape(part)} {re.escape(role)} {re.escape(cls)} 모델 {re.escape(grade)} "
           rf"{re.escape(mid)} effort {re.escape(effort)} 출처 {re.escape(source)}(?=\s|$)(.*)$")
    m = re.search(pat, out, re.M)
    if not m:
        return False
    return confirmed is None or f"하향 확인 {confirmed}" in m.group(1)


# (이름, 인자, CEO 설정 칸(None이면 파일 없음), 기대 종료 코드, 기대 줄 목록)
# 기대 줄: (파트, 역할, 분류, 등급, 등급 이름(모델 ID로 바꿈), effort, 출처, 하향 확인 시각)
RESOLVE_CASES = [
    ("no_settings", ["--class", "Critical", "--part", "Q05"], None, 0,
     [("Q05", "판정", "Critical", "고급", "고급", "medium", "기본값", None)]),
    ("empty_cells", ["--class", "Major", "--part", "E02"], [], 0,
     [("E02", "작성", "Major", "고급", "고급", "medium", "기본값", None)]),  # 「중급(시범)」은 시범 전 고급
    ("override_model_effort", ["--class", "Major", "--part", "E01"],
     [{"part": "E01", "role": "작성", "class": "Major", "model": "중급", "effort": "high"}], 0,
     [("E01", "작성", "Major", "중급", "중급", "high", "CEO 설정", None)]),
    ("override_effort_only", ["--class", "Minor", "--part", "V01"],
     [{"part": "V01", "role": "작성", "class": "Minor", "effort": "low"}], 0,
     [("V01", "작성", "Minor", "중급", "중급", "low", "CEO 설정", None)]),
    ("other_cell_untouched", ["--class", "Major", "--part", "V01"],
     [{"part": "E01", "role": "작성", "class": "Major", "model": "중급"}], 0,
     [("V01", "작성", "Major", "고급", "고급", "medium", "기본값", None)]),
    ("judge_downgrade_unconfirmed", ["--class", "Major", "--part", "Q05"],
     [{"part": "Q05", "role": "판정", "class": "Major", "model": "중급"}], 1, []),
    ("critical_downgrade_unconfirmed", ["--class", "Critical", "--part", "E01"],
     [{"part": "E01", "role": "작성", "class": "Critical", "model": "중급"}], 1, []),
    ("downgrade_bad_time", ["--class", "Major", "--part", "Q05"],
     [{"part": "Q05", "role": "판정", "class": "Major", "model": "중급", "downgrade_confirmed_at": "어제"}], 1, []),
    ("downgrade_confirmed", ["--class", "Major", "--part", "Q05"],
     [{"part": "Q05", "role": "판정", "class": "Major", "model": "중급", "downgrade_confirmed_at": CONFIRMED_AT}], 0,
     [("Q05", "판정", "Major", "중급", "중급", "medium", "CEO 설정", CONFIRMED_AT)]),
    ("top_without_model_id", ["--class", "Major", "--part", "E01"],
     [{"part": "E01", "role": "작성", "class": "Major", "model": "최고급"}], 1, []),
    ("unknown_part", ["--class", "Major"],
     [{"part": "Z99", "role": "작성", "class": "Major", "model": "고급"}], 1, []),
    ("bad_value", ["--class", "Major"],
     [{"part": "E01", "role": "작성", "class": "Major", "effort": "huge"}], 1, []),
    ("escalated_default", ["--class", "Minor", "--escalated", "--part", "P02"], None, 0,
     [("P02", "기록", "Minor", "고급", "고급", "medium", "격상", None)]),
    ("escalated_over_ceo", ["--class", "Minor", "--escalated", "--part", "E01"],
     [{"part": "E01", "role": "작성", "class": "Minor", "model": "중급"}], 0,
     [("E01", "작성", "Minor", "고급", "고급", "medium", "격상", None)]),
    ("active_later_major", ["--class", "Major", "--part", "O01"], None, 0,
     [("O01", "작성", "Major", "고급", "고급", "medium", "기본값", None)]),
    ("active_later_minor", ["--class", "Minor", "--part", "O01"], None, 0,
     [("O01", "작성", "Minor", "중급", "중급", "medium", "기본값", None)]),
    ("approved_effort_high", ["--class", "Critical", "--approved-effort", "high"], None, 0,
     [("Q05", "판정", "Critical", "고급", "고급", "high", "REQ 결정", None),
      ("E01", "작성", "Critical", "고급", "고급", "high", "REQ 결정", None),
      ("P01", "작성", "Critical", "고급", "고급", "medium", "기본값", None)]),
    ("approved_effort_low", ["--class", "Critical", "--approved-effort", "low"], None, 0,
     [("Q05", "판정", "Critical", "고급", "고급", "medium", "기본값", None),
      ("E01", "작성", "Critical", "고급", "고급", "low", "REQ 결정", None)]),
]


@pytest.mark.parametrize("name,args,cells,exp_code,lines", RESOLVE_CASES, ids=[c[0] for c in RESOLVE_CASES])
def test_c8_3_resolve_model(request, reflected, tmp_path, name, args, cells, exp_code, lines):
    """8 ③: CEO 설정 파일(시험용)과 모델 매트릭스를 합친 유효 값이 04 1.2·1.4절의 규칙대로 나온다."""
    ids = model_ids(design_wf(request.config))
    settings = tmp_path / "absent.json" if cells is None else _settings(tmp_path, cells)
    code, out = resolve(reflected, *args, settings=settings)
    assert code == exp_code, f"{name}: 종료 코드 {code}(기대 {exp_code}):\n{tail(out)}"
    first = next((l for l in out.splitlines() if l.strip()), "")
    if code == 0:
        assert ("없음(기본값)" in first) if cells is None else (SAVED_AT in first), f"첫 줄: {first}"
    for part, role, cls, grade, id_grade, effort, source, confirmed in lines:
        assert has_line(out, part, role, cls, grade, ids[id_grade], effort, source, confirmed), \
            f"{name}: 기대 줄 [INFO] {part} {role} {cls} 모델 {grade} {ids[id_grade]} effort {effort} 출처 {source}" \
            f"{' 하향 확인 ' + confirmed if confirmed else ''}이 없습니다:\n{tail(out)}"


def test_c8_3_resolve_invalid_json(reflected, tmp_path):
    """8 ③: JSON으로 읽히지 않는 CEO 설정 파일은 실패(종료 코드 1)."""
    code, out = resolve(reflected, "--class", "Major", settings=_settings(tmp_path, None, raw="{ not json"))
    assert code == 1, f"종료 코드 {code}(기대 1):\n{tail(out)}"


@pytest.mark.parametrize("cell", [
    {"part": "S01", "role": "작성", "class": "Major", "model": "고급"},
    {"part": "Q03", "role": "판정", "class": "Minor", "model": "고급"},
], ids=["secretariat_cell", "na_cell"])
def test_c8_3_resolve_unusable_cell_warns(reflected, tmp_path, cell):
    """8 ③: 쓸 수 없는 칸(비서실 세션 파트, 「해당 없음」 칸)의 설정은 [WARN]을 내고 무시한다."""
    code, out = resolve(reflected, "--class", cell["class"], settings=_settings(tmp_path, [cell]))
    assert code == 0, f"종료 코드 {code}(기대 0):\n{tail(out)}"
    assert any(l.startswith("[WARN]") for l in out.splitlines()), tail(out)
    assert not re.search(rf"^\[INFO\] {cell['part']} .* 출처 CEO 설정", out, re.M), tail(out)


def test_c8_3_resolve_hotfix(request, reflected, tmp_path):
    """8 ③: --hotfix는 「분류 없음」 키가 있는 칸만 읽고 V03은 고급·medium."""
    ids = model_ids(design_wf(request.config))
    code, out = resolve(reflected, "--hotfix", settings=tmp_path / "absent.json")
    assert code == 0, f"종료 코드 {code}:\n{tail(out)}"
    assert has_line(out, "V03", "작성", NO_CLASS, "고급", ids["고급"], "medium", "기본값"), tail(out)
    assert re.search(r"^\[INFO\] S01 작성 분류 없음 모델 제한 없음", out, re.M), tail(out)
    for part in ("P01", "P02", "E01", "Q05", "S03"):
        assert not re.search(rf"^\[INFO\] {part} ", out, re.M), f"「분류 없음」 키가 없는 {part}가 출력되었습니다:\n{tail(out)}"


def test_c8_11_glossary_and_old_terms(request):
    """8 ⑪: 「모델 매트릭스」·「CEO 설정」 행과 「쓰지 않는 말」, 옛 용어 「모델·effort 원장」·「대표님 설정」 없음,
    「원장」은 근거 자료 안의 표 이름 「권고 원장」을 부르는 곳뿐."""
    rows = glossary_rows(request.config)
    for term, words in (("모델 매트릭스", ("모델·effort 원장", "원장(모델 매트릭스를 가리킬 때)")),
                        ("CEO 설정", ("대표님 설정 파일", "대표님 설정(CEO 설정을 가리킬 때)"))):
        assert term in rows, f"01 「용어」 표에 「{term}」 행이 없습니다"
        missing = [w for w in words if w not in rows[term][-1]]
        assert not missing, f"「{term}」 행 「쓰지 않는 말」에 없는 말: {missing}"
    hits = old_term_hits(request.config, r"모델\s*·\s*effort\s*원장|대표님\s*설정")
    hits += old_term_hits(request.config, r"원장", allow=lambda line, m: line[max(0, m.start() - 3):m.start()] == "권고 ")
    assert not hits, "옛 용어:\n" + "\n".join(hits)


# ================================================================ 체크리스트 15

def test_c15_3_issued_orders_unchanged(request):
    """15 ③: 이미 발행된 ORDER 파일(inbox/ORD-*)이 이 REQ로 바뀌지 않았다(git diff, 적용본에 ORDER 사본 없음)."""
    out = git_ok(REPO, "diff", "--name-status", "HEAD", "--", f"{INBOX}/ORD-*")
    assert not out.strip(), f"발행된 ORDER 파일의 변경:\n{out}"
    out = git_ok(REPO, "diff", "--cached", "--name-status", "HEAD", "--", f"{INBOX}/ORD-*")
    assert not out.strip(), f"스테이징된 ORDER 파일의 변경:\n{out}"
    for base in (design_dir(request.config), dev_dir(request.config)):
        bad = [rel for rel, _ in applied_files(base) if rel.startswith(INBOX + "/ORD-")]
        assert not bad, f"적용본에 ORDER 파일 사본이 있습니다: {bad}"


def test_c15_8_glossary_and_old_term(request):
    """15 ⑧: 「작업 큐」 행과 「쓰지 않는 말」, 옛 용어 「처리 순서 대장」 없음."""
    rows = glossary_rows(request.config)
    assert "작업 큐" in rows, "01 「용어」 표에 「작업 큐」 행이 없습니다"
    missing = [w for w in ("처리 순서 대장", "대장(작업 큐를 가리킬 때)") if w not in rows["작업 큐"][-1]]
    assert not missing, f"「작업 큐」 행 「쓰지 않는 말」에 없는 말: {missing}"
    hits = old_term_hits(request.config, r"처리\s*순서\s*대장")
    assert not hits, "옛 용어 「처리 순서 대장」:\n" + "\n".join(hits)
