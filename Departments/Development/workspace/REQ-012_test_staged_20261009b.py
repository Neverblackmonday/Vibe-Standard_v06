#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
REQ-012_test_staged_20261009b.py - 적용본 v02의 05 1.1절 6번(스테이징 범위)과 check_standard.py 동작 대조 시험 (일회성)

EC-012_v03 3.4절 1번 ④를 적용본 v02 기준으로 다시 확인한다. 이 저장소는 건드리지 않는다.
REQ-012_test_staged_20261009a.py(S1~S6)의 보조 함수를 불러 쓰고, 저장소 밖 임시 Git 저장소에서 실행한다.
  S7: 안건 001의 변경을 05 1.1절 6번 ①~⑥으로 분류해 스테이징(최종 판정서 자신, 승인 기록 두 건,
      related_req ORDER, 적용본 폴더, workspace 검증 스크립트, 반영 원본, 정리로 지운 경로 포함)하고
      다른 안건의 변경은 작업 트리에 둔다. 분류 결과가 기대 목록과 같고, --staged 종료 코드 0,
      pre-commit 훅을 켠 git commit 성공, 커밋 뒤 작업 트리에 다른 안건 변경만 남는다
  S8: S7에 다른 안건의 EC(scope 밖)까지 스테이징. --staged 종료 코드 1
  S9: S7에 다른 안건의 대조 제외 구역 파일(ORDER, Audits, research)까지 스테이징. --staged 종료 코드 0
      (검사기가 막지 않는다는 사실 확인. 이 경우의 통제는 6번 분류 절차뿐이다)

