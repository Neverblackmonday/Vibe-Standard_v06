# -*- coding: utf-8 -*-
"""REQ-022 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 REQ-022 체크리스트 10 가운데 실행 결과로 확인하는 부분(⑥, ⑫)이다(ACC-022 2절).
  설계 적용본: Departments/Design/workspace/REQ-022_적용본_vNN/  (가장 높은 버전)
  개발 적용본: Departments/Development/workspace/REQ-022_적용본_vNN/  (EC-022 2.1절대로 만들지 않으면 원본을 본다)
  개발 결과서: Departments/Development/results/DEV-022_vNN.md 가운데 구현 단계 결과서(v03 이상)의 가장 높은 버전
    (v01·v02는 실험 단계 결과서다. EC-022 1절 「결과서 번호」)
--acc-design-dir, --acc-dev-result 옵션은 결함 사본으로 Red를 확인할 때만 쓴다(conftest.py).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 파일을 읽기만 하며 임시 파일을 만들지 않는다.
"""

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
DESIGN_BASE = REPO / "Departments" / "Design" / "workspace"
DEV_BASE = REPO / "Departments" / "Development" / "workspace"
DEV_RESULTS = REPO / "Departments" / "Development" / "results"
APPLIED_GLOB = "REQ-022_적용본_v[0-9][0-9]"
DESIGN_SUB = "Workflow.적용본"
DEV_RESULT_NAME = re.compile(r"^DEV-022_v(\d{2})\.md$")
FIRST_IMPL_VERSION = 3  # 구현 단계 결과서 번호(EC-022 1절 「결과서 번호」)
AGENT_NAMES = ("design.md", "development.md", "quality.md", "operations.md", "marketing.md", "visual.md")
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt", ".html", ".ini", ".cmd"}

# 개정 이력 표의 행은 지난 개정의 기록이므로 규정 문장이 아니다(체크리스트 10 ⑥ 「개정 이력 행」 제외와 같은 처리).
HISTORY_ROW = re.compile(r"^\|\s*(REQ-\d|HOTFIX-\d|v\d|CEO\s*\|)")

# 원본(커밋 97262f3)에서 분류·단계·REQ 승인과 관계없이 파이프라인 안 세션이나 판정의 모델을 하나로 정하던 문장 형태.
# 체크리스트 10 ⑥이 이름을 든 두 문장, 예로 든 04 1절 표 행과 「모든 실행 명령에 같은 모델 ID」(05 3절, REQ 서식 6절).
MODEL_FIXED = [
    ("Fable 사용 금지", re.compile(r"Fable[^|]*쓰지 않는다")),
    ("판정서 auditor.model을 Claude Opus 5.5로 고정", re.compile(r"auditor\.model`?은\s*`?Claude Opus 5\.5`?\s*여야")),
    ("04 1절 표: 오케스트레이터와 모든 서브에이전트를 한 모델로",
     re.compile(r"파이프라인 안의 모든 서브에이전트\s*\|\s*Claude ")),
    ("실행 명령 형식에 고정 모델 ID", re.compile(r"--model\s+claude-[a-z0-9-]+")),
]

# DEV-022_v03 「대조」 ①의 검색어(REQ-022 체크리스트 10 ⑥, EC-022 3.4절 2번 ①). grep -E와 같은 패턴이다.
SEARCH = re.compile(r"Fable|Opus 5\.5|claude-opus-5-5|auditor\.model")
SEARCH_TERMS = [re.compile(p) for p in (r"Fable", r"Opus 5\\?\.5", r"claude-opus-5-5", r"auditor\\?\.model")]

# 정의 파일 본문이 모델 등급·등급별 모델을 다시 적을 때 쓰는 말(EC-022 3.4절 2번 ②, F14).
AGENT_MODEL_WORDS = re.compile(r"최고급|고급|중급|Opus|Sonnet|Fable|Astra|claude-opus|claude-sonnet")

# 커밋 전 검사가 분류·모델·auditor·author·effort 필드를 해석하면 쓰게 되는 이름(EC-022 3.4절 2번 ③).
CHECK_FIELD_WORDS = re.compile(r"classification|auditor|author|model|effort")


# ---------------------------------------------------------------- 공통 도구

def _latest(base):
    dirs = sorted(p for p in base.glob(APPLIED_GLOB) if p.is_dir())
    return dirs[-1] if dirs else None


def _lines(path):
    # grep과 같은 줄 번호를 얻으려고 줄바꿈을 \n으로만 나눈다(universal newline 변환을 끈다).
    with open(path, encoding="utf-8-sig", newline="") as f:
        return f.read().split("\n")


