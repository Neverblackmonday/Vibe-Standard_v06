#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-007_test_gitignore_20261008a.py - REQ-007 .gitignore 적용본 규칙과 비우기 명령 시험 (일회성)

EC-007_v02 3.4절 3번의 시험을 임시 Git 저장소에서 실행한다. 이 저장소는 건드리지 않는다.
  확인 ①: git status --porcelain -uall 에 두 폴더 바로 아래 .gitkeep 두 파일만 나타난다
  확인 ②: 두 .gitkeep 커밋 뒤 git clean -ndX 삭제 예정 목록에 두 .gitkeep이 없고 나머지가 있다.
          이어서 git clean -fdX 를 실제로 실행해 두 .gitkeep만 남는지 확인한다
  확인 ③: .gitattributes 적용본을 둔 상태에서 git archive HEAD 에 두 .gitkeep이 들어간다
  대조군: 원본 .gitignore(두 폴더 규칙 없음)로 확인 ①을 실행하면 실패해야 한다.
          시험이 규칙 유무를 실제로 구분하는지 보이기 위한 것이다(Red 확인)

준비물에는 풀어 놓은 배포본을 흉내 낸 하위 .gitignore 사본(Package_sample/.gitignore)과
그 사본의 예외 규칙이 가리키는 Package_sample/Package_sample/.gitkeep 도 넣는다
(RPT-007_v01 5절 「풀어 놓은 배포본 안의 .gitignore 사본」).

20261007a와의 차이: 확인 ③에서 tarfile.getnames()가 폴더 항목을 끝 / 없이 돌려주어
폴더 항목(Package_sample, Package_update)이 파일 목록에 섞여 FAIL로 오판했다.
파일 항목(TarInfo.isfile())만 골라 비교하도록 고쳤다. 나머지는 같다.

