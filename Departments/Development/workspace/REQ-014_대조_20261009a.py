#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-014_대조_20261009a.py - REQ-014 적용본 규칙과 check_standard.py·.gitattributes 동작 대조 (일회성)

EC-014_v02 3.4절 1번 가운데 동작 확인이 필요한 항목을 실행으로 확인한다.
  C1 (①②④) is_whitelisted(): 새 비서실 경로(planning/, briefings/*.html, workspace/실행기록_REQ-*.md)는
             대조 제외, 새 서식(Workflow/templates/*)은 대조 대상
  C2 (④)    item_covers(): REQ-014 scope의 Workflow/templates가 새 서식 네 개를 덮는다
  C3 (②)    load_latest(): REQ-*.md와 실행기록_REQ-*.md가 한 폴더에 있어도 실행 기록을 REQ로 읽지 않는다
  C4 (④)    git check-attr export-ignore: planning/·briefings/·실행 기록은 배포본 제외, 새 서식은 배포본 포함
  C5 (⑤)    임시 저장소에서 ORDER 여러 버전(related_req가 빈 버전 포함)·실행 기록·적용본·결과서·scope 변경을
             함께 스테이징한 뒤 check_standard.py --staged가 종료 코드 0
  C6 (⑤ 대조군) C5에 scope 밖 거버넌스 파일(Workflow/06)을 더하면 종료 코드 1
  C7 (⑤ 대조군) C5에서 REQ approved를 비우면 종료 코드 1

C1~C3은 이 저장소의 check_standard.py를 모듈로 읽어 함수만 호출한다. C4는 이 저장소에서
읽기 전용 명령(git check-attr)만 실행한다. C5~C7은 저장소 밖 임시 폴더에 새 Git 저장소를 만들므로
이 저장소의 기록과 작업 트리는 바뀌지 않는다.

사용법: python Departments/Development/workspace/REQ-014_대조_20261009a.py
종료 코드: 0 모든 항목이 기대와 같음, 1 하나 이상 다름
"""

import importlib.util
import io
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Windows 콘솔에서 한국어 출력이 깨지지 않도록 출력 인코딩을 UTF-8로 고정한다
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[3]
CHECKER_REL = "Departments/Development/assets/scripts/check_standard.py"
CHECKER = ROOT / CHECKER_REL
REQ_REL = "Departments/Secretariat/docs/requests/REQ-014_v01.md"
KST = timezone(timedelta(hours=9))

# 새 비서실 경로(07 적용본 1절 문서 체계의 이름 규칙으로 만든 예시 이름)
PLANNING = [
    "Departments/Secretariat/assets/planning/백로그_20261009_시험_v01.md",
    "Departments/Secretariat/assets/planning/기획안_20261009_시험_v01.md",
]
BRIEFING = "Departments/Secretariat/assets/briefings/브리핑_20261009_시험_v01.html"
RUNLOG = "Departments/Secretariat/workspace/실행기록_REQ-014.md"
RUNLOG_DERIVED = "Departments/Secretariat/workspace/실행기록_REQ-014-1.md"
NEW_TEMPLATES = [
    "Workflow/templates/BACKLOG_TEMPLATE.md",
    "Workflow/templates/PLAN_TEMPLATE.md",
    "Workflow/templates/BRIEFING_TEMPLATE.html",
    "Workflow/templates/PM_DIRECTIVE_TEMPLATE.md",
]

results = []


def now():
    return datetime.now(KST).isoformat(timespec="seconds")


def record(name, expected, actual, detail=""):
    ok = expected == actual
    results.append(ok)
    print(f"[{'OK' if ok else 'NG'}] {name}: 기대 {expected!r}, 결과 {actual!r}{(' / ' + detail) if detail else ''}")


def load_checker():
    spec = importlib.util.spec_from_file_location("check_standard_under_test", CHECKER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def c1_c2_c3(cs):
    print("== C1 is_whitelisted() ==")
    for p in PLANNING + [BRIEFING, RUNLOG, RUNLOG_DERIVED]:
        record(f"C1 대조 제외 {p}", True, cs.is_whitelisted(p))
    for p in NEW_TEMPLATES:
        record(f"C1 대조 대상 {p}", False, cs.is_whitelisted(p))

    print("== C2 item_covers() (REQ-014 scope 항목 Workflow/templates) ==")
    for p in NEW_TEMPLATES:
        record(f"C2 {p}", True, cs.item_covers("Workflow/templates", p))

    print("== C3 load_latest() ==")
    with tempfile.TemporaryDirectory(prefix="req014_c3_") as tmp:
        folder = Path(tmp)
        (folder / "REQ-014_v01.md").write_text("x\n", encoding="utf-8")
        (folder / Path(RUNLOG).name).write_text("x\n", encoding="utf-8")
        (folder / Path(RUNLOG_DERIVED).name).write_text("x\n", encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            got = [f.name for f in cs.load_latest(folder, "REQ")]
        record("C3 REQ로 읽은 파일", ["REQ-014_v01.md"], got)
        record("C3 실행 기록 관련 [INFO] 출력", False, "실행기록" in buf.getvalue(), buf.getvalue().strip() or "출력 없음")


def c4():
    print("== C4 git check-attr export-ignore (이 저장소, 읽기 전용) ==")
    paths = PLANNING + [BRIEFING, RUNLOG] + NEW_TEMPLATES
    res = git(ROOT, "check-attr", "export-ignore", "--", *paths)
    attrs = {}
    for line in res.stdout.strip().splitlines():
        path, _, value = line.rsplit(": ", 2)
        attrs[path] = value
    for p in PLANNING + [BRIEFING, RUNLOG]:
        record(f"C4 배포본 제외 {p}", "set", attrs.get(p))
    for p in NEW_TEMPLATES:
        record(f"C4 배포본 포함 {p}", "unspecified", attrs.get(p))


def make_repo(base, name, req_text):
    repo = base / name
    repo.mkdir()
    hooks = base / f"{name}_nohooks"
    hooks.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "REQ-014 test")
    git(repo, "config", "user.email", "req-014-test@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    # 사용자 전역 훅이 첫 커밋에 끼어들지 않게 빈 훅 폴더를 쓴다
    git(repo, "config", "core.hooksPath", str(hooks))
    (repo / CHECKER_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(CHECKER, repo / CHECKER_REL)
    write(repo, REQ_REL, req_text)
    write(repo, "AGENTS.md", "base\n")
    write(repo, "Workflow/03_라이프사이클.md", "base\n")
    write(repo, "Workflow/06_통제장치_및_배포.md", "base\n")
    write(repo, "Departments/Secretariat/assets/inbox/ORD-003_v01.md", '---\nrelated_req: []\n---\n')
    write(repo, "Departments/Secretariat/assets/inbox/ORD-003_v02.md", '---\nrelated_req: []\n---\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo


def stage_case(repo, extra=()):
    """REQ-014 최종 판정서 승인 뒤 커밋의 스테이징 대상(05 적용본 1.1절 6항 ①~⑦)을 흉내 낸다."""
    changes = {
        # ① 안건 기록 (EC는 scope 안, 결과서·판정서는 부서 results/)
        "Departments/Design/docs/tad/EC-014_v01.md": "ec1\n",
        "Departments/Design/docs/tad/EC-014_v02.md": "ec2\n",
        "Departments/Design/results/RPT-014_v01.md": "rpt\n",
        "Departments/Development/results/DEV-014_v01.md": "dev\n",
        "Departments/Quality/results/RES-014_v01.md": "res\n",
        # ② 승인 기록
        "Departments/Secretariat/assets/inbox/승인기록_20261009_REQ-014_v01.md": "approval\n",
        # ③ ORDER의 모든 버전: v03은 related_req 비어 있음, v04만 기재
        "Departments/Secretariat/assets/inbox/ORD-003_v03.md": '---\nrelated_req: []\n---\n',
        "Departments/Secretariat/assets/inbox/ORD-003_v04.md": '---\nrelated_req: ["REQ-014_v01"]\n---\n',
        # ④ 적용본 폴더
        "Departments/Design/workspace/REQ-014_적용본_v01/AGENTS.md.적용본": "applied\n",
        # ⑤ 결과서에 적힌 workspace 스크립트
        "Departments/Design/workspace/REQ-014_복사_20261009a.py": "# script\n",
        # ⑥ scope 안 원본 반영 (기존 파일 수정, 새 서식 생성)
        "AGENTS.md": "applied\n",
        "Workflow/03_라이프사이클.md": "applied\n",
        # ⑦ PM 실행 기록
        RUNLOG: '---\ntask_id: "014"\ncreated: "2026-10-09"\n---\n',
        # 새 비서실 경로(브리핑·기획 자료)도 함께 섞는다
        BRIEFING: "<!doctype html>\n",
        PLANNING[0]: "backlog\n",
    }
    for p in NEW_TEMPLATES:
        changes[p] = "template\n"
    for p in extra:
        changes[p] = "extra\n"
    for rel, text in changes.items():
        write(repo, rel, text)
    git(repo, "add", "-A")
    staged = git(repo, "diff", "--cached", "--name-only", "-z").stdout.split("\0")
    return [s for s in staged if s]


def run_checker(repo):
    res = subprocess.run([sys.executable, str(repo / CHECKER_REL), "--staged"], cwd=repo,
                         capture_output=True, encoding="utf-8", errors="replace")
    return res.returncode, (res.stdout + res.stderr).strip()


def c5_c6_c7():
    req_text = (ROOT / REQ_REL).read_text(encoding="utf-8")
    req_unapproved = "\n".join(
        'approved: ""' if line.startswith("approved:") else line for line in req_text.splitlines()) + "\n"
    with tempfile.TemporaryDirectory(prefix="req014_staged_") as tmp:
        base = Path(tmp)
        cases = [
            ("C5 ORDER 여러 버전·실행 기록 포함 스테이징", req_text, (), 0),
            ("C6 대조군: scope 밖 Workflow/06 추가", req_text, ("Workflow/06_통제장치_및_배포.md",), 1),
            ("C7 대조군: REQ approved 비움", req_unapproved, (), 1),
        ]
        for i, (name, text, extra, expected) in enumerate(cases):
            print(f"== {name} ==")
            repo = make_repo(base, f"case{i}", text)
            staged = stage_case(repo, extra)
            print(f"스테이징 {len(staged)}건:")
            for s in staged:
                print(f"  - {s}")
            code, out = run_checker(repo)
            print("check_standard.py --staged 출력:")
            print("\n".join("  | " + line for line in out.splitlines()))
            record(f"{name} 종료 코드", expected, code)


def main():
    print(f"시작 {now()} / 대상 검사기 {CHECKER_REL}")
    cs = load_checker()
    c1_c2_c3(cs)
    c4()
    c5_c6_c7()
    passed = sum(results)
    print(f"종료 {now()} / 기대와 같음 {passed}건, 다름 {len(results) - passed}건")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
