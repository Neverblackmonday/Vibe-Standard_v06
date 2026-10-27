# -*- coding: utf-8 -*-
"""REQ-036 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 개발 적용본(EC-036 2.1절 9·10번)이다.
  Departments/Development/workspace/REQ-036_적용본_vNN/.claude.적용본/settings.json
  Departments/Development/workspace/REQ-036_적용본_vNN/.gitattributes.적용본
폴더 버전이 여럿이면 가장 높은 버전을 쓴다. 명령행 옵션 --acc-dev-dir(conftest.py)을 주면 그 폴더를
개발 적용본으로 본다. 결함 사본으로 시험이 실제로 실패하는지(Red) 확인할 때만 쓴다.

원본은 EC-036 1절 「변경 배경」의 기준 커밋 57e55ec의 파일이다.

권한 규칙 일치 판단은 Claude Code 권한 규칙의 접두 일치를 단순화한 것이다(끝의 「 *」는 단어 경계,
그 밖의 *는 임의 문자열. REQ-019 인수 시험과 같은 방식). 실제 세션에서의 동작은 이 시험의 대상이 아니다.

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 임시 Git 저장소는 pytest tmp_path 아래에 만든다.
"""

import fnmatch
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
BASE_COMMIT = "57e55ec"  # EC-036 1절 「변경 배경」의 원본 커밋
DEV_WORKSPACE = REPO / "Departments/Development/workspace"
DESIGN_WORKSPACE = REPO / "Departments/Design/workspace"
APPLIED_GLOB = "REQ-036_적용본_v[0-9][0-9]"
APPLIED_SETTINGS_REL = ".claude.적용본/settings.json"
APPLIED_GITATTRIBUTES_REL = ".gitattributes.적용본"
APPLIED_AGENTS_REL = ".claude.적용본/agents"

RULE_RE = re.compile(r"^(Bash|PowerShell)\((.*)\)$", re.S)

# 체크리스트 1 ①: PowerShell 도구로 내리는 커밋·푸시의 표준 절차 형태(저장소 루트에서 실행하는 형태)
COMMIT_PUSH_COMMANDS = [
    'git commit -m "chore: [CEO] 기록 추가"',  # Workflow/05 1절 「커밋」
    'git commit -m "feat: [REQ-036] 제목 줄" '
    '-m "Approved-REQ: Departments/Secretariat/docs/requests/REQ-036_v02.md"',  # Workflow/05 1.1절 8번의 예
    'git commit --no-verify -m "chore: [CEO] 거버넌스 파일 수정"',  # Workflow/05 8.3절 「요청 커밋」 예외 (나)
    "git commit",
    "git commit --amend",  # Workflow/05 8.1절 금지 명령 ②
    'git commit -a -m "x"',  # Workflow/05 8.1절 금지 명령 ③
    "git push origin v06-main",  # Workflow/05 8.3절 「요청 푸시」 3)
    "git push",
    "git push --force",  # Workflow/05 8.1절 금지 명령 ④
    "git push -f",
    "git push --force-with-lease",
]

# 체크리스트 1 ①: Remove-Item·Move-Item과 그 기본 별칭. 별칭은 이 PC의 Windows PowerShell 5.1에서
# 「Get-Alias -Definition Remove-Item, Move-Item」으로 조회한 값이다(ACC-036 2절).
REMOVE_NAMES = ["Remove-Item", "del", "erase", "rd", "ri", "rm", "rmdir"]
MOVE_NAMES = ["Move-Item", "mi", "move", "mv"]
DELETE_MOVE_COMMANDS = (
    [f"{name} Departments/Quality/workspace/REQ-036_x.md" for name in REMOVE_NAMES]
    + ["Remove-Item -Recurse -Force Departments/Quality/workspace/REQ-036_x",
       "Remove-Item -LiteralPath 'Departments/Quality/workspace/REQ-036_x y.md'"]
    + [f"{name} Departments/Quality/workspace/a.md Departments/Quality/workspace/b.md"
       for name in MOVE_NAMES]
    + ["Move-Item -Path Departments/Quality/workspace/a.md -Destination Departments/Quality/workspace/b.md"]
)

# 체크리스트 4 ③: 품질 밖 정의 파일
OTHER_AGENT_FILES = ["development.md", "engineering.md", "marketing.md", "operations.md"]


# ---------------------------------------------------------------- 공통 도구

def git(args, cwd=REPO, env=None, check=True):
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, env=env)
    if check and res.returncode != 0:
        pytest.fail(f"git {' '.join(args)} 실패(종료 코드 {res.returncode}): "
                    f"{res.stderr.decode('utf-8', 'replace')}")
    return res