사용법: python Departments/Development/workspace/REQ-012_test_staged_20261009b.py
종료 코드: 0 모든 사례가 기대 결과와 같음, 1 하나 이상 다름
"""

import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("req012_a", HERE / "REQ-012_test_staged_20261009a.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

NUM = "001"
APPROVED = A.APPROVED
REQ = f"{A.REQ_DIR}/REQ-{NUM}_v01.md"
SCOPE = [f"Departments/Design/docs/tad/EC-{NUM}", "AGENTS.md", "Workflow/03_라이프사이클.md",
         "Workflow/templates/OLD_TEMPLATE.md"]

# 안건 001의 파일(05 1.1절 6번 번호별)
AGENDA = {
    "①": [REQ,
          f"Departments/Design/docs/tad/EC-{NUM}_v01.md",
          f"Departments/Design/results/RPT-{NUM}_v01.md",
          f"Departments/Development/results/DEV-{NUM}_v01.md",
          f"Departments/Quality/results/RES-{NUM}-REQ_v01.md",
          f"Departments/Quality/results/RES-{NUM}-EC_v01.md",
          f"Departments/Quality/results/RES-{NUM}_v01.md"],  # 승인을 받은 최종 판정서 자신
    "②": [f"Departments/Secretariat/assets/inbox/승인기록_20261009_REQ-{NUM}_v01.md",
          f"Departments/Secretariat/assets/inbox/승인기록_20261009_RES-{NUM}_v01.md"],
    "③": ["Departments/Secretariat/assets/inbox/ORD-101_v01.md"],
    "④": [f"Departments/Design/workspace/REQ-{NUM}_적용본_v01/AGENTS.md.적용본",
          f"Departments/Design/workspace/REQ-{NUM}_적용본_v01/Workflow.적용본/03_라이프사이클.md"],
    "⑤": ["Departments/Design/workspace/REQ001_check_20261009a.py",
          "Departments/Development/workspace/REQ-001_test_20261009a.py"],
}
REFLECTED = ["AGENTS.md", "Workflow/03_라이프사이클.md"]  # ⑥ 반영 명령으로 바뀐 원본
DELETED = ["Workflow/templates/OLD_TEMPLATE.md",  # ⑥ 정리로 지운 경로(scope 안)
           "Departments/Design/workspace/REQ001_old_20261001a.py"]  # ⑥ 정리로 지운 경로(workspace)
# 결과서 「변경 파일」·판정서 「검증 기록」 명령 열에 적힌 workspace 파일(⑤의 입력)
LISTED = AGENDA["⑤"]

# 다른 안건의 변경(스테이징하지 않음)
OTHER_EC = "Departments/Design/docs/tad/EC-002_v01.md"
OTHER_WHITELISTED = ["Departments/Secretariat/assets/inbox/ORD-102_v01.md",
                     "Audits/AUDIT_20261008_시험_v01.md",
                     "Departments/Secretariat/assets/research/조사_20261008_시험_v01.md"]
OTHER_MODIFIED = "Workflow/04_모델_운용.md"
ORDER_NO_REQ = "Departments/Secretariat/assets/inbox/ORD-100_v01.md"  # related_req 기재 전 버전


def order_text(order_id, reqs):
    lines = "".join(f"  - {r}\n" for r in reqs)
    return f'---\norder_id: "{order_id}"\nrelated_req:\n{lines}---\n\n# ORD-{order_id}: 시험\n'


def make_repo(base):
    repo = base / "repo_b"
    repo.mkdir()
    A.git(repo, "init", "-q")
    A.git(repo, "config", "user.name", "REQ-012 test")
    A.git(repo, "config", "user.email", "req-012-test@example.invalid")
    A.git(repo, "config", "core.autocrlf", "false")
    (repo / A.CHECKER_REL).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(A.CHECKER, repo / A.CHECKER_REL)
    (repo / ".githooks").mkdir()
    shutil.copyfile(A.HOOK, repo / ".githooks" / "pre-commit")
    for rel in REFLECTED + [OTHER_MODIFIED] + DELETED:
        A.write(repo, rel, "# 시험용 원본\n")
    A.write(repo, f"{A.REQ_DIR}/.gitkeep", "")
    A.git(repo, "add", "-A")
    A.git(repo, "commit", "-q", "-m", "init")  # 훅을 켜기 전의 첫 커밋
    A.git(repo, "config", "core.hooksPath", ".githooks")
    return repo


def setup(repo):
    A.write(repo, REQ, A.req_text(f'approved: "{APPROVED}"', SCOPE))
    for group in ("①", "②", "④", "⑤"):
        for rel in AGENDA[group]:
            if rel != REQ:
                A.write(repo, rel, "# 시험\n")
    A.write(repo, AGENDA["③"][0], order_text("101", [f"REQ-{NUM}"]))
    for rel in REFLECTED:
        A.append(repo, rel, "적용본 반영\n")
    for rel in DELETED:
        (repo / rel).unlink()
    # 다른 안건
    A.write(repo, OTHER_EC, "# 다른 안건 EC\n")
    for rel in OTHER_WHITELISTED:
        A.write(repo, rel, "# 다른 안건\n")
    A.write(repo, ORDER_NO_REQ, order_text("100", []))
    A.write(repo, "Departments/Secretariat/assets/inbox/ORD-102_v01.md", order_text("102", ["REQ-002"]))
    A.append(repo, OTHER_MODIFIED, "다른 안건의 변경\n")


def status_paths(repo):
    res = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall", "-z"],
                         cwd=repo, capture_output=True, encoding="utf-8", errors="replace", check=True)
    return sorted(tok[3:] for tok in res.stdout.split("\0") if tok)


def classify(repo, paths, checker):
    """05 1.1절 6번 ①~⑥으로 나눈다. (안건 변경 목록, 그 밖의 변경 목록)을 돌려준다."""
    rec_name = re.compile(rf"^(REQ|EC|DEV|RPT|RES)-{NUM}(-(REQ|EC))?_v\d{{2}}\.md$")
    approval = re.compile(rf"^승인기록_\d{{8}}_(REQ|RES)-{NUM}_v\d{{2}}\.md$")
    applied = re.compile(rf"^Departments/[^/]+/workspace/REQ-{NUM}_적용본_v\d{{2}}/")
    mine, others = [], []
    for p in paths:
        name = p.rsplit("/", 1)[-1]
        hit = (rec_name.match(name)  # ①
               or (p.startswith("Departments/Secretariat/assets/inbox/") and approval.match(name))  # ②
               or (re.match(r"^ORD-\d{3}_v\d{2}\.md$", name) and (repo / p).exists()
                   and f"  - REQ-{NUM}\n" in (repo / p).read_text(encoding="utf-8"))  # ③
               or applied.match(p)  # ④
               or p in LISTED  # ⑤
               or any(checker.item_covers(s, p) for s in SCOPE) or p in REFLECTED or p in DELETED)  # ⑥
        (mine if hit else others).append(p)
    return mine, others


def part3(results, base):
    print("== 3부: 05 1.1절 6번(적용본 v02) 스테이징 범위 ==")
    checker = A.load_checker()
    repo = make_repo(base)
    expected_mine = sorted(sum(AGENDA.values(), []) + REFLECTED + DELETED)
    expected_others = sorted(OTHER_WHITELISTED + [OTHER_EC, OTHER_MODIFIED, ORDER_NO_REQ])

    print("--- 사례 S7: ①~⑥ 분류대로 스테이징 ---")
    A.reset(repo)
    setup(repo)
    A.git(repo, "status", "--porcelain", "-uall")
    mine, others = classify(repo, status_paths(repo), checker)
    A.report(results, "S7 분류(①~⑥)", mine == expected_mine and others == expected_others,
             f"안건 변경 {len(mine)}건, 그 밖의 변경 {others}")
    A.git(repo, "add", "-A", "--", *mine)
    A.git(repo, "status", "--porcelain", "-uall")
    A.check(results, "S7 --staged", A.run_checker(repo, True), 0, f"REQ-{NUM}_v01.md")
    res = A.git(repo, "commit", "-q", "-m", f"feat: [REQ-{NUM}] 시험", check=False)
    A.report(results, "S7 pre-commit 훅 커밋", res.returncode == 0 and "[SUCCESS]" in (res.stdout + res.stderr),
             f"git commit 종료 코드 {res.returncode}")
    if res.returncode == 0:
        show = A.git(repo, "show", "--name-status", "--format=", "HEAD")
        committed = show.stdout
        has_final = f"Departments/Quality/results/RES-{NUM}_v01.md" in committed
        deletions = all(f"D\t{d}" in committed for d in DELETED)
        A.report(results, "S7 커밋 내용(최종 판정서 자신, 삭제 2건)", has_final and deletions,
                 f"최종 판정서 포함={has_final}, 삭제 포함={deletions}")
        left = status_paths(repo)
        A.report(results, "S7 커밋 뒤 남은 변경", left == expected_others, f"{left}")
        A.git(repo, "reset", "-q", "--hard", "HEAD~1")

    print("--- 사례 S8: 다른 안건의 EC(scope 밖)까지 스테이징 ---")
    A.reset(repo)
    setup(repo)
    mine, _ = classify(repo, status_paths(repo), checker)
    A.git(repo, "add", "-A", "--", *mine, OTHER_EC)
    A.check(results, "S8 --staged", A.run_checker(repo, True), 1, OTHER_EC)

    print("--- 사례 S9: 다른 안건의 대조 제외 구역 파일까지 스테이징 ---")
    A.reset(repo)
    setup(repo)
    mine, _ = classify(repo, status_paths(repo), checker)
    A.git(repo, "add", "-A", "--", *mine, *OTHER_WHITELISTED)
    A.check(results, "S9 --staged(검사기가 막지 않음)", A.run_checker(repo, True), 0, f"REQ-{NUM}_v01.md")


def main():
    for src in (A.CHECKER, A.HOOK):
        if not src.exists():
            print(f"[FAIL] 시험 입력 파일이 없습니다: {src}")
            return 1
    print(f"[START] {A.now()}")
    results = {}
    with tempfile.TemporaryDirectory(prefix="req012b_", ignore_cleanup_errors=True) as tmp:
        part3(results, Path(tmp))
    print("== 요약 ==")
    for name, ok in results.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"[END] {A.now()}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
