# -*- coding: utf-8 -*-
"""REQ-034 인수 시험: 계층형 지침, 전역 지침 처리, 형상통제, v04 규정 전수 이관.

작성 기준은 Workflow/03_라이프사이클 「시험실」, 절차서는 Departments/Quality/Test/results/ACC-034_v02.md다.

- 시험은 저장소 파일을 만들거나 고치지 않는다. 임시 파일, 시험용 적용본 사본, 시험 저장소는 모두 pytest tmp_path 아래에 만든다.
- 「설계 적용본」·「개발 적용본」은 명세팀·구현팀 workspace의 REQ-034_적용본_vNN 가운데 가장 높은 버전이다.
  「현행 거버넌스 파일」은 적용본이 있는 파일은 적용본(개발 적용본이 설계 적용본보다 앞섬), 없는 파일은 원본이다
  (REQ-034_v06 5절 머리 안내).
- 반영 전이므로 개발부 스크립트(check_config.py, build_guides.py, check_prejudge.py, apply_delta.py)는 개발 적용본에서
  실행하고, 두 적용본을 --overlay로 준다(EC-034_v02 3.19절). 커밋 전 검사(check_standard.py --staged)는 이 저장소를
  tmp 아래로 복제하고 적용본(설계 → 개발)을 원본 경로에 덮어 쓴 「반영 뒤 상태」에서 실행한다.
- 기대값(생성물의 구성, 출력 형식, 시험용 결함, 변경 파일 반영 결과)은 승인된 EC-034_v02와 설계 적용본
  Workflow/04 5절, 05 8.8절, 06 4.6·4.7절, 06 5절 2항에서 옮긴 것이며, 개발부 스크립트의 구현과 독립된 기대값으로 쓴다.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

# ---------------------------------------------------------------- 기본값

SCRIPTS = "Departments/Development/Implementation/assets/scripts"
GOV_PATHS = ("AGENTS.md", "CLAUDE.md", "Workflow", ".claude", SCRIPTS)
REQ_PATH = "Departments/Secretariat/PM/docs/requests/REQ-034_v06.md"
EC_PATH = "Departments/Design/EC/docs/EC-034_v02.md"
RPT_PATH = "Departments/Design/EC/results/RPT-034_v02.md"
DEV_WORKSPACE = "Departments/Development/Implementation/workspace"
SUBAGENT_PARTS = ("E01", "E02", "E03", "V01", "Q01", "Q02", "Q03", "Q05", "Q06", "Q07", "X01")
SESSION_PARTS = ("P01", "P02", "V03", "C01", "C02", "C03", "S01", "S02", "S03")  # D16 ①과 대안 (가)의 파트
DEPT_FOLDERS = {"비서실": "Secretariat", "설계부": "Design", "개발부": "Development",
                "품질보증부": "Quality", "운영부": "Operations", "마케팅부": "Marketing"}
SAFETY_NAMES = ("보안 및 불변 데이터 보호", "파일 삭제·덮어쓰기 전 사용자 승인",
                "Git 커밋 및 푸시는 명시적 요청 시에만 수행", "지침 문서 수정 전 사용자 승인")
GEN_MARKER = "<!-- 생성물: 손으로 고치지 않는다."
TAG_RE = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")  # Workflow/07 「개정 이력과 리비전 태그」 절차 2
SRC_RE = re.compile(r"^<!-- 원천: (.+?) -->\s*$")
REFS_TITLE = "필요할 때 읽는 문서"
# refs 목록은 이 낱말만을 제목으로 둔 제목 줄 아래에 있다. 원천 글자(04 「타깃 컨텍스트 규칙」·「계층형 지침」 등)에도
# 「필요할 때 읽는 문서」라는 언급이 있어, 낱말이 든 줄에서 멈추면 생성물 본문이 그 언급에서 잘린다(ACC-034_v02 6절).
REFS_HEAD_RE = re.compile(rf"^#{{1,6}}\s+{re.escape(REFS_TITLE)}\s*$")
OLD_PATH_SAMPLE = "Departments" + "/Quality/results/acc_old.md"  # 옛 경로(부서 폴더 바로 아래 공통 하위 폴더)


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


def fail_blocks(out):
    """[FAIL] 줄부터 다음 [로 시작하는 줄 앞까지를 한 덩어리로 돌려준다(원인·조치 줄 포함)."""
    blocks, cur = [], None
    for line in out.splitlines():
        if line.startswith("["):
            if cur is not None:
                blocks.append("\n".join(cur))
                cur = None
            if line.startswith("[FAIL]"):
                cur = [line]
        elif cur is not None:
            cur.append(line)
    if cur is not None:
        blocks.append("\n".join(cur))
    return blocks


def has_fail(out, label):
    pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(label)}(?![0-9])")
    return any(pat.search(b) for b in fail_blocks(out))


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
    return _highest("Departments/Design/Spec/workspace", r"REQ-034_적용본_v(\d{2})")


def dev_dir(config):
    opt = config.getoption("--acc-dev-dir")
    if opt:
        return (REPO / opt).resolve()
    return _highest(DEV_WORKSPACE, r"REQ-034_적용본_v(\d{2})")


def design_root(config):
    d = design_dir(config)
    assert d is not None and d.is_dir(), "설계 적용본 폴더(REQ-034_적용본_vNN)가 없습니다(명세 단계 산출물)"
    return d


def design_wf(config):
    p = design_root(config) / "Workflow.적용본"
    assert p.is_dir(), f"설계 적용본에 Workflow.적용본/이 없습니다: {p}"
    return p


def dev_root(config):
    d = dev_dir(config)
    assert d is not None and d.is_dir(), "개발 적용본 폴더(REQ-034_적용본_vNN)가 없습니다(구현 단계 산출물)"
    return d


def dev_script(config, name):
    p = dev_root(config) / (SCRIPTS + ".적용본") / name
    assert p.is_file(), f"개발 적용본에 {name}이 없습니다: {p}"
    return p


def gen_root(config):
    """개발 적용본의 생성물 위치(반영 뒤 .claude/)."""
    p = dev_root(config) / ".claude.적용본"
    assert (p / "guides").is_dir(), f"개발 적용본에 생성물(.claude.적용본/guides/)이 없습니다: {p}"
    return p


def applied_files(base):
    """적용본 폴더의 파일을 (원본 경로, 적용본 파일)로 돌려준다. 첫 「.적용본」 경로 조각에서 접미어를 뗀다."""
    out = []
    if base is None or not base.is_dir():
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
    files = {rel: REPO / rel for rel in git_z(REPO, "ls-files", "-z", "--", *GOV_PATHS)}
    for base in (design_dir(config), dev_dir(config)):
        for rel, p in applied_files(base):
            files[rel] = p
    return files


def overlay_args(config, dev=None, design=None):
    return ["--overlay", dev or dev_root(config), "--overlay", design or design_root(config)]


def copy_tree(src, dst):
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
    return dst


# ---------------------------------------------------------------- 문서 읽기

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def read(path):
    return Path(path).read_text(encoding="utf-8")


def write(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8", newline="\n")


def title_of(line):
    """제목 줄에서 #, 앞 번호, 리비전 태그를 뗀 글자."""
    m = re.match(r"^#{1,6}\s+(.*)$", line)
    t = TAG_RE.sub("", m.group(1)).strip()
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", t)


def headings(lines, max_level=4):
    """코드 울타리 밖의 제목 줄 (줄 번호, 단계, 제목 글자)."""
    out, fence = [], False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        m = re.match(r"^(#{1,6})\s", line)
        if m and not fence and len(m.group(1)) <= max_level:
            out.append((i, len(m.group(1)), title_of(line)))
    return out


def find_section(text, title):
    """제목이 title인 H2~H4 절의 (줄 목록, 제목 줄, 절 끝, 자신의 본문 끝). 없거나 둘 이상이면 None."""
    lines = text.splitlines()
    hs = headings(lines)
    found = [(i, lv) for i, lv, t in hs if t == title and lv >= 2]
    if len(found) != 1:
        return None
    start, level = found[0]
    end = next((i for i, lv, _ in hs if i > start and lv <= level), len(lines))
    own = next((i for i, lv, _ in hs if i > start), len(lines))
    return lines, start, end, min(own, end)


def item_titles(lines):
    """맨 앞 단계 항목의 표제(굵은 글자, 없으면 표시 기호 뒤 글자)."""
    out = []
    for line in lines:
        m = re.match(r"^(?:[-*+]|\d+\.)\s+(.*)$", line)
        if not m:
            continue
        b = re.match(r"^\*\*(.+?)\*\*", m.group(1))
        out.append(b.group(1) if b else m.group(1))
    return out


def row_firsts(lines):
    out = []
    for line in lines:
        s = line.strip()
        if s.startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", s):
            out.append(s.strip("|").split("|")[0].strip())
    return out


def source_exists(files, src):
    """대응표·선택자 원천(doc, section[, item|row])이 현행 거버넌스 파일에 있는지. 없으면 사유를 돌려준다."""
    doc = src.get("doc")
    if doc not in files:
        return f"문서 없음 {doc}"
    if "section" not in src:
        return None
    sec = find_section(read(files[doc]), src["section"])
    if sec is None:
        return f"절 없음 또는 같은 제목 둘 이상 {doc} 「{src['section']}」"
    lines, start, _end, own = sec
    body = lines[start + 1:own]
    if src.get("item") is not None:
        item = src["item"]
        if not any(t == item or t.startswith(item) for t in item_titles(body)):
            return f"항목 없음 {doc} 「{src['section']}」 항목 {item}"
    if src.get("row") is not None:
        if src["row"] not in row_firsts(body):
            return f"행 없음 {doc} 「{src['section']}」 행 {src['row']}"
    return None


def org_table(config):
    """02 「조직 표」: {코드: {부, 팀, 팀 폴더, 파트, 상태}}."""
    text = read(current_gov(config)["Workflow/02_부서_구조_및_작업구역.md"])
    sec = find_section(text, "조직 표")
    assert sec, "02 「조직 표」 절이 없습니다"
    lines, start, end, _ = sec
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[start + 1:end]
            if l.strip().startswith("|") and not re.fullmatch(r"\|[\s:|-]+\|", l.strip())]
    head = rows[0]
    out = {}
    for r in rows[1:]:
        d = dict(zip(head, r))
        out[d["코드"]] = {"부": d["부"], "팀": d["팀"], "팀 폴더": d["팀 폴더"].strip("`"), "파트": d["파트"],
                         "상태": d["상태"]}
    return out


