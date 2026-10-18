# -*- coding: utf-8 -*-
"""REQ-026 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-026 체크리스트 12 ①~⑬ 가운데 실행 결과로 확인하는 부분이다(ACC-026 2절).
  설계 적용본: Departments/Design/workspace/REQ-026_적용본_vNN/        (명세 단계 산출물)
  개발 적용본: Departments/Development/workspace/REQ-026_적용본_vNN/   (구현 단계 산출물. EC G12상 없음)
  개발 결과서: Departments/Development/results/DEV-026_vNN.md           (가장 높은 버전. 구현 단계 산출물)

REQ-026 5절 머리 안내의 정의를 그대로 쓴다.
  「적용본」: 설계·개발 적용본 폴더의 최신 버전. 같은 파일이 양쪽에 있으면 개발 쪽을 쓴다.
  「현행 거버넌스 파일」: Workflow/ 전체, .claude/agents/ 전체, AGENTS.md에서 적용본이 있는 파일은 적용본,
    없는 파일은 원본(이 묶음을 「현행」이라 부른다).
적용본 안의 경로는 경로 조각 끝의 「.적용본」을 떼어 원본 경로로 바꾼다
(Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항. 예: AGENTS.md.적용본, Workflow.적용본/03_….md).
--acc-* 옵션은 결함 사본으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽고 git status를 조회하며,
체크리스트 12 ⑦에 따라 현행 03 5.2절 「완료 시각」 항이 정한 시각 조회 명령(읽기 전용)을 실행한다.
"""

import difflib
import os
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DESIGN_BASE = REPO / "Departments" / "Design" / "workspace"
DEV_BASE = REPO / "Departments" / "Development" / "workspace"
DEV_RESULTS = REPO / "Departments" / "Development" / "results"
APPLIED_GLOB = "REQ-026_적용본_v[0-9][0-9]"
DEV_RESULT_NAME = re.compile(r"^DEV-026_v(\d{2})\.md$")
SUFFIX = ".적용본"

AGENTS = "AGENTS.md"
DOC_02 = "Workflow/02_부서_구조_및_작업구역.md"
DOC_03 = "Workflow/03_라이프사이클.md"
DOC_05 = "Workflow/05_인수인계_및_실행명령.md"
DOC_07 = "Workflow/07_문서_서식_및_번호.md"
ORDER_T = "Workflow/templates/ORDER_TEMPLATE.md"
REQ_T = "Workflow/templates/REQ_TEMPLATE.md"
HOTFIX_T = "Workflow/templates/HOTFIX_TEMPLATE.md"
RES_T = "Workflow/templates/RES_TEMPLATE.md"
AGENT_NAMES = ("design.md", "development.md", "marketing.md", "operations.md", "quality.md", "visual.md")
RECORD_PATHS = ("Departments/Secretariat/docs/requests", "Departments/Secretariat/results",
                "Departments/Quality/results")