사용법: python Departments/Development/workspace/REQ-007_test_gitignore_20261008a.py
종료 코드: 0 모든 확인 통과, 1 하나 이상 실패
"""

import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[3]
APPLY_DIR = ROOT / "Departments" / "Development" / "workspace" / "REQ-007_적용본_v01"
APPLY_GITIGNORE = APPLY_DIR / ".gitignore.적용본"
APPLY_GITATTRIBUTES = APPLY_DIR / ".gitattributes.적용본"
ORIGINAL_GITIGNORE = ROOT / ".gitignore"

KST = timezone(timedelta(hours=9))
KEEP = ["Package_sample/.gitkeep", "Package_update/.gitkeep"]
# 무시되어야 하는 파일: 하위 폴더 .gitkeep, 일반 파일, 풀어 놓은 배포본의 하위 .gitignore 사본
IGNORED = [
    "Package_sample/Audits/.gitkeep",
    "Package_sample/AGENTS.md",
    "Package_sample/.gitignore",
    "Package_sample/Package_sample/.gitkeep",
    "Package_update/Workflow/.gitkeep",
    "Package_update/.claude/settings.json",
]


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def git(repo, *args, check=True):
    # -c core.quotepath=false: 경로를 따옴표·8진 이스케이프 없이 받아 기대값과 그대로 비교한다
    cmd = ["git", "-c", "core.quotepath=false", *args]
    res = subprocess.run(cmd, cwd=repo, capture_output=True, encoding="utf-8", errors="replace")
    print(f"$ {' '.join(args)}  [{now()}] (종료 코드 {res.returncode})")
    out = res.stdout.rstrip("\n")
    if out:
        print(out)
    if res.stderr.strip():
        print(f"[stderr] {res.stderr.strip()}")
    if check and res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패(종료 코드 {res.returncode}): {res.stderr.strip()}")
    return res.stdout


def make_repo(base, name, gitignore_src):
    repo = base / name
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "REQ-007 test")
    git(repo, "config", "user.email", "req-007-test@example.invalid")
    shutil.copyfile(gitignore_src, repo / ".gitignore")
    for rel in KEEP:
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_bytes(b"")
    for rel in IGNORED:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("/.gitignore"):
            # 배포본을 풀면 루트 .gitignore 사본이 Package_sample/ 아래에 생기는 상황을 재현한다
            shutil.copyfile(gitignore_src, p)
        else:
            p.write_text("dummy\n", encoding="utf-8")
    return repo


def status_paths(repo):
    out = git(repo, "status", "--porcelain", "-uall")
    return sorted(line[3:] for line in out.splitlines() if line)


def check1(repo):
    pkg = [p for p in status_paths(repo) if p.startswith("Package_")]
    ok = pkg == sorted(KEEP)
    print(f"[{'PASS' if ok else 'FAIL'}] 확인 ①: Package_ 경로 = {pkg} (기대값 {sorted(KEEP)})")
    return ok


def check2(repo):
    git(repo, "add", "--", ".gitignore", *KEEP)
    git(repo, "commit", "-q", "-m", "keep")
    preview = git(repo, "clean", "-ndX", "--", "Package_sample/", "Package_update/")
    prefix = "Would remove "
    listed = [l[len(prefix):].strip() if l.startswith(prefix) else l.strip()
              for l in preview.splitlines() if l]
    keep_absent = not any(k in listed for k in KEEP)
    # 무시된 하위 폴더는 폴더 단위(끝에 /)로 나오므로 경로 또는 그 상위 폴더가 목록에 있으면 포함으로 본다
    def listed_or_parent(rel):
        parts = rel.split("/")
        cands = {"/".join(parts[:i]) + "/" for i in range(2, len(parts))} | {rel}
        return any(c in listed for c in cands)
    rest_present = all(listed_or_parent(r) for r in IGNORED)
    ok_preview = keep_absent and rest_present
    print(f"[{'PASS' if ok_preview else 'FAIL'}] 확인 ②-미리보기: .gitkeep 미포함={keep_absent}, 나머지 포함={rest_present}")

    git(repo, "clean", "-fdX", "--", "Package_sample/", "Package_update/")
    remaining = sorted(
        p.relative_to(repo).as_posix()
        for d in ("Package_sample", "Package_update")
        for p in (repo / d).rglob("*") if p.is_file()
    )
    ok_run = remaining == sorted(KEEP)
    print(f"[{'PASS' if ok_run else 'FAIL'}] 확인 ②-실행: 남은 파일 = {remaining} (기대값 {sorted(KEEP)})")
    clean_status = [p for p in status_paths(repo) if p.startswith("Package_")]
    ok_status = clean_status == []
    print(f"[{'PASS' if ok_status else 'FAIL'}] 확인 ②-실행 뒤 상태: Package_ 변경 = {clean_status} (기대값 [])")
    return ok_preview and ok_run and ok_status


def check3(repo):
    shutil.copyfile(APPLY_GITATTRIBUTES, repo / ".gitattributes")
    git(repo, "add", "--", ".gitattributes")
    git(repo, "commit", "-q", "-m", "attributes")
    res = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=repo, capture_output=True)
    print(f"$ archive --format=tar HEAD  [{now()}] (종료 코드 {res.returncode})")
    if res.returncode != 0:
        print(f"[FAIL] 확인 ③: git archive 실패: {res.stderr.decode('utf-8', 'replace').strip()}")
        return False
    members = tarfile.open(fileobj=io.BytesIO(res.stdout)).getmembers()
    print(f"archive 목록: {sorted(m.name + ('/' if m.isdir() else '') for m in members)}")
    # getnames()는 폴더 항목을 끝 / 없이 돌려주므로 이름 문자열로는 폴더와 파일을 구분할 수 없다
    pkg = sorted(m.name for m in members if m.isfile() and m.name.startswith("Package_"))
    ok = pkg == sorted(KEEP)
    print(f"[{'PASS' if ok else 'FAIL'}] 확인 ③: archive의 Package_ 파일 = {pkg} (기대값 {sorted(KEEP)})")
    return ok


def main():
    for src in (APPLY_GITIGNORE, APPLY_GITATTRIBUTES, ORIGINAL_GITIGNORE):
        if not src.exists():
            print(f"[FAIL] 시험 입력 파일이 없습니다: {src.relative_to(ROOT).as_posix()}")
            return 1
    print(f"[START] {now()}")
    results = {}
    with tempfile.TemporaryDirectory(prefix="req007_") as tmp:
        base = Path(tmp)
        print("== 적용본 .gitignore ==")
        repo = make_repo(base, "apply", APPLY_GITIGNORE)
        results["확인 ①"] = check1(repo)
        results["확인 ②"] = check2(repo)
        results["확인 ③"] = check3(repo)

        print("== 대조군: 원본 .gitignore (확인 ①이 FAIL이어야 정상) ==")
        control = make_repo(base, "control", ORIGINAL_GITIGNORE)
        results["대조군(확인 ① 실패 기대)"] = not check1(control)

    print("== 요약 ==")
    for name, ok in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[END] {now()}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