def layers(config):
    return load_json(design_wf(config) / "data" / "guide_layers.json")


def migration_map(config):
    """설계 적용본의 전수 대응표. --acc-red를 주면 결함 사본 확인용 결함을 메모리 안에서 넣는다(파일은 바꾸지 않음)."""
    mm = load_json(design_wf(config) / "data" / "migration_map.json")
    if config.getoption("--acc-red"):
        mm["baseline_commit"] = "0" * 40
        mm["targets"] = mm["targets"][1:]
        row = next(r for r in mm["rows"] if r.get("action") == "이관" and isinstance(r.get("source"), dict))
        row["source"] = dict(row["source"], section="없는 절 시험")
    return mm


def selectors(layer_obj, key):
    return (layer_obj.get(key) or {}).get("select", [])


def chain_sources(config, code):
    """그 파트 사슬(표준 공통 → 부 → 팀 → 파트)의 선택자 (doc, section) 목록."""
    gl, org = layers(config), org_table(config)
    info = org[code]
    out = [(s["doc"], s["section"]) for s in gl["standard"]]
    if code != "X01":
        out += [(s["doc"], s["section"]) for s in selectors(gl["depts"], info["부"])]
        out += [(s["doc"], s["section"]) for s in selectors(gl["teams"], info["팀"])]
    out += [(s["doc"], s["section"]) for s in selectors(gl["parts"], code)]
    return out


def gen_sources(text):
    """생성물의 출처 줄 (doc, section) 목록과 안전장치 핵심 출처 줄 수."""
    out, safety = [], 0
    for line in text.splitlines():
        m = SRC_RE.match(line.strip())
        if not m:
            continue
        body = m.group(1)
        if body.startswith("사용자 전역 지침"):
            safety += 1
            continue
        m2 = re.match(r"^(\S+) 「(.+?)」", body)
        out.append((m2.group(1), m2.group(2)) if m2 else ("?", body))
    return out, safety


def front_matter(text):
    assert text.startswith("---\n"), "머리말(---)로 시작하지 않습니다"
    end = text.index("\n---\n", 4)
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm, text[end + 5:]


def refs_start(lines):
    """refs 목록 제목 줄(「필요할 때 읽는 문서」만을 제목으로 둔 마지막 제목 줄)의 줄 위치. 없으면 len(lines)."""
    found = [i for i, l in enumerate(lines) if REFS_HEAD_RE.match(l.strip())]
    return found[-1] if found else len(lines)


def body_len(text):
    """생성물 본문 글자 수의 근사값(머리 줄·출처 줄·refs 목록 제외)."""
    keep = []
    lines = text.splitlines()
    for line in lines[:refs_start(lines)]:
        if line.strip().startswith("<!--"):
            continue
        keep.append(line)
    return len("\n".join(keep).strip())


# ---------------------------------------------------------------- 공통 실행 결과

@pytest.fixture(scope="session")
def cc_run(request):
    """check_config.py를 두 적용본 overlay로 옵션 없이(모든 행) 실행한 결과."""
    config = request.config
    return py(dev_script(config, "check_config.py"), *overlay_args(config), cwd=REPO)


def cc(config, *args, dev=None, design=None):
    return py(dev_script(config, "check_config.py"), *overlay_args(config, dev, design), *args, cwd=REPO)


# ---------------------------------------------------------------- 반영 뒤 상태(복제본)

@pytest.fixture(scope="session")
def reflected(request, tmp_path_factory):
    """이 저장소의 복제본에 적용본(설계 → 개발)을 원본 경로로 덮어 쓰고 커밋한 상태.

    비서팀·PM팀의 미추적 기록(승인된 REQ-034_v06과 그 승인 기록 등)을 함께 복사해, 복제본의 변경이 승인된 REQ의
    scope 안에 들게 한다. 그 밖의 미추적 파일은 복사하지 않는다(커밋 전 검사의 다른 순서가 이 시험과 관계없는
    파일로 달라지지 않게 하기 위해서다).
    """
    config = request.config
    dev_script(config, "check_standard.py")  # 개발 적용본이 없으면 여기서 실패한다(구현 전)
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
    git_ok(repo, "config", "core.hooksPath", str(hooks))
    git_ok(repo, "add", "-A")
    git_ok(repo, "commit", "-q", "-m", "acc: reflected base")
    return repo


def restore(repo):
    git_ok(repo, "reset", "-q", "--hard", "HEAD")
    git_ok(repo, "clean", "-fdq")


def staged_check(repo):
    return py(f"{SCRIPTS}/check_standard.py", "--staged", cwd=repo)


