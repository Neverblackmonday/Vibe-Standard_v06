#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_standard.py - 바이브 코딩 표준 v02 무결성 검사기
1. Init Commit Exception: 초기화 커밋은 안전하게 허용 (.git 미생성 또는 HEAD 부재 시)
2. Git Query Fail-Closed: Git 조회 실패 시 원인과 조치를 출력하고 차단
3. CEO Protection: CEO/ 구역 무단 수정 절대 차단 (Fail-Closed)
4. Approval & Scope Quarantine: 변경 파일이 승인된 REQ 또는 확인된 HOTFIX의 scope:에 부합하는지 정밀 대조
5. Strict Whitelist: 부서 직속 depth 2의 results/ 및 workspace/, 비서실 inbox/만 허용 (F4-3 패치)
6. Multi-REQ Matching: 초안 REQ가 존재해도 해당 승인 안건 정상 커밋 지원 (F4-4 패치)
7. Test On Source Change: 소스코드 변경 시에만 단위 테스트 실행
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent

# Scope 대조 제외 정상 산출물 구역 (화이트리스트)
WHITELIST_PREFIXES = (
    "Departments/Secretariat/docs/requests/",  # REQ 문서는 scope 대상 아님
    "Departments/Secretariat/assets/inbox/",  # 대표님 요구사항 메모는 승인 전 허용 구역
    "Audits/",  # 외부 감사 보고서는 독립 감사 산출물
    "_archive/",
)

# 핫픽스 scope에 넣을 수 없는 거버넌스 경로 (AGENTS.md 「핵심 원칙」 거버넌스 구역 및 CEO/)
GOVERNANCE_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "setup.cmd",
    ".claude",
    ".githooks",
    "Departments/Development/assets/scripts",
    "Workflow",
    "CEO",
)
HOTFIX_MAX_SCOPE = 3

def is_whitelisted(filepath):
    norm = filepath.replace("\\", "/")
    parts = norm.split("/")
    # F4-3 패치: 부서 직속 1차 하위 폴더(depth 2)의 results/ 및 workspace/만 허용
    # 예: Departments/<Dept>/results/... 또는 Departments/<Dept>/workspace/...
    if len(parts) >= 3 and parts[0] == "Departments" and parts[2] in ("results", "workspace"):
        return True
    if any(norm.startswith(p) for p in WHITELIST_PREFIXES):
        return True
    return False

def is_initial_commit():
    dot_git = ROOT_DIR / ".git"
    if not dot_git.exists():
        return True
    res = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT_DIR, capture_output=True)
    return res.returncode != 0

def parse_header(path, approval_key):
    """머리말에서 승인 필드(approval_key) 값, 분류(classification/tier), scope 목록을 읽는다."""
    content = path.read_text(encoding="utf-8")
    approved = None
    classification = None
    scope_lines = []
    in_scope = False

    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith(approval_key + ":"):
            val = trimmed.split(":", 1)[1].split("#", 1)[0].strip().strip("'\"")
            if val and val.lower() != "null" and val.lower() != "false":
                approved = val
            continue
        if trimmed.startswith("classification:") or trimmed.startswith("tier:"):
            classification = trimmed.split(":", 1)[1].split("#", 1)[0].strip().strip("'\"")
            continue
        if trimmed.startswith("scope:"):
            in_scope = True
            continue
        if in_scope:
            if line.startswith("  - ") or line.startswith("    - "):
                p = line.split("-", 1)[1].strip().strip("'\"")
                scope_lines.append(p.replace("\\", "/").rstrip("/"))
            elif trimmed and not line.startswith(" ") and not line.startswith("#"):
                break

    return {
        "name": path.name,
        "scope": set(scope_lines),
        "approved": approved,
        "classification": classification,
    }

def load_all_reqs():
    req_dir = ROOT_DIR / "Departments" / "Secretariat" / "docs" / "requests"
    if not req_dir.exists():
        return []

    req_files = sorted([f for f in req_dir.glob("REQ-*.md") if f.name != "REQ_TEMPLATE.md"])
    return [parse_header(f, "approved") for f in req_files]

