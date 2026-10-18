# -*- coding: utf-8 -*-
"""REQ-027 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-027 체크리스트 6 ①~⑩ 가운데 실행 결과로 확인하는 부분이다(ACC-027 2절).
  설계 적용본: Departments/Design/workspace/REQ-027_적용본_vNN/        (명세 단계 산출물)
  개발 적용본: Departments/Development/workspace/REQ-027_적용본_vNN/   (구현 단계 산출물)
  개발 결과서: Departments/Development/results/DEV-027_vNN.md           (가장 높은 버전. 구현 단계 산출물)

REQ-027 5절 머리 안내의 정의를 그대로 쓴다.
  「적용본」: 설계·개발 적용본 폴더의 최신 버전. 같은 파일이 양쪽에 있으면 개발 쪽을 쓴다.
  「현행 거버넌스 파일」: Workflow/ 전체, .claude/agents/ 전체, AGENTS.md에서 적용본이 있는 파일은 적용본,
    없는 파일은 원본이며, 결과서의 반영 명령·삭제 대상이 지우는 파일은 뺀다(이 묶음을 「현행」이라 부른다).
  지우는 파일은 개발 결과서(DEV-027 최신)와 설계 결과서(RPT-027 최신)의 「삭제 대상」 절에 적힌 경로로 정한다.
  Grep 확인에서는 개정 이력 표(제목이 「개정 이력」인 절)를 뺀다.
적용본 안의 경로는 경로 조각 끝의 「.적용본」을 떼어 원본 경로로 바꾼다
(Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항. 예: AGENTS.md.적용본, .claude.적용본/agents/….md).
--acc-* 옵션은 결함 사본으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽고 git status를 조회한다.
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DESIGN_BASE = REPO / "Departments" / "Design" / "workspace"
DEV_BASE = REPO / "Departments" / "Development" / "workspace"
DEV_RESULTS = REPO / "Departments" / "Development" / "results"
DESIGN_RESULTS = REPO / "Departments" / "Design" / "results"
APPLIED_GLOB = "REQ-027_적용본_v[0-9][0-9]"
DEV_RESULT_NAME = re.compile(r"^DEV-027_v(\d{2})\.md$")
RPT_RESULT_NAME = re.compile(r"^RPT-027_v(\d{2})\.md$")
SUFFIX = ".적용본"

AGENTS = "AGENTS.md"
DOC_01 = "Workflow/01_표준_개요.md"
DOC_02 = "Workflow/02_부서_구조_및_작업구역.md"
DOC_03 = "Workflow/03_라이프사이클.md"
DOC_07 = "Workflow/07_문서_서식_및_번호.md"
ENGINEERING = ".claude/agents/engineering.md"
AGENT_NAMES = ("design.md", "development.md", "engineering.md", "marketing.md",
               "operations.md", "quality.md", "visual.md")
VISUAL_TRACKED = tuple(f"Departments/Visual/{p}/.gitkeep" for p in
                       ("assets/fonts", "assets/icons", "assets/images", "docs", "results", "workspace"))
MARKETING_NEW = tuple(f"Departments/Marketing/assets/{p}/.gitkeep" for p in ("icons", "fonts", "images"))
RECORD_PATHS = ("Departments/Secretariat/docs/requests", "Departments/Design/results",
                "Departments/Design/docs/tad", "Departments/Development/results",
                "Departments/Quality/results")

HEADING = re.compile(r"^(#{1,6})\s")
HISTORY = re.compile(r"^##\s*(\d+\.\s*)?개정 이력\s*$")
DELETE_HEADING = re.compile(r"^#{2,6}\s.*삭제 대상")
SEC_AGENTS_1 = re.compile(r"^##\s*1\.\s*조직")
SEC_01_4 = re.compile(r"^##\s*4\.\s*용어")
SEC_02_2 = re.compile(r"^##\s*2\.\s")
SEC_03_5 = re.compile(r"^##\s*5\.\s")
SEC_03_5_5 = re.compile(r"^###\s*5\.5\s*시각 디자인 단계")
SEC_07_1 = re.compile(r"^##\s*1\.\s*문서 체계")
CODE = re.compile(r"`([^`]+)`")
VISUAL_WORDS = ("비주얼", "visual", "Visual")
DESIGN_NAME_WORDS = ("`design`", "name: design")


# ---------------------------------------------------------------- 공통 도구

def _versions(base):
    return sorted(p for p in base.glob(APPLIED_GLOB) if p.is_dir())


def _lines(path):
    # grep과 같은 줄 번호를 얻으려고 줄바꿈을 \n으로만 나눈다(universal newline 변환을 끈다).
    with open(path, encoding="utf-8-sig", errors="replace", newline="") as f:
        return [line.rstrip("\r") for line in f.read().split("\n")]


def _files(root):
    return sorted(p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts)


def _display(path):
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def _logical(rel_parts):
    return "/".join(part[: -len(SUFFIX)] if part.endswith(SUFFIX) else part for part in rel_parts)


def _applied_map(folder):
    """적용본 폴더 안 파일을 {원본 경로: 실제 파일}로 돌려준다."""
    if folder is None or not folder.is_dir():
        return {}
    return {_logical(p.relative_to(folder).parts): p for p in _files(folder)}


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _latest(base, pattern, name_re):
    found = []
    for p in base.glob(pattern):
        m = name_re.match(p.name)
        if m:
            found.append((int(m.group(1)), p))
    return max(found)[1] if found else None


@pytest.fixture(scope="session")
def roots(request):
    d_opt = request.config.getoption("--acc-design-dir")
    v_opt = request.config.getoption("--acc-dev-dir")
    design_all = [Path(d_opt)] if d_opt else _versions(DESIGN_BASE)
    dev_all = [Path(v_opt)] if v_opt else _versions(DEV_BASE)
    if not design_all or not design_all[-1].is_dir():
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-027_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    return {"design": design_all[-1], "dev": dev_all[-1] if dev_all else None}


@pytest.fixture(scope="session")
def dev_result(request):
    """(경로, 본문). 개발 결과서가 없으면 (None, None)."""
    opt = request.config.getoption("--acc-dev-result")
    path = Path(opt) if opt else _latest(DEV_RESULTS, "DEV-027_v*.md", DEV_RESULT_NAME)
    if path is None or not path.is_file():
        return None, None
    return path, path.read_text(encoding="utf-8-sig", errors="replace")


def _require_dev(dev_result):
    path, text = dev_result
    if path is None:
        pytest.fail("개발 결과서(Departments/Development/results/DEV-027_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
    return path, text


def _deletion_paths(path):
    """결과서의 「삭제 대상」 절(제목에 「삭제 대상」이 든 절)에 코드 조각으로 적힌 경로."""
    if path is None or not path.is_file():
        return set()
    lines = _lines(path)
    out = set()
    level = None
    for line in lines:
        m = HEADING.match(line)
        if level is None:
            if DELETE_HEADING.match(line):
                level = len(m.group(1))
            continue
        if m and len(m.group(1)) <= level:
            level = None
            if DELETE_HEADING.match(line):
                level = len(m.group(1))
            continue
        for span in CODE.findall(line):
            # `git rm -- <경로>`처럼 명령째 적은 경우도 경로를 얻으려고 낱말마다 넣는다.
            out.add(span.strip())
            out.update(span.split())
    return out


@pytest.fixture(scope="session")
def deleted(dev_result):
    rpt = _latest(DESIGN_RESULTS, "RPT-027_v*.md", RPT_RESULT_NAME)
    return _deletion_paths(dev_result[0]) | _deletion_paths(rpt)


@pytest.fixture(scope="session")
def originals():
    files = {}
    for p in _files(REPO / "Workflow"):
        files["Workflow/" + p.relative_to(REPO / "Workflow").as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
    files[AGENTS] = REPO / AGENTS
    return files


def _governance(key):
    return key == AGENTS or key.startswith("Workflow/") or key.startswith(".claude/agents/")


@pytest.fixture(scope="session")
def applied(roots):
    """최신 적용본: {원본 경로: 실제 파일}. 개발 적용본이 뒤에 와서 같은 파일이면 개발 쪽을 쓴다."""
    files = {}
    for folder in (roots["design"], roots["dev"]):
        files.update(_applied_map(folder))
    return {k: v for k, v in files.items() if _governance(k)}


@pytest.fixture(scope="session")
def current(originals, applied, deleted):
    files = dict(originals)
    files.update(applied)
    return {k: v for k, v in files.items() if k not in deleted}


def _section(lines, heading):
    """heading에 맞는 제목 줄부터 같은 수준 이상의 다음 제목 앞까지의 줄 번호(1부터)."""
    nums = []
    level = None
    for no, line in enumerate(lines, 1):
        m = HEADING.match(line)
        if level is None:
            if heading.match(line):
                level = len(m.group(1)) if m else 2
                nums.append(no)
            continue
        if m and len(m.group(1)) <= level:
            break
        nums.append(no)
    return nums


def _section_lines(path, heading):
    lines = _lines(path)
    return [lines[n - 1] for n in _section(lines, heading)]


def _header(path):
    """첫 줄 --- 부터 다음 --- 앞까지의 머리말 줄."""
    lines = _lines(path)
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        out.append(line)
    return []


def _outside_history(path):
    """개정 이력 절(제목 「개정 이력」) 밖의 (줄 번호, 줄)."""
    lines = _lines(path)
    skip = set(_section(lines, HISTORY))
    return [(no, line) for no, line in enumerate(lines, 1) if no not in skip]


def _hits(files, needles):
    hits = []
    for key, path in sorted(files.items()):
        for no, line in _outside_history(path):
            for needle in needles:
                if needle in line:
                    hits.append(f"{_display(path)}:{no}: [{needle}] {line.strip()[:160]}")
    return hits


def _git(*args):
    # 조회만 한다. GIT_OPTIONAL_LOCKS=0은 git status가 .git/index를 고쳐 쓰지 않게 한다.
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    return subprocess.run(["git", *args], cwd=REPO, env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def _git_status(*paths):
    proc = _git("-c", "core.quotepath=false", "status", "--porcelain", "-uall", "--", *paths)
    assert proc.returncode == 0, f"git status 실패(종료 코드 {proc.returncode}): {proc.stderr.strip()}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _status_paths(line):
    return [p.strip().strip('"') for p in line[3:].split(" -> ")]


def _rows(path, heading, first_cell):
    return [l for l in _section_lines(path, heading)
            if l.strip().startswith("|") and _cells(l)[0] == first_cell]


# ---------------------------------------------------------------- 체크리스트 6 ① (D1)

def test_c6_1_marketing_starts_only_by_workflow(current):
    path = current[AGENTS]
    rows = _rows(path, SEC_AGENTS_1, "마케팅")
    assert len(rows) == 1, f"{_display(path)} 1절 조직 표에 첫 칸이 「마케팅」인 행이 하나가 아닙니다({len(rows)}줄)"
    assert "REQ `workflow:`에 기재된 경우에만 기동한다" in rows[0], (
        f"마케팅 행에 「REQ `workflow:`에 기재된 경우에만 기동한다」가 없습니다: {rows[0][:200]}")


# ---------------------------------------------------------------- 체크리스트 6 ③ (D3)

def test_c6_3_visual_is_marketing_function_in_three_docs(current):
    problems = []
    # AGENTS.md 1절: 비주얼이 조직으로 없고, 마케팅 행에 시각 디자인이 마케팅의 기능으로 적혀 있다.
    a_path = current[AGENTS]
    a_sec = _section_lines(a_path, SEC_AGENTS_1)
    if not a_sec:
        problems.append(f"{_display(a_path)}에 1절 「조직…」이 없습니다")
    bad = [l for l in a_sec if any(w in l for w in ("비주얼", "Departments/Visual"))]
    if bad:
        problems.append(f"{_display(a_path)} 1절에 비주얼이 남아 있습니다: {[l[:120] for l in bad]}")
    m_rows = _rows(a_path, SEC_AGENTS_1, "마케팅")
    if len(m_rows) != 1 or not ("시각 디자인" in m_rows[0] and "마케팅의 기능" in m_rows[0]):
        problems.append(f"{_display(a_path)} 1절 마케팅 행(하나)에 「시각 디자인」·「마케팅의 기능」이 없습니다: {m_rows}")
    # 01 「용어」 「조직」 행
    o_path = current[DOC_01]
    o_rows = _rows(o_path, SEC_01_4, "조직")
    if len(o_rows) != 1:
        problems.append(f"{_display(o_path)} 4절에 「조직」 행이 하나가 아닙니다({len(o_rows)}줄)")
    else:
        if "비주얼" in o_rows[0]:
            problems.append(f"{_display(o_path)} 「조직」 행에 비주얼이 남아 있습니다")
        if not ("시각 디자인" in o_rows[0] and "마케팅의 기능" in o_rows[0]):
            problems.append(f"{_display(o_path)} 「조직」 행에 「시각 디자인」·「마케팅의 기능」이 없습니다")
    # 02 2절: 비주얼 행이 없고, 시각 디자인이 마케팅의 기능으로 적혀 있다.
    t_path = current[DOC_02]
    t_sec = _section_lines(t_path, SEC_02_2)
    if _rows(t_path, SEC_02_2, "비주얼"):
        problems.append(f"{_display(t_path)} 2절 표에 비주얼 행이 남아 있습니다")
    if not any("시각 디자인" in l and "마케팅의 기능" in l for l in t_sec):
        problems.append(f"{_display(t_path)} 2절에 시각 디자인이 마케팅의 기능이라는 줄이 없습니다")
    assert not problems, "\n".join(problems)


def test_c6_3_no_visual_in_current_governance(current):
    hits = _hits(current, VISUAL_WORDS)
    assert not hits, ("현행 거버넌스 파일(개정 이력 표 제외, 결과서 삭제 대상 제외)에 "
                      "「비주얼」·`visual`·`Visual`이 남아 있습니다:\n" + "\n".join(hits))


def test_c6_3_dev_result_visual_processing(dev_result, deleted):
    path, text = _require_dev(dev_result)
    problems = []
    for p in (".claude/agents/visual.md",) + VISUAL_TRACKED:
        if p not in deleted:
            problems.append(f"개발 결과서 「삭제 대상」 절에 {p}가 없습니다")
    if ".claude.적용본/agents/marketing.md" not in text:
        problems.append("개발 결과서에 마케팅 정의 적용본(.claude.적용본/agents/marketing.md)이 없습니다")
    for p in MARKETING_NEW:
        if not (REPO / p).is_file():
            problems.append(f"작업 트리에 {p}가 없습니다")
    assert not problems, f"({_display(path)})\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 6 ④ (D4)

def test_c6_4_brand_and_screen_responsibility(current):
    path = current[DOC_02]
    problems = []
    m_rows = _rows(path, SEC_02_2, "마케팅")
    d_rows = _rows(path, SEC_02_2, "설계")
    if len(m_rows) != 1:
        problems.append(f"2절 표에 마케팅 행이 하나가 아닙니다({len(m_rows)}줄)")
    else:
        resp = _cells(m_rows[0])[2] if len(_cells(m_rows[0])) > 2 else ""
        for word in ("브랜드 자산", "화면의 시각 규칙"):
            if word not in resp:
                problems.append(f"마케팅 행 책임 칸에 「{word}」가 없습니다: {resp[:160]}")
    if len(d_rows) != 1:
        problems.append(f"2절 표에 설계 행이 하나가 아닙니다({len(d_rows)}줄)")
    else:
        resp = _cells(d_rows[0])[2] if len(_cells(d_rows[0])) > 2 else ""
        if "화면의 구조·동작 명세" not in resp:
            problems.append(f"설계 행 책임 칸에 「화면의 구조·동작 명세」가 없습니다: {resp[:160]}")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 6 ⑤ (D5)

def test_c6_5_dev_engineering_definition(roots):
    dev = _applied_map(roots["dev"])
    assert ENGINEERING in dev, ("개발 적용본(Departments/Development/workspace/REQ-027_적용본_vNN 최신)에 "
                                ".claude/agents/engineering.md가 없습니다. 구현 단계 산출물이 있어야 합니다.")
    names = [l for l in _header(dev[ENGINEERING]) if l.startswith("name:")]
    assert names == ["name: engineering"], f"{_display(dev[ENGINEERING])} 머리말 name 줄이 「name: engineering」 하나가 아닙니다: {names}"


def test_c6_5_dev_result_deletes_design(dev_result, deleted):
    path, _ = _require_dev(dev_result)
    assert ".claude/agents/design.md" in deleted, f"{_display(path)} 「삭제 대상」 절에 .claude/agents/design.md가 없습니다"


def test_c6_5_workflow02_subagent_engineering(current):
    path = current[DOC_02]
    rows = _rows(path, SEC_02_2, "설계")
    assert len(rows) == 1, f"{_display(path)} 2절 표에 설계 행이 하나가 아닙니다({len(rows)}줄)"
    cells = _cells(rows[0])
    assert len(cells) > 1 and cells[1] == "`engineering`", (
        f"{_display(path)} 2절 표 설계 행의 서브에이전트 열이 `engineering`이 아닙니다: {cells[1:2]}")


def test_c6_5_no_design_subagent_name(current):
    hits = _hits(current, DESIGN_NAME_WORDS)
    assert not hits, ("현행 거버넌스 파일(개정 이력 표 제외, 결과서 삭제 대상 제외)에 설계 서브에이전트를 "
                      "`design`으로 부르는 곳(`` `design` ``, `name: design`)이 있습니다:\n" + "\n".join(hits))


# ---------------------------------------------------------------- 체크리스트 6 ⑥ (D6)

DESIGN_FOLDER = "Departments/Design"
DESIGN_NOTATION = re.compile(r"\bDesign: ")
RENAMED = re.compile(r"Departments/Engineering|\bEngineering: ")


def test_c6_6_design_folder_and_notation_kept(applied, originals, current):
    problems = []
    for key, path in sorted(applied.items()):
        if key not in originals:
            continue
        before = [l for _, l in _outside_history(originals[key])]
        after = [l for _, l in _outside_history(path)]
        for label, count in (("Departments/Design", lambda ls: sum(l.count(DESIGN_FOLDER) for l in ls)),
                             ("workflow: 부서 표기 Design", lambda ls: sum(len(DESIGN_NOTATION.findall(l)) for l in ls))):
            b, a = count(before), count(after)
            if a < b:
                problems.append(f"{_display(path)}: {label} 개수가 원본 {b}에서 {a}로 줄었습니다")
    for key, path in sorted(current.items()):
        for no, line in _outside_history(path):
            if RENAMED.search(line):
                problems.append(f"{_display(path)}:{no}: 바뀐 부서 폴더·표기 {line.strip()[:160]}")
    assert not problems, "\n".join(problems)


def test_c6_6_design_folder_status(request):
    own = request.config.getoption("--acc-own-req")
    allowed = (f"Departments/Design/docs/tad/EC-{own}", f"Departments/Design/results/RPT-{own}",
               f"Departments/Design/workspace/REQ-{own}_")
    bad = [line for line in _git_status("Departments/Design")
           if any(not p.startswith(allowed) for p in _status_paths(line))]
    assert not bad, ("git status --porcelain -uall -- Departments/Design 결과에 " + ", ".join(allowed)
                     + " 밖의 경로가 있습니다:\n" + "\n".join(bad))


# ---------------------------------------------------------------- 체크리스트 6 ⑦ (D7)

def test_c6_7_design_doc_in_document_system(current):
    path = current[DOC_07]
    rows = [l for l in _section_lines(path, SEC_07_1)
            if l.strip().startswith("|") and "Departments/Marketing/docs/DESIGN.md" in l]
    assert len(rows) == 1, f"{_display(path)} 1절에 Departments/Marketing/docs/DESIGN.md를 담은 표 행이 하나가 아닙니다({len(rows)}줄)"
    cells = _cells(rows[0])
    problems = []
    if len(cells) < 5:
        problems.append(f"행의 칸 수가 모자랍니다: {cells}")
    else:
        if cells[2] != "마케팅":
            problems.append(f"작성 주체 칸이 「마케팅」이 아닙니다: {cells[2]}")
        if "버전을 붙이지 않는다" not in cells[3]:
            problems.append(f"위치 칸에 파일명에 버전을 붙이지 않는다는 문구가 없습니다: {cells[3]}")
    assert not problems, f"(현행 파일 {_display(path)} 1절 문서 체계 표)\n" + "\n".join(problems)


def test_c6_7_no_new_template_file():
    bad = [line for line in _git_status("Workflow/templates") if line.startswith("??")]
    assert not bad, "git status --porcelain -uall -- Workflow/templates 결과에 `??` 줄이 있습니다:\n" + "\n".join(bad)


def test_c6_7_no_design_md_created():
    lines = _git_status("Departments/Marketing")
    bad = [line for line in lines if any(p.endswith("DESIGN.md") for p in _status_paths(line))]
    assert not bad, "git status --porcelain -uall -- Departments/Marketing 결과에 DESIGN.md가 있습니다:\n" + "\n".join(bad)
    assert not (REPO / "Departments/Marketing/docs/DESIGN.md").exists(), "Departments/Marketing/docs/DESIGN.md가 있습니다"


# ---------------------------------------------------------------- 체크리스트 6 ⑧ (D8)

def test_c6_8_design_review_rule_and_criteria(current):
    path = current[DOC_03]
    problems = []
    rows = _rows(path, SEC_03_5, "시각 디자인 판정")
    if len(rows) != 1:
        problems.append(f"5절 표에 「시각 디자인 판정」 행이 하나가 아닙니다({len(rows)}줄)")
    else:
        cells = _cells(rows[0])
        if len(cells) < 5 or cells[1] != "품질" or "RES-xxx-DESIGN" not in cells[3] or "①" not in cells[4]:
            problems.append(f"「시각 디자인 판정」 행의 부서(품질)·산출물(RES-xxx-DESIGN)·판정 기준(①…)이 맞지 않습니다: {cells}")
    sec = _section_lines(path, SEC_03_5_5)
    if not sec:
        problems.append("5.5절 「시각 디자인 단계」가 없습니다")
    else:
        judge = [l for l in sec if re.match(r"^\d+\.\s*\*\*판정\*\*", l)]
        if len(judge) != 1 or "품질" not in judge[0]:
            problems.append(f"5.5절에 품질이 판정한다는 「판정」 항이 하나가 아닙니다: {judge}")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


def test_c6_8_implementation_input(current):
    path = current[DOC_03]
    rows = _rows(path, SEC_03_5, "구현")
    assert len(rows) == 1, f"{_display(path)} 5절 표에 「구현」 행이 하나가 아닙니다({len(rows)}줄)"
    cells = _cells(rows[0])
    assert len(cells) > 2 and "판정 `pass`를 받은 시각 디자인 문서" in cells[2], (
        f"「구현」 행 입력 칸에 「판정 `pass`를 받은 시각 디자인 문서」가 없습니다: {cells[2:3]}")


def test_c6_8_design_and_dev_input_rule(current):
    path = current[DOC_03]
    sec = _section_lines(path, SEC_03_5_5)
    assert sec, f"{_display(path)}에 5.5절 「시각 디자인 단계」가 없습니다"
    problems = []
    for who in ("설계", "개발"):
        rows = [l for l in sec if re.match(rf"^\s*-\s*{who}\s*:", l)]
        if len(rows) != 1:
            problems.append(f"5.5절에 「- {who}:」 항목이 하나가 아닙니다({len(rows)}줄)")
        elif not ("시각 디자인 문서" in rows[0] and "입력" in rows[0]):
            problems.append(f"「- {who}:」 항목에 시각 디자인 문서를 입력으로 쓴다는 문구가 없습니다: {rows[0][:160]}")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 6 ⑨ (D9)

def test_c6_9_application_timing_rule(current):
    path = current[DOC_02]
    rows = [l for l in _section_lines(path, SEC_02_2)
            if "`REQ-027` 커밋 뒤에 기동하는 PM 세션" in l and "engineering" in l]
    assert len(rows) == 1, (f"{_display(path)} 2절에 서브에이전트 이름·조직 구성의 적용 시점"
                            f"(`REQ-027` 커밋 뒤에 기동하는 PM 세션) 항목이 하나가 아닙니다({len(rows)}줄)")
    assert "바꾸지 않는다" in rows[0], f"적용 시점 항목에 이미 작성된 기록을 바꾸지 않는다는 문구가 없습니다: {rows[0][:200]}"


def test_c6_9_no_other_records_changed(request):
    own = re.escape(request.config.getoption("--acc-own-req"))
    # 「이 REQ 번호」의 문서: <종류>-<번호>_…, <종류>-<번호>-REQ/EC/SPEC/DESIGN_…. 파생 안건(<번호>-n)은 다른 번호다.
    own_doc = re.compile(rf"^[A-Z]+-{own}(-(REQ|EC|SPEC|DESIGN))?_")
    bad = []
    for line in _git_status(*RECORD_PATHS):
        if not (set(line[:2]) & set("MDRT")):
            continue  # 미추적(??)·추가(A)는 이미 작성된 기록의 변경이 아니다
        if any(not own_doc.match(p.rsplit("/", 1)[-1]) for p in _status_paths(line)):
            bad.append(line)
    assert not bad, ("git status --porcelain -uall -- " + " ".join(RECORD_PATHS)
                     + " 결과에 이 REQ 번호가 아닌 기록 경로의 수정이 있습니다:\n" + "\n".join(bad))


# ---------------------------------------------------------------- 체크리스트 6 ⑩

COMPARE_HEADING = re.compile(r"^#{2,6}\s.*대조")


def test_c6_10_dev_result_records_comparison(dev_result):
    path, _ = _require_dev(dev_result)
    # EC 3.8절 6번: 대조 결과는 개발 결과서의 「대조」 절에 적는다. 제목에 「대조」가 든 절의 본문만 본다.
    lines = _lines(path)
    level, picked = None, []
    for line in lines:
        m = HEADING.match(line)
        if m and (level is None or len(m.group(1)) <= level):
            level = len(m.group(1)) if COMPARE_HEADING.match(line) else None
            continue
        if level is not None:
            picked.append(line)
    text = "\n".join(picked)
    problems = []
    if not picked:
        problems.append("개발 결과서에 제목에 「대조」가 든 절이 없습니다")
    if ".claude/agents" not in text:
        problems.append("개발 결과서에 대조 대상 「.claude/agents」가 없습니다")
    for name in AGENT_NAMES:
        if name not in text:
            problems.append(f"개발 결과서에 정의 파일 「{name}」의 대조 결과가 없습니다")
    if "check_standard.py" not in text:
        problems.append("개발 결과서에 「check_standard.py」 대조 결과가 없습니다")
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)