# ================================================================ 체크리스트 5

def test_c5_2_cards_and_layers(request):
    """5 ②·6 ②: 서브에이전트 파트 11개마다 파트 카드가 있고, 머리말이 04 5절 5항 ①과 같으며(omitClaudeMd: true),
    카드에 실리는 지침이 안전장치 핵심, 표준 공통 핵심, 그 파트의 부·팀 지침(X01은 없음), 파트 지침뿐이다."""
    config = request.config
    gen, gl, org = gen_root(config), layers(config), org_table(config)
    cards = sorted(p.name for p in (gen / "agents").glob("part-*.md"))
    assert cards == sorted(f"part-{c.lower()}.md" for c in SUBAGENT_PARTS), f"파트 카드 목록: {cards}"
    assert sorted(c for c, v in gl["parts"].items() if v.get("card")) == sorted(SUBAGENT_PARTS), "구성표 card: true 목록"
    safety_body = [l for l in read(gen / "guides" / "core" / "safety.md").splitlines()
                   if l.strip() and not l.strip().startswith("<!--")]
    problems = []
    for code in SUBAGENT_PARTS:
        text = read(gen / "agents" / f"part-{code.lower()}.md")
        fm, body = front_matter(text)
        exp = {"name": f"part-{code.lower()}", "model": "inherit", "disallowedTools": "Agent", "omitClaudeMd": "true"}
        for k, v in exp.items():
            if fm.get(k) != v:
                problems.append(f"{code} 머리말 {k}={fm.get(k)!r}(기대 {v!r})")
        desc = fm.get("description", "")
        if code not in desc or org[code]["파트"] not in desc:
            problems.append(f"{code} description에 코드·파트 이름이 없음: {desc!r}")
        body_lines = body.splitlines()
        first = next((l for l in body_lines if l.strip()), "")
        if not first.startswith(GEN_MARKER):
            problems.append(f"{code} 머리말 다음 줄이 생성물 표시가 아님: {first[:60]}")
        got, n_safety = gen_sources(body)
        if n_safety != 1:
            problems.append(f"{code} 안전장치 핵심 출처 줄 {n_safety}개")
        expect = chain_sources(config, code)
        if Counter(got) != Counter(expect):
            problems.append(f"{code} 실린 원천이 사슬과 다름: 빠짐 {sorted((Counter(expect) - Counter(got)).elements())}, "
                            f"남음 {sorted((Counter(got) - Counter(expect)).elements())}")
        if got and got[0] != expect[0]:
            problems.append(f"{code} 첫 원천이 표준 공통 핵심이 아님: {got[0]}")
        nonblank = [l for l in body_lines if l.strip()]
        if not safety_body or "\n".join(safety_body) not in "\n".join(nonblank):
            problems.append(f"{code} 안전장치 핵심 본문이 카드에 그대로 있지 않음")
        else:
            safety_at = nonblank.index(safety_body[0])
            first_src = next((i for i, l in enumerate(nonblank) if SRC_RE.match(l.strip())
                              and not l.strip().startswith("<!-- 원천: 사용자")), len(nonblank))
            if safety_at > first_src:
                problems.append(f"{code} 안전장치 핵심이 표준 공통 핵심보다 뒤에 있음")
        if code == "X01" and "해당 없음" not in body:
            problems.append("X01 카드에 부·팀 계층의 「해당 없음」이 없음")
        refs = (gl["parts"].get(code) or {}).get("refs", [])
        if refs:
            ri = refs_start(body_lines)
            if ri == len(body_lines):
                problems.append(f"{code} 「{REFS_TITLE}」 제목 줄이 없음")
            else:
                refs_text = "\n".join(body_lines[ri:])
                missing = [r["doc"] for r in refs if r["doc"] not in refs_text]
                if missing:
                    problems.append(f"{code} refs 문서가 카드 끝 목록에 없음: {missing}")
    for name in ("development.md", "engineering.md", "marketing.md", "operations.md", "quality.md"):
        p = gen / "agents" / name
        if p.exists() and p.read_bytes() != (REPO / ".claude" / "agents" / name).read_bytes():
            problems.append(f"부서 정의 {name}을 고침(D14: 전환 때까지 함께 둠)")
    assert not problems, "\n".join(problems)


def test_c5_3_config_check_no_errors(request, cc_run):
    """5 ③·5 ⑤·7 ③·16 ③: 두 적용본을 overlay로 준 형상통제 대조(모든 행)가 오류 0건으로 끝난다(예산 초과는 막지 않음)."""
    code, out = cc_run
    assert code == 0, f"형상통제 대조 종료 코드 {code}:\n{tail(out, 80)}"
    assert not fail_blocks(out), "\n".join(fail_blocks(out))[:4000]


def test_c5_3_regenerate_matches_applied(request, tmp_path):
    """5 ③: 생성 명령을 같은 입력(두 적용본 overlay)으로 다시 실행한 결과가 개발 적용본의 생성물과 바이트 단위로 같다."""
    config = request.config
    out_dir = tmp_path / "out"
    code, out = py(dev_script(config, "build_guides.py"), "--out", out_dir, *overlay_args(config), cwd=REPO)
    assert code == 0, f"생성 명령 종료 코드 {code}:\n{tail(out)}"
    gen = gen_root(config)

    def listing(base):
        files = {p.relative_to(base).as_posix(): p for p in (base / "guides").rglob("*") if p.is_file()}
        files.update({p.relative_to(base).as_posix(): p for p in (base / "agents").glob("part-*.md")})
        return files

    got, exp = listing(out_dir), listing(gen)
    assert set(got) == set(exp), f"파일 목록 차이: 생성만 {sorted(set(got) - set(exp))}, 적용본만 {sorted(set(exp) - set(got))}"
    diff = [k for k in sorted(exp) if got[k].read_bytes() != exp[k].read_bytes()]
    assert not diff, f"내용이 다른 생성물: {diff}"
    for k, p in exp.items():
        data = p.read_bytes()
        assert not data.startswith(b"\xef\xbb\xbf") and b"\r\n" not in data, f"{k}: BOM 또는 CRLF"


def test_c5_3_generated_text_is_source_text(request):
    """5 ③: 생성물의 출처 줄 아래 글자가 그 원천 문서(현행 거버넌스 파일)의 줄 그대로다(제목 줄의 리비전 태그만 뗌).
    규정 문장마다 원천 절이 하나이며 같은 원천을 한 생성물에 두 번 싣지 않는다."""
    config = request.config
    gen, files = gen_root(config), current_gov(config)
    doc_lines = {}
    problems = []
    targets = sorted(p for p in (gen / "guides").rglob("*.md") if p.name != "safety.md")
    targets += sorted((gen / "agents").glob("part-*.md"))
    for path in targets:
        text = read(path)
        lines = text.splitlines()
        i0 = 0
        if lines and lines[0] == "---":
            i0 = lines.index("---", 1) + 1
        doc, skip = None, False
        seen = Counter()
        stop = refs_start(lines)
        for no, line in enumerate(lines[i0:stop], i0 + 1):
            s = line.strip()
            m = SRC_RE.match(s)
            if m:
                body = m.group(1)
                skip = body.startswith("사용자 전역 지침")
                m2 = re.match(r"^(\S+) 「(.+?)」(.*)$", body)
                doc = m2.group(1) if m2 and not skip else None
                if m2 and not skip:
                    seen[body] += 1
                    if doc not in files:
                        problems.append(f"{path.name}:{no} 원천 문서 없음 {doc}")
                        doc = None
                continue
            if skip or not s or s.startswith("<!--") or s.startswith("#") or s == "---" or "해당 없음" in s:
                continue
            if doc is None:
                problems.append(f"{path.relative_to(gen).as_posix()}:{no} 출처 줄 없이 나온 글자: {s[:80]}")
                continue
            if doc not in doc_lines:
                doc_lines[doc] = {TAG_RE.sub("", l).rstrip() for l in read(files[doc]).splitlines()}
            if line.rstrip() not in doc_lines[doc] and TAG_RE.sub("", line).rstrip() not in doc_lines[doc]:
                problems.append(f"{path.relative_to(gen).as_posix()}:{no} 원천 {doc}에 없는 줄: {s[:80]}")
        dup = [k for k, v in seen.items() if v > 1]
        if dup:
            problems.append(f"{path.relative_to(gen).as_posix()} 같은 원천을 두 번 실음: {dup}")
    assert not problems, "\n".join(problems[:60]) + (f"\n… 외 {len(problems) - 60}건" if len(problems) > 60 else "")


