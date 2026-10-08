"""REQ-012 명세 단계 조회 스크립트 v02 적용본용(일회성, 읽기 전용).

REQ012_check_20261009a.py와 같은 조회를 적용본 폴더 v02로 다시 하고,
직전 적용본 폴더(v01)와 v02의 차이를 함께 출력한다.
대상 목록을 본문에 둔 일회성 스크립트라 파일명에 날짜와 접미사를 붙였다.
저장소 파일을 바꾸지 않고 조회 결과만 출력한다.
"""
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[3]
PREV = "Departments/Design/workspace/REQ-012_적용본_v01"
APPLIED = "Departments/Design/workspace/REQ-012_적용본_v02"

# (원본, 적용본 상대 경로) 짝. 원본은 작업 트리이며 git status로 커밋 1044e1e와 같음을 따로 확인한다
NAMES = [("AGENTS.md", "AGENTS.md.적용본")]
for name in ["01_표준_개요", "02_부서_구조_및_작업구역", "03_라이프사이클", "04_모델_운용",
             "05_인수인계_및_실행명령", "06_통제장치_및_배포", "07_문서_서식_및_번호"]:
    NAMES.append((f"Workflow/{name}.md", f"Workflow.적용본/{name}.md"))
for t in ["REQ", "EC", "DEV", "RES"]:
    NAMES.append((f"Workflow/templates/{t}_TEMPLATE.md", f"Workflow.적용본/templates/{t}_TEMPLATE.md"))
PAIRS = [(orig, f"{APPLIED}/{rel}") for orig, rel in NAMES]

TAG_RE = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")
UNUSED = ["창구", "비서실 세션", "요구 메모", "1차 게이트", "2차 게이트", "삼중 검수", "점검표",
          "재작업 절차서", "재의뢰", "개정안", "Update_Package", "REQ 검토"]
COPY_KEYS = ["문체 반영", "실행 명령 기준", "요약 보고", "상세 보고", "[CEO]", "최종 판정서 승인",
             "assets/research", "assets/briefings", "결함」과 「문체", "기계적 갱신",
             "related_req`에 그 안건", "그 안건의 변경"]


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def section_of(lines, idx):
    """idx 줄이 속한 마지막 H2·H3 제목을 돌려준다(개정 이력 표 판별용)."""
    for j in range(idx, -1, -1):
        if lines[j].startswith("## ") or lines[j].startswith("### "):
            return lines[j].strip()
    return "(제목 없음)"


def print_diff(a, b):
    rc, out = run(["git", "-c", "core.quotepath=false", "diff", "--no-index", "-U0", a, b])
    _, stat = run(["git", "diff", "--no-index", "--shortstat", a, b])
    print(f"\n=== {a} -> {b} (종료 코드 {rc}) {stat.strip()}")
    for line in out.splitlines():
        if line.startswith("@@"):
            print(line)
        elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            print("   " + line[:200])


def prev_diffs():
    print(f"\n## 0. 직전 적용본(v01)과 v02 차이 (-U0) {now()}")
    for _, rel in NAMES:
        print_diff(f"{PREV}/{rel}", f"{APPLIED}/{rel}")


def diffs():
    print(f"\n## 1. 원본과 적용본 차이 (-U0) {now()}")
    for orig, app in PAIRS:
        print_diff(orig, app)


def tags():
    print(f"\n## 2. 리비전 태그 정규식 {now()}")
    for orig, app in PAIRS[:8]:
        lines = (ROOT / app).read_text(encoding="utf-8").splitlines()
        hits = [(i + 1, l) for i, l in enumerate(lines) if TAG_RE.search(l)]
        print(f"=== {app}: {len(hits)}건")
        for n, l in hits:
            heading = l.startswith("## ") or l.startswith("### ")
            print(f"  {n}: {l}  [{'제목' if heading else '제목 아님'}]")


def unused_words():
    print(f"\n## 3. 쓰지 않는 말 {now()}")
    for _, app in PAIRS:
        lines = (ROOT / app).read_text(encoding="utf-8").splitlines()
        for i, l in enumerate(lines):
            for w in UNUSED:
                if w in l:
                    sec = section_of(lines, i)
                    print(f"  {app}:{i + 1} [{w}] 절={sec} :: {l[:100]}")


def copies():
    print(f"\n## 4. 사본 대조 키워드 {now()}")
    targets = [app for _, app in PAIRS]
    others = sorted(p.as_posix() for p in (ROOT / "Workflow" / "templates").glob("*.md")
                    if p.name not in {"REQ_TEMPLATE.md", "EC_TEMPLATE.md", "DEV_TEMPLATE.md", "RES_TEMPLATE.md"})
    others += sorted(p.as_posix() for p in (ROOT / ".claude" / "agents").glob("*.md"))
    others.append((ROOT / "CLAUDE.md").as_posix())
    for path in targets + others:
        p = Path(path) if Path(path).is_absolute() else ROOT / path
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, l in enumerate(lines):
            for k in COPY_KEYS:
                if k in l:
                    sec = section_of(lines, i)
                    rel = p.relative_to(ROOT).as_posix()
                    print(f"  {rel}:{i + 1} [{k}] 절={sec}")


if __name__ == "__main__":
    print(f"실행 시각 {now()}, 저장소 {ROOT}")
    rc, head = run(["git", "log", "--oneline", "-1"])
    print("HEAD:", head.strip())
    _, st = run(["git", "status", "--porcelain", "-uall"])
    modified = [l for l in st.splitlines() if not l.startswith("??")]
    print(f"추적 파일 변경(?? 제외): {len(modified)}건")
    for l in modified:
        print("  " + l)
    prev_diffs()
    diffs()
    tags()
    unused_words()
    copies()
