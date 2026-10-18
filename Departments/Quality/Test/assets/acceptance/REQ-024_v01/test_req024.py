# -*- coding: utf-8 -*-
"""REQ-024 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-024 체크리스트 11 가운데 실행 결과로 확인하는 부분(① ④ ⑥ ⑦ ⑧ ⑨의 실행 부분)이다(ACC-024 2절).
  설계 적용본: Departments/Design/workspace/REQ-024_적용본_vNN/        (명세 단계 산출물)
  개발 적용본: Departments/Development/workspace/REQ-024_적용본_vNN/   (구현 단계 산출물. G11에 따라 없을 수 있다)
  개발 결과서: Departments/Development/results/DEV-024_vNN.md           (가장 높은 버전. 구현 단계 산출물)

REQ-024 5절 머리 안내의 정의를 그대로 쓴다.
  「현행 거버넌스 파일」: Workflow/ 전체, .claude/agents/ 전체, AGENTS.md에서 적용본이 있는 파일은 적용본(최신 버전
    폴더), 없는 파일은 원본. 설계·개발 적용본에 같은 파일이 있으면 개발 쪽을 쓴다.
  「적용본이 없다」: 설계·개발 적용본 폴더의 모든 버전 안에 그 원본 경로에 해당하는 파일이 없다.
적용본 안의 경로는 경로 조각 끝의 「.적용본」을 떼어 원본 경로로 바꾼다
(Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항. 예: Workflow.적용본/03_….md, AGENTS.md.적용본).
--acc-* 옵션은 결함 사본으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽고 git status를 조회만 하며 임시 파일을 만들지 않는다.
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
APPLIED_GLOB = "REQ-024_적용본_v[0-9][0-9]"
DEV_RESULT_NAME = re.compile(r"^DEV-024_v(\d{2})\.md$")
SUFFIX = ".적용본"

DOC_01 = "Workflow/01_표준_개요.md"
DOC_03 = "Workflow/03_라이프사이클.md"
DOC_07 = "Workflow/07_문서_서식_및_번호.md"
NCR_TEMPLATE = "Workflow/templates/NCR_TEMPLATE.md"
DEV_TEMPLATE = "Workflow/templates/DEV_TEMPLATE.md"
AGENTS = "AGENTS.md"
AGENT_NAMES = ("design.md", "development.md", "quality.md", "operations.md", "marketing.md", "visual.md")

# 체크리스트 11 ⑧의 글자열. 띄어쓰기 변형까지 잡는다(EC-024 3.4절 3번 검색 패턴과 같다).
RP_DOC = re.compile(r"재작업 ?절차서")

HEADING = re.compile(r"^(#{1,6})\s")
HISTORY_HEADING = re.compile(r"^#{1,6}\s*개정 이력")
SEC_TERMS = re.compile(r"^#{2,3}\s*\d+\.\s*용어")
SEC_HOTFIX = re.compile(r"^#{2,3}\s*\d+\.\s*핫픽스 트랙")
HOTFIX_CONDITION = re.compile(r"^\s*-\s*\*\*대상 조건")


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
    """적용본 폴더 안 파일을 {원본 경로: 실제 파일}로 돌려준다.

    폴더 바로 아래에 Workflow·.claude·AGENTS.md에 해당하는 것이 없으면(Red 확인용으로 다른 폴더를 준 경우)
    그 폴더 자체를 Workflow/의 적용본으로 본다(ACC-023의 방식과 같다).
    """
    if folder is None or not folder.is_dir():
        return {}
    tops = {_logical([p.name]) for p in folder.iterdir()}
    as_workflow = not (tops & {"Workflow", ".claude", AGENTS})
    out = {}
    for p in _files(folder):
        rel = p.relative_to(folder).parts
        key = _logical(rel)
        if as_workflow:
            key = "Workflow/" + key
        out[key] = p
    return out


@pytest.fixture(scope="session")
def roots(request):
    d_opt = request.config.getoption("--acc-design-dir")
    v_opt = request.config.getoption("--acc-dev-dir")
    design_all = [Path(d_opt)] if d_opt else _versions(DESIGN_BASE)
    dev_all = [Path(v_opt)] if v_opt else _versions(DEV_BASE)
    if not design_all or not design_all[-1].is_dir():
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-024_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    o_opt = request.config.getoption("--acc-original-dir")
    return {
        "design": design_all[-1],
        "dev": dev_all[-1] if dev_all else None,
        # 「적용본이 없다」의 확인 대상. 옵션을 하나라도 주면 준 폴더만 본다.
        "all": ([Path(x) for x in (d_opt, v_opt) if x] if (d_opt or v_opt) else design_all + dev_all),
        "original": Path(o_opt) if o_opt else REPO / "Workflow",
    }


def _in_scope(key):
    return key.startswith("Workflow/") or key.startswith(".claude/agents/") or key == AGENTS


@pytest.fixture(scope="session")
def originals(roots):
    files = {}
    for p in _files(roots["original"]):
        files["Workflow/" + p.relative_to(roots["original"]).as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
    if (REPO / AGENTS).is_file():
        files[AGENTS] = REPO / AGENTS
    return files


@pytest.fixture(scope="session")
def current(roots, originals):
    """현행 거버넌스 파일: {원본 경로: 실제 파일}. 개발 적용본이 뒤에 와서 같은 파일이면 개발 쪽을 쓴다."""
    files = dict(originals)
    for applied in (roots["design"], roots["dev"]):
        for key, p in _applied_map(applied).items():
            if _in_scope(key):
                files[key] = p
    return files


def _applied_hits(roots, targets):
    found = []
    for folder in roots["all"]:
        for key, p in _applied_map(folder).items():
            if key in targets:
                found.append(f"{key} <- {_display(p)}")
    return found


def _section_lines(lines, heading):
    """heading에 맞는 제목 줄부터 같은 수준 이상의 다음 제목 앞까지의 줄 번호(1부터)."""
    nums = set()
    level = None
    for no, line in enumerate(lines, 1):
        m = HEADING.match(line)
        if level is None:
            if heading.match(line):
                level = len(m.group(1)) if m else 2
                nums.add(no)
            continue
        if m and len(m.group(1)) <= level:
            break
        nums.add(no)
    return nums


def _history_rows(lines):
    """개정 이력 절 안의 표 행 줄 번호(1부터)."""
    nums = set()
    inside = False
    for no, line in enumerate(lines, 1):
        if HISTORY_HEADING.match(line):
            inside = True
            continue
        if inside and HEADING.match(line):
            inside = False
        if inside and line.lstrip().startswith("|"):
            nums.add(no)
    return nums


def _term_rows(lines):
    """「용어」 절 안의 표 행 줄 번호(1부터)."""
    return {n for n in _section_lines(lines, SEC_TERMS) if lines[n - 1].lstrip().startswith("|")}


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def _excluded(key, lines):
    """대조에서 빼는 줄: 「용어」 표(Workflow/01)와 개정 이력 표 행."""
    nums = set(_history_rows(lines))
    if key == DOC_01:
        nums |= _term_rows(lines)
    return nums


def _git_status(*paths):
    # 조회만 한다. GIT_OPTIONAL_LOCKS=0은 git status가 .git/index를 고쳐 쓰지 않게 한다.
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall", "--", *paths],
                          cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"git status 실패(종료 코드 {proc.returncode}): {proc.stderr.strip()}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


def _status_paths(line):
    body = line[3:]
    return [p.strip().strip('"') for p in body.split(" -> ")]


def _dev_result(request):
    opt = request.config.getoption("--acc-dev-result")
    if opt:
        path = Path(opt)
    else:
        found = []
        for p in DEV_RESULTS.glob("DEV-024_v*.md"):
            m = DEV_RESULT_NAME.match(p.name)
            if m:
                found.append((int(m.group(1)), p))
        if not found:
            pytest.fail("개발 결과서(Departments/Development/results/DEV-024_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
        path = max(found)[1]
    if not path.is_file():
        pytest.fail(f"개발 결과서가 없습니다: {path}")
    return path, path.read_text(encoding="utf-8-sig", errors="replace")


# ---------------------------------------------------------------- 체크리스트 11 ① (D1)

def test_c11_1_no_ncr_dev_template_applied(roots):
    found = _applied_hits(roots, {NCR_TEMPLATE, DEV_TEMPLATE})
    assert not found, "NCR_TEMPLATE.md·DEV_TEMPLATE.md의 적용본이 있습니다:\n" + "\n".join(found)


def test_c11_1_ncr_dev_templates_status_clean():
    out = _git_status(NCR_TEMPLATE, DEV_TEMPLATE)
    assert not out, "git status --porcelain -uall -- " + f"{NCR_TEMPLATE} {DEV_TEMPLATE} 결과가 비어 있지 않습니다:\n" + "\n".join(out)


# ---------------------------------------------------------------- 체크리스트 11 ④ (D4)

def test_c11_4_no_agents_applied(roots):
    found = _applied_hits(roots, {AGENTS})
    assert not found, "AGENTS.md의 적용본이 있습니다:\n" + "\n".join(found)


def _hotfix_condition(path):
    lines = _lines(path)
    nums = _section_lines(lines, SEC_HOTFIX)
    rows = [lines[n - 1] for n in sorted(nums) if HOTFIX_CONDITION.match(lines[n - 1])]
    return nums, rows


def test_c11_4_hotfix_condition_same_as_original(current, originals):
    assert DOC_03 in originals, f"원본 {DOC_03}이 없습니다"
    o_sec, before = _hotfix_condition(originals[DOC_03])
    c_sec, after = _hotfix_condition(current[DOC_03])
    assert o_sec and before, f"원본 {_display(originals[DOC_03])}에서 「핫픽스 트랙」 절의 대상 조건 줄을 찾지 못했습니다"
    assert c_sec, f"현행 {_display(current[DOC_03])}에 「핫픽스 트랙」 절이 없습니다"
    assert after == before, (f"「핫픽스 트랙」 절의 대상 조건이 원본과 다릅니다.\n원본: {before}\n현행: {after}\n"
                             f"(현행 파일 {_display(current[DOC_03])})")


def test_c11_4_agents_status_clean():
    out = _git_status(AGENTS)
    assert not out, "git status --porcelain -uall -- AGENTS.md 결과가 비어 있지 않습니다:\n" + "\n".join(out)


# ---------------------------------------------------------------- 체크리스트 11 ⑥ (D6)

def test_c11_6_no_other_res_changed(request):
    own = re.escape(request.config.getoption("--acc-own-req"))
    # 「이 REQ 번호」의 판정서: RES-<번호>_vNN, RES-<번호>-REQ/EC/SPEC_vNN. 파생 안건(RES-<번호>-n)은 다른 번호다.
    own_res = re.compile(rf"^RES-{own}(-(REQ|EC|SPEC))?_v\d{{2}}\.md$")
    bad = []
    for line in _git_status("Departments/Quality/results"):
        for p in _status_paths(line):
            name = p.rsplit("/", 1)[-1]
            if name.startswith("RES-") and not own_res.match(name):
                bad.append(line)
                break
    assert not bad, ("git status --porcelain -uall -- Departments/Quality/results 결과에 이 REQ 번호가 아닌 RES-* 경로가 있습니다:\n"
                     + "\n".join(bad))


# ---------------------------------------------------------------- 체크리스트 11 ⑦

def test_c11_7_template_list_same_as_original(current, originals):
    prefix = "Workflow/templates/"
    before = sorted(k for k in originals if k.startswith(prefix))
    after = sorted(k for k in current if k.startswith(prefix))
    assert before, "원본 Workflow/templates/ 아래 파일을 찾지 못했습니다"
    extra = [f"{k} ({_display(current[k])})" for k in after if k not in before]
    assert not extra, "현행 거버넌스 파일의 Workflow/templates/에 원본에 없는 파일이 있습니다:\n" + "\n".join(extra)
    assert after == before


def test_c11_7_no_doc07_applied(roots):
    found = _applied_hits(roots, {DOC_07})
    assert not found, "Workflow/07_문서_서식_및_번호.md의 적용본이 있습니다:\n" + "\n".join(found)


def test_c11_7_doc07_templates_status_clean():
    out = _git_status(DOC_07, "Workflow/templates")
    assert not out, ("git status --porcelain -uall -- Workflow/07_문서_서식_및_번호.md Workflow/templates 결과가 비어 있지 않습니다:\n"
                     + "\n".join(out))


# ---------------------------------------------------------------- 체크리스트 11 ⑧

def _rework_repair_row(current):
    lines = _lines(current[DOC_01])
    rows = [(n, _cells(lines[n - 1])) for n in sorted(_term_rows(lines))]
    rows = [(n, c) for n, c in rows if len(c) >= 3]
    for n, c in rows:  # Rework·Repair 행
        if "Rework" in c[0] or "Repair" in c[0]:
            return n, c
    for n, c in rows:  # 따로 행을 두지 않고 다른 행의 뜻에 넣은 경우
        if "Rework" in c[1] and "Repair" in c[1]:
            return n, c
    return None, None


def test_c11_8_term_row_unused_words_not_used(current):
    no, cells = _rework_repair_row(current)
    assert cells, (f"현행 {_display(current[DOC_01])} 「용어」 표에서 Rework·Repair의 행을 찾지 못했습니다"
                   "(체크리스트 11 ⑧ 첫 문장)")
    words = [w.strip() for w in cells[2].split(",") if w.strip() and w.strip() not in ("—", "-")]
    # 괄호가 있는 말은 괄호 안 맥락으로 판단하므로 열람 부분이다(ACC-024 2절). 괄호가 없는 말만 모든 쓰임을 본다.
    plain = [w for w in words if "(" not in w]
    bad = []
    for key in sorted(current):
        path = current[key]
        lines = _lines(path)
        skip = _excluded(key, lines)
        for n, line in enumerate(lines, 1):
            if n in skip:
                continue
            for w in plain:
                if w in line:
                    bad.append(f"{_display(path)}:{n}: 「{w}」: {line.strip()[:120]}")
    assert not bad, ("「용어」 표와 개정 이력 표 밖에서 Rework·Repair 행"
                     f"({_display(current[DOC_01])}:{no})의 쓰지 않는 말을 썼습니다:\n" + "\n".join(bad))


def test_c11_8_no_rework_procedure_string(current):
    bad = []
    for key in sorted(current):
        path = current[key]
        lines = _lines(path)
        skip = _excluded(key, lines)
        for n, line in enumerate(lines, 1):
            if n not in skip and RP_DOC.search(line):
                bad.append(f"{_display(path)}:{n}: {line.strip()[:120]}")
    assert not bad, "「용어」 표와 개정 이력 표 밖에서 「재작업 절차서」를 썼습니다:\n" + "\n".join(bad)


# ---------------------------------------------------------------- 체크리스트 11 ⑨

def test_c11_9_dev_result_records_comparison(request):
    path, text = _dev_result(request)
    problems = []
    if not re.search(r"^#+ .*대조", text, re.M):
        problems.append("개발 결과서에 「대조」 절이 없습니다")
    for target in (".claude/agents", "check_standard.py"):
        if target not in text:
            problems.append(f"개발 결과서에 대조 대상 「{target}」이 없습니다")
    for name in AGENT_NAMES:
        if name not in text:
            problems.append(f"개발 결과서에 정의 파일 「{name}」의 대조 결과가 없습니다")
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)
