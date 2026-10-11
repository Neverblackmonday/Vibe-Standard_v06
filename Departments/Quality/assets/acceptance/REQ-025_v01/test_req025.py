# -*- coding: utf-8 -*-
"""REQ-025 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-025 체크리스트 1~5 가운데 실행 결과로 확인하는 부분이다(ACC-025 2절).
  설계 적용본: Departments/Design/workspace/REQ-025_적용본_vNN/        (명세 단계 산출물)
  개발 적용본: Departments/Development/workspace/REQ-025_적용본_vNN/   (구현 단계 산출물)
  개발 결과서: Departments/Development/results/DEV-025_vNN.md           (가장 높은 버전. 구현 단계 산출물)

REQ-025 5절 머리 안내의 정의를 그대로 쓴다.
  「적용본」: 설계·개발 적용본 폴더의 최신 버전. 같은 파일이 양쪽에 있으면 개발 쪽을 쓴다.
    적용본이 없는 파일은 원본을 쓴다(이 묶음을 「현행」이라 부른다).
  「적용본이 없다」: 설계·개발 적용본 폴더의 모든 버전 안에 그 원본 경로에 해당하는 파일이 없다.
적용본 안의 경로는 경로 조각 끝의 「.적용본」을 떼어 원본 경로로 바꾼다
(Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항. 예: Workflow.적용본/03_….md, .claude.적용본/agents/…).
--acc-* 옵션은 결함 사본으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽고 git status를 조회하며,
체크리스트 4 ③에 따라 적용본이 정한 커밋 해시 조회 명령(읽기 전용 git 명령)을 실행한다.
"""

import difflib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DESIGN_BASE = REPO / "Departments" / "Design" / "workspace"
DEV_BASE = REPO / "Departments" / "Development" / "workspace"
DEV_RESULTS = REPO / "Departments" / "Development" / "results"
APPLIED_GLOB = "REQ-025_적용본_v[0-9][0-9]"
DEV_RESULT_NAME = re.compile(r"^DEV-025_v(\d{2})\.md$")
SUFFIX = ".적용본"

DOC_03 = "Workflow/03_라이프사이클.md"
DOC_06 = "Workflow/06_통제장치_및_배포.md"
RES_TEMPLATE = "Workflow/templates/RES_TEMPLATE.md"
SETTINGS = ".claude/settings.json"
TEMPLATES = ("Workflow/templates/DEV_TEMPLATE.md", "Workflow/templates/EC_TEMPLATE.md",
             "Workflow/templates/ACC_TEMPLATE.md", "Workflow/templates/NCR_TEMPLATE.md")
TARGET_AGENTS = tuple(f".claude/agents/{n}" for n in ("design.md", "development.md", "operations.md", "quality.md"))
AGENT_NAMES = ("design.md", "development.md", "operations.md", "quality.md", "marketing.md", "visual.md")
RECORD_PATHS = ("Departments/Design/results", "Departments/Design/docs/tad", "Departments/Development/results",
                "Departments/Quality/results", "Departments/Quality/docs/nonconformance")

HEADING = re.compile(r"^(#{1,6})\s")
SEC_STOP = re.compile(r"^#{2,3}\s*7\.\s*중단 조건")
SEC_HOTFIX = re.compile(r"^#{2,3}\s*\d+\.\s*핫픽스 트랙")
SEC_5_2 = re.compile(r"^#{3}\s*5\.2\s")
STOP_5 = re.compile(r"^5\.\s")
HOTFIX_KEEP = (re.compile(r"^\s*-\s*\*\*대상 조건"), re.compile(r"^\s*2\.\s*\*\*수정과 검증"),
               re.compile(r"^\s*3\.\s*\*\*사후 확인"))
BUNDLE_ITEM = re.compile(r"\*\*원리 안에서 할 수 없는")
HASH_ITEM = re.compile(r"\*\*커밋 해시 조회\*\*")
GOV_5_2 = re.compile(r"^2\.\s.*기준 커밋")
SEC_GOV = re.compile(r"^#{2}\s*5\.\s*거버넌스 파일 개정 절차")
CODE = re.compile(r"`([^`]+)`")
RULE = re.compile(r"^(Bash|PowerShell)\((.*)\)$")
NEED_ONLY = re.compile(r"필요할 때(에)?만")
UNRUN_HEADER = ("명령 원문", "도구", "메시지 원문", "대신한 수단")
SHELL_META = set(";&|<>`$(){}\n")


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
    그 폴더 자체를 Workflow/의 적용본으로 본다(ACC-024의 방식과 같다).
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
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-025_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    o_opt = request.config.getoption("--acc-original-dir")
    return {
        "design": design_all[-1],
        "dev": dev_all[-1] if dev_all else None,
        # 「적용본이 없다」의 확인 대상. 옵션을 하나라도 주면 준 폴더만 본다.
        "all": ([Path(x) for x in (d_opt, v_opt) if x] if (d_opt or v_opt) else design_all + dev_all),
        "original": Path(o_opt) if o_opt else REPO / "Workflow",
    }