def _read(path):
    return path.read_text(encoding="utf-8-sig")


def _text_files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix.lower() in TEXT_SUFFIXES:
            yield p


def _dev_applied():
    return _latest(DEV_BASE)


def _governance_file(applied_rel, original_rel):
    """개발 적용본에 그 파일의 적용본이 있으면 적용본을, 없으면 원본을 돌려준다(EC-022 2.1절: 개발 적용본은 만들지 않는다)."""
    dev = _dev_applied()
    if dev is not None and (dev / applied_rel).is_file():
        return dev / applied_rel
    return REPO / original_rel


@pytest.fixture(scope="session")
def design_root(request):
    """설계 적용본 폴더(REQ-022_적용본_vNN) 자체를 돌려준다. grep의 검색 대상과 같은 폴더다. 옵션은 검사할 폴더 자체를 받는다."""
    opt = request.config.getoption("--acc-design-dir")
    if opt:
        root = Path(opt)
    else:
        root = _latest(DESIGN_BASE)
    if root is None or not root.is_dir():
        pytest.fail("설계 적용본 폴더(Departments/Design/workspace/REQ-022_적용본_vNN)가 없습니다. 명세 단계 산출물이 있어야 합니다.")
    return root


def _design_doc(design_root, name):
    for cand in (design_root / DESIGN_SUB / name, design_root / name):
        if cand.is_file():
            return cand
    pytest.fail(f"설계 적용본에 {name}이 없습니다: {design_root}")


def _scan_roots(design_root):
    roots = [design_root]
    dev = _dev_applied()
    if dev is not None:
        roots.append(dev)
    return roots


@pytest.fixture(scope="session")
def dev_result(request):
    opt = request.config.getoption("--acc-dev-result")
    if opt:
        return Path(opt)
    found = []
    for p in DEV_RESULTS.glob("DEV-022_v*.md"):
        m = DEV_RESULT_NAME.match(p.name)
        if m and int(m.group(1)) >= FIRST_IMPL_VERSION:
            found.append((int(m.group(1)), p))
    if not found:
        pytest.fail("구현 단계 개발 결과서(Departments/Development/results/DEV-022_v03.md 이상)가 없습니다. "
                    "구현 단계 산출물이 있어야 합니다.")
    return max(found)[1]


# ---------------------------------------------------------------- 체크리스트 10 ⑥

def test_c10_6_applied_04_has_no_fable_ban_or_fixed_judge_model(design_root):
    text = "\n".join(line for line in _lines(_design_doc(design_root, "04_모델_운용.md")) if not HISTORY_ROW.match(line))
    problems = []
    if re.search(r"Fable 5\.1`?은 쓰지 않는다", text):
        problems.append("04 적용본에 「`Claude Fable 5.1`은 쓰지 않는다」가 남아 있습니다")
    if re.search(r"auditor\.model`?은\s*`?Claude Opus 5\.5`?\s*여야", text):
        problems.append("04 적용본에 「`auditor.model`은 `Claude Opus 5.5`여야 한다」가 남아 있습니다")
    assert not problems, "\n".join(problems)


def test_c10_6_applied_has_no_single_model_sentence(design_root):
    files = []
    hits = []
    for root in _scan_roots(design_root):
        for path in _text_files(root):
            files.append(path)
            for no, line in enumerate(_lines(path), 1):
                if HISTORY_ROW.match(line):
                    continue
                for name, pat in MODEL_FIXED:
                    if pat.search(line):
                        hits.append(f"{path.relative_to(root.parent).as_posix()}:{no}: [{name}]")
    assert files, f"적용본 폴더에 읽을 파일이 없습니다: {design_root}"
    assert not hits, "파이프라인 안 세션이나 판정의 모델을 하나로 정하는 원본 문장 형태가 적용본에 남아 있습니다:\n" + "\n".join(hits)


def test_c10_6_dev_result_records_search_and_every_hit(design_root, dev_result):
    assert dev_result.is_file(), f"개발 결과서가 없습니다: {dev_result}"
    text = _read(dev_result)
    command_lines = [line for line in text.splitlines() if all(t.search(line) for t in SEARCH_TERMS)]
    problems = []
    if not command_lines:
        problems.append("개발 결과서에 검색어 「Fable」, 「Opus 5.5」, 「claude-opus-5-5」, 「auditor.model」을 함께 쓴 검색 명령이 없습니다")
    hits = []
    for root in _scan_roots(design_root):
        for path in _text_files(root):
            for no, line in enumerate(_lines(path), 1):
                if SEARCH.search(line):
                    hits.append(f"{path.name}:{no}")
    assert hits, "적용본에서 검색어에 맞는 줄을 찾지 못했습니다(04 적용본 1.1절 표의 기본 모델이 있어야 합니다)"
    # 「04_모델_운용.md:1」이 「…:14」에 맞지 않게 줄 번호 뒤에 숫자가 오지 않는 것만 센다.
    missing = [h for h in hits if not re.search(re.escape(h) + r"(?!\d)", text)]
    if missing:
        problems.append("검색 결과 원문 가운데 개발 결과서에 없는 줄(<파일>:<줄 번호>):\n" + "\n".join(missing))
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 10 ⑫

