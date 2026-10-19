#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_prejudge.py - 판정 전 점검 스크립트(작성 단계가 산출물을 넘기기 전의 형식 점검)

규칙의 원천은 Workflow/03_라이프사이클 「판정 전 점검」이고, 명령의 동작은 Workflow/06_통제장치_및_배포
「준비·판단 명령」 5항이 정한다. 문서 종류는 파일 이름(Workflow/07_문서_서식_및_번호 「문서 체계」)으로, 필수 머리말
필드는 같은 문서 「머리말」 표로, 리비전 태그는 같은 문서 「개정 이력과 리비전 태그」로 정한다. 이 스크립트는 그 구현이다.

사용법: python check_prejudge.py <문서 경로> [--req <REQ 경로>] [--applied <적용본 폴더>]
결정적 항목: ① 서식 절 ② 머리말 ③ scope 포함과 결정 반영 대조(--req) ④ 리비전 태그(--applied, --req)
종료 코드: 0 결함 없음, 1 결함 있음, 2 문서를 읽지 못함. 이 점검은 판정이 아니며 판정을 대신하지 않는다.
읽기만 하고 파일을 쓰지 않는다.
"""

import re
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import build_guides as bg  # noqa: E402  (적용본 overlay 읽기와 .변경.md 적용)
import check_standard as cs  # noqa: E402  (출력 인코딩 고정, 머리말 값 읽기, scope 일치, 시각 형식)

RULE = "Workflow/03_라이프사이클 「판정 전 점검」"
FORMAT_DOC = "Workflow/07_문서_서식_및_번호.md"
TAG_RE = re.compile(r"\s*\((?:REQ|HOTFIX)-\d{3}(?:-\d+)?_v\d{2}\)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LIST_FIELDS = ("scope", "workflow", "related_req", "causes", "proposals")
DATE_FIELDS = ("created", "updated")
TIME_FIELDS = ("created_at", "approved", "confirmed", "completed_at", "recorded_at", "ceo_checked_at")
# 파일 이름 → (「머리말」 표의 문서 이름, 서식 파일). 원천은 07 「문서 체계」 표의 「위치와 파일명」·「서식」 열이다
KINDS = (
    (re.compile(r"^REQ-\d{3}(?:-\d+)?_v\d{2}\.md$"), "REQ", "REQ_TEMPLATE.md"),
    (re.compile(r"^EC-\d{3}(?:-\d+)?_v\d{2}\.md$"), "EC", "EC_TEMPLATE.md"),
    (re.compile(r"^DEV-\d{3}(?:-\d+)?_v\d{2}\.md$"), "DEV·RPT", "DEV_TEMPLATE.md"),
    (re.compile(r"^RPT-\d{3}(?:-\d+)?_v\d{2}\.md$"), "DEV·RPT", "DEV_TEMPLATE.md"),
    (re.compile(r"^RES-\d{3}(?:-\d+)?(?:-(?:REQ|EC|SPEC|DESIGN))?_v\d{2}\.md$"), "RES", "RES_TEMPLATE.md"),
    (re.compile(r"^ACC-\d{3}(?:-\d+)?_v\d{2}\.md$"), "ACC", "ACC_TEMPLATE.md"),
    (re.compile(r"^NCR-\d{3}(?:-\d+)?_\d{2}\.md$"), "NCR", "NCR_TEMPLATE.md"),
    (re.compile(r"^HOTFIX-\d{3}(?:-\d+)?_v\d{2}\.md$"), "HOTFIX", "HOTFIX_TEMPLATE.md"),
    (re.compile(r"^ORD-\d{3}_v\d{2}\.md$"), "ORDER", "ORDER_TEMPLATE.md"),
)


class Report:
    def __init__(self):
        self.fails = 0

    def fail(self, item, cause, action):
        self.fails += 1
        print(f"[FAIL] {item}: {cause}")
        print(f"       조치: {action}")


def front_matter(text):
    """머리말을 {키: (값, 목록 항목들)}로 읽는다. 머리말이 없으면 None."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    out, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        m = re.match(r"^([A-Za-z_]+):(.*)$", line)
        if m:
            key = m.group(1)
            out[key] = (cs.strip_value(m.group(2)), [])
        elif key and re.match(r"^\s+- ", line):
            out[key][1].append(cs.strip_value(line.split("-", 1)[1]))
    return None