@pytest.fixture(scope="session")
def originals(roots):
    files = {}
    for p in _files(roots["original"]):
        files["Workflow/" + p.relative_to(roots["original"]).as_posix()] = p
    for p in _files(REPO / ".claude" / "agents"):
        files[".claude/agents/" + p.relative_to(REPO / ".claude" / "agents").as_posix()] = p
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
    files.update(applied)
    return files


def _applied_hits(roots, targets):
    found = []
    for folder in roots["all"]:
        for key, p in _applied_map(folder).items():
            if key in targets:
                found.append(f"{key} <- {_display(p)}")
    return found


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


def _section_rows(path, heading, row):
    lines = _lines(path)
    nums = _section(lines, heading)
    return nums, [lines[n - 1] for n in nums if row.match(lines[n - 1])]


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


def _allow_rules():
    data = json.loads((REPO / SETTINGS).read_text(encoding="utf-8-sig"))
    return data["permissions"]["allow"]


def _rule_prefix(inner):
    # 권한 규칙은 `*` 앞부분의 문자열로 명령 앞부분을 맞춘다(Workflow/06 「무인 실행 권한」).
    return inner.split("*", 1)[0]


def _hash_commands(path):
    """06의 「커밋 해시 조회」 항목(없으면 5절 2항)에서 git 명령 코드 조각을 뽑는다. rev-parse는 뺀다."""
    lines = _lines(path)
    rows = [l for l in lines if HASH_ITEM.search(l)]
    if not rows:
        sec = _section(lines, SEC_GOV)
        rows = [lines[n - 1] for n in sec if GOV_5_2.match(lines[n - 1])]
    cmds = []
    for row in rows:
        for span in CODE.findall(row):
            span = span.strip()
            if span.startswith("git ") and "rev-parse" not in span:
                cmds.append(span)
    return rows, cmds


def _head_hash():
    """.git의 파일에서 HEAD 커밋 해시를 구한다. 시험 대상 명령(git log)의 결과와 독립된 기대값이다."""
    git_dir = REPO / ".git"
    head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    if not head.startswith("ref:"):
        return head
    ref = head.split(":", 1)[1].strip()
    loose = git_dir / ref
    if loose.is_file():
        return loose.read_text(encoding="utf-8").strip()
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] == ref:
                return parts[0]
    pytest.fail(f".git에서 {ref}의 해시를 찾지 못했습니다")


