#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-013_재현시험_20261009a.py - check_standard.py의 CEO/ 처리 재현 시험 (일회성)

EC-013_v02 3.4절 1번의 T1~T10을 원본 check_standard.py와 REQ-013 적용본에 똑같이 실행해
종료 코드를 나란히 출력한다. 시험마다 저장소 밖 임시 폴더에 새 Git 저장소를 만들므로
이 저장소의 기록과 작업 트리는 바뀌지 않는다.

시험 저장소 구성(첫 커밋):
  CEO/c1.txt, CEO/c2.txt, CEO/c3.txt        대표님 구역
  src/a.txt                                 승인된 REQ-900 scope(src) 안
  other/b.txt                               scope 밖
  Departments/Secretariat/assets/x.md       대조 제외 구역
  Departments/Quality/results/r.md          대조 제외 구역(부서 results/)
  Departments/Secretariat/docs/requests/REQ-900_v01.md   approved 기재, scope: src
  Departments/Development/assets/scripts/check_standard.py  시험 대상 검사기 사본
  .githooks/pre-commit                      이 저장소 훅 사본 (첫 커밋 뒤 core.hooksPath 설정)

「기대」는 적용본 기준이다. 원본 열은 Red 확인(T1·T5·T9에서 원본이 실패)과 비교용이다.
「대조」 열은 같은 작업 트리에서 CEO/ 변경만 뺀 경우의 결과다(T2~T4).