def h2_titles(text):
    titles, fence = [], False
    for line in text.split("\n"):
        if line.startswith("```"):
            fence = not fence
            continue
        m = re.match(r"^## (.*)$", line)
        if m and not fence:
            titles.append(bg.section_name(m.group(1)))
    return titles


def strip_parens(text):
    """괄호 안(중첩 포함)의 글자를 뗀다. 머리말 표의 필드 설명 안 백틱을 필드 이름으로 읽지 않기 위해서다."""
    out, depth = [], 0
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return "".join(out)


def required_fields(docs, kind):
    rows = bg.first_table(docs.get(FORMAT_DOC), "머리말", ("문서", "필수 머리말 필드"))
    if rows is None:
        return None
    for r in rows:
        if r.get("문서") == kind:
            return re.findall(r"`([a-z_]+)`", strip_parens(r.get("필수 머리말 필드", "")))
    return None


def table_rows(doc_text, title):
    """제목이 title인 절 자신의 본문 안 표의 데이터 행 칸 목록."""
    d = bg.Doc("", doc_text)
    r = d.own_range(title)
    if r is None:
        return None
    rows = []
    for i in range(*r):
        line = d.lines[i]
        if line.startswith("|") and not bg.ROW_SEP_RE.match(line):
            nxt = d.lines[i + 1] if i + 1 < len(d.lines) else ""
            if bg.ROW_SEP_RE.match(nxt):
                continue
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def req_decisions(req_text):
    rows = table_rows(req_text, "결정 사항 및 선택지") or []
    return [r[0] for r in rows if re.fullmatch(r"D\d+", r[0])]


def check_template(rep, docs, text, template):
    tpl = bg.read_text(docs.source, f"Workflow/templates/{template}")
    if tpl is None:
        rep.fail("① 서식 절", f"서식 파일이 없습니다: Workflow/templates/{template}", "서식 위치를 확인한다")
        return
    have, pos = h2_titles(text), 0
    for t in h2_titles(tpl):
        optional = bool(re.search(r"\([^()]*만\)\s*$", t))
        if t in have[pos:]:
            pos = have.index(t, pos) + 1
        elif not optional:
            rep.fail("① 서식 절", f"서식({template})의 절 「{t}」이 없거나 순서가 다릅니다",
                     f"서식의 H2 절을 같은 순서로 모두 둔다({RULE})")


def check_front(rep, docs, text, kind):
    fm = front_matter(text)
    if fm is None:
        rep.fail("② 머리말", "--- 로 감싼 머리말이 없습니다", f"{FORMAT_DOC} 「머리말」 형식으로 머리말을 둔다")
        return None
    need = required_fields(docs, kind)
    if need is None:
        rep.fail("② 머리말", f"{FORMAT_DOC} 「머리말」 표에서 {kind} 행을 찾지 못했습니다", "멈춰 보고한다")
        return fm
    for key in need:
        if key not in fm:
            rep.fail("② 머리말", f"필수 필드 {key}가 없습니다", f"{FORMAT_DOC} 「머리말」 표의 {kind} 행 필드를 모두 둔다")
    for key, (val, items) in fm.items():
        if key in DATE_FIELDS and val and not DATE_RE.match(val):
            rep.fail("② 머리말", f"{key} 값이 날짜 형식(YYYY-MM-DD)이 아닙니다: {val}", "날짜 형식으로 고친다")
        if key in TIME_FIELDS and val and not cs.APPROVAL_TIME.match(val):
            rep.fail("② 머리말", f"{key} 값이 시각 형식(YYYY-MM-DDTHH:MM:SS+09:00)이 아닙니다: {val}", "시각 형식으로 고친다")
        if key in LIST_FIELDS and val not in ("", "[]"):
            rep.fail("② 머리말", f"{key}가 목록 형식(두 칸 들여쓰기 뒤 「- 」)이 아닙니다", "목록 형식으로 고친다")
    return fm


