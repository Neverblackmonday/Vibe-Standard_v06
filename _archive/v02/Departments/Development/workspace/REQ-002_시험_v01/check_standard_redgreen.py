#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REQ-002 EC 3.4절 2번 check_standard.py 패치의 Red/Green 시험.

원본(Departments/Development/assets/scripts/check_standard.py)과
적용본(Departments/Development/workspace/REQ-002_적용본_v01/...)을
저장소 밖 임시 Git 저장소에 각각 배치해 같은 시나리오를 실행한다.

판정 구분:
- redgreen: 원본은 기대 결과를 충족하지 못하고(Red) 적용본은 충족해야(Green) 한다.
- guard: 새 기능이 거부해야 하는 입력. 원본도 같은 결과이므로 Red가 없다.
- green: 결함이 없는 경로의 확인(EC 3.4절 2번 ⑦). Red가 없다.

사용법: python Departments/Development/workspace/REQ-002_시험_v01/check_standard_redgreen.py
종료 코드: 모든 시나리오가 기대대로이면 0, 아니면 1.
"""

import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ORIGINAL = REPO / "Departments/Development/assets/scripts/check_standard.py"
PATCHED = REPO / "Departments/Development/workspace/REQ-002_적용본_v01/Departments/Development/assets/scripts/check_standard.py"
SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def git(cwd, *args, check=True):
    res = subprocess.run(["git", *args], cwd=cwd, capture_output=True, encoding="utf-8", errors="replace")
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패 ({res.returncode}): {res.stderr.strip()}")
    return res


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def req_text(scope, approved="2026-10-06"):
    lines = ["---", 'task_id: "001"', 'tier: "Major"', f'approved: "{approved}"', "scope:"]
    lines += [f"  - {s}" for s in scope]
    lines += ["---", "", "# REQ-001: 시험", ""]
    return "\n".join(lines)


def hotfix_text(scope, confirmed="2026-10-06"):
    lines = ["---", 'hotfix_id: "001"', f'confirmed: "{confirmed}"', "scope:"]
    lines += [f"  - {s}" for s in scope]
    lines += ["---", "", "# HOTFIX-001: 시험", ""]
    return "\n".join(lines)


def init_repo(git_root, std_root, script, req_scope, extra_files=None):
    """git_root에 저장소를 만들고 std_root(표준 루트)에 표준 골격과 시험 대상 스크립트를 넣어 첫 커밋한다."""
    write(std_root, "Departments/Secretariat/docs/requests/REQ-001.md", req_text(req_scope))
    write(std_root, "Departments/Secretariat/assets/inbox/.gitkeep", "")
    write(std_root, "Departments/Development/docs/api.md", "v1\n")
    write(std_root, "Departments/Development/assets/src/main.py", "print('v1')\n")
    write(std_root, "AGENTS.md", "v1\n")
    for rel, text in (extra_files or {}).items():
        write(std_root, rel, text)
    dst = Path(std_root) / SCRIPT_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(script, dst)
    git(git_root, "init", "-q")
    git(git_root, "config", "user.name", "redgreen")
    git(git_root, "config", "user.email", "redgreen@example.invalid")
    git(git_root, "config", "core.quotepath", "false")
    git(git_root, "add", "-A")
    # 임시 저장소 전용 커밋. 전역 훅이 개입하지 않도록 훅을 건너뛴다
    git(git_root, "commit", "-q", "--no-verify", "-m", "base")


# 각 시나리오: (번호, 구분, 설명, 준비 함수, 기대 종료 코드, 포함 문자열 목록, 불포함 문자열 목록)
def s1_untracked_subfolder(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Design/docs/prd/new/01_개요.md"])
    write(tmp, "Departments/Design/docs/prd/new/01_개요.md", "new\n")
    return tmp


def s2a_toplevel_fail(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Development/docs"])
    write(tmp, "Departments/Development/docs/api.md", "v2\n")
    git(tmp, "config", "core.bare", "true")
    return tmp


def s2b_status_fail(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Development/docs"])
    write(tmp, "Departments/Development/docs/api.md", "v2\n")
    (Path(tmp) / ".git" / "index").write_bytes(b"corrupt-index")
    return tmp


def s3_outside_root(tmp, script):
    std = Path(tmp) / "std"
    write(tmp, "outside.txt", "v1\n")
    init_repo(tmp, std, script, ["Departments/Development/docs"])
    # 표준 루트에 빈 .git 폴더를 두면 is_initial_commit()은 .git 존재로 보고,
    # Git은 유효하지 않은 .git을 건너뛰어 상위 저장소를 찾는다(표준이 더 큰 저장소 안에 있는 상황)
    (std / ".git").mkdir()
    write(tmp, "outside.txt", "v2\n")
    return std


def s4a_no_tests(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Development/assets/src"])
    write(tmp, "Departments/Development/assets/src/main.py", "print('v2')\n")
    return tmp


def s4b_pytest_rc5(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Development/assets/src"],
              {"Departments/Development/assets/tests/test_empty.py": "# 수집할 테스트 없음\n"})
    write(tmp, "Departments/Development/assets/src/main.py", "print('v2')\n")
    return tmp


def s5_inbox(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Development/docs"])
    write(tmp, "Departments/Secretariat/assets/inbox/memo.md", "메모\n")
    write(tmp, "Departments/Secretariat/assets/inbox/sub/memo2.md", "메모2\n")
    return tmp


def s6_hotfix_confirmed(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Design/docs/prd"])
    write(tmp, "Departments/Secretariat/results/HOTFIX-001.md", hotfix_text(["Departments/Development/docs/api.md"]))
    write(tmp, "Departments/Development/docs/api.md", "v2\n")
    return tmp


def s6g_hotfix_unconfirmed(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Design/docs/prd"])
    write(tmp, "Departments/Secretariat/results/HOTFIX-001.md", hotfix_text(["Departments/Development/docs/api.md"], confirmed=""))
    write(tmp, "Departments/Development/docs/api.md", "v2\n")
    return tmp


def s6g_hotfix_four_files(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Design/docs/prd"])
    scope = ["Departments/Development/docs/api.md", "Departments/Development/docs/a.md",
             "Departments/Development/docs/b.md", "Departments/Development/docs/c.md"]
    write(tmp, "Departments/Secretariat/results/HOTFIX-001.md", hotfix_text(scope))
    write(tmp, "Departments/Development/docs/api.md", "v2\n")
    return tmp


def s6g_hotfix_governance(tmp, script):
    init_repo(tmp, tmp, script, ["Departments/Design/docs/prd"])
    write(tmp, "Departments/Secretariat/results/HOTFIX-001.md", hotfix_text(["AGENTS.md"]))
    write(tmp, "AGENTS.md", "v2\n")
    return tmp


def s7_governance_in_req(tmp, script):
    init_repo(tmp, tmp, script, ["AGENTS.md"])
    write(tmp, "AGENTS.md", "v2\n")
    return tmp


SCENARIOS = [
    ("①", "redgreen", "새 하위 폴더 안 파일이 파일 단위 scope와 일치", s1_untracked_subfolder, 0, [], []),
    ("②a", "redgreen", "git rev-parse --show-toplevel 실패(core.bare=true) 시 차단", s2a_toplevel_fail, 1, ["[FAIL]"], []),
    ("②b", "redgreen", "git status 실패(인덱스 손상) 시 차단", s2b_status_fail, 1, ["[FAIL]"], []),
    ("③", "redgreen", "표준 루트 밖 변경 경로를 [INFO]로 출력", s3_outside_root, 0, ["[INFO]", "outside.txt"], []),
    ("④a", "redgreen", "src 변경·테스트 파일 없음 시 [WARN]", s4a_no_tests, 0, ["[WARN]"], []),
    ("④b", "redgreen", "src 변경·pytest 종료 코드 5 시 [WARN]", s4b_pytest_rc5, 0, ["[WARN]"], ["단위 테스트 전원 통과"]),
    ("⑤", "redgreen", "inbox 메모·inbox 하위 폴더 메모 통과", s5_inbox, 0, [], []),
    ("⑥", "redgreen", "confirmed HOTFIX scope 안 변경 통과", s6_hotfix_confirmed, 0, ["HOTFIX-001.md"], []),
    ("⑥g1", "guard", "confirmed 미기재 HOTFIX는 승인 범위 아님", s6g_hotfix_unconfirmed, 1, ["[FAIL]"], []),
    ("⑥g2", "guard", "scope 4개 HOTFIX는 승인 범위 아님", s6g_hotfix_four_files, 1, ["[FAIL]"], []),
    ("⑥g3", "guard", "거버넌스 경로 HOTFIX는 승인 범위 아님", s6g_hotfix_governance, 1, ["[FAIL]"], []),
    ("⑦", "green", "거버넌스 파일 변경이 승인 REQ scope 안이면 통과", s7_governance_in_req, 0, [], []),
]


def run_case(prepare, script):
    # 임시 저장소는 시험마다 새로 만든다. Windows에서 Git 객체 파일 잠금으로 정리가 실패해도
    # 시험 결과와 무관한 OS 임시 폴더이므로 정리 오류는 무시한다
    with tempfile.TemporaryDirectory(prefix="req002_rg_", ignore_cleanup_errors=True) as tmp:
        std = prepare(tmp, script)
        res = subprocess.run([sys.executable, str(Path(std) / SCRIPT_REL)], cwd=std,
                             capture_output=True, encoding="utf-8", errors="replace", env=ENV)
        return res.returncode, (res.stdout + res.stderr).strip()


def meets(rc, out, exp_rc, must, must_not):
    return rc == exp_rc and all(m in out for m in must) and not any(m in out for m in must_not)


def main():
    # 콘솔 기본 코드 페이지(cp949)로 출력하면 Git Bash에서 한국어가 깨지므로 UTF-8로 고정한다
    sys.stdout.reconfigure(encoding="utf-8")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    print(f"시각: {now}")
    print(f"원본: {ORIGINAL.relative_to(REPO).as_posix()}")
    print(f"적용본: {PATCHED.relative_to(REPO).as_posix()}")
    ok = True
    for no, kind, desc, prepare, exp_rc, must, must_not in SCENARIOS:
        o_rc, o_out = run_case(prepare, ORIGINAL)
        p_rc, p_out = run_case(prepare, PATCHED)
        o_ok = meets(o_rc, o_out, exp_rc, must, must_not)
        p_ok = meets(p_rc, p_out, exp_rc, must, must_not)
        if kind == "redgreen":
            verdict = "Red→Green" if (not o_ok and p_ok) else ("Red 없음" if o_ok else "Green 실패")
            case_ok = (not o_ok) and p_ok
        else:
            verdict = "Green" if p_ok else "Green 실패"
            case_ok = p_ok
        ok = ok and case_ok
        print(f"\n=== {no} [{kind}] {desc} | 기대 종료 코드 {exp_rc} | 판정 {verdict}")
        print(f"--- 원본 (종료 코드 {o_rc}, 기대 충족 {o_ok})")
        print(o_out)
        print(f"--- 적용본 (종료 코드 {p_rc}, 기대 충족 {p_ok})")
        print(p_out)
    print(f"\n전체 결과: {'모두 기대대로' if ok else '기대와 다른 시나리오 있음'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