HEADING = re.compile(r"^(#{1,6})\s")
HISTORY = re.compile(r"^##\s*(\d+\.\s*)?개정 이력\s*$")
SEC_02_2 = re.compile(r"^##\s*2\.\s")
SEC_02_4 = re.compile(r"^##\s*4\.\s*작업 구역")
SEC_03_5_1 = re.compile(r"^###\s*5\.1\s")
SEC_03_5_2 = re.compile(r"^###\s*5\.2\s")
SEC_05_1_1 = re.compile(r"^###\s*1\.1\s")
SEC_07_1 = re.compile(r"^##\s*1\.\s*문서 체계")
SEC_07_3 = re.compile(r"^##\s*3\.\s*머리말")
SEC_07_3_1 = re.compile(r"^###\s*3\.1\s")
SEC_AGENTS_2 = re.compile(r"^##\s*2\.\s*불변 원칙")
SEC_RES_4 = re.compile(r"^##\s*4\.\s*검증 기록")
CODE = re.compile(r"`([^`]+)`")
HEADER_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")
LINK_TABLE_HEAD = re.compile(r"^\s*\|\s*기록\s*\|\s*이어지는 기록\s*\|\s*연결 자리\s*\|\s*$")
LINK_ROWS = ("HOTFIX", "승인 기록", "AUDIT", "브리핑", "조사 자료", "실험 파일")
SERVER_ROOM = re.compile(r"서버실|Storage/server")


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
    그 폴더 자체를 Workflow/의 적용본으로 본다(ACC-025의 방식과 같다).
    """
    if folder is None or not folder.is_dir():
        return {}
    tops = {_logical([p.name]) for p in folder.iterdir()}
    as_workflow = not (tops & {"Workflow", ".claude", "AGENTS.md"})
    out = {}
    for p in _files(folder):
        key = _logical(p.relative_to(folder).parts)
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
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-026_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    return {"design": design_all[-1], "dev": dev_all[-1] if dev_all else None}


@pytest.fixture(scope="session")
def originals():
    files = {}
    for p in _files(REPO / "Workflow"):
        files["Workflow/" + p.relative_to(REPO / "Workflow").as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
    files[AGENTS] = REPO / AGENTS
    return files


@pytest.fixture(scope="session")
def applied(roots):
    """최신 적용본: {원본 경로: 실제 파일}. 개발 적용본이 뒤에 와서 같은 파일이면 개발 쪽을 쓴다."""
    files = {}
    for folder in (roots["design"], roots["dev"]):
        files.update(_applied_map(folder))
    return files


@pytest.fixture(scope="session")
def current(originals, applied):
    files = dict(originals)
    files.update({k: v for k, v in applied.items()
                  if k == AGENTS or k.startswith("Workflow/") or k.startswith(".claude/agents/")})
    return files


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
    skip = set()
    for no, line in enumerate(lines, 1):
        if HISTORY.match(line):
            skip.update(_section(lines, HISTORY))
            break
    return [(no, line) for no, line in enumerate(lines, 1) if no not in skip]


def _stale_hits(current, needles):
    hits = []
    for key, path in sorted(current.items()):
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


def _field_order(path, field):
    """머리말에서 field와 scope:의 줄 위치. 없으면 None."""
    head = _header(path)
    pos = {"field": None, "scope": None}
    for i, line in enumerate(head):
        if pos["field"] is None and re.match(rf"^{re.escape(field)}:", line):
            pos["field"] = i
        if pos["scope"] is None and re.match(r"^scope:", line):
            pos["scope"] = i
    return pos


def _dev_result(request):
    opt = request.config.getoption("--acc-dev-result")
    if opt:
        path = Path(opt)
    else:
        found = []
        for p in DEV_RESULTS.glob("DEV-026_v*.md"):
            m = DEV_RESULT_NAME.match(p.name)
            if m:
                found.append((int(m.group(1)), p))
        if not found:
            pytest.fail("개발 결과서(Departments/Development/results/DEV-026_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
        path = max(found)[1]
    if not path.is_file():
        pytest.fail(f"개발 결과서가 없습니다: {path}")
    return path, path.read_text(encoding="utf-8-sig", errors="replace")


# ---------------------------------------------------------------- 체크리스트 12 ② (D2)

def test_c12_2_req_template_source_order_field(current):
    path = current[REQ_T]
    pos = _field_order(path, "source_order")
    assert pos["field"] is not None, f"{_display(path)} 머리말에 source_order 필드가 없습니다"
    assert pos["scope"] is not None and pos["field"] < pos["scope"], (
        f"{_display(path)} 머리말에서 source_order가 scope: 앞에 있지 않습니다(위치 {pos})")


def test_c12_2_order_row_related_req_unchanged(current, originals):
    def row(path):
        return [l for l in _section_lines(path, SEC_07_3) if l.startswith("| ORDER |")]
    before, after = row(originals[DOC_07]), row(current[DOC_07])
    assert len(before) == 1, f"원본 {_display(originals[DOC_07])} 3절에서 ORDER 행을 하나로 찾지 못했습니다: {before}"
    assert after == before, (f"07 3절 ORDER 행이 원본과 다릅니다(현행 파일 {_display(current[DOC_07])}).\n"
                             f"원본: {before}\n현행: {after}")


# ---------------------------------------------------------------- 체크리스트 12 ④ (D4)

def test_c12_4_no_stale_commit_message_rule(current):
    hits = _stale_hits(current, ("버전은 적지 않는다", "--format=%s"))
    assert not hits, ("현행 거버넌스 파일의 개정 이력 밖에 바뀌기 전 커밋 메시지 규칙(제목·근거 줄 구분 없는 "
                      "「버전은 적지 않는다」, 한글 확인 `--format=%s`)이 남아 있습니다:\n" + "\n".join(hits))


# ---------------------------------------------------------------- 체크리스트 12 ⑤ (D5)

def test_c12_5_hotfix_template_origin_field(current):
    path = current[HOTFIX_T]
    pos = _field_order(path, "origin")
    assert pos["field"] is not None, f"{_display(path)} 머리말에 origin 필드가 없습니다"
    assert pos["scope"] is not None and pos["field"] < pos["scope"], (
        f"{_display(path)} 머리말에서 origin이 scope: 앞에 있지 않습니다(위치 {pos})")


def test_c12_5_workflow02_lists_request_record(current):
    path = current[DOC_02]
    problems = []
    sec2 = [l for l in _section_lines(path, SEC_02_2) if l.startswith("| 비서실 |")]
    if len(sec2) != 1:
        problems.append(f"2절 표에서 비서실 행을 하나로 찾지 못했습니다: {len(sec2)}줄")
    elif "요청 기록" not in sec2[0]:
        problems.append("2절 표 비서실 행에 「요청 기록」이 없습니다")
    sec4 = [l for l in _section_lines(path, SEC_02_4) if re.match(r"^\|\s*요청 기록\s*\|", l)]
    if len(sec4) != 1:
        problems.append(f"4절 작업 구역 표에 「요청 기록」 행이 하나가 아닙니다({len(sec4)}줄)")
    elif "Departments/Secretariat/assets/inbox/" not in sec4[0]:
        problems.append("4절 「요청 기록」 행에 경로 Departments/Secretariat/assets/inbox/가 없습니다")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 12 ⑥ (D6)

def test_c12_6_link_table_rows(current):
    path = current[DOC_07]
    sec = _section_lines(path, SEC_07_1)
    start = next((i for i, l in enumerate(sec) if LINK_TABLE_HEAD.match(l)), None)
    assert start is not None, (f"{_display(path)} 1절에 머리가 「| 기록 | 이어지는 기록 | 연결 자리 |」인 "
                               "추적 관계 연결 표가 없습니다")
    rows = []
    for line in sec[start + 2:]:
        if not line.strip().startswith("|"):
            break
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    problems = []
    for name in LINK_ROWS:
        hit = [r for r in rows if name in r[0]]
        if not hit:
            problems.append(f"「{name}」 행이 없습니다")
        elif any(len(r) < 3 or not r[1] or not r[2] for r in hit):
            problems.append(f"「{name}」 행의 「이어지는 기록」 또는 「연결 자리」 칸이 비어 있습니다: {hit}")
    assert not problems, f"(현행 파일 {_display(path)} 1절 연결 표)\n" + "\n".join(problems)


def test_c12_6_order_template_source_line(current):
    path = current[ORDER_T]
    rows = [l for l in _lines(path) if re.match(r"^-\s*근거 자료\s*:", l)]
    assert len(rows) == 1, f"{_display(path)}에 「- 근거 자료:」 줄이 하나가 아닙니다({len(rows)}줄)"
    assert "조사 자료" in rows[0] and "외부 보고서" in rows[0], (
        f"「근거 자료」 줄에 조사 자료·외부 보고서가 없습니다: {rows[0]}")


# ---------------------------------------------------------------- 체크리스트 12 ⑦ (D7)

def _time_commands(path):
    """03 5.2절에서 「완료 시각」 항(6.)의 시각 조회 명령 코드 조각."""
    rows = [l for l in _section_lines(path, SEC_03_5_2) if re.match(r"^\d+\.\s*\*\*완료 시각", l)]
    cmds = []
    for row in rows:
        for span in CODE.findall(row):
            span = span.strip()
            if span.startswith("date ") or span.startswith("Get-Date"):
                cmds.append(span)
    return rows, cmds


def _run_time_command(cmd):
    """명령을 실행해 (실행 여부, 결과). 해당 도구가 없으면 (False, 사유)."""
    if cmd.startswith("date "):
        exe = shutil.which("date")
        if not exe:
            return False, "date 실행 파일을 찾지 못함"
        argv = [exe, *shlex.split(cmd, posix=True)[1:]]
    else:
        exe = shutil.which("powershell") or shutil.which("pwsh")
        if not exe:
            return False, "PowerShell 실행 파일을 찾지 못함"
        argv = [exe, "-NoProfile", "-NonInteractive", "-Command", cmd]
    proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return True, (proc.returncode, proc.stdout.strip(), proc.stderr.strip())


def test_c12_7_time_commands_output_header_format(current):
    rows, cmds = _time_commands(current[DOC_03])
    assert rows, f"현행 {_display(current[DOC_03])} 5.2절에 「완료 시각」 항이 없습니다"
    assert cmds, f"「완료 시각」 항에서 시각 조회 명령(`date …`, `Get-Date …`)을 찾지 못했습니다: {rows}"
    # 항이 든 명령은 모두 실행한다. 실행 파일을 찾지 못해도 실패로 본다(항이 「두 명령」 어느 쪽이든 쓰게 하므로).
    problems = []
    for cmd in cmds:
        ok, res = _run_time_command(cmd)
        if not ok:
            problems.append(f"{cmd}: 실행하지 못함({res})")
            continue
        code, out, err = res
        if code != 0 or not HEADER_TIME.match(out):
            problems.append(f"{cmd}: 종료 코드 {code}, 출력 {out!r}, stderr {err[:200]!r}. "
                            "머리말 형식 YYYY-MM-DDTHH:MM:SS+09:00과 같지 않습니다")
    assert not problems, "\n".join(problems)


def test_c12_7_res_template_completed_at(current):
    path = current[RES_T]
    _, cmds = _time_commands(current[DOC_03])
    problems = []
    head = [l for l in _header(path) if l.startswith("completed_at:")]
    if len(head) != 1:
        problems.append(f"머리말 completed_at 줄이 하나가 아닙니다({len(head)}줄)")
    elif "판정 세션의 명령 실행" not in head[0]:
        problems.append(f"머리말 completed_at 주석이 「판정 세션의 명령 실행」을 가리키지 않습니다: {head[0]}")
    rows = [l for l in _section_lines(path, SEC_RES_4) if re.match(r"^\|\s*완료 시각 조회\s*\|", l)]
    if len(rows) != 1:
        problems.append(f"4절 「검증 기록」에 「완료 시각 조회」 행이 하나가 아닙니다({len(rows)}줄)")
    else:
        spans = [s.strip() for s in CODE.findall(rows[0])]
        if not any(s in cmds for s in spans):
            problems.append(f"「완료 시각 조회」 행의 명령 {spans}이 03 5.2절 「완료 시각」 항의 명령 {cmds}에 없습니다")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


def test_c12_7_no_stale_time_example(current):
    hits = _stale_hits(current, ("Get-Date -Format o",))
    assert not hits, ("현행 거버넌스 파일의 개정 이력 밖에 머리말 형식과 출력이 다른 시각 조회 예 "
                      "`Get-Date -Format o`가 남아 있습니다:\n" + "\n".join(hits))


# ---------------------------------------------------------------- 체크리스트 12 ⑧ (D8)

def test_c12_8_staging_items_9_10(current):
    path = current[DOC_05]
    sec = _section_lines(path, SEC_05_1_1)
    problems = []
    for mark, where in (("⑨", "Departments/Secretariat/assets/briefings/"),
                        ("⑩", "Departments/Secretariat/assets/research/")):
        rows = [l for l in sec if re.match(rf"^\s*-\s*{mark}\s", l)]
        if len(rows) != 1:
            problems.append(f"1.1절에 「- {mark}」 항목이 하나가 아닙니다({len(rows)}줄)")
        elif where not in rows[0]:
            problems.append(f"「{mark}」 항목에 경로 {where}가 없습니다: {rows[0][:160]}")
    assert not problems, f"(현행 파일 {_display(path)})\n" + "\n".join(problems)


def test_c12_8_no_stale_staging_range(current):
    hits = _stale_hits(current, ("①~⑧",))
    assert not hits, "현행 거버넌스 파일의 개정 이력 밖에 바뀌기 전 스테이징 범위 「①~⑧」이 남아 있습니다:\n" + "\n".join(hits)


# ---------------------------------------------------------------- 체크리스트 12 ⑨ (D9)

def _body_same(current, originals, key, heading):
    def body(path):
        return _section_lines(path, heading)[1:]  # 제목 줄(리비전 태그)은 뺀다
    before, after = body(originals[key]), body(current[key])
    assert before, f"원본 {_display(originals[key])}에서 {heading.pattern} 절을 찾지 못했습니다"
    assert after, f"현행 {_display(current[key])}에서 {heading.pattern} 절을 찾지 못했습니다"
    diff = list(difflib.unified_diff(before, after, "원본", "현행", lineterm="", n=0))
    assert not diff, (f"{heading.pattern} 절 본문이 원본과 다릅니다(현행 파일 {_display(current[key])}):\n"
                      + "\n".join(diff[:20]))


def test_c12_9_lifecycle_5_1_same_as_original(current, originals):
    _body_same(current, originals, DOC_03, SEC_03_5_1)


def test_c12_9_numbering_3_1_same_as_original(current, originals):
    _body_same(current, originals, DOC_07, SEC_07_3_1)


# ---------------------------------------------------------------- 체크리스트 12 ⑩ (D10)

def test_c12_10_no_server_room_rule_added(applied, originals):
    bad = []
    for key, path in sorted(applied.items()):
        if not (key == AGENTS or key.startswith("Workflow/") or key.startswith(".claude/agents/")):
            continue
        before = _lines(originals[key]) if key in originals else []
        for line in difflib.unified_diff(before, _lines(path), lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++") and SERVER_ROOM.search(line):
                bad.append(f"{_display(path)}: {line[1:].strip()[:160]}")
    assert not bad, "원본과 적용본의 차이에 서버실(Storage/server)을 다루는 더한 줄이 있습니다:\n" + "\n".join(bad)


# ---------------------------------------------------------------- 체크리스트 12 ⑪ (D11)

def test_c12_11_agents_traceability_principle(current):
    path = current[AGENTS]
    rows = [l for l in _section_lines(path, SEC_AGENTS_2) if re.match(r"^\d+\.\s*\*\*추적성\*\*", l)]
    assert len(rows) == 1, f"{_display(path)} 2절 「불변 원칙」에 「추적성」 항이 하나가 아닙니다({len(rows)}줄)"
    assert "Workflow/07_문서_서식_및_번호" in rows[0] and "문서 체계" in rows[0], (
        f"「추적성」 항이 세부의 원천 `Workflow/07_문서_서식_및_번호` 「문서 체계」를 가리키지 않습니다: {rows[0][:200]}")


# ---------------------------------------------------------------- 체크리스트 12 ⑫ (D12)

def test_c12_12_no_other_records_changed(request):
    own = re.escape(request.config.getoption("--acc-own-req"))
    # 「이 REQ 번호」의 문서: <종류>-<번호>_…, <종류>-<번호>-REQ/EC/SPEC_…. 파생 안건(<번호>-n)은 다른 번호다.
    own_doc = re.compile(rf"^[A-Z]+-{own}(-(REQ|EC|SPEC))?_")
    bad = []
    for line in _git_status(*RECORD_PATHS):
        code = line[:2]
        if not (set(code) & set("MDRT")):
            continue  # 미추적(??)·추가(A)는 이미 작성된 기록의 변경이 아니다
        for p in _status_paths(line):
            if not own_doc.match(p.rsplit("/", 1)[-1]):
                bad.append(line)
                break
    assert not bad, ("git status --porcelain -uall -- " + " ".join(RECORD_PATHS)
                     + " 결과에 이 REQ 번호가 아닌 기록 경로의 수정이 있습니다:\n" + "\n".join(bad))


# ---------------------------------------------------------------- 체크리스트 12 ⑬

def test_c12_13_dev_result_records_comparison(request):
    path, text = _dev_result(request)
    problems = []
    if ".claude/agents" not in text:
        problems.append("개발 결과서에 대조 대상 「.claude/agents」가 없습니다")
    for name in AGENT_NAMES:
        if name not in text:
            problems.append(f"개발 결과서에 정의 파일 「{name}」의 대조 결과가 없습니다")
    if "check_standard.py" not in text:
        problems.append("개발 결과서에 「check_standard.py」 대조 결과가 없습니다")
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)
