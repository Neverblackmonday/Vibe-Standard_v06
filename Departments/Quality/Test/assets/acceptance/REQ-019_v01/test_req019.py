# -*- coding: utf-8 -*-
"""REQ-019 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 개발 적용본의 권한 설정이다.
  Departments/Development/workspace/REQ-019_적용본_vNN/.claude.적용본/settings.json
폴더 버전이 여럿이면 가장 높은 버전을 쓴다(REQ-019 5절 머리 안내 「적용본은 최신 버전」).
명령행 옵션 --acc-target(conftest.py)을 주면 그 경로나 JSON 문자열을 대상으로 한다. 결함 사본으로
시험이 실제로 실패하는지(Red) 확인할 때만 쓴다.

원본은 기준 커밋 69ba21d의 .claude/settings.json이다(EC-019 F11).

규칙 일치 판단은 Claude Code 권한 규칙의 접두 일치를 단순화한 것이다(끝의 「 *」는 단어 경계,
그 밖의 *는 임의 문자열). 실제 세션에서의 동작은 개발의 재현 시험(EC-019 3.4절 3번 R1~R7)이
확인하며, 이 시험은 그 재현 시험이 기대는 설정 조건만 결정적으로 확인한다.

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 임시 파일을 만들지 않는다.
"""

import fnmatch
import json
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
BASE_COMMIT = "69ba21d"  # 적용본의 기준 커밋(EC-019 F11)
SETTINGS_REL = ".claude/settings.json"
APPLIED_GLOB = "REQ-019_적용본_v[0-9][0-9]"
APPLIED_SETTINGS_REL = ".claude.적용본/settings.json"

RULE_RE = re.compile(r"^(Bash|PowerShell)\((.*)\)$", re.S)

# 표준 절차의 대상 명령(REQ-019 D3, 03 적용본 5.2절 1항, EC-019 F5)을 06 적용본 2.1절
# 「명령 형태」대로(저장소 루트 기준 상대 경로, -C·cd·환경 변수 대입 없음) 적은 것
GIT_AND_CHECK_COMMANDS = [
    "git status --porcelain -uall",
    "git status --porcelain -uall -- Departments/Quality",
    "git diff --stat HEAD",
    "git diff --no-index --full-index /dev/null Departments/Quality/assets/acceptance/REQ-019_v01/test_req019.py",
    "git diff --no-index --stat Departments/Secretariat/docs/requests/REQ-019_v02.md "
    "Departments/Secretariat/docs/requests/REQ-019_v03.md",
    "git log -1 --format=%h",
    "git show --stat HEAD",
    "git ls-files Lab",
    "python Departments/Development/assets/scripts/check_standard.py",
    "python Departments/Development/assets/scripts/check_standard.py --staged",
    "python -m pytest Departments/Quality/assets/acceptance/REQ-019_v01",
]
BASH_ONLY_COMMANDS = [
    "date +%Y-%m-%dT%H:%M:%S%z",
    "date -Iseconds",
]

# 사례의 수정 전 형태(EC-019 3.1절 원인 A~D). 설정 변경으로 이 형태가 허용되면
# 형태 규정이 아니라 규칙 완화로 원인을 가린 것이다(EC-019 2.3절 「Bash(...) 규칙의 추가」)
CASE_FORM_COMMANDS = [
    ("A", 'git -C "D:/acc/clone" status --porcelain -uall'),
    ("A", 'git -C "D:/acc/clone" log -1 --format=%h'),
    ("C", 'cd "D:/acc/clone/Departments/Secretariat/docs/requests"'),
    ("D", "FOO=1 python -m pytest --version"),
    ("B", 'echo "exit=$?"'),
]


# ---------------------------------------------------------------- 공통 도구

def parse_rules(entries):
    """권한 항목 목록에서 (도구, 패턴) 쌍을 돌려준다. Bash·PowerShell 밖의 항목은 뺀다."""
    rules = []
    for entry in entries:
        m = RULE_RE.match(entry)
        if m:
            rules.append((m.group(1), m.group(2)))
    return rules


def rule_matches(pattern, command):
    if pattern.endswith(" *") and command == pattern[:-2]:
        return True
    return fnmatch.fnmatchcase(command, pattern)


def allowed(rules, tool, command):
    return any(t == tool and rule_matches(p, command) for t, p in rules)