@pytest.mark.parametrize("case", ["source_changed", "card_changed", "surplus_card"])
def test_c5_3_config_check_detects_mismatch(request, tmp_path, case):
    """5 ③: 원천 절 한 글자를 바꾼 상태, 파트 카드 한 줄을 바꾼 상태, 남는 part-*.md가 있는 상태에서 생성물 대조(C2) 오류."""
    config = request.config
    design, dev = design_root(config), dev_root(config)
    if case == "source_changed":
        design = copy_tree(design, tmp_path / "design")
        p = design / "AGENTS.md.적용본"
        text = read(p)
        assert "단순성 우선" in [i for s in layers(config)["standard"] for i in s.get("items", [])]
        lines = text.splitlines()
        idx = next(i for i, l in enumerate(lines) if "**단순성 우선**" in l)
        lines[idx] += " 시험 문구"
        write(p, "\n".join(lines) + "\n")
    else:
        dev = copy_tree(dev, tmp_path / "dev")
        agents = dev / ".claude.적용본" / "agents"
        if case == "card_changed":
            p = agents / "part-q05.md"
            write(p, read(p).rstrip("\n") + " 시험 문구\n")
        else:
            shutil.copyfile(agents / "part-q05.md", agents / "part-z99.md")
    code, out = cc(config, dev=dev, design=design)
    assert code == 1, f"{case}: 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert has_fail(out, "C2"), f"{case}: C2 오류가 없습니다:\n{tail(out)}"


def test_c5_4_budget_output(request, cc_run):
    """5 ④(D3·D4): 상한을 분명히 넘은 계층은 「[INFO] 예산 초과」로 나오고, 분명히 안쪽인 계층은 나오지 않으며,
    예산 초과는 [FAIL]이 아니다(종료 코드는 5 ③ 시험이 본다)."""
    config = request.config
    code, out = cc_run
    gen, gl, org = gen_root(config), layers(config), org_table(config)
    budgets = gl["budgets"]
    over = []
    for line in out.splitlines():
        m = re.search(r"예산 초과\s+(.*?)\s+(\d[\d,]*)\s*/\s*(\d[\d,]*)\s*$", line)
        if m:
            assert line.startswith("[INFO]"), f"예산 초과가 [INFO]가 아닙니다: {line}"
            over.append((m.group(1), int(m.group(2).replace(",", "")), int(m.group(3).replace(",", ""))))

    def named(text, *names):
        return any(re.search(rf"(^|\s){re.escape(n)}(\s|$)", text) for n in names if n)

    def reported(*names, limit):
        return [o for o in over if o[2] == limit and named(o[0], *names)]

    entities = []  # (설명, 이름들, 근사 글자 수, 상한)
    std = read(gen / "guides" / "core" / "standard.md")
    entities.append(("표준 공통", ("표준", "표준 공통", "standard"), body_len(std), budgets["standard"]))
    dept_len, team_len = {}, {}
    for dept, folder in DEPT_FOLDERS.items():
        dept_len[dept] = body_len(read(gen / "guides" / "depts" / f"{folder}.md"))
        entities.append((f"부 {dept}", (dept, folder), dept_len[dept], budgets["dept"]))
    teams = {(v["팀"], v["팀 폴더"]) for v in org.values() if v["팀"] not in ("—", "")}
    for team, folder in sorted(teams):
        team_len[team] = body_len(read(gen / "guides" / "teams" / f"{folder}.md"))
        entities.append((f"팀 {team}", (team, folder), team_len[team], budgets["team"]))
    for code_, v in org.items():
        whole = body_len(read(gen / "guides" / "parts" / f"{code_}.md"))
        part_only = whole - dept_len.get(v["부"], 0) - team_len.get(v["팀"], 0)
        entities.append((f"파트 {code_}", (code_,), part_only, budgets["part"]))
    problems = []
    for label, names, n, limit in entities:
        rep = reported(*names, limit=limit)
        if n > limit * 1.3 and not rep:
            problems.append(f"{label}: 본문 약 {n}자(상한 {limit})인데 예산 초과 출력이 없음")
        if n < limit * 0.7 and rep:
            problems.append(f"{label}: 본문 약 {n}자(상한 {limit})인데 예산 초과로 나옴 {rep}")
        for _, cnt, _lim in rep:
            if cnt <= limit:
                problems.append(f"{label}: 예산 초과 글자 수 {cnt}가 상한 {limit} 이하")
    assert not problems, "\n".join(problems) + "\n--- 예산 초과 출력\n" + "\n".join(map(str, over))


def test_c5_7_session_part_guides(request):
    """5 ⑦(D16 ①·대안 (가)): 조직 표의 모든 파트(활성·대기)와 모든 부·팀에 생성 지침이 있고,
    P01·P02·V03·C01~C03·S01~S03의 파트 지침에 실린 원천이 그 파트의 부·팀·파트 선택자와 같다."""
    config = request.config
    gen, gl, org = gen_root(config), layers(config), org_table(config)
    problems = []
    for code, v in org.items():
        if not (gen / "guides" / "parts" / f"{code}.md").is_file():
            problems.append(f"파트 지침 없음 {code}")
    for dept, folder in DEPT_FOLDERS.items():
        if not (gen / "guides" / "depts" / f"{folder}.md").is_file():
            problems.append(f"부 지침 없음 {dept}({folder})")
    for team, folder in {(v["팀"], v["팀 폴더"]) for v in org.values() if v["팀"] not in ("—", "")}:
        if not (gen / "guides" / "teams" / f"{folder}.md").is_file():
            problems.append(f"팀 지침 없음 {team}({folder})")
    for name in ("safety.md", "standard.md"):
        if not (gen / "guides" / "core" / name).is_file():
            problems.append(f"핵심 없음 {name}")
    for code in SESSION_PARTS:
        p = gen / "guides" / "parts" / f"{code}.md"
        if not p.is_file():
            continue
        got, n_safety = gen_sources(read(p))
        info = org[code]
        expect = [(s["doc"], s["section"]) for s in selectors(gl["depts"], info["부"])]
        expect += [(s["doc"], s["section"]) for s in selectors(gl["teams"], info["팀"])]
        expect += [(s["doc"], s["section"]) for s in selectors(gl["parts"], code)]
        if n_safety:
            problems.append(f"{code} 파트 지침에 안전장치 핵심이 실림(D16 ①: 전역 지침을 그대로 실음)")
        if Counter(got) != Counter(expect):
            problems.append(f"{code} 실린 원천이 부·팀·파트 선택자와 다름: 빠짐 "
                            f"{sorted((Counter(expect) - Counter(got)).elements())}, "
                            f"남음 {sorted((Counter(got) - Counter(expect)).elements())}")
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("code", ["S01", "S02", "S03"])
def test_c5_7_placement_secretary(request, code):
    """5 ⑦ 끝 문장(EC 5절 2행): S01~S03에 적용되는 규정의 대응표 행이 --placement 출력에 나온다."""
    config = request.config
    mm = load_json(design_wf(config) / "data" / "migration_map.json")
    mine = [r["id"] for r in mm["rows"] if f"파트:{code}" in r.get("loaded_in", [])]
    assert mine, f"대응표에 「실리는 곳」이 파트:{code}인 행이 없습니다"
    rc, out = cc(config, "--placement", code)
    assert rc == 0, f"--placement {code} 종료 코드 {rc}:\n{tail(out)}"
    missing = [i for i in mine if i not in out]
    assert not missing, f"--placement {code} 출력에 없는 행: {missing[:20]}\n{tail(out, 20)}"