사용법: python Departments/Development/workspace/REQ-013_재현시험_20261009a.py
종료 코드: 0 적용본 결과가 모두 기대와 같고 원본 Red 확인도 성립, 1 하나 이상 다름
"""

import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows 콘솔에서 한국어 출력이 깨지지 않도록 출력 인코딩을 UTF-8로 고정한다
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[3]
ORIGINAL = ROOT / "Departments/Development/assets/scripts/check_standard.py"
APPLIED = (ROOT / "Departments/Development/workspace/REQ-013_적용본_v01/Departments/Development/assets"
           / "scripts.적용본/check_standard.py")
HOOK = ROOT / ".githooks/pre-commit"
CHECKER_REL = "Departments/Development/assets/scripts/check_standard.py"
KST = timezone(timedelta(hours=9))

BASE_FILES = {
    "CEO/c1.txt": "c1\n",
    "CEO/c2.txt": "c2\n",
    "CEO/c3.txt": "c3\n",
    "src/a.txt": "a\n",
    "other/b.txt": "b\n",
    "Departments/Secretariat/assets/x.md": "x\n",
    "Departments/Quality/results/r.md": "r\n",
    "Departments/Secretariat/docs/requests/REQ-900_v01.md":
        '---\ntask_id: "900"\napproved: "2026-10-09T06:00:00+09:00"\nscope:\n  - src\n---\n\n# REQ-900: 시험\n',
}

CAUSE = "원인: CEO/ 변경은 그 밖의 변경과 따로 커밋해야 합니다"
ACTION = "조치: git restore --staged <경로>로 한쪽을 스테이징에서 빼고 나눠 커밋하십시오."
INFO = "[INFO] CEO/ 아래 변경은 작업 트리 검사에서 뺍니다(대표님 구역):"


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def git(repo, *args, check=True):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=repo,
                         capture_output=True, encoding="utf-8", errors="replace")
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패 (종료 코드 {res.returncode}): {res.stderr.strip()}")
    return res


def write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def make_repo(base, name, checker):
    repo = base / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "REQ-013 test")
    git(repo, "config", "user.email", "req-013-test@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    for rel, text in BASE_FILES.items():
        write(repo, rel, text)
    (repo / CHECKER_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(checker, repo / CHECKER_REL)
    (repo / ".githooks").mkdir()
    shutil.copyfile(HOOK, repo / ".githooks" / "pre-commit")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")  # 훅을 켜기 전의 첫 커밋
    git(repo, "config", "core.hooksPath", ".githooks")
    return repo


# ---- 변경 동작 ----
def add(*paths):
    return lambda r: [write(r, p, "new\n") for p in paths]


def mod(*paths):
    return lambda r: [write(r, p, "changed\n") for p in paths]


def delete(*paths):
    return lambda r: [(r / p).unlink() for p in paths]


def ren(*pairs):
    """작업 트리 이름 변경(스테이징 전). git status에는 삭제와 추가로 나타난다."""
    def act(r):
        for src, dst in pairs:
            (r / dst).parent.mkdir(parents=True, exist_ok=True)
            (r / src).rename(r / dst)
    return act


def gmv(*pairs):
    """git mv 이름 변경(스테이징된 상태). git status에 이름 변경으로 나타난다."""
    def act(r):
        for src, dst in pairs:
            (r / dst).parent.mkdir(parents=True, exist_ok=True)
            git(r, "mv", src, dst)
    return act


def stage_all(*acts):
    """변경을 만든 뒤 전부 스테이징한다(--staged·커밋 시험용)."""
    def act(r):
        for a in acts:
            a(r)
        git(r, "add", "-A")
    return act


def seq(*acts):
    def act(r):
        for a in acts:
            a(r)
    return act


# ---- 시험 실행 ----
def run_check(repo, staged):
    cmd = [sys.executable, str(repo / CHECKER_REL)] + (["--staged"] if staged else [])
    res = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    return res.returncode, (res.stdout + res.stderr).strip()


def run_commit(repo):
    res = git(repo, "commit", "-q", "-m", "test", check=False)
    return res.returncode, (res.stdout + res.stderr).strip()


def execute(base, label, checker, act, mode):
    repo = make_repo(base, label, checker)
    act(repo)
    status = git(repo, "status", "--porcelain", "-uall").stdout.strip()
    if mode == "commit":
        code, out = run_commit(repo)
    else:
        code, out = run_check(repo, mode == "staged")
    return code, out, status


# (번호, 설명, 모드, 동작, 적용본 기대 종료 코드, 대조 동작(CEO/ 변경을 뺀 같은 작업 트리) 또는 None, 출력 확인 문자열 목록)
C1 = ("CEO/c1.txt",)
CN = ("CEO/c1.txt", "CEO/c2.txt")
CASES = [
    ("T1-1", "작업 트리 CEO/ 추가 1개", "wt", add("CEO/n1.txt"), 0, None, [INFO]),
    ("T1-2", "작업 트리 CEO/ 추가 여러 개", "wt", add("CEO/n1.txt", "CEO/n2.txt", "CEO/sub/n3.txt"), 0, None, [INFO]),
    ("T1-3", "작업 트리 CEO/ 수정 1개", "wt", mod(*C1), 0, None, [INFO]),
    ("T1-4", "작업 트리 CEO/ 수정 여러 개", "wt", mod(*CN), 0, None, [INFO]),
    ("T1-5", "작업 트리 CEO/ 삭제 1개", "wt", delete(*C1), 0, None, [INFO]),
    ("T1-6", "작업 트리 CEO/ 삭제 여러 개", "wt", delete(*CN), 0, None, [INFO]),
    ("T1-7", "작업 트리 CEO/ 이름 변경 1개(CEO/→CEO/)", "wt", ren(("CEO/c1.txt", "CEO/r1.txt")), 0, None, [INFO]),
    ("T1-8", "작업 트리 CEO/ 이름 변경 여러 개(CEO/→CEO/)", "wt",
     ren(("CEO/c1.txt", "CEO/r1.txt"), ("CEO/c2.txt", "CEO/sub/r2.txt")), 0, None, [INFO]),
    ("T1-9", "작업 트리 CEO/ 이름 변경 1개(git mv, CEO/→CEO/)", "wt", gmv(("CEO/c1.txt", "CEO/r1.txt")), 0, None, [INFO]),
    ("T2-1", "작업 트리 CEO/ 추가 + scope 안 수정", "wt", seq(add("CEO/n1.txt"), mod("src/a.txt")), 0,
     mod("src/a.txt"), [INFO, "REQ-900_v01.md"]),
    ("T2-2", "작업 트리 CEO/ 수정·삭제 여러 개 + scope 안 추가", "wt",
     seq(mod("CEO/c1.txt"), delete("CEO/c2.txt"), add("src/n.txt")), 0, add("src/n.txt"), [INFO, "REQ-900_v01.md"]),
    ("T3-1", "작업 트리 CEO/ 추가 + scope 밖 수정", "wt", seq(add("CEO/n1.txt"), mod("other/b.txt")), 1,
     mod("other/b.txt"), ["other/b.txt"]),
    ("T3-2", "작업 트리 CEO/ 수정 여러 개 + scope 밖 추가", "wt",
     seq(mod(*CN), add("other/n.txt")), 1, add("other/n.txt"), ["other/n.txt"]),
    ("T4-1", "작업 트리 이름 변경 CEO/→scope 밖", "wt", ren(("CEO/c1.txt", "other/c1.txt")), 1,
     add("other/c1.txt"), ["other/c1.txt"]),
    ("T4-2", "작업 트리 이름 변경 scope 밖→CEO/", "wt", ren(("other/b.txt", "CEO/b.txt")), 1,
     delete("other/b.txt"), ["other/b.txt"]),
    ("T4-3", "작업 트리 이름 변경 CEO/→scope 안", "wt", ren(("CEO/c1.txt", "src/c1.txt")), 0,
     add("src/c1.txt"), ["REQ-900_v01.md"]),
    ("T4-4", "git mv 이름 변경 CEO/→scope 밖(작업 트리 검사)", "wt", gmv(("CEO/c1.txt", "other/c1.txt")), 1,
     add("other/c1.txt"), ["other/c1.txt"]),
    ("T4-5", "git mv 이름 변경 scope 밖→CEO/(작업 트리 검사)", "wt", gmv(("other/b.txt", "CEO/b.txt")), 1,
     delete("other/b.txt"), ["other/b.txt"]),
    ("T4-6", "git mv 이름 변경 CEO/→scope 안(작업 트리 검사)", "wt", gmv(("CEO/c1.txt", "src/c1.txt")), 0,
     add("src/c1.txt"), ["REQ-900_v01.md"]),
]

STAGED_CEO_ONLY = [
    ("1", "추가 1개", add("CEO/n1.txt")),
    ("2", "추가 여러 개", add("CEO/n1.txt", "CEO/n2.txt", "CEO/sub/n3.txt")),
    ("3", "수정 1개", mod(*C1)),
    ("4", "수정 여러 개", mod(*CN)),
    ("5", "삭제 1개", delete(*C1)),
    ("6", "삭제 여러 개", delete(*CN)),
    ("7", "이름 변경 1개(CEO/→CEO/)", gmv(("CEO/c1.txt", "CEO/r1.txt"))),
    ("8", "이름 변경 여러 개(CEO/→CEO/)", gmv(("CEO/c1.txt", "CEO/r1.txt"), ("CEO/c2.txt", "CEO/sub/r2.txt"))),
]
STAGED_MIXED = [
    ("T6-1", "CEO/ 추가 + scope 안 수정", seq(add("CEO/n1.txt"), mod("src/a.txt"))),
    ("T6-2", "CEO/ 수정 여러 개 + scope 안 추가", seq(mod(*CN), add("src/n.txt"))),
    ("T7-1", "CEO/ 추가 + Departments/Secretariat/assets/ 수정", seq(add("CEO/n1.txt"), mod("Departments/Secretariat/assets/x.md"))),
    ("T7-2", "CEO/ 삭제 + Departments/Quality/results/ 수정", seq(delete(*C1), mod("Departments/Quality/results/r.md"))),
    ("T8-1", "이름 변경 CEO/→scope 안", gmv(("CEO/c1.txt", "src/c1.txt"))),
    ("T8-2", "이름 변경 scope 안→CEO/", gmv(("src/a.txt", "CEO/a.txt"))),
    ("T8-3", "이름 변경 CEO/→대조 제외 구역", gmv(("CEO/c1.txt", "Departments/Quality/results/c1.txt"))),
]
MIXED_MARKS = ["[FAIL] CEO/ 아래 변경과 그 밖의 변경이 한 커밋에 섞여 있습니다.", CAUSE, ACTION]

for n, desc, act in STAGED_CEO_ONLY:
    CASES.append((f"T5-{n}", f"--staged CEO/만 {desc}", "staged", stage_all(act), 0, None,
                  ["[PASS] 커밋 대상이 모두 CEO/ 아래 변경입니다(대표님 구역). scope 대조를 생략합니다."]))
for num, desc, act in STAGED_MIXED:
    CASES.append((num, f"--staged {desc}", "staged", stage_all(act), 1, None, MIXED_MARKS))
for n, desc, act in STAGED_CEO_ONLY:
    CASES.append((f"T9-{n}", f"훅 커밋 CEO/만 {desc}", "commit", stage_all(act), 0, None, []))
for num, desc, act in STAGED_MIXED:
    CASES.append((f"T10-{num[1:]}", f"훅 커밋 {desc}", "commit", stage_all(act), 1, None, MIXED_MARKS + ["[BLOCKED]"]))


def main():
    for src in (ORIGINAL, APPLIED, HOOK):
        if not src.exists():
            print(f"[FAIL] 시험 입력 파일이 없습니다: {src}")
            return 1
    print(f"[START] {now()}")
    print(f"원본: {ORIGINAL.relative_to(ROOT).as_posix()}")
    print(f"적용본: {APPLIED.relative_to(ROOT).as_posix()}")
    rows, ok_all = [], True
    with tempfile.TemporaryDirectory(prefix="req013_", ignore_cleanup_errors=True) as tmp:
        base = Path(tmp)
        for i, (num, desc, mode, act, expected, control, marks) in enumerate(CASES):
            print(f"\n=== {num} {desc} (모드 {mode}, 기대 {expected}) {now()} ===")
            o_code, o_out, status = execute(base, f"{i}_orig", ORIGINAL, act, mode)
            a_code, a_out, _ = execute(base, f"{i}_appl", APPLIED, act, mode)
            print("git status --porcelain -uall:")
            print(status)
            print(f"--- 원본 종료 코드 {o_code} ---\n{o_out}")
            print(f"--- 적용본 종료 코드 {a_code} ---\n{a_out}")
            ok = a_code == expected
            missing = [m for m in marks if m not in a_out]
            if missing:
                ok = False
                print(f"[MISMATCH] 적용본 출력에 없는 문자열: {missing}")
            ctrl = "-"
            if control is not None:
                c_code, c_out, c_status = execute(base, f"{i}_ctrl", APPLIED, control, mode)
                co_code, _, _ = execute(base, f"{i}_ctrlo", ORIGINAL, control, mode)
                print(f"--- 대조(CEO/ 변경 제외) git status ---\n{c_status}")
                print(f"--- 대조 적용본 종료 코드 {c_code}, 원본 종료 코드 {co_code} ---\n{c_out}")
                ctrl = f"{c_code}/{co_code}"
                if c_code != a_code or co_code != c_code:
                    ok = False
                    print("[MISMATCH] 대조 결과가 다릅니다.")
            # Red 확인: 원본은 CEO/ 변경만 있는 작업 트리·스테이징·커밋에서 실패해야 한다
            red = "-"
            if num.startswith(("T1-", "T5-", "T9-")):
                red = "성립" if o_code != 0 else "불성립"
                if o_code == 0:
                    ok = False
            ok_all &= ok
            rows.append((num, desc, expected, o_code, a_code, ctrl, red, "PASS" if ok else "FAIL"))
    print("\n== 요약 (번호 | 설명 | 기대 | 원본 | 적용본 | 대조 적용본/원본 | Red | 결과) ==")
    for r in rows:
        print(" | ".join(str(c) for c in r))
    print(f"[END] {now()}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
