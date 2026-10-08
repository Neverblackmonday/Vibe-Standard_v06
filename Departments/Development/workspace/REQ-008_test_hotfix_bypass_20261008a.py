#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-008_test_hotfix_bypass_20261008a.py - HOTFIX scope 표기로 거버넌스 제외 검사를 우회하는지 재현 (일회성)

EC-008_v02 3.4절 2번의 시험을 임시 Git 저장소에서 실행한다. 이 저장소는 건드리지 않는다.
검사기 버전마다 임시 저장소를 따로 만든다(원본용, 적용본용). 두 저장소는 검사기 파일만 다르다.
  사례 A: scope `Departments/Development/assets`, probe_target.py 변경
          원본 통과(우회 재현, 종료 코드 0), 적용본 [FAIL]·종료 코드 1
  사례 B: scope `AGENTS`, AGENTS.md 변경
          원본 통과(우회 재현, 종료 코드 0), 적용본 [FAIL]·종료 코드 1
  사례 C: scope `Departments/Design/docs/prd/01_개요.md`, 같은 파일 변경 (거버넌스와 무관한 정상 HOTFIX)
          원본·적용본 모두 통과, 종료 코드 0
원본용 저장소에서 A·B가 통과하는 것이 결함 사본에서 먼저 실패(우회)를 확인하는 단계다.

사용법: python Departments/Development/workspace/REQ-008_test_hotfix_bypass_20261008a.py
종료 코드: 0 모든 사례가 기대 결과와 같음, 1 하나 이상 다름
"""

import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL_CHECKER = ROOT / "Departments" / "Development" / "assets" / "scripts" / "check_standard.py"
APPLIED_CHECKER = (ROOT / "Departments" / "Development" / "workspace" / "REQ-008_적용본_v01"
                   / "Departments" / "Development" / "assets" / "scripts.적용본" / "check_standard.py")

KST = timezone(timedelta(hours=9))
# 검사기가 자기 위치에서 다섯 단계 위를 루트로 계산하므로(ROOT_DIR) 원래와 같은 깊이에 둔다
CHECKER_REL = "Departments/Development/assets/scripts/check_standard.py"
PROBE_REL = "Departments/Development/assets/scripts/probe_target.py"
AGENTS_REL = "AGENTS.md"
PRD_REL = "Departments/Design/docs/prd/01_개요.md"
HOTFIX_REL = "Departments/Secretariat/results/HOTFIX-001_v01.md"
# 검사기가 HOTFIX를 찾는 폴더. 첫 커밋에 넣기 위해 .gitkeep을 둔다
KEEP_RELS = ["Departments/Secretariat/results/.gitkeep",
             "Departments/Secretariat/docs/requests/.gitkeep"]

CASES = [
    # (사례, HOTFIX scope, 바꾸는 파일, 원본 기대 종료 코드, 적용본 기대 종료 코드)
    ("A", "Departments/Development/assets", PROBE_REL, 0, 1),
    ("B", "AGENTS", AGENTS_REL, 0, 1),
    ("C", PRD_REL, PRD_REL, 0, 0),
]
CONFIRMED = "2026-10-08T15:00:00+09:00"


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def git(repo, *args):
    # -c core.quotepath=false: 한국어 경로를 8진 이스케이프 없이 출력한다
    cmd = ["git", "-c", "core.quotepath=false", *args]
    res = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    print(f"$ git {' '.join(args)}  [{now()}] (종료 코드 {res.returncode})")
    out = res.stdout.rstrip("\n")
    if out:
        print(out)
    if res.stderr.strip():
        print(f"[stderr] {res.stderr.strip()}")
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패(종료 코드 {res.returncode}): {res.stderr.strip()}")
    return res.stdout


def write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def make_repo(base, name, checker_src):
    repo = base / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "REQ-008 test")
    git(repo, "config", "user.email", "req-008-test@example.invalid")
    (repo / CHECKER_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checker_src, repo / CHECKER_REL)
    write(repo, PROBE_REL, "# REQ-008 시험용 파일\n")
    write(repo, AGENTS_REL, "# REQ-008 시험용 AGENTS.md\n")
    write(repo, PRD_REL, "# REQ-008 시험용 PRD\n")
    for rel in KEEP_RELS:
        write(repo, rel, "")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def reset(repo):
    # 사례마다 첫 커밋 상태로 되돌린다. 임시 저장소 안에서만 실행한다
    git(repo, "reset", "-q", "--hard", "HEAD")
    git(repo, "clean", "-q", "-fd")


def hotfix_text(scope_item):
    return ("---\n"
            'task_id: "001"\n'
            f'confirmed: "{CONFIRMED}"\n'
            "scope:\n"
            f"  - {scope_item}\n"
            "---\n\n"
            "# HOTFIX-001: REQ-008 재현 시험용 기록\n")


def run_case(repo, label, case, scope_item, target, expected):
    print(f"--- 사례 {case} / {label} 저장소 / scope `{scope_item}` / 바꾸는 파일 `{target}` ---")
    reset(repo)
    write(repo, HOTFIX_REL, hotfix_text(scope_item))
    with open(repo / target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(f"변경 사례 {case}\n")
    git(repo, "status", "--porcelain", "-uall")
    cmd = [sys.executable, CHECKER_REL]
    started = now()
    res = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    print(f"$ python {CHECKER_REL}  [{started}] (종료 코드 {res.returncode})")
    out = res.stdout.rstrip("\n")
    if out:
        print(out)
    if res.stderr.strip():
        print(f"[stderr] {res.stderr.strip()}")
    has_fail = "[FAIL]" in res.stdout
    ok = res.returncode == expected and (has_fail if expected == 1 else not has_fail)
    print(f"[{'PASS' if ok else 'FAIL'}] 사례 {case} {label}: 종료 코드 {res.returncode} (기대값 {expected}), [FAIL] 출력={has_fail}")
    return ok


def main():
    for src in (ORIGINAL_CHECKER, APPLIED_CHECKER):
        if not src.exists():
            print(f"[FAIL] 시험 입력 파일이 없습니다: {src.relative_to(ROOT).as_posix()}")
            return 1
    print(f"[START] {now()}")
    results = {}
    with tempfile.TemporaryDirectory(prefix="req008_", ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        for label, src, idx in (("원본용", ORIGINAL_CHECKER, 3), ("적용본용", APPLIED_CHECKER, 4)):
            print(f"== {label} 저장소 (검사기: {src.relative_to(ROOT).as_posix()}) ==")
            repo = make_repo(base, "original" if idx == 3 else "applied", src)
            for case in CASES:
                name, scope_item, target = case[0], case[1], case[2]
                results[f"사례 {name} {label}"] = run_case(repo, label, name, scope_item, target, case[idx])
    print("== 요약 ==")
    for name, ok in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[END] {now()}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
