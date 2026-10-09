"""REQ-014 명세: 기준 커밋의 원본을 적용본 폴더로 복사하고 작업 트리 원본과 바이트 대조한다.

일회성 운영 스크립트다. 대상 목록을 본문에 둔다. 인자 없이 실행하면 미리보기만 하고,
--apply를 주면 복사한다. 이미 있는 적용본은 덮어쓰지 않는다(작성 중 내용 보호).
"""
import subprocess
import sys
from pathlib import Path

BASE = "300437f"
DEST = Path("Departments/Design/workspace/REQ-014_적용본_v01")
TARGETS = [
    ("AGENTS.md", DEST / "AGENTS.md.적용본"),
    ("Workflow/01_표준_개요.md", DEST / "Workflow.적용본/01_표준_개요.md"),
    ("Workflow/02_부서_구조_및_작업구역.md", DEST / "Workflow.적용본/02_부서_구조_및_작업구역.md"),
    ("Workflow/03_라이프사이클.md", DEST / "Workflow.적용본/03_라이프사이클.md"),
    ("Workflow/04_모델_운용.md", DEST / "Workflow.적용본/04_모델_운용.md"),
    ("Workflow/05_인수인계_및_실행명령.md", DEST / "Workflow.적용본/05_인수인계_및_실행명령.md"),
    ("Workflow/07_문서_서식_및_번호.md", DEST / "Workflow.적용본/07_문서_서식_및_번호.md"),
    ("Workflow/templates/ORDER_TEMPLATE.md", DEST / "Workflow.적용본/templates/ORDER_TEMPLATE.md"),
    ("Workflow/templates/REQ_TEMPLATE.md", DEST / "Workflow.적용본/templates/REQ_TEMPLATE.md"),
]


def main() -> int:
    apply = "--apply" in sys.argv[1:]
    failed = False
    for src, dst in TARGETS:
        if not apply:
            print(f"[PREVIEW] {BASE}:{src} -> {dst}")
            continue
        if dst.exists():
            print(f"[SKIP] 이미 있음(덮어쓰지 않음): {dst}")
            continue
        data = subprocess.run(["git", "show", f"{BASE}:{src}"], capture_output=True, check=True).stdout
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        same = Path(src).read_bytes() == data
        print(f"[{'SAME' if same else 'DIFF'}] {dst} vs 작업 트리 {src}")
        failed = failed or not same
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