# ================================================================ 체크리스트 6

def _excerpt(config):
    found = sorted((REPO / DEV_WORKSPACE).glob("REQ-034_전역지침발췌_*.md"))
    assert found, "개발부 workspace에 전역 지침 발췌 파일(REQ-034_전역지침발췌_*.md, EC 3.6절 1번)이 없습니다"
    return found[-1]


REQUIRED_SAFETY_PHRASES = (
    "API 키, 비밀번호, 접속 토큰, 개인정보는", "인증 정보는 대리 입력하지 않고",
    "기밀, 식별 정보, 비공개 데이터는", "사람이 확정했거나 마감 날짜가 지정된 기록은", "외부 원자료는",
    "파일 삭제·덮어쓰기 전 사용자 승인:", "승인 목록 밖 대상", "새 파일 생성은 승인 없이",
    "Git 커밋 및 푸시는 명시적 요청 시에만 수행:", "커밋과 푸시(Push)는 각각",
    "지침 문서 수정 전 사용자 승인:", "사용자가 제시한 수정안을 임의로 재구성하지 않는다",
)
# 불변 예외가 아닌 이웃 항목의 글자(이 글자가 있으면 「그 밖의 항목」이 섞인 것이다)
FORBIDDEN_SAFETY_PHRASES = (
    "하위 지침으로 무효화할 수 없다", "덮어쓰기 전 대조", "최종 완성본만", "이하 생략", "파일 이동·이름 변경·삭제 때는",
    "지침 계층은", "숫자, 고유명사", "산출물 분리", "Silent Failure", "번역투", "재판정 한도",
)


def test_c6_3_safety_core_content(request):
    """6 ③(D1): 안전장치 핵심이 불변 예외 네 항목을 세부 규정까지 담고, 그 밖의 항목이 없으며, 머리 표시가 v29 사본을 가리킨다."""
    text = read(gen_root(request.config) / "guides" / "core" / "safety.md")
    lines = text.splitlines()
    assert lines and lines[0].startswith(GEN_MARKER), "첫 줄이 생성물 표시가 아닙니다"
    head = "\n".join(l for l in lines[:4] if l.startswith("<!-- 원천:"))
    assert "사용자 전역 지침" in head and "2026-10-06 · v29" in head and "SHA-256" in head, f"머리 표시: {head}"
    missing = [p for p in REQUIRED_SAFETY_PHRASES if p not in text]
    extra = [p for p in FORBIDDEN_SAFETY_PHRASES if p in text]
    assert not missing, f"안전장치 핵심에 없는 불변 예외 글자: {missing}"
    assert not extra, f"안전장치 핵심에 불변 예외 밖 글자: {extra}"
    heads = [l for l in lines if re.match(r"^#{1,6}\s", l)]
    assert len(heads) == 1 and "보안 및 불변 데이터 보호" in heads[0], f"제목 줄: {heads}"


@pytest.mark.parametrize("case", ["same", "changed"])
def test_c6_5_global_source_compare(request, tmp_path, case):
    """6 ③·⑤(D5): 발췌 파일을 원천으로 준 대조는 일치하고, 불변 예외 문장 한 곳을 바꾼 시험용 원본은 불일치를 낸다."""
    config = request.config
    src = tmp_path / "global_source.md"
    text = read(_excerpt(config))
    if case == "changed":
        lines = text.splitlines()
        idx = next((i for i, l in enumerate(lines) if "Git 커밋 및 푸시는 명시적 요청 시에만 수행:" in l), None)
        assert idx is not None, "발췌 파일에 「Git 커밋 및 푸시는 명시적 요청 시에만 수행:」 항목이 없습니다"
        lines[idx] += " 시험 변경"
        text = "\n".join(lines) + "\n"
    write(src, text)
    code, out = cc(config, "--global-source", src)
    if case == "same":
        assert code == 0 and not fail_blocks(out), f"발췌 파일 대조 종료 코드 {code}:\n{tail(out)}"
    else:
        assert code == 1, f"바꾼 원본에서 종료 코드 {code}(기대 1):\n{tail(out)}"
        assert any("안전장치 핵심이 원천과 다름" in b for b in fail_blocks(out)), tail(out)


# ================================================================ 체크리스트 7

def _regen_into(repo):
    """반영 뒤 상태에서 생성 명령으로 다시 만들어 .claude/의 생성물에 덮어 쓴다(지침 재생성 반영과 같은 경로)."""
    work = "Departments/Secretariat/ConfigControl/workspace/acc_regen"
    code, out = py(f"{SCRIPTS}/build_guides.py", "--out", work, cwd=repo)
    assert code == 0, f"생성 명령 종료 코드 {code}:\n{tail(out)}"
    src = repo / work
    for p in (src / "guides").rglob("*"):
        if p.is_file():
            dst = repo / ".claude" / "guides" / p.relative_to(src / "guides")
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst)
    for p in (src / "agents").glob("part-*.md"):
        shutil.copyfile(p, repo / ".claude" / "agents" / p.name)
    shutil.rmtree(src)


def _change_agents(repo):
    p = repo / "AGENTS.md"
    lines = read(p).splitlines()
    idx = next(i for i, l in enumerate(lines) if "**단순성 우선**" in l)
    lines[idx] += " 시험 문구"
    write(p, "\n".join(lines) + "\n")


@pytest.mark.parametrize("case", ["source_not_regenerated", "card_edited", "regenerated"])
def test_c7_2_staged_commit_check(reflected, case):
    """7 ②: 원천과 생성물이 어긋난 파일을 스테이징하면 커밋 전 검사가 실패하고(C2), 맞으면 통과한다."""
    try:
        if case == "card_edited":
            p = reflected / ".claude" / "agents" / "part-q05.md"
            write(p, read(p).rstrip("\n") + " 시험 문구\n")
            git_ok(reflected, "add", "--", ".claude/agents/part-q05.md")
        else:
            _change_agents(reflected)
            if case == "regenerated":
                _regen_into(reflected)
            git_ok(reflected, "add", "--", "AGENTS.md", ".claude")
        code, out = staged_check(reflected)
    finally:
        restore(reflected)
    if case == "regenerated":
        assert code == 0, f"맞는 상태에서 커밋 전 검사 종료 코드 {code}:\n{tail(out, 80)}"
        assert not fail_blocks(out), "\n".join(fail_blocks(out))
    else:
        assert code == 1, f"{case}: 커밋 전 검사 종료 코드 {code}(기대 1):\n{tail(out, 80)}"
        assert has_fail(out, "C2"), f"{case}: C2 오류가 없습니다:\n{tail(out, 80)}"