def repo_env():
    """저장소 조회가 .git/index를 고쳐 쓰지 않게 한다."""
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def latest_folder(workspace):
    folders = sorted(workspace.glob(APPLIED_GLOB))
    return folders[-1] if folders else None


def dev_folder(config):
    override = config.getoption("--acc-dev-dir")
    if override:
        path = Path(override)
        if not path.is_dir():
            pytest.fail(f"--acc-dev-dir가 가리키는 폴더가 없습니다: {path}")
        return path
    return latest_folder(DEV_WORKSPACE)


def require_dev_file(config, rel):
    folder = dev_folder(config)
    if folder is None:
        pytest.fail("개발 적용본 폴더(Departments/Development/workspace/REQ-036_적용본_vNN)가 없습니다. "
                    "구현 단계 산출물이 있어야 합니다(EC-036 2.1절 9·10번).")
    path = folder / rel
    if not path.is_file():
        pytest.fail(f"개발 적용본 파일이 없습니다: {path}")
    return path


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


def matches_any(rules, tool, command):
    return any(t == tool and rule_matches(p, command) for t, p in rules)


def perms(settings, key):
    return settings.get("permissions", {}).get(key, [])


@pytest.fixture(scope="module")
def original():
    res = git(["show", f"{BASE_COMMIT}:.claude/settings.json"])
    return json.loads(res.stdout.decode("utf-8"))


@pytest.fixture(scope="module")
def applied(request):
    path = require_dev_file(request.config, APPLIED_SETTINGS_REL)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        pytest.fail(f"권한 설정 적용본이 JSON 문법에 맞지 않습니다: {exc}")


# ---------------------------------------------------------------- 체크리스트 1 ①

def check_ask_not_allow(applied, commands):
    ask = parse_rules(perms(applied, "ask"))
    allow = parse_rules(perms(applied, "allow"))
    problems = []
    for cmd in commands:
        if not matches_any(ask, "PowerShell", cmd):
            problems.append(f"ask에 맞지 않음: PowerShell: {cmd}")
        if matches_any(allow, "PowerShell", cmd):
            problems.append(f"allow에 맞음: PowerShell: {cmd}")
    return problems


def test_c1_1_powershell_commit_push_in_ask_not_allow(applied):
    problems = check_ask_not_allow(applied, COMMIT_PUSH_COMMANDS)
    assert not problems, "\n".join(problems)


def test_c1_1_powershell_delete_move_in_ask_not_allow(applied):
    problems = check_ask_not_allow(applied, DELETE_MOVE_COMMANDS)
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 1 ②

def test_c1_2_bash_ask_same_as_original(original, applied):
    orig_bash = [e for e in perms(original, "ask") if e.startswith("Bash(")]
    new_bash = [e for e in perms(applied, "ask") if e.startswith("Bash(")]
    assert len(orig_bash) == 6, f"원본 ask의 Bash 규칙이 여섯 개가 아닙니다: {orig_bash}"
    assert new_bash == orig_bash, f"Bash ask 규칙이 원본과 다릅니다: {new_bash}"


def test_c1_2_deny_same_as_original(original, applied):
    assert perms(applied, "deny") == perms(original, "deny")


def test_c1_2_allow_same_as_original(original, applied):
    """EC-036 3.4절 F1 「`ask`」 끝 항목: 기존 allow도 바꾸지 않는다(체크리스트 1 ②)."""
    assert perms(applied, "allow") == perms(original, "allow")


# ---------------------------------------------------------------- 체크리스트 2 ①②

LF_TEXT_FILES = {
    "AGENTS.md": b"# title\nline 2\n",
    "Workflow/03_라이프사이클.md": "# 03\n본문\n".encode("utf-8"),
    "Departments/Development/assets/scripts/check_standard.py": b"print('a')\nprint('b')\n",
    ".claude/settings.json": b'{\n  "a": 1\n}\n',
    "notes.txt": b"one\ntwo\n",
    ".githooks/pre-commit": b"#!/bin/sh\nexit 0\n",
}
CRLF_FILES = {
    "setup.cmd": b"@echo off\necho cmd\n",
    "tools/run.bat": b"@echo off\necho bat\n",
}
GITHOOK_FILE = ".githooks/pre-commit"
AUTOCRLF_VALUES = ("true", "false")


def isolated_env(tmp):
    """PC의 시스템·사용자 Git 설정(core.autocrlf 등)이 섞이지 않게 한다."""
    empty = tmp / "empty.gitconfig"
    empty.write_bytes(b"")
    env = os.environ.copy()
    for key in list(env):
        if key.startswith("GIT_"):
            del env[key]
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = str(empty)
    return env