def _dev_result(request):
    opt = request.config.getoption("--acc-dev-result")
    if opt:
        path = Path(opt)
    else:
        found = []
        for p in DEV_RESULTS.glob("DEV-025_v*.md"):
            m = DEV_RESULT_NAME.match(p.name)
            if m:
                found.append((int(m.group(1)), p))
        if not found:
            pytest.fail("개발 결과서(Departments/Development/results/DEV-025_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
        path = max(found)[1]
    if not path.is_file():
        pytest.fail(f"개발 결과서가 없습니다: {path}")
    return path, path.read_text(encoding="utf-8-sig", errors="replace")


# ---------------------------------------------------------------- 체크리스트 1 (요구 항목 1)

def test_c1_2_stop5_original_sentences_kept(current, originals):
    """7절 5항: 원본의 두 문장(ask 멈춤, 판정 세션 단서)이 적용본에 글자 그대로 남아 있다(EC G2)."""
    o_sec, before = _section_rows(originals[DOC_03], SEC_STOP, STOP_5)
    c_sec, after = _section_rows(current[DOC_03], SEC_STOP, STOP_5)
    assert o_sec and len(before) == 1, f"원본 {_display(originals[DOC_03])} 7절에서 5항 줄을 하나로 찾지 못했습니다: {before}"
    assert c_sec and len(after) == 1, f"현행 {_display(current[DOC_03])} 7절에서 5항 줄을 하나로 찾지 못했습니다: {after}"
    assert after[0].startswith(before[0]), (f"7절 5항이 원본 문장으로 시작하지 않습니다.\n원본: {before[0]}\n"
                                            f"현행: {after[0]}\n(현행 파일 {_display(current[DOC_03])})")


def test_c1_6_no_other_records_changed(request):
    own = re.escape(request.config.getoption("--acc-own-req"))
    # 「이 REQ 번호」의 문서: <종류>-<번호>_…, <종류>-<번호>-REQ/EC/SPEC_…. 파생 안건(<번호>-n)은 다른 번호다.
    own_doc = re.compile(rf"^[A-Z]+-{own}(-(REQ|EC|SPEC))?_")
    bad = []
    for line in _git_status(*RECORD_PATHS):
        for p in _status_paths(line):
            if not own_doc.match(p.rsplit("/", 1)[-1]):
                bad.append(line)
                break
    assert not bad, ("git status --porcelain -uall -- " + " ".join(RECORD_PATHS)
                     + " 결과에 이 REQ 번호가 아닌 경로가 있습니다:\n" + "\n".join(bad))


# ---------------------------------------------------------------- 체크리스트 2 (요구 항목 2)

def test_c2_6_bundle_paths_in_allow(current):
    lines = _lines(current[DOC_06])
    rows = [l for l in lines if BUNDLE_ITEM.search(l)]
    assert rows, (f"현행 {_display(current[DOC_06])}에 「원리 안에서 할 수 없는 묶음·반복」 항목이 없습니다")
    rules = [s for row in rows for s in CODE.findall(row) if RULE.match(s.strip())]
    assert rules, "「원리 안에서 할 수 없는 묶음·반복」 항목에 실행 경로가 되는 allow 규칙(Bash(…)/PowerShell(…))이 적혀 있지 않습니다"
    allow = _allow_rules()
    missing = [r for r in rules if r.strip() not in allow]
    assert not missing, f"항목이 든 규칙이 {SETTINGS} allow에 없습니다: {missing}"


def test_c2_6_settings_status_clean():
    out = _git_status(SETTINGS)
    assert not out, f"git status --porcelain -uall -- {SETTINGS} 결과가 비어 있지 않습니다:\n" + "\n".join(out)


# ---------------------------------------------------------------- 체크리스트 3 (요구 항목 3)

def _command_line(path):
    return [l for l in _lines(path) if l.lstrip().startswith("- 명령 실행")]


def test_c3_1_agent_lines_same(applied, originals):
    problems = []
    missing = [k for k in TARGET_AGENTS if k not in applied]
    assert not missing, ("정의 파일 적용본(Departments/Development/workspace/REQ-025_적용본_vNN/.claude.적용본/agents/)이 "
                         f"없습니다: {missing}. 구현 단계 산출물이 있어야 합니다.")
    found = {}
    for key in TARGET_AGENTS:
        rows = _command_line(applied[key])
        if len(rows) != 1:
            problems.append(f"{_display(applied[key])}: 「- 명령 실행」 줄이 하나가 아닙니다({len(rows)}줄)")
            continue
        found[key] = rows[0].strip()
        if "Workflow/06_통제장치_및_배포" not in rows[0] or "무인 실행 권한" not in rows[0]:
            problems.append(f"{_display(applied[key])}: 원천(`Workflow/06_통제장치_및_배포` 「무인 실행 권한」) 참조가 없습니다")
        orig = _command_line(originals[key]) if key in originals else []
        if orig and orig[0].strip() == rows[0].strip():
            problems.append(f"{_display(applied[key])}: 「명령 실행」 줄이 원본과 같습니다")
    if len(set(found.values())) > 1:
        problems.append("네 파일의 「명령 실행」 줄이 서로 다릅니다:\n" + "\n".join(f"{k}: {v}" for k, v in found.items()))
    assert not problems, "\n".join(problems)


def test_c3_4_dev_result_records_agents_comparison(request):
    path, text = _dev_result(request)
    problems = []
    if ".claude/agents" not in text:
        problems.append("개발 결과서에 대조 대상 「.claude/agents」가 없습니다")
    for name in AGENT_NAMES:
        if name not in text:
            problems.append(f"개발 결과서에 정의 파일 「{name}」의 대조 결과가 없습니다")
    assert not problems, f"{_display(path)}\n" + "\n".join(problems)


def test_c3_5_hotfix_unchanged_parts(current, originals):
    """D9 대안 (가)로 9절 「절차」 1항은 바뀌지만, 대상 조건과 2·3항은 원본과 같다(EC G7, 3.3절 1번 ⑥)."""
    problems = []
    for row in HOTFIX_KEEP:
        _, before = _section_rows(originals[DOC_03], SEC_HOTFIX, row)
        c_sec, after = _section_rows(current[DOC_03], SEC_HOTFIX, row)
        if len(before) != 1:
            problems.append(f"원본 「핫픽스 트랙」 절에서 {row.pattern} 줄을 하나로 찾지 못했습니다: {before}")
        elif after != before:
            problems.append(f"{row.pattern} 줄이 원본과 다릅니다.\n원본: {before}\n현행: {after}")
    assert not problems, f"(현행 파일 {_display(current[DOC_03])})\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 4 (요구 항목 4)

def test_c4_2_hash_command_matches_allow(current):
    rows, cmds = _hash_commands(current[DOC_06])
    assert cmds, (f"현행 {_display(current[DOC_06])}의 「커밋 해시 조회」 항목(없으면 5절 2항)에서 "
                  f"기준 커밋 조회 명령을 찾지 못했습니다: {rows}")
    prefixes = [_rule_prefix(m.group(2)) for m in (RULE.match(r) for r in _allow_rules()) if m and m.group(1) == "Bash"]
    bad = [c for c in cmds if not any(c.startswith(p) for p in prefixes)]
    assert not bad, f"allow의 Bash(...) 규칙과 앞부분 문자열이 맞지 않는 명령: {bad}"


def test_c4_3_hash_command_runs(current):
    _, cmds = _hash_commands(current[DOC_06])
    assert cmds, f"현행 {_display(current[DOC_06])}에서 기준 커밋 조회 명령을 찾지 못했습니다"
    expected = _head_hash()
    problems = []
    for cmd in cmds:
        if SHELL_META & set(cmd):
            problems.append(f"{cmd}: 셸 구문이 있어 단독 명령으로 실행하지 않습니다")
            continue
        argv = shlex.split(cmd, posix=True)
        proc = _git(*argv[1:])
        out = proc.stdout.strip()
        tokens = re.findall(r"\b[0-9a-f]{7,40}\b", out)
        if proc.returncode != 0:
            problems.append(f"{cmd}: 종료 코드 {proc.returncode}, stderr {proc.stderr.strip()}")
        elif not any(expected.startswith(t) for t in tokens):
            problems.append(f"{cmd}: 출력에 HEAD 해시 {expected}(또는 그 앞부분)가 없습니다. 출력: {out[:200]}")
    assert not problems, "\n".join(problems)


def test_c4_4_no_settings_applied(roots):
    found = _applied_hits(roots, {SETTINGS})
    assert not found, ".claude/settings.json의 적용본이 있습니다:\n" + "\n".join(found)


def test_c4_5_no_need_only_rule_added(applied, originals):
    bad = []
    for key, path in sorted(applied.items()):
        if not (key.startswith("Workflow/") or key in TARGET_AGENTS):
            continue
        before = _lines(originals[key]) if key in originals else []
        for line in difflib.unified_diff(before, _lines(path), lineterm="", n=0):
            if line.startswith("+") and not line.startswith("+++") and NEED_ONLY.search(line):
                bad.append(f"{_display(path)}: {line[1:].strip()[:160]}")
    assert not bad, "원본과 적용본의 차이에 「필요할 때만」 실행 규칙으로 보이는 추가 줄이 있습니다:\n" + "\n".join(bad)


# ---------------------------------------------------------------- 체크리스트 5 (요구 항목 5)

def test_c5_1_templates_have_unrun_table(current):
    problems = []
    for key in TEMPLATES:
        path = current[key]
        lines = _lines(path)
        if not any("실행하지 못한 명령" in l for l in lines):
            problems.append(f"{_display(path)}: 「실행하지 못한 명령」 자리가 없습니다")
        if not any(l.lstrip().startswith("|") and all(h in l for h in UNRUN_HEADER) for l in lines):
            problems.append(f"{_display(path)}: 명령 원문·도구·메시지 원문·대신한 수단 칸을 가진 표 머리가 없습니다")
    assert not problems, "\n".join(problems)


def test_c5_3_no_res_template_applied(roots):
    found = _applied_hits(roots, {RES_TEMPLATE})
    assert not found, "RES_TEMPLATE.md의 적용본이 있습니다:\n" + "\n".join(found)


def test_c5_3_res_template_status_clean():
    out = _git_status(RES_TEMPLATE)
    assert not out, f"git status --porcelain -uall -- {RES_TEMPLATE} 결과가 비어 있지 않습니다:\n" + "\n".join(out)


def test_c5_3_section_5_2_same_as_original(current, originals):
    def body(path):
        lines = _lines(path)
        nums = _section(lines, SEC_5_2)
        return nums, [lines[n - 1] for n in nums[1:]]  # 제목 줄(리비전 태그)은 뺀다
    o_sec, before = body(originals[DOC_03])
    c_sec, after = body(current[DOC_03])
    assert o_sec, f"원본 {_display(originals[DOC_03])}에 5.2절이 없습니다"
    assert c_sec, f"현행 {_display(current[DOC_03])}에 5.2절이 없습니다"
    diff = list(difflib.unified_diff(before, after, "원본 5.2절", "현행 5.2절", lineterm="", n=0))
    assert not diff, f"5.2절 본문이 원본과 다릅니다(현행 파일 {_display(current[DOC_03])}):\n" + "\n".join(diff[:20])
