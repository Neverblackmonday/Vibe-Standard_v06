# -*- coding: utf-8 -*-
"""REQ-023 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-023 체크리스트 13 가운데 실행 결과로 확인하는 부분(③ ④ ⑤ ⑥ ⑦)이다(ACC-023 2절).
  설계 적용본: Departments/Design/workspace/REQ-023_적용본_vNN/        (가장 높은 버전)
  개발 적용본: Departments/Development/workspace/REQ-023_적용본_vNN/   (가장 높은 버전. 구현 단계 산출물)
  개발 결과서: Departments/Development/results/DEV-023_vNN.md           (가장 높은 버전. 구현 단계 산출물)
「현행 거버넌스 파일」은 REQ-023 5절 머리 안내대로 Workflow/ 전체와 .claude/agents/ 전체에서,
적용본이 있는 파일은 적용본을, 없는 파일은 원본을 말한다. 설계·개발 적용본에 같은 파일이 있으면 개발 쪽을 쓴다.
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
APPLIED_GLOB = "REQ-023_적용본_v[0-9][0-9]"
DEV_RESULT_NAME = re.compile(r"^DEV-023_v(\d{2})\.md$")

DOC_03 = "Workflow/03_라이프사이클.md"
DOC_07 = "Workflow/07_문서_서식_및_번호.md"
RES_TEMPLATE = "Workflow/templates/RES_TEMPLATE.md"
AGENT_NAMES = ("design.md", "development.md", "quality.md", "operations.md", "marketing.md", "visual.md")
EXISTING_ACC = tuple(f"Departments/Quality/results/{n}" for n in (
    "ACC-018_v01.md", "ACC-019_v01.md", "ACC-019_v02.md", "ACC-021_v01.md", "ACC-022_v01.md"))

# 띄어쓰기 변형까지 잡는다(EC-023 4절 위험 3, 3.4절 2번 검색 패턴과 같다).
OLD_NAME = re.compile(r"인수 ?시험 ?결과서")
REPORT_NAME = re.compile(r"시험 ?성적서")

HEADING = re.compile(r"^(#{1,6})\s")
HISTORY_HEADING = re.compile(r"^#{1,6}\s*개정 이력")
SEC_03_TESTING_ROOM = re.compile(r"^## 12\. 시험실")
SEC_RES_8 = re.compile(r"^## 8\. 인수 시험 판정")
SEC_07_DOC_SYSTEM = re.compile(r"^## 1\. 문서 체계")


# ---------------------------------------------------------------- 공통 도구

def _latest(base):
    dirs = sorted(p for p in base.glob(APPLIED_GLOB) if p.is_dir())
    return dirs[-1] if dirs else None


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


def _overlay(applied_root):
    """적용본 폴더에서 원본 위치 접두어(Workflow, .claude)와 그 적용본 폴더의 대응을 돌려준다."""
    if applied_root is None:
        return {}
    found = {}
    if (applied_root / "Workflow.적용본").is_dir():
        found["Workflow"] = applied_root / "Workflow.적용본"
    if (applied_root / ".claude.적용본").is_dir():
        found[".claude"] = applied_root / ".claude.적용본"
    if not found:
        found["Workflow"] = applied_root
    return found


@pytest.fixture(scope="session")
def roots(request):
    opt = request.config.getoption("--acc-design-dir")
    design = Path(opt) if opt else _latest(DESIGN_BASE)
    if design is None or not design.is_dir():
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-023_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    opt = request.config.getoption("--acc-dev-dir")
    dev = Path(opt) if opt else _latest(DEV_BASE)
    opt = request.config.getoption("--acc-original-dir")
    original = Path(opt) if opt else REPO / "Workflow"
    return {"design": design, "dev": dev, "original": original}


@pytest.fixture(scope="session")
def current(roots):
    """현행 거버넌스 파일: {논리 경로(Workflow/…, .claude/agents/…): 실제 파일}."""
    files = {}
    for p in _files(roots["original"]):
        files["Workflow/" + p.relative_to(roots["original"]).as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
    for applied in (roots["design"], roots["dev"]):  # 개발 적용본이 뒤에 와서 같은 파일이면 개발 쪽을 쓴다
        for prefix, folder in _overlay(applied).items():
            for p in _files(folder):
                rel = p.relative_to(folder).as_posix()
                if prefix == ".claude" and not rel.startswith("agents/"):
                    continue
                files[prefix + "/" + rel] = p
    return files


@pytest.fixture(scope="session")
def originals(roots):
    files = {}
    for p in _files(roots["original"]):
        files["Workflow/" + p.relative_to(roots["original"]).as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
    return files


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


def _table_rows(lines, nums):
    """줄 번호 집합 안의 표 데이터 행(머리 행과 구분 행을 뺀다)."""
    rows = [lines[n - 1] for n in sorted(nums) if lines[n - 1].lstrip().startswith("|")]
    return rows[2:]


def _hits(current, pattern):
    out = []
    for key in sorted(current):
        path = current[key]
        lines = _lines(path)
        for no, line in enumerate(lines, 1):
            if pattern.search(line):
                out.append((key, path, no, lines))
    return out


def _dev_result(request):
    opt = request.config.getoption("--acc-dev-result")
    if opt:
        path = Path(opt)
    else:
        found = []
        for p in DEV_RESULTS.glob("DEV-023_v*.md"):
            m = DEV_RESULT_NAME.match(p.name)
            if m:
                found.append((int(m.group(1)), p))
        if not found:
            pytest.fail("개발 결과서(Departments/Development/results/DEV-023_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
        path = max(found)[1]
    if not path.is_file():
        pytest.fail(f"개발 결과서가 없습니다: {path}")
    return path, path.read_text(encoding="utf-8-sig", errors="replace")


def _missing_hit_records(text, hits):
    # 「…:1」이 「…:14」에 맞지 않게 줄 번호 뒤에 숫자가 오지 않는 것만 센다.
    missing = []
    for _, path, no, _ in hits:
        ref = f"{_display(path)}:{no}"
        if not re.search(re.escape(ref) + r"(?!\d)", text):
            missing.append(ref)
    return missing


def _git_status(*paths):
    # 조회만 한다. GIT_OPTIONAL_LOCKS=0은 git status가 .git/index를 고쳐 쓰지 않게 한다.
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    proc = subprocess.run(["git", "status", "--porcelain", "-uall", "--", *paths], cwd=REPO, env=env,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, f"git status 실패(종료 코드 {proc.returncode}): {proc.stderr.strip()}"
    return [line for line in proc.stdout.splitlines() if line.strip()]


# ---------------------------------------------------------------- 체크리스트 13 ③ (D3)

def test_c13_3_old_name_only_in_history_rows(current):
    assert current, "현행 거버넌스 파일을 찾지 못했습니다"
    bad = []
    for key, path, no, lines in _hits(current, OLD_NAME):
        if no not in _history_rows(lines):
            bad.append(f"{_display(path)}:{no}: {lines[no - 1].strip()[:120]}")
    assert not bad, "현행 거버넌스 파일의 개정 이력 표 행 밖에 「인수 시험 결과서」가 남아 있습니다:\n" + "\n".join(bad)


def test_c13_3_dev_result_records_old_name_search(request, current):
    path, text = _dev_result(request)
    problems = []
    if not any("grep" in line and "결과서" in line for line in text.splitlines()):
        problems.append("개발 결과서에 「인수 시험 결과서」를 찾는 검색 명령(grep)이 없습니다")
    missing = _missing_hit_records(text, _hits(current, OLD_NAME))
    if missing:
        problems.append("검색 결과 원문 가운데 개발 결과서에 없는 줄(<경로>:<줄 번호>):\n" + "\n".join(missing))
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 13 ④ (D4)

def test_c13_4_report_name_only_in_allowed_places(current):
    bad = []
    for key, path, no, lines in _hits(current, REPORT_NAME):
        if no in _history_rows(lines):
            continue
        if key == DOC_03 and no in _section_lines(lines, SEC_03_TESTING_ROOM):
            continue
        if key == RES_TEMPLATE and no in _section_lines(lines, SEC_RES_8):
            continue
        bad.append(f"{_display(path)}:{no}: {lines[no - 1].strip()[:120]}")
    assert not bad, ("현행 거버넌스 파일에서 「시험성적서」가 03 「시험실」, RES_TEMPLATE.md 8절, 개정 이력 표 행 밖에 있습니다:\n"
                     + "\n".join(bad))


def test_c13_4_report_marking_in_testing_room_and_res_section8(current):
    problems = []
    for key, sec, need in ((DOC_03, SEC_03_TESTING_ROOM, ("시험성적서",)),
                           (RES_TEMPLATE, SEC_RES_8, ("시험성적서", "시험실"))):
        path = current.get(key)
        if path is None:
            problems.append(f"{key}가 현행 거버넌스 파일에 없습니다")
            continue
        lines = _lines(path)
        nums = _section_lines(lines, sec)
        if not nums:
            problems.append(f"{_display(path)}: 대상 절({sec.pattern})을 찾지 못했습니다")
            continue
        body = "\n".join(lines[n - 1] for n in sorted(nums))
        for word in need:
            if word not in body:
                problems.append(f"{_display(path)}: 대상 절({sec.pattern})에 「{word}」가 없습니다")
    assert not problems, "\n".join(problems)


def test_c13_4_dev_result_records_report_name_search(request, current):
    path, text = _dev_result(request)
    problems = []
    if not any("grep" in line and "성적서" in line for line in text.splitlines()):
        problems.append("개발 결과서에 「시험성적서」를 찾는 검색 명령(grep)이 없습니다")
    missing = _missing_hit_records(text, _hits(current, REPORT_NAME))
    if missing:
        problems.append("검색 결과 원문 가운데 개발 결과서에 없는 줄(<경로>:<줄 번호>):\n" + "\n".join(missing))
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 13 ⑤

def _doc_kinds(path):
    lines = _lines(path)
    rows = _table_rows(lines, _section_lines(lines, SEC_07_DOC_SYSTEM))
    return [r.strip().strip("|").split("|")[0].strip() for r in rows]


def test_c13_5_doc_system_kinds_same_as_original(current, originals):
    assert DOC_07 in originals, f"원본 {DOC_07}이 없습니다"
    before = _doc_kinds(originals[DOC_07])
    after = _doc_kinds(current[DOC_07])
    assert before, "원본 07 1절 「문서 체계」 표의 행을 읽지 못했습니다"
    assert after == before, (f"07 1절 「문서 체계」 표의 문서 종류가 원본과 다릅니다.\n원본: {before}\n현행: {after}\n"
                             f"(현행 파일 {_display(current[DOC_07])})")


def test_c13_5_template_list_same_as_original(current, originals):
    prefix = "Workflow/templates/"
    before = sorted(k for k in originals if k.startswith(prefix))
    after = sorted(k for k in current if k.startswith(prefix))
    assert before, "원본 Workflow/templates/ 아래 파일을 찾지 못했습니다"
    extra = [f"{k} ({_display(current[k])})" for k in after if k not in before]
    assert not extra, "현행 거버넌스 파일의 Workflow/templates/에 원본에 없는 파일이 있습니다:\n" + "\n".join(extra)
    assert after == before


def test_c13_5_original_templates_not_modified():
    out = _git_status("Workflow/templates")
    assert not out, "원본 Workflow/templates/에 변경이 있습니다(git status --porcelain -uall -- Workflow/templates):\n" + "\n".join(out)


# ---------------------------------------------------------------- 체크리스트 13 ⑥ (D3)

def test_c13_6_existing_acc_records_unchanged():
    out = _git_status("Departments/Quality/results")
    bad = [line for line in out if any(acc in line for acc in EXISTING_ACC)]
    assert not bad, "이미 작성된 ACC 기록에 변경이 있습니다(git status --porcelain -uall -- Departments/Quality/results):\n" + "\n".join(bad)


def test_c13_6_applied_history_keeps_existing_rows(roots, originals):
    checked = []
    problems = []
    for applied in (roots["design"], roots["dev"]):
        folder = _overlay(applied).get("Workflow")
        if folder is None:
            continue
        for p in _files(folder):
            key = "Workflow/" + p.relative_to(folder).as_posix()
            if key not in originals:
                continue
            orig_lines = _lines(originals[key])
            orig_rows = _table_rows(orig_lines, _history_rows(orig_lines))
            if not orig_rows:
                continue
            new_lines = _lines(p)
            new_rows = _table_rows(new_lines, _history_rows(new_lines))
            checked.append(_display(p))
            tail = new_rows[len(new_rows) - len(orig_rows):] if len(new_rows) >= len(orig_rows) else new_rows
            if tail != orig_rows:
                lost = [r[:80] for r in orig_rows if r not in new_rows]
                problems.append(f"{_display(p)}: 개정 이력 표의 기존 행이 원본과 다릅니다(새 행은 표 맨 위에만 더한다). "
                                f"원본 행 {len(orig_rows)}개, 적용본 행 {len(new_rows)}개. 적용본에 없는 원본 행:\n  "
                                + "\n  ".join(lost))
    assert checked, "개정 이력 표가 있는 적용본을 찾지 못했습니다"
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 13 ⑦

def test_c13_7_dev_result_records_comparison(request):
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
