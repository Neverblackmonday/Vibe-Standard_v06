#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-012_test_staged_20261009a.py - REQ-012 개정 규칙과 check_standard.py 동작 대조 시험 (일회성)

EC-012_v02 3.4절 1번 ①·②·③·④의 동작 확인을 실행한다. 이 저장소는 건드리지 않는다.
  1부(함수 단위, 원본 검사기를 모듈로 불러 실행)
    W1~W5: is_whitelisted()가 research/·briefings/·inbox(최종 판정서 승인 기록)를 대조에서 빼는지(①)
    H1~H3: parse_header()·approval_problem()이 승인 필드 줄 끝 주석(`# 문체 반영`,
           문체 반영본 주석)을 떼고 값을 읽는지, `approved: ""`를 미기재로 처리하는지(②)
    E1:    검사기 소스에 effort를 읽는 코드가 없는지(③)
  2부(저장소 밖 임시 Git 저장소에 원본 검사기를 같은 깊이로 복사해 실행)
    S1: 승인된 REQ scope의 거버넌스 파일 반영분과 승인 기록만 스테이징, scope 밖 변경은 작업 트리에만 둠
        --staged 종료 코드 0, 옵션 없는 실행 종료 코드 1, pre-commit 훅을 켠 git commit 성공(④)
    S2: S1에서 scope 밖 파일까지 스테이징. --staged 종료 코드 1, git commit 실패(④)
    S3: 최신 버전이 `approved: ""`인 문체 반영본(v02). --staged 종료 코드 1(②)
    S4: S3의 v02에 직전 버전 값과 문체 반영본 주석을 기재. --staged 종료 코드 0(②)
    S5: v01 승인 필드에 `# 문체 반영` 주석. --staged 종료 코드 0(②)
    S6: research/·briefings/·inbox 승인 기록만 스테이징. --staged 종료 코드 0(①)