@pytest.mark.parametrize("case", ["card_flag_removed", "part_guide_missing"])
def test_c7_3_part_check_detects(request, tmp_path, case):
    """7 ③: 파트 대조(C4)가 구성표 card 목록과 서브에이전트 파트의 어긋남, 파트 지침이 없는 파트를 오류로 낸다
    (현행 0건은 5 ③ 시험이 본다)."""
    config = request.config
    design, dev = design_root(config), dev_root(config)
    if case == "card_flag_removed":
        design = copy_tree(design, tmp_path / "design")
        p = design / "Workflow.적용본" / "data" / "guide_layers.json"
        gl = load_json(p)
        gl["parts"]["Q07"]["card"] = False
        write_json(p, gl)
    else:
        dev = copy_tree(dev, tmp_path / "dev")
        (dev / ".claude.적용본" / "guides" / "parts" / "S01.md").unlink()
    code, out = cc(config, dev=dev, design=design)
    assert code == 1, f"{case}: 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert has_fail(out, "C4"), f"{case}: C4 오류가 없습니다:\n{tail(out)}"


def test_c7_6_old_path_blocked_by_config_check(reflected):
    """7 ⑥: 옛 경로를 넣은 파일을 스테이징하면 커밋 전 검사가 형상통제 대조의 옛 경로 잔존(C1)으로 실패한다."""
    rel = f"{SCRIPTS}/acc_old_path_note.md"
    try:
        write(reflected / rel, f"# 시험\n\n참고 경로: {OLD_PATH_SAMPLE}\n")
        git_ok(reflected, "add", "--", rel)
        code, out = staged_check(reflected)
    finally:
        restore(reflected)
    assert code == 1, f"커밋 전 검사 종료 코드 {code}(기대 1):\n{tail(out, 80)}"
    assert has_fail(out, "C1"), f"C1 오류가 없습니다:\n{tail(out, 80)}"
    assert any("acc_old_path_note.md" in b for b in fail_blocks(out)), tail(out, 80)


# ================================================================ 체크리스트 11

def _valid_ec():
    """EC-034_v02의 3.2절을 서식 3.3절 「결정 반영 대조」 형식(D1~D16 행 표 하나)으로 고친 시험용 EC."""
    lines = read(REPO / EC_PATH).splitlines()
    i = next(n for n, l in enumerate(lines) if l.startswith("### 3.2 결정 반영 대조"))
    lines[i] = "### 3.2 결정 반영 대조"
    j = next(n for n, l in enumerate(lines) if n > i and l.startswith("이 EC가 정한 구현 방법"))
    k = next(n for n, l in enumerate(lines) if n > j and l.startswith("### "))
    del lines[j:k]
    return lines


def _write_ec(tmp_path, lines, name="base"):
    p = tmp_path / name / "EC-034_v02.md"
    write(p, "\n".join(lines) + "\n")
    return p


def _prejudge(config, doc, *args):
    return py(dev_script(config, "check_prejudge.py"), doc, "--req", REQ_PATH, *args, cwd=REPO)


def test_c11_2_valid_ec_passes(request, tmp_path):
    """11 ②: 서식 절·머리말·scope·결정 반영 대조를 갖춘 시험용 EC는 판정 전 점검을 통과한다(아래 결함 시험의 대조군)."""
    code, out = _prejudge(request.config, _write_ec(tmp_path, _valid_ec()))
    assert code == 0, f"종료 코드 {code}(기대 0):\n{tail(out)}"
    assert not fail_blocks(out) and "[PASS]" in out, tail(out)


@pytest.mark.parametrize("case", ["section_removed", "front_matter_field_removed", "scope_outside_req",
                                  "decision_row_missing"])
def test_c11_2_prejudge_detects(request, tmp_path, case):
    """11 ②: 서식 절 하나를 뺀 EC, 머리말 필드를 뺀 EC, REQ 밖 scope 항목을 둔 EC, 결정 반영 대조에 D번호가 빠진 EC에서
    대조군에 없던 [FAIL]이 그 결함을 가리키며 나오고 종료 코드가 1이다."""
    config = request.config
    base = _valid_ec()
    lines = list(base)
    if case == "section_removed":
        lines.remove("## 4. 위험 분석 및 대응")
        token = "위험 분석 및 대응"
    elif case == "front_matter_field_removed":
        lines = [l for l in lines if not l.startswith("created:")]
        token = "created"
    elif case == "scope_outside_req":
        i = lines.index("  - Departments/Design/EC/docs/EC-034")
        lines.insert(i + 1, "  - Departments/Marketing/Content/docs")
        token = "Departments/Marketing/Content/docs"
    else:
        i = next(n for n, l in enumerate(lines) if l.startswith("| D7 "))
        del lines[i]
        token = "D7"
    b_code, b_out = _prejudge(config, _write_ec(tmp_path, base, "base"))
    d_code, d_out = _prejudge(config, _write_ec(tmp_path, lines, "defect"))
    new = [b for b in fail_blocks(d_out) if b not in fail_blocks(b_out)]
    assert d_code == 1, f"{case}: 종료 코드 {d_code}(기대 1):\n{tail(d_out)}"
    assert any(token in b for b in new), (f"{case}: 결함({token})을 가리키는 새 [FAIL]이 없습니다"
                                          f"\n--- 결함\n{tail(d_out, 30)}\n--- 대조군\n{tail(b_out, 30)}")


def test_c11_2_prejudge_detects_missing_tag(request, tmp_path):
    """11 ②: 실변경 절 제목에 현행 태그가 없는 적용본(--applied)에서 대조군에 없던 [FAIL]이 그 파일을 가리킨다."""
    config = request.config
    bad = copy_tree(design_root(config), tmp_path / "design")
    p = bad / "Workflow.적용본" / "01_표준_개요.md"
    text = read(p)
    assert "## 4. 용어 (REQ-034_v06)" in text, "설계 적용본 01의 「용어」 절 제목에 현행 태그가 없습니다"
    write(p, text.replace("## 4. 용어 (REQ-034_v06)", "## 4. 용어"))
    doc = tmp_path / "doc" / "RPT-034_v02.md"
    write(doc, read(REPO / RPT_PATH))
    b_code, b_out = _prejudge(config, doc, "--applied", design_root(config))
    d_code, d_out = _prejudge(config, doc, "--applied", bad)
    new = [b for b in fail_blocks(d_out) if b not in fail_blocks(b_out)]
    assert d_code == 1, f"종료 코드 {d_code}(기대 1):\n{tail(d_out)}"
    assert any("01_표준_개요" in b or "용어" in b for b in new), \
        f"태그 결함을 가리키는 새 [FAIL]이 없습니다\n--- 결함\n{tail(d_out, 30)}\n--- 대조군\n{tail(b_out, 30)}"


ORIGINAL_DOC = """# 99. 시험 문서

> 이 문서가 정하는 것: 시험.

## 1. 첫째 절 (REQ-033_v04)

첫째 본문.

### 1.1 하위 절 (REQ-032_v06)

하위 본문.
- 항목 하나

## 2. 둘째 절 (REQ-033_v04)

둘째 본문.

## 3. 셋째 절

셋째 본문.

## 4. 넷째 절 (REQ-031_v03)

넷째 본문.

## 개정 이력

| 안건 | 일자 | 변경 요지 |
| :--- | :--- | :--- |
| REQ-033_v04 | 2026-10-18 | 이전 행 |
"""