def load_original():
    res = subprocess.run(["git", "show", f"{BASE_COMMIT}:{SETTINGS_REL}"],
                         cwd=REPO, capture_output=True)
    if res.returncode != 0:
        pytest.fail(f"원본 {BASE_COMMIT}:{SETTINGS_REL}을 읽지 못했습니다: "
                    f"{res.stderr.decode('utf-8', 'replace')}")
    return json.loads(res.stdout.decode("utf-8"))


def applied_text(override):
    """대상 settings.json의 내용을 돌려준다. override는 conftest.py의 --acc-target 값이다."""
    if override:
        if override.lstrip().startswith("{"):
            return override
        path = Path(override)
        if not path.is_file():
            pytest.fail(f"--acc-target이 가리키는 파일이 없습니다: {path}")
        return path.read_text(encoding="utf-8")
    folders = sorted((REPO / "Departments/Development/workspace").glob(APPLIED_GLOB))
    if not folders:
        pytest.fail("개발 적용본 폴더(Departments/Development/workspace/REQ-019_적용본_vNN)가 없습니다. "
                    "구현 단계 산출물이 있어야 합니다.")
    path = folders[-1] / APPLIED_SETTINGS_REL
    if not path.is_file():
        pytest.fail(f"권한 설정 적용본이 없습니다: {path.relative_to(REPO)}")
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def original():
    return load_original()


@pytest.fixture(scope="module")
def applied(request):
    text = applied_text(request.config.getoption("--acc-target"))
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        pytest.fail(f"권한 설정 적용본이 JSON 문법에 맞지 않습니다: {exc}")


def perms(settings, key):
    return settings.get("permissions", {}).get(key, [])


# ---------------------------------------------------------------- 체크리스트 8 ②

def test_c8_2_target_commands_allowed_in_bash_and_powershell(applied):
    """원인 E의 조치: 대상 명령이 Bash와 PowerShell 양쪽의 allow 규칙에 맞는다."""
    rules = parse_rules(perms(applied, "allow"))
    missing = []
    for cmd in GIT_AND_CHECK_COMMANDS:
        for tool in ("Bash", "PowerShell"):
            if not allowed(rules, tool, cmd):
                missing.append(f"{tool}: {cmd}")
    for cmd in BASH_ONLY_COMMANDS:
        if not allowed(rules, "Bash", cmd):
            missing.append(f"Bash: {cmd}")
    assert not missing, "allow 규칙에 맞지 않는 대상 명령:\n" + "\n".join(missing)


def test_c8_2_case_forms_not_allowed_by_settings(applied):
    """원인 A~D의 수정 전 형태가 설정 완화로 허용되지 않는다(형태 규정으로 막는다)."""
    rules = parse_rules(perms(applied, "allow"))
    hits = [f"{tool} [{cause}]: {cmd}"
            for cause, cmd in CASE_FORM_COMMANDS
            for tool in ("Bash", "PowerShell")
            if allowed(rules, tool, cmd)]
    assert not hits, "수정 전 형태가 allow 규칙에 맞음:\n" + "\n".join(hits)


# ---------------------------------------------------------------- 체크리스트 8 ④

def test_c8_4_deny_same_as_original(original, applied):
    assert perms(applied, "deny") == perms(original, "deny")


def test_c8_4_ask_not_reduced(original, applied):
    dropped = [e for e in perms(original, "ask") if e not in perms(applied, "ask")]
    assert not dropped, f"ask에서 빠진 항목: {dropped}"


def test_c8_4_only_powershell_rules_added_to_allow(original, applied):
    """EC-019 3.4절 2번 ①: 바뀐 곳이 allow의 PowerShell(...) 추가뿐이다."""
    orig_allow = perms(original, "allow")
    new_allow = perms(applied, "allow")
    assert new_allow[:len(orig_allow)] == orig_allow, "기존 allow 항목의 순서·내용이 바뀌었습니다"
    added = new_allow[len(orig_allow):]
    not_ps = [e for e in added if not e.startswith("PowerShell(")]
    assert not not_ps, f"PowerShell(...) 밖의 allow 추가: {not_ps}"
    assert perms(applied, "ask") == perms(original, "ask"), "ask가 바뀌었습니다"
    rest_orig = {k: v for k, v in original.items() if k != "permissions"}
    rest_new = {k: v for k, v in applied.items() if k != "permissions"}
    assert rest_new == rest_orig, "permissions 밖의 설정이 바뀌었습니다"
    assert set(applied.get("permissions", {})) == set(original.get("permissions", {})), \
        "permissions의 키 구성이 바뀌었습니다"