def _front_matter(lines):
    if not lines or lines[0].strip() != "---":
        return None, lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1:]
    return None, lines


def test_c10_12_agents_model_inherit_without_effort():
    problems = []
    for name in AGENT_NAMES:
        path = _governance_file(Path(".claude.적용본") / "agents" / name, Path(".claude") / "agents" / name)
        if not path.is_file():
            problems.append(f"{name}: 정의 파일이 없습니다")
            continue
        head, _ = _front_matter(_lines(path))
        if head is None:
            problems.append(f"{name}: 머리말이 없습니다")
            continue
        models = [l.strip() for l in head if re.match(r"^model\s*:", l)]
        if models != ["model: inherit"]:
            problems.append(f"{name}: 머리말 model이 inherit 하나가 아닙니다: {models}")
        if any(re.match(r"^effort\s*:", l) for l in head):
            problems.append(f"{name}: 머리말에 effort가 있습니다(04 적용본 2절, 1.2절 서브에이전트 정의 항목)")
    assert not problems, "\n".join(problems)


def test_c10_12_agents_do_not_restate_model_grades():
    hits = []
    for name in AGENT_NAMES:
        path = _governance_file(Path(".claude.적용본") / "agents" / name, Path(".claude") / "agents" / name)
        if not path.is_file():
            hits.append(f"{name}: 정의 파일이 없습니다")
            continue
        head, body = _front_matter(_lines(path))
        offset = (len(head) + 2) if head is not None else 0
        for no, line in enumerate(body, offset + 1):
            if AGENT_MODEL_WORDS.search(line):
                hits.append(f"{name}:{no}: {line.strip()[:120]}")
    assert not hits, "정의 파일 본문이 모델 등급·등급별 모델을 다시 적었습니다(원천은 04 「모델」):\n" + "\n".join(hits)


def test_c10_12_check_standard_has_no_model_field_logic():
    path = _governance_file(Path("Departments/Development/assets/scripts.적용본/check_standard.py"),
                            Path("Departments/Development/assets/scripts/check_standard.py"))
    assert path.is_file(), f"check_standard.py가 없습니다: {path}"
    hits = [f"{path.name}:{no}: {line.strip()[:120]}"
            for no, line in enumerate(_lines(path), 1) if CHECK_FIELD_WORDS.search(line)]
    assert not hits, ("커밋 전 검사에 분류·모델·auditor·author·effort 필드를 다루는 줄이 있습니다. "
                      "이 안건의 규칙 변경과 대조가 필요합니다:\n" + "\n".join(hits))


def test_c10_12_settings_has_no_model_or_env():
    path = _governance_file(Path(".claude.적용본/settings.json"), Path(".claude/settings.json"))
    assert path.is_file(), f"settings.json이 없습니다: {path}"
    data = json.loads(_read(path))
    problems = [f"settings.json에 최상위 키 「{k}」가 있습니다" for k in ("model", "env") if k in data]
    if "CLAUDE_CODE_SUBAGENT_MODEL_FORCE" in _read(path):
        problems.append("settings.json에 CLAUDE_CODE_SUBAGENT_MODEL_FORCE가 있습니다")
    assert not problems, "\n".join(problems)


def test_c10_12_dev_result_records_comparison(dev_result):
    assert dev_result.is_file(), f"개발 결과서가 없습니다: {dev_result}"
    text = _read(dev_result)
    problems = []
    if not re.search(r"^#+ .*대조", text, re.M):
        problems.append("개발 결과서에 「대조」 절이 없습니다")
    for target in (".claude/agents", "check_standard.py", "settings.json"):
        if target not in text:
            problems.append(f"개발 결과서에 대조 대상 「{target}」이 없습니다")
    for name in AGENT_NAMES:
        if name not in text:
            problems.append(f"개발 결과서에 정의 파일 「{name}」의 대조 결과가 없습니다")
    assert not problems, "\n".join(problems)