DELTA_DOC = """<!-- 변경: 머리 -->
# 99. 시험 문서

> 이 문서가 정하는 것: 시험(바뀜).

<!-- 변경: 교체 「둘째 절」 -->
## 2. 둘째 절 (REQ-034_v06)

둘째 본문(바뀜).

<!-- 변경: 뒤에 추가 「하위 절」 -->
### 1.2 새 하위 절 (REQ-034_v06)

새 본문.

<!-- 변경: 삭제 「셋째 절」 -->
<!-- 변경: 이력 추가 -->
| REQ-034_v06 | 2026-10-19 | 새 행 |
"""


def _blocks(text):
    """머리(첫 H2 앞)와 H1~H3 블록(코드 울타리 밖)으로 나눈다. [(블록 이름 또는 None, 줄 목록)]."""
    lines = text.splitlines()
    hs = [(i, lv, t) for i, lv, t in headings(lines, 3)]
    first_h2 = next((i for i, lv, _ in hs if lv >= 2), len(lines))
    out = [(None, lines[:first_h2])]
    starts = [(i, t) for i, lv, t in hs if i >= first_h2]
    for n, (i, t) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        out.append((t, lines[i:end]))
    return out


def _norm(lines):
    lines = [l.rstrip() for l in lines]
    while lines and not lines[-1]:
        lines.pop()
    while lines and not lines[0]:
        lines.pop(0)
    return lines


def _delta_repo(tmp_path, delta_text):
    repo = tmp_path / "repo"
    repo.mkdir()
    git_ok(repo, "init", "-q")
    write(repo / "Workflow" / "99_시험.md", ORIGINAL_DOC)
    write(repo / "ap" / "Workflow.적용본" / "99_시험.변경.md", delta_text)
    git_ok(repo, "add", "-A")
    git_ok(repo, "-c", "core.hooksPath=nohooks", "commit", "-q", "-m", "acc: delta base")
    return repo


def test_c11_3_delta_apply_keeps_other_blocks(request, tmp_path):
    """11 ③: 교체·추가·삭제·머리·이력 추가가 섞인 변경 파일을 시험 저장소에 반영하면 바뀐 절 밖은 원본과 같고
    (제목 줄의 리비전 태그만 지움), --check가 0으로 끝난다."""
    script = dev_script(request.config, "apply_delta.py")
    repo = _delta_repo(tmp_path, DELTA_DOC)
    delta, orig = "ap/Workflow.적용본/99_시험.변경.md", "Workflow/99_시험.md"
    code, out = py(script, "--check", delta, orig, cwd=repo)
    assert code == 0, f"--check 종료 코드 {code}(기대 0):\n{tail(out)}"
    code, out = py(script, "--write", delta, orig, cwd=repo)
    assert code == 0, f"--write 종료 코드 {code}:\n{tail(out)}"
    got = _blocks(read(repo / orig))
    names = [n for n, _ in got]
    assert names == [None, "첫째 절", "하위 절", "새 하위 절", "둘째 절", "넷째 절", "개정 이력"], f"블록 순서: {names}"
    result = {n: _norm(l) for n, l in got}
    original = {n: _norm(l) for n, l in _blocks(ORIGINAL_DOC)}
    assert result[None] == ["# 99. 시험 문서", "", "> 이 문서가 정하는 것: 시험(바뀜)."], f"머리: {result[None]}"
    assert result["둘째 절"] == ["## 2. 둘째 절 (REQ-034_v06)", "", "둘째 본문(바뀜)."], result["둘째 절"]
    assert result["새 하위 절"] == ["### 1.2 새 하위 절 (REQ-034_v06)", "", "새 본문."], result["새 하위 절"]
    for name in ("첫째 절", "하위 절", "넷째 절"):
        exp = [TAG_RE.sub("", original[name][0])] + original[name][1:]
        assert result[name] == exp, f"바뀌지 않은 블록 「{name}」이 원본과 다름:\n{result[name]}\n기대 {exp}"
    hist = result["개정 이력"]
    sep = next(i for i, l in enumerate(hist) if re.fullmatch(r"\|[\s:|-]+\|", l.strip()))
    assert hist[sep + 1] == "| REQ-034_v06 | 2026-10-19 | 새 행 |", f"이력 추가 위치: {hist}"
    assert hist[:sep + 1] + hist[sep + 2:] == original["개정 이력"], f"개정 이력의 다른 줄이 바뀜: {hist}"
    assert "셋째" not in read(repo / orig), "삭제한 블록이 남았습니다"


@pytest.mark.parametrize("case", ["unknown_block", "replace_without_heading"])
def test_c11_3_delta_errors_keep_original(request, tmp_path, case):
    """11 ③: 없는 블록 이름, 제목 줄로 시작하지 않는 교체 내용은 오류이며 원본을 쓰지 않는다."""
    script = dev_script(request.config, "apply_delta.py")
    if case == "unknown_block":
        delta_text = "<!-- 변경: 교체 「없는 절」 -->\n## 9. 없는 절 (REQ-034_v06)\n\n본문.\n"
    else:
        delta_text = "<!-- 변경: 교체 「둘째 절」 -->\n제목 없는 본문.\n"
    repo = _delta_repo(tmp_path, delta_text)
    before = (repo / "Workflow" / "99_시험.md").read_bytes()
    code, out = py(script, "--write", "ap/Workflow.적용본/99_시험.변경.md", "Workflow/99_시험.md", cwd=repo)
    assert code != 0, f"{case}: 종료 코드 0(오류여야 함):\n{tail(out)}"
    assert "[FAIL]" in out, tail(out)
    assert (repo / "Workflow" / "99_시험.md").read_bytes() == before, f"{case}: 오류인데 원본이 바뀌었습니다"


# ================================================================ 체크리스트 16

def test_c16_1_baseline_commit(request):
    """16 ①: 대응표의 기준본 커밋이 v05 이력의 복제 시점 커밋이고(git log), targets가 기준본 트리의 대상 문서와 같다."""
    mm = migration_map(request.config)
    base = mm.get("baseline_commit", "")
    assert re.fullmatch(r"[0-9a-f]{40}", base), f"baseline_commit 형식: {base!r}"
    log = git_ok(REPO, "log", "--reverse", "--format=%H %P %s").splitlines()
    first_req = next((l for l in log if "[REQ-031]" in l), None)
    assert first_req, "v05 첫 REQ 커밋([REQ-031])을 찾지 못했습니다"
    parts = first_req.split(" ")
    assert parts[1] == base, f"v05 첫 REQ 커밋 {parts[0][:7]}의 부모 {parts[1]}가 기준본 {base}와 다릅니다"
    reflog = [l for l in git_ok(REPO, "log", "-g", "--format=%H %gs", "HEAD").splitlines() if l.strip()]
    assert reflog, "HEAD reflog가 없습니다"
    oldest_hash, _, oldest_msg = reflog[-1].partition(" ")
    assert oldest_hash == base and oldest_msg.startswith("clone:"), \
        f"가장 오래된 reflog 항목이 기준본의 복제 기록이 아닙니다: {reflog[-1]}"
    tree = git_ok(REPO, "ls-tree", "-r", "--name-only", base, "--",
                  "AGENTS.md", "CLAUDE.md", "Workflow", ".claude/agents").splitlines()
    expected = sorted(p for p in tree if p in ("AGENTS.md", "CLAUDE.md") or p.startswith(("Workflow/templates/", ".claude/agents/"))
                      or re.fullmatch(r"Workflow/0[1-7]_[^/]+\.md", p))
    assert sorted(mm.get("targets", [])) == expected, \
        f"targets 차이: 빠짐 {sorted(set(expected) - set(mm.get('targets', [])))}, 남음 {sorted(set(mm.get('targets', [])) - set(expected))}"


