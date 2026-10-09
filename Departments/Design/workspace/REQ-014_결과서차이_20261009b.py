"""REQ-014 명세: RPT-014의 「원본과의 차이」·「리비전 태그 대조」 결과 원문을 채운다.

일회성 운영 스크립트다. 대상 목록을 본문에 둔다. 결과서 안의 표식 줄
(<!--DIFF:번호-->, <!--NEWFILES-->, <!--TAGREGEX-->)을 실행 결과로 바꾼다.
인자 없이 실행하면 바꿀 내용을 표준 출력으로 미리 보여 주기만 하고,
--apply를 주면 결과서 파일을 고쳐 쓴다. 표식이 없으면 실패로 끝낸다.
"""
import datetime
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RPT = Path("Departments/Design/results/RPT-014_v01.md")
DEST = "Departments/Design/workspace/REQ-014_적용본_v01"
PAIRS = [
    ("AGENTS.md", f"{DEST}/AGENTS.md.적용본"),
    ("Workflow/01_표준_개요.md", f"{DEST}/Workflow.적용본/01_표준_개요.md"),
    ("Workflow/02_부서_구조_및_작업구역.md", f"{DEST}/Workflow.적용본/02_부서_구조_및_작업구역.md"),
    ("Workflow/03_라이프사이클.md", f"{DEST}/Workflow.적용본/03_라이프사이클.md"),
    ("Workflow/04_모델_운용.md", f"{DEST}/Workflow.적용본/04_모델_운용.md"),
    ("Workflow/05_인수인계_및_실행명령.md", f"{DEST}/Workflow.적용본/05_인수인계_및_실행명령.md"),
    ("Workflow/07_문서_서식_및_번호.md", f"{DEST}/Workflow.적용본/07_문서_서식_및_번호.md"),
    ("Workflow/templates/ORDER_TEMPLATE.md", f"{DEST}/Workflow.적용본/templates/ORDER_TEMPLATE.md"),
    ("Workflow/templates/REQ_TEMPLATE.md", f"{DEST}/Workflow.적용본/templates/REQ_TEMPLATE.md"),
]
NEW_FILES = [
    f"{DEST}/Workflow.적용본/templates/BACKLOG_TEMPLATE.md",
    f"{DEST}/Workflow.적용본/templates/PLAN_TEMPLATE.md",
    f"{DEST}/Workflow.적용본/templates/BRIEFING_TEMPLATE.html",
    f"{DEST}/Workflow.적용본/templates/PM_DIRECTIVE_TEMPLATE.md",
]
TAG_FILES = [PAIRS[i][1] for i in range(7)]
TAG_RE = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")


def now() -> str:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec="seconds")


def diff_block(src: str, dst: str) -> str:
    cmd = ["git", "diff", "--no-index", "-U0", src, dst]
    when = now()
    proc = subprocess.run(cmd, capture_output=True)
    # 종료 코드 1은 차이가 있다는 뜻이다. 그 밖의 0이 아닌 값은 실행 실패다.
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git diff 실패({proc.returncode}): {proc.stderr.decode('utf-8', 'replace')}")
    out = (proc.stderr + proc.stdout).decode("utf-8", "replace").rstrip("\n")
    return (
        f"- 명령: `git diff --no-index -U0 {src} {dst}`\n"
        f"- 시각: {when}\n"
        f"- 결과 원문(줄 끝 변환 경고 포함):\n\n```text\n{out}\n```"
    )


def newfiles_block() -> str:
    rows = ["| 경로 | 줄 수 |", "| :--- | :---: |"]
    for f in NEW_FILES:
        n = len(Path(f).read_text(encoding="utf-8").splitlines())
        rows.append(f"| `{f}` | {n} |")
    return f"- 확인 시각: {now()} (Python `len(read_text().splitlines())`)\n\n" + "\n".join(rows)


def tagregex_block() -> str:
    lines = []
    for f in TAG_FILES:
        for i, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines(), 1):
            if TAG_RE.search(line):
                lines.append(f"{f}:{i}:{line}")
    return (
        f"- 패턴 `{TAG_RE.pattern}`, 대상 `AGENTS.md.적용본`과 `Workflow.적용본/` 매뉴얼 6개, 시각 {now()}\n"
        f"- 결과 원문({len(lines)}건):\n\n```text\n" + "\n".join(lines) + "\n```"
    )


def main() -> int:
    text = RPT.read_text(encoding="utf-8")
    repl = {f"<!--DIFF:{i + 1}-->": diff_block(s, d) for i, (s, d) in enumerate(PAIRS)}
    repl["<!--NEWFILES-->"] = newfiles_block()
    repl["<!--TAGREGEX-->"] = tagregex_block()
    missing = [k for k in repl if k not in text]
    if missing:
        print(f"[FAIL] 결과서에 표식이 없음: {missing}. 결과서를 확인한 뒤 다시 실행한다.")
        return 1
    for k, v in repl.items():
        text = text.replace(k, v)
    if "--apply" in sys.argv[1:]:
        RPT.write_text(text, encoding="utf-8", newline="\n")
        print(f"[OK] {RPT} 갱신")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
