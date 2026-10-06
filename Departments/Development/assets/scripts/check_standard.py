#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_standard.py - 바이브 코딩 표준 v04 커밋 전 검사기

검사 순서와 규칙의 설명은 Workflow/06_통제장치_및_배포 「커밋 전 검사」에 있다.
사용법: python check_standard.py            # 작업 트리 전체(git status)를 검사한다
        python check_standard.py --staged   # 커밋 대상(index)만 검사한다 (pre-commit 훅)
1. 초기 커밋 예외: .git이나 HEAD가 없으면 검사를 생략한다
2. Git 조회 실패 시 차단한다
3. CEO/ 아래 변경을 차단한다
4. scope 대조 제외 구역(WHITELIST_PREFIXES, 부서 직속 results/·workspace/)을 뺀다
5. 남은 변경 파일 전체가 승인된 REQ(최신 버전) 하나 또는 확인된 HOTFIX(최신 버전) 하나의 scope에 들어가야 한다
6. 소스코드·테스트가 바뀌었으면 단위 테스트를 실행한다
"""

import os
import re
from datetime import datetime
import subprocess
import sys
from pathlib import Path

# Windows 콘솔에서 한국어 출력이 깨지지 않도록 출력 인코딩을 UTF-8로 고정한다
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# scope 대조에서 빼는 경로 (규정상 작업 구역은 Workflow/02 「작업 구역」이 원천이고, 이 목록은 커밋 검사용 구현이다)
WHITELIST_PREFIXES = (
    "Departments/Secretariat/docs/requests/REQ-",  # REQ 기록 (승인 전 초안 포함)
    "Departments/Secretariat/assets/",  # 요구 메모, 조사 자료, 보고 자료
    "Audits/",  # 외부 검토 보고서
)
# _archive/(지난 버전 기록)는 제외하지 않는다. 읽기 전용 구역이므로 변경은 scope 대조에서 차단된다

# 핫픽스 scope에 넣을 수 없는 경로 (AGENTS.md 「불변 원칙」 3항의 거버넌스 구역, CEO/, _archive/)
GOVERNANCE_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "setup.cmd",
    ".gitattributes",
    ".gitignore",
    ".claude",
    ".githooks",
    "Departments/Development/assets/scripts",
    "Workflow",
    "CEO",
    "_archive",
)
HOTFIX_MAX_SCOPE = 3

# 공식 기록 파일명: <종류>-<세 자리 번호>[-<파생 번호>]_v<두 자리 버전>.md (Workflow/07 「번호와 버전」)
RECORD_NAME = re.compile(r"^(REQ|HOTFIX)-(\d{3}(?:-\d+)?)_v(\d{2})\.md$")
# 승인·확인 시각 형식: YYYY-MM-DDTHH:MM:SS+09:00 (Workflow/07 「머리말」)
APPROVAL_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")


def is_whitelisted(filepath):
    norm = filepath.replace("\\", "/")
    parts = norm.split("/")
    # 부서 직속 1차 하위 폴더의 results/와 workspace/만 뺀다 (예: Departments/<부서>/results/...)
    if len(parts) >= 3 and parts[0] == "Departments" and parts[2] in ("results", "workspace"):
        return True
    return any(norm.startswith(p) for p in WHITELIST_PREFIXES)


def is_initial_commit():
    if not (ROOT_DIR / ".git").exists():
        return True
    res = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT_DIR, capture_output=True)
    return res.returncode != 0


def strip_value(raw):
    """YAML 한 줄 값에서 줄 끝 주석과 따옴표를 뗀다."""
    return raw.split(" #", 1)[0].strip().strip("'\"")


def parse_header(path, approval_key):
    """머리말에서 승인 필드(approval_key) 값과 scope 목록을 읽는다."""
    approved = None
    scope_lines = []
    in_scope = False
    for line in path.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if trimmed.startswith(approval_key + ":"):
            val = strip_value(trimmed.split(":", 1)[1])
            if val and val.lower() not in ("null", "false"):
                approved = val
            continue
        if trimmed.startswith("scope:"):
            in_scope = True
            continue
        if in_scope:
            if line.startswith("  - ") or line.startswith("    - "):
                item = strip_value(line.split("-", 1)[1])
                scope_lines.append(item.replace("\\", "/").rstrip("/"))
            elif trimmed and not line.startswith(" ") and not line.startswith("#"):
                break
    return {"name": path.name, "scope": set(scope_lines), "approved": approved}


def load_latest(folder, kind):
    """폴더에서 kind(REQ 또는 HOTFIX) 기록의 번호별 최신 버전만 고른다."""
    if not folder.exists():
        return []
    latest = {}
    for f in folder.glob(f"{kind}-*.md"):
        m = RECORD_NAME.match(f.name)
        if not m or m.group(1) != kind:
            print(f"[INFO] {f.name}: 기록 파일명 형식(<종류>-<번호>_v<버전>.md)이 아니어서 검사에서 제외합니다.")
            continue
        number, version = m.group(2), int(m.group(3))
        if number not in latest or version > latest[number][0]:
            latest[number] = (version, f)
    return [latest[k][1] for k in sorted(latest)]


def is_governance_path(scope_item):
    return any(scope_item == g or scope_item.startswith(g + "/") for g in GOVERNANCE_PATHS)


def approval_problem(rec, key):
    """승인 필드가 비었거나 형식이 틀리면 사유를, 정상이면 None을 돌려준다."""
    if not rec["approved"]:
        return f"{key}: 미기재"
    if not APPROVAL_TIME.match(rec["approved"]):
        return f"{key}: 형식 오류({rec['approved']}). YYYY-MM-DDTHH:MM:SS+09:00 형식이어야 합니다"
    try:
        datetime.fromisoformat(rec["approved"])
    except ValueError:
        return f"{key}: 실재하지 않는 일시({rec['approved']})"
    return None


def load_records():
    """(승인된 기록 목록, 승인되지 않은 기록과 사유 목록)을 돌려준다."""
    approved, rejected = [], []
    for f in load_latest(ROOT_DIR / "Departments" / "Secretariat" / "docs" / "requests", "REQ"):
        rec = parse_header(f, "approved")
        problem = approval_problem(rec, "approved")
        (rejected if problem else approved).append((rec, problem))
    for f in load_latest(ROOT_DIR / "Departments" / "Secretariat" / "results", "HOTFIX"):
        rec = parse_header(f, "confirmed")
        problem = approval_problem(rec, "confirmed")
        if not problem and not 1 <= len(rec["scope"]) <= HOTFIX_MAX_SCOPE:
            problem = f"scope 항목 {len(rec['scope'])}개(허용 1~{HOTFIX_MAX_SCOPE}개)"
        if not problem:
            governance = sorted(s for s in rec["scope"] if is_governance_path(s))
            if governance:
                problem = f"scope에 핫픽스 제외 경로 포함: {', '.join(governance)} - 거버넌스 파일·CEO/·_archive/는 핫픽스 대상이 아님"
        (rejected if problem else approved).append((rec, problem))
    return [r for r, _ in approved], rejected


# 기록 문서의 버전 접미사(_vNN). scope에 버전 없이 적은 항목이 모든 버전을 포함하게 한다
VERSION_SUFFIX = re.compile(r"_v\d{2}$")


def item_covers(s, f):
    """scope 항목 s가 변경 파일 f를 포함하는지 판단한다."""
    if f == s or f.startswith(s + "/"):
        return True
    # 확장자·버전을 떼고 비교하는 규칙은 확장자 없이 적은 scope 항목에만 적용한다
    if os.path.splitext(s.rsplit("/", 1)[-1])[1]:
        return False
    f_no_ext = os.path.splitext(f)[0]
    return f_no_ext == s or VERSION_SUFFIX.sub("", f_no_ext) == s


def covers(rec, files):
    return all(any(item_covers(s, f) for s in rec["scope"]) for f in files)


def changed_files(staged):
    """변경 파일 목록을 돌려준다. Git 조회에 실패하면 None을 돌려준다."""
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT_DIR,
                         capture_output=True, encoding="utf-8", errors="replace")
    if top.returncode != 0:
        print(f"[FAIL] Git 저장소 루트를 조회할 수 없습니다 (종료 코드 {top.returncode}).")
        print(f"       원인: {top.stderr.strip()}")
        print("       조치: 저장소 작업 트리에서 실행했는지와 .git 폴더 상태를 확인하십시오.")
        return None
    git_root = Path(top.stdout.strip())

    if staged:
        # 커밋 대상(index)만 조회한다. -z: 경로를 따옴표·이스케이프 없이 받는다
        cmd = ["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-status", "-M", "-z"]
    else:
        # -uall: 새 폴더 안의 파일을 폴더 한 줄이 아닌 파일 단위로 받는다
        cmd = ["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall", "-z"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[FAIL] Git 변경 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None

    # 이름 변경은 원래 경로와 새 경로를 모두 대조한다
    paths = []
    tokens = res.stdout.split("\0")
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if not tok:
            i += 1
            continue
        if staged:
            status = tok
            count = 2 if status[:1] in ("R", "C") else 1
            paths.extend(tokens[i + 1:i + 1 + count])
            i += 1 + count
        else:
            status, path = tok[:2], tok[3:]
            paths.append(path)
            if "R" in status or "C" in status:
                paths.append(tokens[i + 1])  # -z 형식은 새 경로 뒤에 원래 경로를 둔다
                i += 1
            i += 1

    result = []
    for target in paths:
        try:
            rel = (git_root / target).resolve().relative_to(ROOT_DIR.resolve())
            result.append(rel.as_posix())
        except ValueError:
            print(f"[INFO] 표준 루트 밖 경로를 검사에서 제외합니다: {target}")
    return result


def run_tests(work_files):
    if not any("assets/src/" in f or "assets/tests/" in f for f in work_files):
        print("[PASS] 소스코드·테스트 변경 없음: 단위 테스트를 생략합니다.")
        return True
    test_dir = ROOT_DIR / "Departments" / "Development" / "assets" / "tests"
    if not (test_dir.exists() and list(test_dir.rglob("test_*.py"))):
        print(f"[WARN] 소스코드·테스트 변경이 있으나 테스트 파일(test_*.py)이 없습니다: {test_dir.relative_to(ROOT_DIR).as_posix()}")
        return True
    print("[CHECK] 소스코드·테스트 변경 감지: 단위 테스트를 실행합니다.")
    code = subprocess.run([sys.executable, "-m", "pytest", str(test_dir)], cwd=ROOT_DIR).returncode
    if code == 5:
        print("[WARN] 수집된 단위 테스트가 없습니다 (pytest 종료 코드 5).")
        return True
    if code != 0:
        print(f"[FAIL] 단위 테스트 실패 (종료 코드 {code})")
        return False
    print("[PASS] 단위 테스트 통과.")
    return True


def check_standard(staged=False):
    if is_initial_commit():
        print("[PASS] 초기화 커밋으로 확인되어 검사를 생략합니다.")
        return True

    files = changed_files(staged)
    if files is None:
        return False
    if not files:
        print("[PASS] 변경된 파일이 없습니다.")
        return True

    ceo = [f for f in files if f.startswith("CEO/")]
    if ceo:
        print("[FAIL] CEO/ 아래는 대표님 전용 구역입니다. 다음 변경을 되돌리십시오:")
        for f in ceo:
            print(f"  - {f}")
        return False

    work_files = [f for f in files if not is_whitelisted(f)]
    if not work_files:
        print("[PASS] 모든 변경 파일이 scope 대조 제외 구역 안에 있습니다.")
        return True

    approved, rejected = load_records()
    matched = next((r for r in approved if covers(r, work_files)), None)
    if matched:
        print(f"[PASS] 변경 파일이 {matched['name']} (승인: {matched['approved']})의 scope 안에 있습니다.")
        return run_tests(work_files)

    print("[FAIL] 변경 파일 전체를 포함하는 승인된 REQ 또는 확인된 HOTFIX가 없습니다. 대상 파일:")
    for f in work_files:
        print(f"  - {f}")
    for rec, problem in rejected:
        if covers(rec, work_files):
            print(f"       참고: {rec['name']}의 scope는 대상 파일을 포함하지만 승인 요건을 갖추지 못했습니다 ({problem}).")
    return False


if __name__ == "__main__":
    if not check_standard(staged="--staged" in sys.argv[1:]):
        sys.exit(1)
    print("[SUCCESS] 바이브 표준 v04 커밋 전 검사 통과.")
    sys.exit(0)