ALLOWED = {
    "kind": {"규정", "비규정"},
    "action_rule": {"이관", "개정", "통합", "안전장치 핵심으로 대체", "삭제"},
    "action_nonrule": {"보관", "정리"},
    "owner": {"REQ-031", "REQ-032", "REQ-033", "REQ-034", "ORD-012-9", "ORD-012-10"},
    "status": {"완료", "개정 예정"},
}


def test_c16_3_rows_values_and_sources(request):
    """16 ③(검사 ②·③·⑤를 시험이 직접 대조): 행의 값이 허용 값이고, 원천(source)이 현행 거버넌스 파일에 있으며,
    「통합」·「삭제」 행에 사유가 있다. 5 ⑤의 「뺀 AGENTS.md 내용의 원천 절」도 이 대조에 든다."""
    config = request.config
    mm = migration_map(config)
    files, org = current_gov(config), org_table(config)
    depts = {v["부"] for v in org.values()}
    teams = {v["팀"] for v in org.values()}
    problems = []
    for r in mm["rows"]:
        rid = r.get("id")
        kind, action, loaded = r.get("kind"), r.get("action"), r.get("loaded_in")
        if kind not in ALLOWED["kind"]:
            problems.append(f"{rid} kind {kind!r}")
            continue
        allowed_action = ALLOWED["action_rule"] if kind == "규정" else ALLOWED["action_nonrule"]
        if action not in allowed_action:
            problems.append(f"{rid} action {action!r}")
        if r.get("owner") not in ALLOWED["owner"] or r.get("status") not in ALLOWED["status"]:
            problems.append(f"{rid} owner·status {r.get('owner')!r}·{r.get('status')!r}")
        if not isinstance(loaded, list):
            problems.append(f"{rid} loaded_in 목록 아님")
            continue
        if kind == "비규정" and loaded:
            problems.append(f"{rid} 비규정인데 loaded_in {loaded}")
        if kind == "규정" and action != "삭제" and not loaded:
            problems.append(f"{rid} 실리는 곳 없음")
        for v in loaded:
            ok = (v in ("표준 공통", "안전장치 핵심", "원천 절만")
                  or (v.startswith("부:") and v[2:] in depts) or (v.startswith("팀:") and v[2:] in teams)
                  or (v.startswith("파트:") and v[3:] in org))
            if not ok:
                problems.append(f"{rid} loaded_in 값 {v!r}")
        if "원천 절만" in loaded and len(loaded) > 1:
            problems.append(f"{rid} 「원천 절만」과 다른 값을 함께 씀")
        if action in ("통합", "삭제") and not str(r.get("note") or "").strip():
            problems.append(f"{rid} {action} 사유 없음")
        src = r.get("source")
        if action in ("이관", "개정", "통합", "보관"):
            if not isinstance(src, dict):
                problems.append(f"{rid} source 없음")
                continue
            why = source_exists(files, src)
            if why:
                problems.append(f"{rid} {why}")
        elif action == "안전장치 핵심으로 대체":
            if not isinstance(src, dict) or src.get("safety") not in SAFETY_NAMES or loaded != ["안전장치 핵심"]:
                problems.append(f"{rid} 안전장치 핵심 원천·실리는 곳 {src} {loaded}")
    assert not problems, f"{len(problems)}건\n" + "\n".join(problems[:80])


def test_c16_3_units_match_map(request):
    """16 ③(검사 ①): 개발부 --units의 기준본 단위 목록이 대응표 id 목록(나눈 행은 # 앞)과 같다."""
    config = request.config
    code, out = cc(config, "--units")
    assert code == 0, f"--units 종료 코드 {code}:\n{tail(out)}"
    units = set(re.findall(r"^\s*(\S+?\.(?:md|html):\d+)\b", out, re.M))
    mm = load_json(design_wf(config) / "data" / "migration_map.json")
    ids = {r["id"].split("#", 1)[0] for r in mm["rows"]}
    assert units, f"--units 출력에서 단위 id를 읽지 못했습니다:\n{tail(out, 20)}"
    assert units == ids, f"단위만 {sorted(units - ids)[:20]}, 대응표만 {sorted(ids - units)[:20]}"


def _pick_row(mm, **cond):
    for r in mm["rows"]:
        if "#" in r["id"]:
            continue
        if all((r.get(k) == v) if not callable(v) else v(r.get(k)) for k, v in cond.items()):
            return r
    raise AssertionError(f"조건에 맞는 대응표 행이 없습니다: {cond}")


@pytest.mark.parametrize("case", ["row_removed", "source_missing", "loaded_in_wrong", "delete_without_note"])
def test_c16_3_migration_check_detects(request, tmp_path, case):
    """16 ③: 행 하나를 뺀 대응표, 원천 절을 없는 절로 바꾼 대응표, 「실리는 곳」을 원천이 실리지 않는 파트로 바꾼 대응표,
    사유 없는 「삭제」 행에서 이관 검사(C5, --owner REQ-034)가 위반을 낸다."""
    config = request.config
    design = copy_tree(design_root(config), tmp_path / "design")
    p = design / "Workflow.적용본" / "data" / "migration_map.json"
    mm = load_json(p)
    gl = load_json(design / "Workflow.적용본" / "data" / "guide_layers.json")
    row = _pick_row(mm, owner="REQ-034", action="이관", kind="규정",
                    source=lambda s: isinstance(s, dict) and "section" in s and "item" not in s and "row" not in s,
                    loaded_in=lambda v: isinstance(v, list) and any(x.startswith("파트:") for x in v))
    rid = row["id"]
    if case == "row_removed":
        mm["rows"] = [r for r in mm["rows"] if r["id"] != rid]
    elif case == "source_missing":
        row["source"]["section"] = "없는 절 시험"
    elif case == "loaded_in_wrong":
        assert not gl["parts"]["M01"]["select"], "M01 파트 계층에 선택자가 있어 이 시험의 전제가 맞지 않습니다"
        row["loaded_in"] = ["파트:M01"]
    else:
        row.update({"action": "삭제", "source": None, "loaded_in": [], "note": ""})
    write_json(p, mm)
    code, out = cc(config, "--owner", "REQ-034", design=design)
    assert code == 1, f"{case}({rid}): 종료 코드 {code}(기대 1):\n{tail(out)}"
    assert any(re.search(r"(?<![A-Za-z0-9])C5(?![0-9])", b) and rid in b for b in fail_blocks(out)), \
        f"{case}: 행 {rid}을 가리키는 C5 위반이 없습니다:\n{tail(out)}"


def test_c16_3_staged_commit_blocks_row_removed(reflected):
    """16 ③: 행 하나를 뺀 대응표를 스테이징한 커밋 전 검사가 이관 검사(C5)로 실패한다(커밋하는 REQ-034가 담당인 행)."""
    rel = "Workflow/data/migration_map.json"
    try:
        mm = load_json(reflected / rel)
        row = _pick_row(mm, owner="REQ-034", action="이관")
        mm["rows"] = [r for r in mm["rows"] if r["id"] != row["id"]]
        write_json(reflected / rel, mm)
        git_ok(reflected, "add", "--", rel)
        code, out = staged_check(reflected)
    finally:
        restore(reflected)
    assert code == 1, f"커밋 전 검사 종료 코드 {code}(기대 1):\n{tail(out, 80)}"
    assert any(re.search(r"(?<![A-Za-z0-9])C5(?![0-9])", b) and row["id"] in b for b in fail_blocks(out)), \
        f"행 {row['id']}을 가리키는 C5 위반이 없습니다:\n{tail(out, 80)}"
