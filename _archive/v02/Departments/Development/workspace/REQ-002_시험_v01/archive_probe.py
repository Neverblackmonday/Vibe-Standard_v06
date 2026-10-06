#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REQ-002 적용본 반영 상태의 check_standard.py 실행과 git archive 목록 확인 (EC 5절 3번·7번).

1. 저장소를 저장소 밖 임시 폴더에 복제하고, 현재 작업 트리(.git 제외)를 덮어써 변경 상태를 재현한다.
2. 설계·개발 적용본 폴더(Departments/*/workspace/REQ-002_적용본_v01/)를 원본 위치에 반영한다.
   경로 구성 요소 끝의 `.적용본`은 반영할 때 뗀다(Workflow/06 「거버넌스 파일 개정 절차」).
3. 반영된 check_standard.py를 실행한다(그대로, 그리고 커밋하지 않은 `Claude outputs/` 파일을 뺀 상태로).
4. 임시 저장소에서 git add·commit 뒤 `git archive HEAD | tar -t` 목록으로 EC 5절 3번 ①~④를 확인한다.
원본 저장소에는 아무것도 쓰거나 커밋하지 않는다.

사용법: python Departments/Development/workspace/REQ-002_시험_v01/archive_probe.py
종료 코드: archive 목록 ①~④가 모두 기대대로이고 `Claude outputs/` 제외 상태의 검사 종료 코드가 0이면 0, 아니면 1.
"""

import datetime
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
APPLIED_DIRS = [
    REPO / "Departments/Design/workspace/REQ-002_적용본_v01",
    REPO / "Departments/Development/workspace/REQ-002_적용본_v01",
]
SUFFIX = ".적용본"
SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(cmd, cwd, check=True, **kw):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, **kw)
    if check and res.returncode != 0:
        err = res.stderr if isinstance(res.stderr, str) else res.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"{' '.join(cmd)} 실패 ({res.returncode}): {err.strip()}")
    return res


def strip_suffix(rel):
    return Path(*[p[: -len(SUFFIX)] if p.endswith(SUFFIX) else p for p in rel.parts])


def apply_copies(work):
    applied = []
    for base in APPLIED_DIRS:
        for src in sorted(base.rglob("*")):
            if src.is_file():
                rel = strip_suffix(src.relative_to(base))
                dst = work / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                applied.append(rel.as_posix())
    return applied


def run_check(work, label):
    res = subprocess.run([sys.executable, str(work / SCRIPT_REL)], cwd=work, capture_output=True,
                         encoding="utf-8", errors="replace", env=ENV)
    print(f"\n=== check_standard.py ({label}) | 종료 코드 {res.returncode}")
    print((res.stdout + res.stderr).strip())
    return res.returncode


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")
    print(f"시각: {now}")
    head = run(["git", "rev-parse", "HEAD"], REPO, encoding="utf-8").stdout.strip()
    print(f"원본 저장소 HEAD: {head}")

    # 정리 실패는 OS 임시 폴더의 잔여물일 뿐 시험 결과와 무관하므로 무시한다
    with tempfile.TemporaryDirectory(prefix="req002_archive_", ignore_cleanup_errors=True) as tmp:
        work = Path(tmp) / "repo"
        run(["git", "clone", "-q", "--no-hardlinks", str(REPO), str(work)], tmp)
        run(["git", "config", "core.quotepath", "false"], work)
        run(["git", "config", "user.name", "archive-probe"], work)
        run(["git", "config", "user.email", "archive-probe@example.invalid"], work)
        # 작업 트리 전체를 복사하면 core.autocrlf=true 환경에서 줄 끝만 다른 파일이 변경으로 잡히므로
        # 원본 저장소 git status가 보고한 경로만 복사해 변경 상태를 그대로 재현한다
        raw = run(["git", "status", "--porcelain", "-uall", "-z"], REPO).stdout.decode("utf-8")
        entries = [e for e in raw.split("\0") if e]
        deleted = [e for e in entries if "D" in e[:2]]
        if deleted:
            raise RuntimeError(f"삭제 항목은 재현하지 않으므로 시험을 중단합니다: {deleted}")
        for e in entries:
            rel = e[3:]
            dst = work / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / rel, dst)
        repro = run(["git", "status", "--porcelain", "-uall"], work, encoding="utf-8").stdout.splitlines()
        print(f"원본 저장소 변경 {len(entries)}건 복사, 임시 저장소 변경 {len(repro)}건")

        applied = apply_copies(work)
        print(f"\n적용본 반영 {len(applied)}건:")
        for rel in applied:
            print(f"  - {rel}")

        rc_raw = run_check(work, "적용본 반영 상태 그대로")
        outputs = [l[3:] for l in run(["git", "status", "--porcelain", "-uall"], work, encoding="utf-8").stdout.splitlines()
                   if l.startswith("??") and l[3:].strip('"').startswith("Claude outputs/")]
        for rel in outputs:
            (work / rel.strip('"')).unlink()
        print(f"\n커밋하지 않은 Claude outputs/ 파일 {len(outputs)}건을 임시 저장소에서만 제거: {outputs}")
        rc_clean = run_check(work, "Claude outputs/ 미커밋 파일 제외")

        run(["git", "add", "-A"], work)
        # 임시 저장소 전용 커밋. 원본 저장소의 커밋 전 검사 훅이 개입하지 않도록 훅을 건너뛴다
        run(["git", "commit", "-q", "--no-verify", "-m", "archive probe"], work)
        archive = run(["git", "archive", "--format=tar", "HEAD"], work).stdout
        # GNU tar는 출력할 수 없다고 보는 바이트(예: UTF-8 한국어의 0x80)를 8진수로 이스케이프하므로 원형 그대로 받는다
        # Windows의 프로세스 검색은 System32의 bsdtar를 먼저 찾으므로 EC가 지정한 Git Bash GNU tar를 경로로 지정한다
        exec_path = run(["git", "--exec-path"], work, encoding="utf-8").stdout.strip()
        gnu_tar = Path(exec_path).parents[2] / "usr" / "bin" / "tar.exe"
        if not gnu_tar.exists():
            raise RuntimeError(f"Git Bash GNU tar를 찾을 수 없습니다: {gnu_tar}")
        print(f"\n목록 확인 tar: {gnu_tar}")
        listing_raw = run([str(gnu_tar), "--quoting-style=literal", "-tf", "-"], work, input=archive).stdout
        try:
            listing = listing_raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            print(f"[DEBUG] tar 목록 UTF-8 해석 실패 위치 {exc.start}: {listing_raw[max(0, exc.start - 80):exc.end + 40]!r}")
            raise
        files = [l for l in listing.splitlines() if l and not l.endswith("/")]
        print(f"\ngit archive HEAD 파일 항목 {len(files)}건:")
        for f in files:
            print(f"  {f}")

        c1 = [f for f in files if f.startswith(("_archive/", "Claude outputs/"))]
        prefixes = ("REQ-0", "EC-0", "DEV-0", "RES-0", "RES_DEV-0", "HOTFIX-0")
        c2 = [f for f in files if f.rsplit("/", 1)[-1].startswith(prefixes)]
        ws = [f for f in files if f.startswith("Departments/") and f.split("/")[2:3] == ["workspace"]]
        inbox = [f for f in files if f.startswith("Departments/Secretariat/assets/inbox/")]
        c3_ok = (all(f.endswith("/workspace/.gitkeep") for f in ws) and len(ws) == 7
                 and inbox == ["Departments/Secretariat/assets/inbox/.gitkeep"])
        design_docs = sorted(f for f in files if f.startswith("Departments/Design/docs/"))
        expected_docs = sorted([
            "Departments/Design/docs/prd/.gitkeep", "Departments/Design/docs/prd/PRD_TEMPLATE.md",
            "Departments/Design/docs/tad/.gitkeep", "Departments/Design/docs/tad/EC_TEMPLATE.md",
            "Departments/Design/docs/tad/TAD_TEMPLATE.md",
        ])
        print(f"\n① _archive/·Claude outputs/ 아래 파일: {len(c1)}건 {c1}")
        print(f"② REQ-0·EC-0·DEV-0·RES-0·RES_DEV-0·HOTFIX-0 시작 파일: {len(c2)}건 {c2}")
        print(f"③ workspace/ 파일 {len(ws)}건 {ws}, inbox/ 파일 {len(inbox)}건 {inbox}, 기대 충족 {c3_ok}")
        print(f"④ Departments/Design/docs/ 파일 {design_docs}, 기대 충족 {design_docs == expected_docs}")

        ok = not c1 and not c2 and c3_ok and design_docs == expected_docs and rc_clean == 0
        print(f"\n검사 종료 코드: 그대로 {rc_raw}, Claude outputs/ 제외 {rc_clean}")
        print(f"전체 결과: {'기대대로' if ok else '기대와 다름'}")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
