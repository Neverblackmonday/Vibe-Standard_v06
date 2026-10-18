# -*- coding: utf-8 -*-
"""REQ-021 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 설계 적용본과 개발 적용본이다.
  설계: Departments/Design/workspace/REQ-021_적용본_vNN/Workflow.적용본/
  개발: Departments/Development/workspace/REQ-021_적용본_vNN/.claude.적용본/agents/
폴더 버전이 여럿이면 가장 높은 버전을 쓴다(REQ-021 5절 머리 안내 「적용본은 최신 버전」).
--acc-design-dir, --acc-dev-dir 옵션은 결함 사본(원본 Workflow/, .claude/agents/ 등)으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽기만 하며 임시 파일을 만들지 않는다.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DESIGN_BASE = REPO / "Departments" / "Design" / "workspace"
DEV_BASE = REPO / "Departments" / "Development" / "workspace"
APPLIED_GLOB = "REQ-021_적용본_v[0-9][0-9]"
DESIGN_SUB = "Workflow.적용본"
DEV_SUB = Path(".claude.적용본") / "agents"
AGENT_NAMES = ("design.md", "development.md", "quality.md")
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt", ".html", ".ini", ".cmd"}

# 개정 이력 표의 행은 지난 개정의 기록이므로 규정 문장이 아니다(EC-021 3.4절 2번 ①).
HISTORY_ROW = re.compile(r"^\|\s*(REQ-\d|HOTFIX-\d|v\d)")

# 원본(커밋 ee95f5a)에서 분류로 EC 작성·EC 판정의 유무를 정하던 문장 형태(REQ-021 2절 「배경」, EC-021 1절 「변경 배경」).
# 적용본 전체에 이 형태가 남아 있으면 체크리스트 2 ②를 어긴다.
CLASS_DECIDES_EC = [
    ("Minor는 EC 작성·EC 판정이 없다", re.compile(r"Minor는 EC 작성·EC 판정이 없다")),
    ("Critical·Major는 EC 경로를 포함", re.compile(r"Critical·Major는 EC 경로를 포함")),
    ("Critical·Major는 EC-xxx 포함(REQ scope)", re.compile(r"Critical·Major는 \S*EC-xxx")),
    ("EC(Minor는 …)", re.compile(r"EC\(Minor는")),
    ("EC 판정(Minor는 최종 판정)", re.compile(r"EC 판정\(Minor는 최종 판정\)")),
    ("Critical·Major는 EC 작성 전/앞(실험 위치)", re.compile(r"Critical·Major는 EC 작성 (전|앞)")),
    ("EC 줄의 Minor는 「해당 없음」", re.compile(r"EC.*Minor는 「해당 없음」")),
    ("흐름도 분류 분기에서 바로 EC 작성", re.compile(r"\"Critical·Major\"\s*-->\s*\w+\[\"EC 작성")),
    ("대괄호 없는 EC 작성 → EC 판정 단계 목록", re.compile(r"(?<!\[)EC 작성 → EC 판정")),
    ("Critical·Major는 EC가", re.compile(r"Critical·Major는 EC가")),
    ("구현 방법은 EC에서 정한다(조건 없음)", re.compile(r"구현 방법은 EC에서 정한다")),
]

# EC의 정의와 붙이는 기준(03 적용본 2.1절 1~4항)을 다시 적을 때 쓰는 말(EC-021 3.5절 4번의 사본 대조 검색어 가운데 기준 문구).
EC_CRITERIA_WORDS = re.compile(r"Engineering Change|변경점|동작·규칙·규격|늘 붙|붙이지 않")

# 정의 파일의 참조: `Workflow/<파일>` 뒤에 붙은 「절 제목」(·로 이어진 여러 개 포함)
REF = re.compile(r"`(Workflow/[^`]+?)`((?:\s*「[^」]+」(?:·「[^」]+」)*)?)")
TITLE = re.compile(r"「([^」]+)」")


# ---------------------------------------------------------------- 공통 도구

def _latest(base):
    dirs = sorted(p for p in base.glob(APPLIED_GLOB) if p.is_dir())
    return dirs[-1] if dirs else None


def _read(path):
    return path.read_text(encoding="utf-8-sig")


def _text_files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() in TEXT_SUFFIXES:
            yield p


def _class_ec_hits(root):
    hits = []
    for path in _text_files(root):
        for no, line in enumerate(_read(path).splitlines(), 1):
            if HISTORY_ROW.match(line):
                continue
            for name, pat in CLASS_DECIDES_EC:
                if pat.search(line):
                    hits.append(f"{path.relative_to(root).as_posix()}:{no}: [{name}]")
    return hits


@pytest.fixture(scope="session")
def design_root(request):
    """설계 적용본의 Workflow.적용본 폴더(문서가 바로 들어 있는 폴더)를 돌려준다. 옵션은 그 폴더 자체를 받는다."""
    opt = request.config.getoption("--acc-design-dir")
    if opt:
        root = Path(opt)
    else:
        latest = _latest(DESIGN_BASE)
        root = latest / DESIGN_SUB if latest else None
    if root is None or not root.is_dir():
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-021_적용본_vNN/Workflow.적용본)가 없습니다. "
                    "명세 단계 산출물이 있어야 합니다.")
    return root


@pytest.fixture(scope="session")
def dev_root(request):
    """개발 적용본의 .claude.적용본/agents 폴더를 돌려준다. 옵션은 그 폴더 자체를 받는다."""
    opt = request.config.getoption("--acc-dev-dir")
    if opt:
        return Path(opt)
    root = _latest(DEV_BASE)
    if root is None or not (root / DEV_SUB).is_dir():
        pytest.fail("개발 적용본 폴더(Departments/Development/workspace/REQ-021_적용본_vNN/.claude.적용본/agents)가 없습니다. "
                    "구현 단계 산출물이 있어야 합니다.")
    return root / DEV_SUB


def _agent(dev_root, name):
    path = dev_root / name
    if not path.is_file():
        pytest.fail(f"개발 적용본에 {DEV_SUB.as_posix()}/{name}이 없습니다(EC-021 2.1절 16~18번).")
    return path


# ---------------------------------------------------------------- 체크리스트 2 ②

def test_c2_2_design_applied_has_no_classification_deciding_ec(design_root):
    files = list(_text_files(design_root))
    assert files, f"설계 적용본 폴더에 읽을 파일이 없습니다: {design_root}"
    hits = _class_ec_hits(design_root)
    assert not hits, "분류로 EC 작성·EC 판정의 유무를 정하는 원본 문장 형태가 설계 적용본에 남아 있습니다:\n" + "\n".join(hits)


def test_c2_2_dev_applied_has_no_classification_deciding_ec(dev_root):
    for name in AGENT_NAMES:
        _agent(dev_root, name)
    hits = _class_ec_hits(dev_root)
    assert not hits, "분류로 EC 작성·EC 판정의 유무를 정하는 원본 문장 형태가 개발 적용본에 남아 있습니다:\n" + "\n".join(hits)


# ---------------------------------------------------------------- 체크리스트 2 ⑨

def _resolve_workflow(design_root, rel):
    """정의 파일이 참조한 Workflow 문서를 설계 적용본에서 먼저 찾고, 없으면 원본에서 찾는다."""
    rel = rel[len("Workflow/"):]
    if not rel.endswith(".md"):
        rel += ".md"
    applied = design_root / rel
    if applied.is_file():
        return applied
    original = REPO / "Workflow" / rel
    return original if original.is_file() else None


def _has_title(text, title):
    for line in text.splitlines():
        if line.startswith("#") and title in line:
            return True
    return f"**{title}**" in text


def test_c2_9_agent_references_resolve_in_revised_rules(design_root, dev_root):
    problems = []
    checked = 0
    for name in AGENT_NAMES:
        text = _read(_agent(dev_root, name))
        for m in REF.finditer(text):
            target = _resolve_workflow(design_root, m.group(1))
            if target is None:
                problems.append(f"{name}: `{m.group(1)}` 문서가 없습니다")
                continue
            body = _read(target)
            for title in TITLE.findall(m.group(2) or ""):
                checked += 1
                if not _has_title(body, title):
                    problems.append(f"{name}: `{m.group(1)}` 「{title}」 절이 없습니다")
    assert checked > 0, "정의 파일 적용본에서 절 참조를 찾지 못했습니다"
    assert not problems, "정의 파일 적용본의 참조가 개정된 규칙과 맞지 않습니다:\n" + "\n".join(problems)


def test_c2_9_agents_name_new_stage_duties(design_root, dev_root):
    rules = _read(design_root / "03_라이프사이클.md")
    for stage in ("EC 판단", "명세 판정"):
        assert stage in rules, f"03 적용본에 단계 이름 「{stage}」가 없습니다"
    assert re.search(r"^#+ .*EC 적용 기준", rules, re.M), "03 적용본에 「EC 적용 기준」 절이 없습니다"

    design = _read(_agent(dev_root, "design.md"))
    quality = _read(_agent(dev_root, "quality.md"))
    problems = []
    if "EC 판단" not in design:
        problems.append("design.md에 설계의 업무 「EC 판단」이 없습니다")
    if "「EC 적용 기준」" not in design:
        problems.append("design.md가 EC 판단의 원천 「EC 적용 기준」을 참조하지 않습니다")
    if "명세 판정" not in quality:
        problems.append("quality.md에 품질의 업무 「명세 판정」이 없습니다")
    assert not problems, "\n".join(problems)


def test_c2_9_agents_do_not_restate_ec_criteria(dev_root):
    hits = []
    for name in AGENT_NAMES:
        for no, line in enumerate(_read(_agent(dev_root, name)).splitlines(), 1):
            if EC_CRITERIA_WORDS.search(line):
                hits.append(f"{name}:{no}: {line.strip()[:120]}")
    assert not hits, "정의 파일 적용본이 EC의 정의·붙이는 기준을 다시 적었습니다(원천은 03 「EC 적용 기준」):\n" + "\n".join(hits)