사용법: python Departments/Development/workspace/REQ-012_test_staged_20261009a.py
종료 코드: 0 모든 사례가 기대 결과와 같음, 1 하나 이상 다름
"""

import importlib.util
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
CHECKER_REL = "Departments/Development/assets/scripts/check_standard.py"
CHECKER = ROOT / CHECKER_REL
HOOK = ROOT / ".githooks" / "pre-commit"
KST = timezone(timedelta(hours=9))

APPROVED = "2026-10-09T01:03:52+09:00"
REQ_DIR = "Departments/Secretariat/docs/requests"
REQ_V1 = f"{REQ_DIR}/REQ-001_v01.md"
REQ_V2 = f"{REQ_DIR}/REQ-001_v02.md"
SCOPE = ["AGENTS.md", "Workflow/03_라이프사이클.md"]
OUT_OF_SCOPE = "Workflow/04_모델_운용.md"
OTHER_UNTRACKED = "Departments/Design/docs/tad/EC-002_v01.md"
APPROVAL_RECORD = "Departments/Secretariat/assets/inbox/승인기록_20261009_RES-001_v01.md"
RESEARCH = "Departments/Secretariat/assets/research/조사_20261009_시험_v01.md"
BRIEFING = "Departments/Secretariat/assets/briefings/시험_v01.md"
STYLE_COMMENT = "# 문체 반영"
STYLE_COPY_COMMENT = (f"# 문체 반영본: 승인 근거 {REQ_V1}, "
                      "대조 Departments/Quality/results/RES-001-REQ_v02.md")


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def report(results, name, ok, detail):
    results[name] = ok
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def load_checker():
    spec = importlib.util.spec_from_file_location("check_standard_under_test", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def req_text(approved_line, scope):
    lines = "".join(f"  - {s}\n" for s in scope)
    return ("---\n"
            'task_id: "001"\n'
            f"{approved_line}\n"
            "scope:\n"
            f"{lines}"
            "---\n\n"
            "# REQ-001: REQ-012 시험용 기록\n")


def part1(mod, results, tmp):
    print("== 1부: 함수 단위 ==")
    for name, path, expected in (
            ("W1 research", RESEARCH, True),
            ("W2 briefings", BRIEFING, True),
            ("W3 inbox 최종 판정서 승인 기록", APPROVAL_RECORD, True),
            ("W4 REQ 기록(비교)", REQ_V1, True),
            ("W5 AGENTS.md(비교)", "AGENTS.md", False)):
        got = mod.is_whitelisted(path)
        report(results, name, got == expected, f"is_whitelisted('{path}') = {got} (기대 {expected})")

    for name, line, expected_value, expect_problem in (
            ("H1 `# 문체 반영` 주석", f'approved: "{APPROVED}" {STYLE_COMMENT}', APPROVED, None),
            ("H2 문체 반영본 주석", f'approved: "{APPROVED}" {STYLE_COPY_COMMENT}', APPROVED, None),
            ("H3 문체 반영본 대조 전", 'approved: ""', None, "approved: 미기재")):
        p = tmp / f"{name[:2]}.md"
        p.write_text(req_text(line, SCOPE), encoding="utf-8", newline="\n")
        rec = mod.parse_header(p, "approved")
        problem = mod.approval_problem(rec, "approved")
        ok = rec["approved"] == expected_value and problem == expect_problem and rec["scope"] == set(SCOPE)
        report(results, name, ok,
               f"줄 `{line}` → approved={rec['approved']!r}, problem={problem!r}, scope={sorted(rec['scope'])}")

    src = CHECKER.read_text(encoding="utf-8")
    hits = [i + 1 for i, ln in enumerate(src.splitlines()) if "effort" in ln.lower()]
    report(results, "E1 effort 읽기 코드", not hits, f"검사기 소스의 `effort` 일치 줄 {hits}")


def git(repo, *args, check=True):
    cmd = ["git", "-c", "core.quotepath=false", *args]
    res = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    print(f"$ git {' '.join(args)}  [{now()}] (종료 코드 {res.returncode})")
    out = (res.stdout.rstrip("\n") + ("\n" + res.stderr.strip() if res.stderr.strip() else "")).strip()
    if out:
        print(out)
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패(종료 코드 {res.returncode}): {res.stderr.strip()}")
    return res


def write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def append(repo, rel, text):
    with open(repo / rel, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def make_repo(base):
    repo = base / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "REQ-012 test")
    git(repo, "config", "user.email", "req-012-test@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    (repo / CHECKER_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CHECKER, repo / CHECKER_REL)
    (repo / ".githooks").mkdir()
    shutil.copyfile(HOOK, repo / ".githooks" / "pre-commit")
    for rel in SCOPE + [OUT_OF_SCOPE]:
        write(repo, rel, "# REQ-012 시험용 원본\n")
    for rel in (f"{REQ_DIR}/.gitkeep", "Departments/Secretariat/results/.gitkeep"):
        write(repo, rel, "")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def reset(repo):
    # 사례마다 첫 커밋 상태로 되돌린다. 임시 저장소 안에서만 실행한다
    git(repo, "reset", "-q", "--hard", "HEAD")
    git(repo, "clean", "-q", "-fdx")


def run_checker(repo, staged):
    args = [sys.executable, CHECKER_REL] + (["--staged"] if staged else [])
    started = now()
    res = subprocess.run(args, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    print(f"$ python {CHECKER_REL}{' --staged' if staged else ''}  [{started}] (종료 코드 {res.returncode})")
    if res.stdout.strip():
        print(res.stdout.rstrip("\n"))
    if res.stderr.strip():
        print(f"[stderr] {res.stderr.strip()}")
    return res


def check(results, name, res, expected, must_contain=None):
    has_fail = "[FAIL]" in res.stdout
    ok = res.returncode == expected and (has_fail if expected == 1 else not has_fail)
    if must_contain:
        ok = ok and must_contain in res.stdout
    report(results, name, ok, f"종료 코드 {res.returncode} (기대 {expected}), [FAIL] 출력={has_fail}"
           + (f", 포함 문구 `{must_contain}`={must_contain in res.stdout}" if must_contain else ""))


def setup_reflection(repo, req_v1_line, req_v2_line=None):
    """승인된 REQ와 그 scope의 반영분, 최종 판정서 승인 기록, 다른 안건의 변경을 만든다."""
    write(repo, REQ_V1, req_text(req_v1_line, SCOPE))
    if req_v2_line is not None:
        write(repo, REQ_V2, req_text(req_v2_line, SCOPE))
    for rel in SCOPE:
        append(repo, rel, "적용본 반영\n")
    write(repo, APPROVAL_RECORD, "# 승인 기록 시험\n")
    # 다른 안건의 변경: 스테이징하지 않는다
    append(repo, OUT_OF_SCOPE, "다른 안건의 변경\n")
    write(repo, OTHER_UNTRACKED, "# 다른 안건 EC\n")
    git(repo, "add", "--", *SCOPE, APPROVAL_RECORD)


def part2(results, base):
    print("== 2부: 임시 Git 저장소 ==")
    repo = make_repo(base)
    v1 = f'approved: "{APPROVED}"'

    print("--- 사례 S1: 이 안건 변경만 스테이징, 다른 안건 변경은 작업 트리에 남김 ---")
    reset(repo)
    setup_reflection(repo, v1)
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S1 --staged", run_checker(repo, True), 0, "REQ-001_v01.md")
    check(results, "S1 옵션 없음(비교)", run_checker(repo, False), 1, OUT_OF_SCOPE)
    res = git(repo, "commit", "-q", "-m", "feat: [REQ-001] 시험", check=False)
    ok = res.returncode == 0 and "[SUCCESS]" in (res.stdout + res.stderr)
    report(results, "S1 pre-commit 훅 커밋", ok, f"git commit 종료 코드 {res.returncode}")
    if res.returncode == 0:
        git(repo, "reset", "-q", "--hard", "HEAD~1")

    print("--- 사례 S2: scope 밖 파일까지 스테이징 ---")
    reset(repo)
    setup_reflection(repo, v1)
    git(repo, "add", "--", OUT_OF_SCOPE)
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S2 --staged", run_checker(repo, True), 1, OUT_OF_SCOPE)
    res = git(repo, "commit", "-q", "-m", "feat: [REQ-001] 시험", check=False)
    report(results, "S2 pre-commit 훅 커밋", res.returncode != 0 and "[BLOCKED]" in (res.stdout + res.stderr),
           f"git commit 종료 코드 {res.returncode} (기대 0이 아님)")
    if res.returncode == 0:
        git(repo, "reset", "-q", "--hard", "HEAD~1")

    print("--- 사례 S3: 최신 버전이 대조 전 문체 반영본(approved: \"\") ---")
    reset(repo)
    setup_reflection(repo, v1, 'approved: ""')
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S3 --staged", run_checker(repo, True), 1, "REQ-001_v02.md의 scope는 대상 파일을 포함하지만 승인 요건을 갖추지 못했습니다 (approved: 미기재)")

    print("--- 사례 S4: 문체 반영본에 직전 버전 값과 문체 반영본 주석 기재 ---")
    reset(repo)
    setup_reflection(repo, v1, f"{v1} {STYLE_COPY_COMMENT}")
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S4 --staged", run_checker(repo, True), 0, f"REQ-001_v02.md (승인: {APPROVED})")

    print("--- 사례 S5: 대표님 본인 기재 승인 필드의 `# 문체 반영` 주석 ---")
    reset(repo)
    setup_reflection(repo, f"{v1} {STYLE_COMMENT}")
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S5 --staged", run_checker(repo, True), 0, f"REQ-001_v01.md (승인: {APPROVED})")

    print("--- 사례 S6: 조사·보고 자료와 승인 기록만 스테이징 ---")
    reset(repo)
    for rel in (RESEARCH, BRIEFING, APPROVAL_RECORD):
        write(repo, rel, "# 시험\n")
    git(repo, "add", "--", RESEARCH, BRIEFING, APPROVAL_RECORD)
    git(repo, "status", "--porcelain", "-uall")
    check(results, "S6 --staged", run_checker(repo, True), 0, "scope 대조 제외 구역")


def main():
    for src in (CHECKER, HOOK):
        if not src.exists():
            print(f"[FAIL] 시험 입력 파일이 없습니다: {src}")
            return 1
    print(f"[START] {now()}")
    results = {}
    with tempfile.TemporaryDirectory(prefix="req012_", ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        part1(load_checker(), results, base)
        part2(results, base)
    print("== 요약 ==")
    for name, ok in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[END] {now()}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