def is_governance_path(scope_item):
    return any(scope_item == g or scope_item.startswith(g + "/") for g in GOVERNANCE_PATHS)

def load_valid_hotfixes():
    """승인 요건(confirmed: 기재, scope 3개 이하, 거버넌스 경로 제외)을 갖춘 HOTFIX만 돌려준다."""
    hotfix_dir = ROOT_DIR / "Departments" / "Secretariat" / "results"
    if not hotfix_dir.exists():
        return []

    valid = []
    for f in sorted(hotfix_dir.glob("HOTFIX-*.md")):
        hf = parse_header(f, "confirmed")
        # 요건 미달 HOTFIX는 승인 범위에서 빼되, 커밋 차단 원인을 추적할 수 있도록 사유를 출력한다
        if not hf["approved"]:
            print(f"[INFO] {hf['name']}: confirmed: 미기재로 승인 범위에서 제외합니다.")
            continue
        if not hf["scope"] or len(hf["scope"]) > HOTFIX_MAX_SCOPE:
            print(f"[INFO] {hf['name']}: scope 항목 {len(hf['scope'])}개(허용 1~{HOTFIX_MAX_SCOPE}개)로 승인 범위에서 제외합니다.")
            continue
        governance = sorted(s for s in hf["scope"] if is_governance_path(s))
        if governance:
            print(f"[INFO] {hf['name']}: scope에 거버넌스 경로({', '.join(governance)})가 있어 승인 범위에서 제외합니다.")
            continue
        valid.append(hf)
    return valid