def check_decisions(rep, text, decisions, where):
    rows = table_rows(text, "결정 반영 대조")
    if rows is None:
        rep.fail("③ 결정 반영 대조", f"「결정 반영 대조」 절이 없습니다(REQ 결정 {len(decisions)}개)",
                 "결정마다 두 범위를 나란히 적은 「결정 반영 대조」 표를 둔다(EC 서식 3.3절, DEV 서식 10절)")
        return
    found = {}
    for r in rows:
        m = re.match(r"^(D\d+)\b", r[0])
        if m:
            found[m.group(1)] = r
    for d in decisions:
        r = found.get(d)
        if r is None:
            rep.fail("③ 결정 반영 대조", f"{where}의 「결정 반영 대조」 표에 REQ 결정 {d}의 행이 없습니다",
                     "REQ 3절 표의 D번호마다 한 행을 둔다")
        elif len(r) < 3 or not r[1] or not r[2]:
            rep.fail("③ 결정 반영 대조", f"결정 {d} 행의 「결정 문안의 범위」나 「구현한 판단 수단이 덮는 범위」 칸이 비어 있습니다",
                     "두 범위 칸을 모두 적는다")


def changed_paths(text):
    """결과서 「변경 파일」 표의 경로 칸에 적은 경로."""
    rows = table_rows(text, "변경 파일") or []
    out = []
    for r in rows:
        if len(r) >= 2:
            out += re.findall(r"`([^`]+)`", r[1])
    return out


def in_team_area(path):
    parts = path.split("/")
    return len(parts) >= 4 and parts[0] == "Departments" and parts[3] in ("results", "workspace")


def check_scope(rep, kind, fm, text, req_fm, req_text, name):
    req_scope = {s.rstrip("/") for s in req_fm.get("scope", ("", []))[1]}
    if kind == "EC":
        for s in (fm.get("scope", ("", []))[1] if fm else []):
            if not any(cs.item_covers(r, s.rstrip("/")) for r in req_scope):
                rep.fail("③ scope 포함", f"EC scope 항목 {s}가 REQ scope 안에 없습니다", "EC scope를 REQ scope의 부분집합으로 둔다")
        check_decisions(rep, text, req_decisions(req_text), name)
    elif kind == "DEV·RPT":
        for p in changed_paths(text):
            p = p.strip()
            if p.startswith("…") or "<" in p or not p.startswith(("Departments/", "Workflow", "AGENTS", "CLAUDE", ".claude",
                                                                   "Lab/", "setup.cmd", ".git")):
                print(f"[INFO] ③ scope 포함: 경로로 대조하지 않는 칸을 건너뜁니다: {p}")
                continue
            if not (any(cs.item_covers(r, p) for r in req_scope) or in_team_area(p)):
                rep.fail("③ scope 포함", f"변경 파일 {p}가 REQ scope와 팀 results/·workspace/ 밖입니다",
                         "REQ scope 안이나 그 파트의 작업 구역(Workflow/02_부서_구조_및_작업구역 「작업 구역」)에 둔다")
        if table_rows(text, "결정 반영 대조") is not None:
            check_decisions(rep, text, req_decisions(req_text), name)


