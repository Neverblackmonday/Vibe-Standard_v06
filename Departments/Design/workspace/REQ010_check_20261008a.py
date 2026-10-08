"""REQ-010 명세 단계 점검용 일회성 스크립트 (EC-010 3.5절, 3.6절 4번).

대상 목록을 본문에 적은 일회성 스크립트이므로 파일명에 날짜와 접미사를 붙였다.
파일을 수정하지 않고 조회 결과만 출력한다.

사용법 (저장소 루트):
    python Departments/Design/workspace/REQ010_check_20261008a.py diff
    python Departments/Design/workspace/REQ010_check_20261008a.py terms
    python Departments/Design/workspace/REQ010_check_20261008a.py refs
    python Departments/Design/workspace/REQ010_check_20261008a.py tags
    python Departments/Design/workspace/REQ010_check_20261008a.py files
"""

import os
import re
import subprocess
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")

APPLY_ROOT = "Departments/Design/workspace/REQ-010_적용본_v01"
APPLY = APPLY_ROOT + "/Workflow.적용본"

TERM_PATTERN = re.compile(
    r"창구|비서실|secretariat|Secretariat|오케스트레이터|요구 메모|요구메모|Claude Code|메인 세션"
)
TAG_PATTERN = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")
# 「」 참조 앞의 백틱 경로(있으면)를 함께 잡는다.
REF_PATTERN = re.compile(r"(`[^`]+`\s*)?「([^」]+)」")
HEADING_PATTERN = re.compile(r"^(#{2,3})\s+(.*)$")


def now():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def tracked_workflow_files():
    out = subprocess.run(
        ["git", "ls-files", "Workflow"], capture_output=True, text=True,
        encoding="utf-8", check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def target_files():
    """점검 대상: 추적 파일(적용본이 있으면 적용본) + 적용본의 새 파일."""
    targets = []
    for orig in tracked_workflow_files():
        rel = orig[len("Workflow/"):]
        applied = APPLY + "/" + rel
        if os.path.exists(applied):
            targets.append((orig, applied, "적용본"))
        else:
            targets.append((orig, orig, "원본"))
    for dirpath, _, names in os.walk(APPLY):
        for name in names:
            path = os.path.join(dirpath, name).replace("\\", "/")
            rel = path[len(APPLY) + 1:]
            if not os.path.exists("Workflow/" + rel):
                targets.append(("Workflow/" + rel + " (새 파일)", path, "적용본(새 파일)"))
    return targets


def history_start(lines):
    """개정 이력 표 시작 줄 번호(1부터). 없으면 None."""
    for i, line in enumerate(lines, 1):
        if line.strip() == "## 개정 이력":
            return i
    return None


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def cmd_diff():
    print("시각:", now())
    for orig, path, kind in target_files():
        if kind != "적용본":
            continue
        stat = subprocess.run(
            ["git", "diff", "--no-index", "--stat", orig, path],
            capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip().splitlines()
        hunks = subprocess.run(
            ["git", "diff", "--no-index", "-U0", orig, path],
            capture_output=True, text=True, encoding="utf-8",
        ).stdout.splitlines()
        print("===", orig)
        print("  ", stat[-1] if stat else "(차이 없음)")
        for h in hunks:
            if h.startswith("@@"):
                print("  ", h)


def cmd_terms():
    print("시각:", now())
    print("패턴:", TERM_PATTERN.pattern)
    total = 0
    for orig, path, kind in target_files():
        lines = read_lines(path)
        hist = history_start(lines)
        for i, line in enumerate(lines, 1):
            if TERM_PATTERN.search(line):
                total += 1
                mark = " [개정 이력]" if hist and i > hist else ""
                print(f"{path}:{i}{mark}: {line.strip()[:160]}")
    print("일치 줄 합계:", total)


def headings(path):
    names = set()
    for line in read_lines(path):
        m = HEADING_PATTERN.match(line)
        if m:
            title = TAG_PATTERN.sub("", m.group(2)).strip()
            title = re.sub(r"^[\d.]+\s+", "", title)
            names.add(title)
    return names


def bold_items(path):
    text = "\n".join(read_lines(path))
    return {m.strip() for m in re.findall(r"\*\*([^*]+)\*\*", text)}


def resolve_doc(token):
    """`Workflow/03_라이프사이클` 같은 경로를 점검 대상 파일로 바꾼다."""
    token = token.strip("` ").strip()
    if token == "AGENTS.md":
        return "AGENTS.md"
    if token.startswith("Workflow/"):
        rel = token[len("Workflow/"):]
        if rel.endswith(".md"):
            rel = rel[:-3]
        for cand in (APPLY + "/" + rel + ".md", "Workflow/" + rel + ".md"):
            if os.path.exists(cand):
                return cand
        return "없음:" + token
    return None


def cmd_refs():
    print("시각:", now())
    total = 0
    for orig, path, kind in target_files():
        lines = read_lines(path)
        hist = history_start(lines)
        for i, line in enumerate(lines, 1):
            if hist and i > hist:
                continue
            for m in REF_PATTERN.finditer(line):
                total += 1
                doc_token, name = m.group(1), m.group(2)
                doc = resolve_doc(doc_token) if doc_token else None
                if doc is None:
                    status = "문서 미지정(같은 문서·인용·용어)"
                elif doc.startswith("없음:"):
                    status = "경로 없음"
                else:
                    found = name in headings(doc) or name in bold_items(doc)
                    status = ("실재 " if found else "절 이름 없음 ") + doc
                print(f"{path}:{i}: 「{name}」 -> {status}")
    print("참조 합계:", total)


def cmd_tags():
    print("시각:", now())
    for orig, path, kind in target_files():
        for i, line in enumerate(read_lines(path), 1):
            if TAG_PATTERN.search(line):
                print(f"{path}:{i}: {line.strip()[:120]}")


def cmd_files():
    print("시각:", now())
    for dirpath, _, names in os.walk(APPLY_ROOT):
        for name in names:
            print(os.path.join(dirpath, name).replace("\\", "/"))


COMMANDS = {
    "diff": cmd_diff, "terms": cmd_terms, "refs": cmd_refs,
    "tags": cmd_tags, "files": cmd_files,
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print("사용법: python " + sys.argv[0] + " [" + "|".join(COMMANDS) + "]")
        sys.exit(2)
    COMMANDS[sys.argv[1]]()