def check_standard():
    # 1. 초기 커밋(HEAD 부재 또는 .git 부재) 확인
    if is_initial_commit():
        print("[PASS] 프로젝트 초기화 커밋으로 감지되었습니다. 표준 검사를 통과합니다.")
        return True

    # 2. Git 저장소 루트 확인 (조회 실패를 통과로 처리하면 검사 없이 커밋되므로 차단한다)
    toplevel_res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if toplevel_res.returncode != 0:
        print(f"[FAIL] Git 저장소 루트를 조회할 수 없습니다 (git rev-parse --show-toplevel 종료 코드 {toplevel_res.returncode}).")
        print(f"       원인: {toplevel_res.stderr.strip()}")
        print("       조치: 저장소 작업 트리에서 실행했는지, core.bare 설정과 .git 폴더 상태를 확인하십시오.")
        return False
    git_root = Path(toplevel_res.stdout.strip())

    # 3. 변경된 파일 목록 조회 (git status). -uall: 새 폴더를 폴더 단위가 아닌 파일 단위로 받아 scope와 대조한다
    res = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=ROOT_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[FAIL] Git 상태를 조회할 수 없습니다 (git status 종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.strip()}")
        print("       조치: git status를 직접 실행해 오류(인덱스 손상, 잠금 파일 등)를 해결한 뒤 다시 커밋하십시오.")
        return False

    raw_changed = []
    for line in res.stdout.splitlines():
        if not line.strip():
            continue
        filepath = line[3:].strip().strip('"')

        targets = []
        if " -> " in filepath:
            old_p, new_p = filepath.split(" -> ", 1)
            targets.append(old_p.strip().strip('"'))
            targets.append(new_p.strip().strip('"'))
        else:
            targets.append(filepath)

        for target in targets:
            abs_p = (git_root / target).resolve()
            try:
                rel_p = abs_p.relative_to(ROOT_DIR.resolve())
                norm_p = rel_p.as_posix()
                raw_changed.append(norm_p)
            except ValueError:
                # 표준 루트가 더 큰 저장소 안에 있으면 표준 밖 변경도 조회된다.
                # 표준의 scope 규칙이 적용되지 않는 경로이므로 대조에서 빼되, 빠진 사실은 출력한다.
                print(f"[INFO] 표준 루트 밖 경로를 검사에서 제외합니다: {target}")
                continue

    if not raw_changed:
        print("[PASS] 변경된 파일이 없습니다.")
        return True

    # 4. CEO/ 보호 검사 (절대 차단)
    ceo_violations = [f for f in raw_changed if f.startswith("CEO/")]
    if ceo_violations:
        print("[FAIL] CEO/References/ 구역은 대표님 전용 자료입니다. AI의 수정/생성이 절대 금지됩니다:")
        for v in ceo_violations:
            print(f"  - {v}")
        return False

    # 5. 화이트리스트 제외 순수 작업 파일 추출
    work_files = [f for f in raw_changed if not is_whitelisted(f)]
    if not work_files:
        print("[PASS] 모든 변경 파일이 정상 산출물 허용 구역(requests, inbox, results, workspace, _archive) 내에 있습니다.")
        return True

    # 6. F4-4 패치: 작업 파일들을 커버하는 승인된 REQ 역추적 매칭. REQ에 없으면 확인된 HOTFIX와 대조한다
    all_reqs = load_all_reqs()
    hotfixes = load_valid_hotfixes()
    if not all_reqs and not hotfixes:
        print("[FAIL] 등록된 REQ 안건 문서와 확인된 HOTFIX 기록이 없습니다. 비서실에서 REQ를 먼저 작성하고 승인을 받으십시오.")
        return False

    # 작업 파일들이 어느 REQ 또는 HOTFIX의 scope에 속하는지 매칭 (최신 REQ 우선 검색)
    matched_req = None
    for req in list(reversed(all_reqs)) + hotfixes:
        scope_set = req["scope"]
        all_matched = True
        for f in work_files:
            f_no_ext = os.path.splitext(f)[0]
            if not any(f == s or f.startswith(s + "/") or f_no_ext == s for s in scope_set):
                all_matched = False
                break
        if all_matched:
            matched_req = req
            break

    if not matched_req:
        print("[FAIL] 변경된 파일들이 어떤 REQ 또는 확인된 HOTFIX의 승인된 scope에도 온전히 포함되지 않습니다:")
        for f in work_files:
            print(f"  - {f}")
        return False

    if not matched_req["approved"]:
        print(f"[FAIL] 매칭된 {matched_req['name']} 안건이 아직 대표님의 승인을 받지 않았습니다 (approved: 필드 누락).")
        print("       대표님의 명시적 승인(approved: \"YYYY-MM-DD\") 후 커밋하십시오.")
        return False

    print(f"[PASS] Scope Quarantine 통과: 변경 파일이 {matched_req['name']} (승인: {matched_req['approved']}) scope에 일치합니다.")

    # 7. 단위 테스트 (소스코드 변경 시에만 조건부 실행)
    src_changed = any("assets/src/" in f for f in work_files)
    if src_changed:
        test_dir = ROOT_DIR / "Departments" / "Development" / "assets" / "tests"
        if test_dir.exists() and list(test_dir.glob("test_*.py")):
            print("[CHECK] 소스코드 변경 감지: 단위 테스트 실행 중...")
            t_res = subprocess.run([sys.executable, "-m", "pytest", str(test_dir)], cwd=ROOT_DIR)
            if t_res.returncode == 5:
                print("[WARN] 수집된 단위 테스트가 없습니다 (pytest 종료 코드 5). 소스코드 변경이 테스트로 검증되지 않았습니다.")
            elif t_res.returncode != 0:
                print(f"[FAIL] 단위 테스트 실패 (Exit code: {t_res.returncode})")
                return False
            else:
                print("[PASS] 단위 테스트 전원 통과.")
        else:
            print(f"[WARN] 소스코드 변경이 있으나 테스트 파일(test_*.py)이 없습니다: {test_dir.relative_to(ROOT_DIR).as_posix()}")
    else:
        print("[PASS] 소스코드 변경 없음: 단위 테스트 실행을 생략합니다.")

    return True

if __name__ == "__main__":
    if not check_standard():
        sys.exit(1)
    print("[SUCCESS] 바이브 표준 v02 안전성 검사 전원 통과.")
    sys.exit(0)