@pytest.fixture(scope="module")
def checkouts(request, tmp_path_factory):
    """적용본 .gitattributes를 넣은 임시 저장소의 같은 커밋을 두 core.autocrlf 설정으로 체크아웃한다."""
    attrs = require_dev_file(request.config, APPLIED_GITATTRIBUTES_REL).read_bytes()
    tmp = tmp_path_factory.mktemp("req036_eol")
    env = isolated_env(tmp)
    src = tmp / "src"
    src.mkdir()
    git(["init", "-q"], cwd=src, env=env)
    files = {".gitattributes": attrs, **LF_TEXT_FILES, **CRLF_FILES}
    for rel, data in files.items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    git(["add", "-A"], cwd=src, env=env)
    git(["-c", "user.name=acc", "-c", "user.email=acc@example.invalid", "-c", "core.autocrlf=false",
         "commit", "-q", "-m", "init"], cwd=src, env=env)
    result = {}
    for value in AUTOCRLF_VALUES:
        dst = tmp / f"autocrlf_{value}"
        git(["clone", "-q", "-c", f"core.autocrlf={value}", str(src), str(dst)], cwd=tmp, env=env)
        got = git(["config", "core.autocrlf"], cwd=dst, env=env).stdout.decode().strip()
        assert got == value, f"임시 복제의 core.autocrlf가 {value}가 아닙니다: {got}"
        result[value] = dst
    return result


def test_c2_1_text_files_same_hash_and_lf(checkouts):
    text_rels = [".gitattributes", *LF_TEXT_FILES]
    problems = []
    for rel in text_rels:
        digests = {}
        for value, root in checkouts.items():
            data = (root / rel).read_bytes()
            digests[value] = hashlib.sha256(data).hexdigest()
            if b"\r" in data:
                problems.append(f"core.autocrlf={value}: {rel}에 CR이 있습니다(LF가 아님)")
        if len(set(digests.values())) != 1:
            problems.append(f"{rel}: 두 설정의 작업 트리 해시가 다릅니다 {digests}")
    assert not problems, "\n".join(problems)


def test_c2_2_bat_cmd_crlf_and_githooks_lf(checkouts):
    problems = []
    for value, root in checkouts.items():
        for rel, data in CRLF_FILES.items():
            got = (root / rel).read_bytes()
            if got != data.replace(b"\n", b"\r\n"):
                problems.append(f"core.autocrlf={value}: {rel}이 CRLF로 체크아웃되지 않았습니다: {got!r}")
        got = (root / GITHOOK_FILE).read_bytes()
        if got != LF_TEXT_FILES[GITHOOK_FILE]:
            problems.append(f"core.autocrlf={value}: {GITHOOK_FILE}이 LF로 체크아웃되지 않았습니다: {got!r}")
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 4 ③

def test_c4_3_other_agent_files_not_in_applied_or_same(request):
    """품질 밖 정의 파일은 적용본이 없거나, 있으면 git diff --no-index 결과가 비어 있다."""
    folders = [f for f in (dev_folder(request.config), latest_folder(DESIGN_WORKSPACE)) if f is not None]
    problems = []
    for folder in folders:
        for name in OTHER_AGENT_FILES:
            applied_file = folder / APPLIED_AGENTS_REL / name
            if not applied_file.exists():
                continue
            res = git(["diff", "--no-index", "--exit-code", f".claude/agents/{name}", str(applied_file)],
                      env=repo_env(), check=False)
            if res.returncode != 0 or res.stdout.strip():
                problems.append(f"{applied_file}: 원본과 다릅니다(종료 코드 {res.returncode})\n"
                                f"{res.stdout.decode('utf-8', 'replace')}")
    assert not problems, "\n".join(problems)


def test_c4_3_original_agent_files_unchanged():
    """비교 기준인 원본 정의 파일 네 개가 원본 커밋과 같다."""
    paths = [f".claude/agents/{name}" for name in OTHER_AGENT_FILES]
    for p in paths:
        assert (REPO / p).is_file(), f"원본 정의 파일이 없습니다: {p}"
    res = git(["diff", "--quiet", BASE_COMMIT, "--", *paths], env=repo_env(), check=False)
    assert res.returncode == 0, (f"원본 정의 파일이 {BASE_COMMIT}과 다릅니다(종료 코드 {res.returncode}): "
                                 f"{res.stderr.decode('utf-8', 'replace')}")