def sections(text):
    """H2·H3 절 {이름: (제목 글자, 자신의 본문)}. 끝의 빈 줄·구분선은 절 내용이 아니다."""
    lines = text.split("\n")
    heads, fence = [], False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        m = re.match(r"^(#{2,3}) (.*)$", line)
        if m and not fence:
            heads.append((i, m.group(2)))
    out = {}
    for k, (i, title) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        body = lines[i + 1:end]
        while body and body[-1].strip() in ("", "---"):
            body = body[:-1]
        out[bg.section_name(title)] = (title, "\n".join(body))
    return out


def history_rows(text):
    sec = sections(text).get("개정 이력")
    if not sec:
        return []
    return [ln for ln in sec[1].split("\n") if ln.startswith("|") and not bg.ROW_SEP_RE.match(ln)]


def check_tags(rep, applied, tag):
    """④ 적용본 Markdown 파일의 실변경 절과 현행 태그, 이전 태그, 개정 이력 행(07 「개정 이력과 리비전 태그」)."""
    root = bg.repo_root()
    base = Path(applied)
    seen = 0
    for p in sorted(base.rglob("*.md")):
        if "__pycache__" in p.parts:
            continue
        rel, is_delta = bg.overlay_rel(base, p)
        if rel.startswith("Workflow/templates/") or not (rel in ("AGENTS.md", "CLAUDE.md") or rel.startswith("Workflow/")):
            if rel.startswith("Workflow/templates/"):
                if TAG_RE.search("\n".join(ln for ln in p.read_text(encoding="utf-8").split("\n") if ln.startswith("#"))):
                    rep.fail("④ 리비전 태그", f"서식 파일 제목에 리비전 태그가 있습니다: {rel}", "서식 파일에는 태그를 두지 않는다")
            continue
        seen += 1
        new_text = p.read_text(encoding="utf-8").replace("\r\n", "\n")
        orig_path = root / rel
        if is_delta:
            # 변경 파일은 담긴 블록(교체·추가)이 실변경 절이다(07 「개정 이력과 리비전 태그」 절차 1)
            for m in re.finditer(r"^(#{2,3}) (.*)$", new_text, re.M):
                name = bg.section_name(m.group(2))
                olds = [t for t in re.findall(r"\((?:REQ|HOTFIX)-\d{3}(?:-\d+)?_v\d{2}\)", m.group(2)) if t != tag]
                if not m.group(2).rstrip().endswith(tag):
                    rep.fail("④ 리비전 태그", f"{rel} 「{name}」 변경 파일의 블록 제목에 현행 태그 {tag}가 없습니다",
                             "바뀐 절의 제목 끝에 현행 태그를 붙인다")
                if olds:
                    rep.fail("④ 리비전 태그", f"{rel} 「{name}」 제목에 이전 태그 {olds}가 남아 있습니다", "이전 태그를 지운다(절차 2)")
            if not re.search(r"^<!-- 변경: 이력 추가 -->\s*\n\s*\| " + re.escape(tag[1:-1]) + r" \|", new_text, re.M):
                rep.fail("④ 리비전 태그", f"{rel} 변경 파일에 그 안건의 개정 이력 행(이력 추가)이 없습니다", "개정 이력 행을 더한다")
            continue
        old_text = orig_path.read_text(encoding="utf-8").replace("\r\n", "\n") if orig_path.is_file() else ""
        so, sn = sections(old_text), sections(new_text)
        for name, (title, body) in sn.items():
            if name == "개정 이력":
                continue
            ob = so.get(name, (None, None))[1]
            changed = ob is None or TAG_RE.sub("", ob).strip() != TAG_RE.sub("", body).strip()
            has_tag = title.rstrip().endswith(tag)
            olds = [t for t in re.findall(r"\((?:REQ|HOTFIX)-\d{3}(?:-\d+)?_v\d{2}\)", title) if t != tag]
            if changed and not has_tag:
                rep.fail("④ 리비전 태그", f"{rel} 「{name}」 실변경 절의 제목에 현행 태그 {tag}가 없습니다",
                         "실제로 바뀐 절의 제목 끝에 현행 태그를 붙인다(07 「개정 이력과 리비전 태그」 절차 3)")
            if not changed and has_tag:
                rep.fail("④ 리비전 태그", f"{rel} 「{name}」 바뀌지 않은 절에 현행 태그 {tag}가 붙어 있습니다",
                         "바뀌지 않은 절에는 태그를 붙이지 않는다")
            if olds:
                rep.fail("④ 리비전 태그", f"{rel} 「{name}」 제목에 이전 태그 {olds}가 남아 있습니다", "이전 태그를 지운다(절차 2)")
        if old_text and not any(r.startswith(f"| {tag[1:-1]} |") for r in history_rows(new_text)):
            rep.fail("④ 리비전 태그", f"{rel} 개정 이력 표에 {tag[1:-1]} 행이 없습니다", "개정 이력 표에 한 행을 더한다(절차 4)")
    return seen


def main(argv):
    if not argv or argv[0].startswith("--"):
        print("[FAIL] 사용법: python check_prejudge.py <문서 경로> [--req <REQ 경로>] [--applied <적용본 폴더>]")
        return 2
    doc_path, req_path, applied = argv[0], None, None
    i = 1
    while i < len(argv):
        if argv[i] == "--req" and i + 1 < len(argv):
            req_path = argv[i + 1]
            i += 2
        elif argv[i] == "--applied" and i + 1 < len(argv):
            applied = argv[i + 1]
            i += 2
        else:
            print(f"[FAIL] 사용법 오류: 알 수 없는 인자 {argv[i]}")
            return 2
    try:
        text = Path(doc_path).read_text(encoding="utf-8").replace("\r\n", "\n")
        req_text = Path(req_path).read_text(encoding="utf-8").replace("\r\n", "\n") if req_path else None
        root = bg.repo_root()
        cs.ROOT_DIR = root
        docs = bg.Docs(bg.WorkTreeSource(root, [applied] if applied else []))
    except (OSError, UnicodeDecodeError, bg.SourceError) as e:
        print(f"[FAIL] 문서를 읽을 수 없습니다: {type(e).__name__}: {e}")
        print("       조치: 경로를 확인하고 다시 실행하십시오.")
        return 2
    name = Path(doc_path).name
    kind = next(((k, t) for pat, k, t in KINDS if pat.match(name)), None)
    if kind is None:
        print(f"[FAIL] 파일 이름으로 문서 종류를 정할 수 없습니다: {name}")
        print(f"       조치: {FORMAT_DOC} 「문서 체계」의 파일명 형식을 확인한다.")
        return 2
    kind, template = kind
    rep = Report()
    print(f"[INFO] 판정 전 점검: {doc_path} (종류 {kind}, 서식 {template}). 원천: {RULE}. 이 점검은 판정이 아니다.")
    check_template(rep, docs, text, template)
    fm = check_front(rep, docs, text, kind)
    if req_text is not None:
        req_fm = front_matter(req_text) or {}
        check_scope(rep, kind, fm, text, req_fm, req_text, name)
    else:
        print("[INFO] ③ scope 포함: --req가 없어 건너뜁니다.")
    if applied:
        if not req_path:
            rep.fail("④ 리비전 태그", "--applied에는 --req가 필요합니다(현행 태그를 REQ 파일 이름으로 정한다)", "--req를 함께 준다")
        else:
            tag = f"({Path(req_path).stem})"
            n = check_tags(rep, applied, tag)
            print(f"[INFO] ④ 리비전 태그: 적용본 Markdown 거버넌스 파일 {n}개를 현행 태그 {tag}로 대조했습니다.")
    if rep.fails:
        print(f"[FAIL] 판정 전 점검 결함 {rep.fails}건. 결함을 고친 뒤 다시 실행하고 산출물을 넘긴다.")
        return 1
    print("[PASS] 판정 전 점검: 결정적 항목 결함 없음. 사람이 확인하는 항목은 점검표를 따른다.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
