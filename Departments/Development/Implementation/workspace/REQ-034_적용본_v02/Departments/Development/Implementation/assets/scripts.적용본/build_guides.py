#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_guides.py - 계층형 지침 생성물과 기준선 기록을 만드는 생성 명령

규칙의 원천은 Workflow/04_모델_운용 「계층형 지침」(계층과 예산, 원천과 생성물, 계층 구성표, 안전장치 핵심과
표준 공통 핵심, 세션별 구성)이고, 명령의 동작은 Workflow/06_통제장치_및_배포 「생성·반영 명령」 1항, 기준선 기록의
내용은 Workflow/05_인수인계_및_실행명령 「형상통제 절차」 2항이 정한다. 이 스크립트는 그 구현이다.

사용법: python build_guides.py --out <폴더> [--overlay <폴더>]… [--global-source <파일>]
        python build_guides.py --out <파일> --baseline --record <기록 이름> [--overlay <폴더>]…
  --out은 첫 인자로 둔다(allow 규칙이 --out으로 시작하는 형태만 허용하기 때문이다).
종료 코드: 0 성공, 1 생성 오류·쓰기 거부(생성물을 쓰지 않음), 2 사용법 오류·읽기 실패
쓰는 곳은 --out 아래뿐이며, --out이 거버넌스 경로(AGENTS.md 「불변 원칙」 3항 목록)나 CEO/·_archive/ 안이면 쓰지 않는다.
커밋·삭제·이동·Git 설정 변경을 하지 않는다. 형상통제 대조(check_config.py)가 같은 함수로 생성물을 다시 만들어 대조한다.
"""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import apply_delta  # noqa: E402  (.변경.md overlay를 원본에 적용해 읽는다. 06 「생성·반영 명령」 2항)
import check_standard as cs  # noqa: E402  (출력 인코딩 고정, 거버넌스 경로 목록, index 내용 읽기)

LAYERS_REL = "Workflow/data/guide_layers.json"
PROCESS_MAP_REL = "Workflow/data/process_map.json"
ORG_DOC_REL = "Workflow/02_부서_구조_및_작업구역.md"
AGENTS_REL = "AGENTS.md"
SAFETY_REL = "guides/core/safety.md"  # 생성물 경로는 --out(원본은 .claude/) 기준이다
STANDARD_REL = "guides/core/standard.md"
GEN_ROOT = ".claude/"
SOURCE_RULE = "Workflow/04_모델_운용 「계층형 지침」"
COMMAND_RULE = "Workflow/06_통제장치_및_배포 「생성·반영 명령」"
MARKER = ("<!-- 생성물: 손으로 고치지 않는다. 원천은 Workflow/data/guide_layers.json이 고른 절이며 "
          "생성 명령은 build_guides.py다 -->")
SAFETY_INTRO = "아래는 사용자 전역 지침이 하위 지침으로 바꿀 수 없다고 정한 항목(불변 예외)의 원문이다."
SAFETY_HEAD_RE = re.compile(r"^<!-- 원천: 사용자 전역 지침, 갱신 표기 (\[갱신:[^\]]*\]), 추출 SHA-256 ([0-9a-f]{64}), "
                            r"생성 근거 (.+) -->$")
BASIS_RE = re.compile(r"^<!-- 생성 근거: (.+?) -->\s*$", re.M)
UPDATE_MARK_RE = re.compile(r"\[갱신:[^\]]*\]")
REFS_TITLE = "필요할 때 읽는 문서"
NO_DEPT = "(실행마다 정해짐)"
NO_TEAM = "—"
X01_NOTE = ("해당 없음: 이 파트는 팀이 없고 부가 실행마다 정해지며, 실험 파일에는 조직마다의 작성 제한이 적용되지 않으므로 "
            "부·팀 계층을 두지 않는다(`Workflow/04_모델_운용` 「계층형 지침」 5항 ①). 판정과 범위 통제의 한계는 표준 공통 핵심과 "
            "파트 지침에 실린다.")
KST = timezone(timedelta(hours=9))

TAG_RE = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")
HEAD_RE = re.compile(r"^(#{1,6}) (.*)$")
NUM_RE = re.compile(r"^\d+(\.\d+)*\.?\s+")
ITEM_RE = re.compile(r"^(- |\* |\+ |\d+\. )")
BOLD_RE = re.compile(r"^\*\*(.+?)\*\*")
ROW_SEP_RE = re.compile(r"^\|\s*:?-{3,}")


class SourceError(Exception):
    """원천을 읽지 못함(종료 코드 2)."""


def repo_root():
    """저장소 루트(git rev-parse --show-toplevel. 실행 폴더 기준).

    적용본 폴더의 스크립트로 실행해도 저장소 루트를 쓰게 하려고 스크립트 위치가 아니라 실행 폴더로 구한다.
    """
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    if res.returncode != 0:
        raise SourceError("저장소 루트를 조회할 수 없습니다(git rev-parse --show-toplevel 실패): "
                          + res.stderr.decode("utf-8", "replace").strip())
    return Path(res.stdout.decode("utf-8").strip())


def git_lines(root, *args):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=root, capture_output=True)
    if res.returncode != 0:
        raise SourceError(f"git {' '.join(args)} 실패: {res.stderr.decode('utf-8', 'replace').strip()}")
    return [p for p in res.stdout.decode("utf-8", "replace").split("\0") if p]


# ---------------------------------------------------------------- 원천 읽기 (작업 트리·overlay, index)

def overlay_rel(base, path):
    """overlay 파일의 원본 경로. 경로 조각 끝의 .적용본을 떼고, .변경.md는 원본 .md로 맞춘다."""
    parts = [p[:-len(".적용본")] if p.endswith(".적용본") else p for p in path.relative_to(base).parts]
    rel = "/".join(parts)
    if rel.endswith(".변경.md"):
        return rel[:-len(".변경.md")] + ".md", True
    return rel, False


class WorkTreeSource:
    """작업 트리를 읽고, overlay(적용본 폴더)가 있으면 그 파일을 원본 대신 읽는다(앞의 폴더가 이긴다)."""

    def __init__(self, root, overlays=()):
        self.root = Path(root)
        self.layers = []
        for ov in overlays:
            base = Path(ov)
            if not base.is_dir():
                raise SourceError(f"--overlay 폴더가 없습니다: {ov}")
            mapping = {}
            for p in sorted(base.rglob("*")):
                if p.is_file() and "__pycache__" not in p.parts:
                    rel, is_delta = overlay_rel(base, p)
                    mapping[rel] = (p, is_delta)
            self.layers.append(mapping)
        self._files = None

    def read_bytes(self, rel, start=0):
        for i in range(start, len(self.layers)):
            hit = self.layers[i].get(rel)
            if hit is None:
                continue
            path, is_delta = hit
            if not is_delta:
                return path.read_bytes()
            base = self.read_bytes(rel, i + 1)
            if base is None:
                raise SourceError(f"변경 파일의 원본이 없습니다: {path} → {rel}")
            try:
                text, _ = apply_delta.apply(base.decode("utf-8").replace("\r\n", "\n"),
                                            path.read_text(encoding="utf-8").replace("\r\n", "\n"))
            except apply_delta.DeltaError as e:
                raise SourceError(f"변경 파일을 적용할 수 없습니다: {path} ({e})")
            return text.encode("utf-8")
        path = self.root / rel
        return path.read_bytes() if path.is_file() else None

    def read_many(self, rels):
        out = {}
        for rel in rels:
            data = self.read_bytes(rel)
            if data is not None:
                out[rel] = data
        return out

    def files(self):
        if self._files is None:
            found = set(git_lines(self.root, "ls-files", "-z"))
            found.update(git_lines(self.root, "ls-files", "-z", "--others", "--exclude-standard"))
            for mapping in self.layers:
                found.update(mapping)
            self._files = sorted(found)
        return self._files

    def describe(self):
        return "작업 트리" + (f"(overlay {len(self.layers)}개)" if self.layers else "")


class StagedSource:
    """커밋 대상(index)의 내용을 읽는다(커밋 전 검사 --staged). check_standard.py의 함수를 쓴다."""

    def __init__(self):
        self.entries = cs.index_entries()
        if self.entries is None:
            raise SourceError("커밋 대상 목록(git ls-files -s)을 조회하지 못했습니다")
        self.cache = {}

    def read_many(self, rels):
        want = {r: self.entries[r] for r in rels if r in self.entries and r not in self.cache}
        if want:
            blobs = cs.read_blobs(want.values())
            if blobs is None:
                raise SourceError("커밋 대상의 내용을 읽지 못했습니다")
            for r, sha in want.items():
                self.cache[r] = blobs[sha]
        return {r: self.cache[r] for r in rels if r in self.cache}

    def read_bytes(self, rel):
        return self.read_many([rel]).get(rel)

    def files(self):
        return sorted(self.entries)

    def describe(self):
        return "커밋 대상(index)"


def read_text(source, rel):
    data = source.read_bytes(rel)
    if data is None:
        return None
    try:
        return data.decode("utf-8").replace("\r\n", "\n")
    except UnicodeDecodeError as e:
        raise SourceError(f"UTF-8로 읽히지 않습니다: {rel} ({e})")


# ---------------------------------------------------------------- Markdown 절·항목·행 (덮는 범위. 04 「계층형 지침」 3항)

def section_name(title):
    return NUM_RE.sub("", TAG_RE.sub("", title).strip()).strip()


class Doc:
    """문서 하나의 제목·절·항목·행. 줄 번호는 0부터 센다. 코드 울타리 안의 # 줄은 제목이 아니다."""

    def __init__(self, rel, text):
        self.rel = rel
        self.lines = text.split("\n")
        self.heads = []
        fence = False
        for i, line in enumerate(self.lines):
            if line.startswith("```"):
                fence = not fence
                continue
            m = HEAD_RE.match(line)
            if m and not fence and len(m.group(1)) <= 4:
                self.heads.append((i, len(m.group(1)), section_name(m.group(2))))

    def find(self, name):
        return [h for h in self.heads if h[1] >= 2 and h[2] == name]

    def whole_range(self, name):
        """「절 S의 줄」: 제목 줄부터 다음 같은 단계 이하 제목 줄 앞까지(하위 절 포함)."""
        hits = self.find(name)
        if len(hits) != 1:
            return None
        i, lv, _ = hits[0]
        end = next((j for j, lv2, _ in self.heads if j > i and lv2 <= lv), len(self.lines))
        return i, end

    def own_range(self, name):
        """「절 S 자신의 본문」: 제목 줄 다음부터 첫 하위 제목 줄 앞까지."""
        hits = self.find(name)
        if len(hits) != 1:
            return None
        i = hits[0][0]
        end = next((j for j, _, _ in self.heads if j > i), len(self.lines))
        return i + 1, end

    def _col0_break(self, i):
        line = self.lines[i]
        if line.startswith("|") or line.startswith(">"):
            return True
        return i > 0 and not self.lines[i - 1].strip()

    def items(self, name):
        """절 자신의 본문 안 맨 앞 단계 항목 {표제: [(시작, 끝)]}. 표제는 굵은 글자, 없으면 표시 기호 뒤 첫 30자."""
        r = self.own_range(name)
        if r is None:
            return None
        s, e = r
        res, cur, fence = [], None, False
        for i in range(s, e):
            line = self.lines[i]
            if line.startswith("```"):
                fence = not fence
            if not fence and ITEM_RE.match(line):
                if cur:
                    res.append(cur)
                body = ITEM_RE.sub("", line, count=1)
                m = BOLD_RE.match(body)
                cur = [m.group(1) if m else body[:30], i, i + 1]
            elif cur is not None:
                if fence or line.startswith((" ", "\t")) or (line.strip() and not self._col0_break(i)):
                    cur[2] = i + 1
                elif not line.strip():
                    pass
                else:
                    res.append(cur)
                    cur = None
        if cur:
            res.append(cur)
        out = {}
        for title, a, b in res:
            while b > a + 1 and not self.lines[b - 1].strip():
                b -= 1
            out.setdefault(title, []).append((a, b))
        return out

    def rows(self, name):
        """절 자신의 본문 안 열 0 표의 데이터 행 {첫 칸: [줄]}(머리 줄·구분 줄 제외)."""
        r = self.own_range(name)
        if r is None:
            return None
        s, e = r
        out, fence = {}, False
        for i in range(s, e):
            line = self.lines[i]
            if line.startswith("```"):
                fence = not fence
                continue
            if fence or not line.startswith("|") or ROW_SEP_RE.match(line):
                continue
            nxt = self.lines[i + 1] if i + 1 < len(self.lines) else ""
            if ROW_SEP_RE.match(nxt):
                continue
            out.setdefault(line.split("|")[1].strip(), []).append(i)
        return out


class Docs:
    def __init__(self, source):
        self.source = source
        self.cache = {}

    def get(self, rel):
        if rel not in self.cache:
            text = read_text(self.source, rel)
            self.cache[rel] = None if text is None else Doc(rel, text)
        return self.cache[rel]


def sel_label(sel):
    label = f"{sel['doc']} 「{sel.get('section', '')}」" if sel.get("section") is not None else sel["doc"]
    keys = sel.get("items") or ([sel["item"]] if sel.get("item") else None)
    if keys:
        return label + " 항목: " + "".join(f"「{k}」" for k in keys)
    keys = sel.get("rows") or ([sel["row"]] if sel.get("row") else None)
    if keys:
        return label + " 행: " + "".join(f"「{k}」" for k in keys)
    return label


def cover(docs, sel):
    """선택자·원천의 덮는 범위(줄 번호 집합)와 오류 사유. 대응표 원천의 item·row도 같은 규칙이다."""
    d = docs.get(sel.get("doc"))
    if d is None:
        return None, f"문서가 없습니다: {sel.get('doc')}"
    sec = sel.get("section")
    if sec is None:
        return set(range(len(d.lines))), None
    hits = d.find(sec)
    if not hits:
        return None, f"절이 없습니다: {sel['doc']} 「{sec}」"
    if len(hits) > 1:
        return None, f"같은 제목의 절이 둘 이상입니다: {sel['doc']} 「{sec}」"
    items = sel.get("items") or ([sel["item"]] if sel.get("item") else None)
    rows = sel.get("rows") or ([sel["row"]] if sel.get("row") else None)
    if items and rows:
        return None, f"items와 rows를 함께 두었습니다: {sel_label(sel)}"
    if items:
        found, out = d.items(sec), set()
        for k in items:
            if k not in found:
                return None, f"절 자신의 본문에 항목이 없습니다: {sel['doc']} 「{sec}」 항목 「{k}」"
            for a, b in found[k]:
                out |= set(range(a, b))
        return out, None
    if rows:
        found, out = d.rows(sec), set()
        for k in rows:
            if k not in found:
                return None, f"절 자신의 본문에 행이 없습니다: {sel['doc']} 「{sec}」 행 「{k}」"
            out |= set(found[k])
        return out, None
    a, b = d.whole_range(sec)
    return set(range(a, b)), None


def strip_heading_tags(lines):
    out, fence = [], False
    for line in lines:
        if line.startswith("```"):
            fence = not fence
        out.append(TAG_RE.sub("", line) if (not fence and HEAD_RE.match(line)) else line)
    return out


def selector_text(docs, sel):
    """선택자가 고른 원천 글자. 절은 그대로(끝의 빈 줄·구분선 제외), 항목은 고른 항목, 행은 표 머리 줄·구분 줄과 고른 행."""
    d = docs.get(sel["doc"])
    sec = sel.get("section")
    items, rows = sel.get("items"), sel.get("rows")
    if items:
        found = d.items(sec)
        ranges = sorted({r for k in items for r in found[k]})
        chunks, prev_end = [], None
        for a, b in ranges:
            if prev_end is not None:
                chunks.append("" if a > prev_end else None)
            chunks.extend(d.lines[a:b])
            prev_end = b
        return "\n".join(strip_heading_tags([c for c in chunks if c is not None]))
    if rows:
        found = d.rows(sec)
        picked = sorted({i for k in rows for i in found[k]})
        tables = {}
        for i in picked:
            j = i
            while j > 0 and d.lines[j - 1].startswith("|"):
                j -= 1
            tables.setdefault(j, []).append(i)
        parts = []
        for j in sorted(tables):
            block = []
            if j + 1 < len(d.lines) and ROW_SEP_RE.match(d.lines[j + 1]) and j not in tables[j]:
                block += [d.lines[j], d.lines[j + 1]]
            block += [d.lines[i] for i in tables[j]]
            parts.append("\n".join(block))
        return "\n\n".join(parts)
    a, b = d.whole_range(sec) if sec is not None else (0, len(d.lines))
    lines = d.lines[a:b]
    while lines and lines[-1].strip() in ("", "---"):
        lines.pop()
    return "\n".join(strip_heading_tags(lines))


# ---------------------------------------------------------------- 조직 표와 표 읽기

def split_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def first_table(doc, name, need):
    """절 자신의 본문에서 머리 칸에 need가 모두 있는 첫 표를 [{머리: 값}]으로 돌려준다."""
    r = doc.own_range(name) if doc else None
    if r is None:
        return None
    s, e = r
    head, rows = None, []
    for i in range(s, e):
        line = doc.lines[i]
        if not line.startswith("|"):
            if head is not None and rows:
                break
            if head is not None and not line.strip():
                continue
            continue
        if ROW_SEP_RE.match(line):
            continue
        cells = split_cells(line)
        if head is None:
            if all(n in cells for n in need):
                head = cells
            continue
        rows.append(dict(zip(head, cells)))
    return rows if head else None


def org_table(docs):
    """02 「조직 표」: [(코드, {부, 팀, 팀 폴더, 파트, 주요 업무, 상태})](표 순서)."""
    rows = first_table(docs.get(ORG_DOC_REL), "조직 표", ("부", "팀", "팀 폴더", "코드", "파트", "주요 업무", "상태"))
    if rows is None:
        raise SourceError(f"{ORG_DOC_REL} 「조직 표」에서 부·팀·팀 폴더·코드·파트·주요 업무·상태 열이 있는 표를 찾지 못했습니다")
    out = []
    for r in rows:
        out.append((r["코드"], {"부": r["부"], "팀": r["팀"], "팀 폴더": r["팀 폴더"].strip("`"), "파트": r["파트"],
                               "주요 업무": r["주요 업무"], "상태": r["상태"]}))
    return out


def subagent_parts(docs):
    """02 「조직 표」 「파트의 일을 맡는 세션」 항목의 서브에이전트 파트 코드 목록."""
    d = docs.get(ORG_DOC_REL)
    r = d.own_range("조직 표") if d else None
    if r is None:
        return None
    text = "\n".join(d.lines[r[0]:r[1]])
    m = re.search(r"서브에이전트 파트\(([A-Z0-9, ]+)\)", text)
    return [c.strip() for c in m.group(1).split(",")] if m else None


def dept_folders(docs):
    """AGENTS.md 「조직·구역과 권한 한계」 조직 표의 {부서: Departments/ 아래 폴더 이름}."""
    rows = first_table(docs.get(AGENTS_REL), "조직·구역과 권한 한계", ("부서", "폴더"))
    if rows is None:
        raise SourceError(f"{AGENTS_REL} 「조직·구역과 권한 한계」에서 부서·폴더 열이 있는 표를 찾지 못했습니다")
    out = {}
    for r in rows:
        m = re.fullmatch(r"`?Departments/([^/`]+)/?`?", r["폴더"])
        if m:
            out[r["부서"]] = m.group(1)
    return out


# ---------------------------------------------------------------- 안전장치 핵심 (04 「계층형 지침」 4항)

def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _item_extent(lines, i):
    """목록 항목 i와 그 하위 줄(더 깊이 들여쓴 줄. 사이의 빈 줄 포함)의 끝(제외)."""
    base, end, j = _indent(lines[i]), i + 1, i + 1
    while j < len(lines):
        line = lines[j]
        if line.strip():
            if _indent(line) <= base:
                break
            end = j + 1
        j += 1
    return end


def extract_safety(text):
    """원천 글자에서 (갱신 표기, 항목 이름 목록, 추출 글자)를 돌려준다. 찾지 못한 이름이 있으면 SourceError."""
    lines = text.replace("\r\n", "\n").split("\n")
    mark = UPDATE_MARK_RE.search(text)
    if not mark:
        raise SourceError("전역 지침에서 갱신 표기([갱신: …])를 찾지 못했습니다")
    start = next((i for i, ln in enumerate(lines) if re.match(r"^\s*[*-] 불변 예외:", ln)), None)
    if start is None:
        raise SourceError("전역 지침에서 「불변 예외:」로 시작하는 목록 항목을 찾지 못했습니다")
    names = []
    for ln in lines[start + 1:_item_extent(lines, start)]:
        m = re.match(r"^\s+[*-] .*?「(.+?)」", ln)
        if m:
            names.append(m.group(1))
    if not names:
        raise SourceError("「불변 예외:」 항목 아래에서 「…」로 적은 항목 이름을 찾지 못했습니다")
    heads, fence = [], False
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            fence = not fence
            continue
        m = HEAD_RE.match(ln)
        if m and not fence:
            heads.append((i, len(m.group(1)), m.group(2)))
    blocks = []
    for name in names:
        hit = next(((i, lv) for i, lv, t in heads if 2 <= lv <= 4 and name in t), None)
        if hit:
            i, lv = hit
            end = next((j for j, lv2, _ in heads if j > i and lv2 <= lv), len(lines))
            block = lines[i:end]
        else:
            k = next((j for j, ln in enumerate(lines) if re.match(r"^\s*[*-] " + re.escape(name) + ":", ln)), None)
            if k is None:
                raise SourceError(f"불변 예외 항목 「{name}」을 제목이나 목록 항목에서 찾지 못했습니다")
            block = lines[k:_item_extent(lines, k)]
        while block and not block[-1].strip():
            block.pop()
        blocks.append("\n".join(block))
    return mark.group(0), names, "\n\n".join(blocks)


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safety_from_global(path):
    """--global-source 파일로 안전장치 핵심 글자를 만든다."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise SourceError(f"--global-source 파일을 읽을 수 없습니다: {path} ({type(e).__name__}: {e})")
    mark, names, body = extract_safety(text)
    basis_m = BASIS_RE.search(text)
    basis = basis_m.group(1).strip() if basis_m else str(path)
    head = f"<!-- 원천: 사용자 전역 지침, 갱신 표기 {mark}, 추출 SHA-256 {sha256(body)}, 생성 근거 {basis} -->"
    return "\n".join([MARKER, head, SAFETY_INTRO, "", body]) + "\n"


def parse_safety(text):
    """안전장치 핵심 생성물을 (갱신 표기, 추출 SHA-256, 본문, 카드에 넣을 덩어리)로 읽는다. 형식이 틀리면 None."""
    lines = text.replace("\r\n", "\n").split("\n")
    if len(lines) < 4 or lines[0] != MARKER:
        return None
    m = SAFETY_HEAD_RE.match(lines[1])
    if not m or lines[2] != SAFETY_INTRO:
        return None
    body = "\n".join(lines[3:]).strip("\n")
    block = "\n".join(lines[1:]).rstrip("\n")
    return {"mark": m.group(1), "sha": m.group(2), "basis": m.group(3), "body": body, "block": block}


# ---------------------------------------------------------------- 생성

class Generated:
    def __init__(self):
        self.files = {}  # --out 기준 경로 → bytes
        self.errors = []  # (검사 번호, 원인)
        self.budgets = []  # (계층, 이름, 글자 수, 상한)
        self.sources = {}  # sel_label → (doc, section, sha256)
        self.safety = None


def render_layer(docs, sels, gen, where):
    """선택자 목록을 출처 줄과 원천 글자 덩어리로 만들고 (글자, 본문 글자 수)를 돌려준다."""
    blocks, chars = [], 0
    for sel in sels:
        lines, err = cover(docs, sel)
        if lines is None:
            gen.errors.append(("C2", f"{where}: {err}"))
            continue
        text = selector_text(docs, sel)
        chars += len(text)
        label = sel_label(sel)
        gen.sources.setdefault(label, (sel["doc"], sel.get("section"), sha256(text)))
        blocks.append(f"<!-- 원천: {label} -->\n{text}")
    if not blocks:
        return "<!-- 이 계층에 고른 원천이 없다 -->", 0
    return "\n\n".join(blocks), chars


def refs_text(refs):
    seen, lines = set(), []
    for r in refs:
        key = (r.get("doc"), r.get("section"))
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- `{r['doc']}`" + (f" 「{r['section']}」" if r.get("section") else ""))
    return f"# {REFS_TITLE}\n\n" + "\n".join(lines) if lines else ""


def yaml_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def check_layout(docs, gl, org, pm, gen):
    """배치 규칙 ③(중복)·④(누락), 제외 절과의 겹침, 조직 표와 구성표의 대응(04 「계층형 지침」 3항)."""
    excluded = []
    for ex in gl.get("excluded_sections", []):
        lines, err = cover(docs, ex)
        if lines is None:
            gen.errors.append(("C2", f"excluded_sections: {err}"))
        else:
            excluded.append((ex["doc"], lines, ex.get("section")))
    layers = {"standard": gl.get("standard", [])}
    for kind, key in (("부", "depts"), ("팀", "teams"), ("파트", "parts")):
        for name, ent in gl.get(key, {}).items():
            layers[f"{kind}:{name}"] = ent.get("select", [])
    resolved = {}
    for lname, sels in layers.items():
        resolved[lname] = []
        for s in sels:
            lines, err = cover(docs, s)
            if lines is None:
                continue  # 사유는 생성(render_layer)이 C2로 낸다
            for doc, ex, exname in excluded:
                if doc == s["doc"] and lines & ex:
                    gen.errors.append(("C2", f"{lname}: 선택자 {sel_label(s)}의 덮는 범위가 제외 절 {doc} 「{exname}」과 겹칩니다"))
            resolved[lname].append((s, lines))
    codes = [c for c, _ in org]
    info = dict(org)
    for c in codes:
        if c not in gl.get("parts", {}):
            gen.errors.append(("C4", f"구성표 parts에 조직 표의 파트 {c}가 없습니다"))
    for c in gl.get("parts", {}):
        if c not in info:
            gen.errors.append(("C4", f"구성표 parts에 조직 표 밖 코드 {c}가 있습니다"))
    for d in sorted({v["부"] for v in info.values() if v["부"] != NO_DEPT}):
        if d not in gl.get("depts", {}):
            gen.errors.append(("C4", f"구성표 depts에 조직 표의 부 {d}가 없습니다"))
    for t in sorted({v["팀"] for v in info.values() if v["팀"] != NO_TEAM}):
        if t not in gl.get("teams", {}):
            gen.errors.append(("C4", f"구성표 teams에 조직 표의 팀 {t}가 없습니다"))

    def chain(code):
        v = info[code]
        ch = ["standard"]
        if f"부:{v['부']}" in resolved:
            ch.append(f"부:{v['부']}")
        if f"팀:{v['팀']}" in resolved:
            ch.append(f"팀:{v['팀']}")
        if f"파트:{code}" in resolved:
            ch.append(f"파트:{code}")
        return ch

    seen_msgs = set()
    for code in codes:
        items = [(l, s, lines) for l in chain(code) for s, lines in resolved[l]]
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                if a[1]["doc"] == b[1]["doc"] and a[2] & b[2]:
                    msg = f"배치 규칙 ③ 중복: {a[0]} {sel_label(a[1])} / {b[0]} {sel_label(b[1])}"
                    if msg not in seen_msgs:
                        seen_msgs.add(msg)
                        gen.errors.append(("C4", f"{msg} (파트 {code}의 사슬)"))

    def refs_of(code):
        v = info[code]
        out = list(gl.get("parts", {}).get(code, {}).get("refs", []))
        out += gl.get("depts", {}).get(v["부"], {}).get("refs", [])
        out += gl.get("teams", {}).get(v["팀"], {}).get("refs", [])
        return out

    missing = set()
    for st in (pm or {}).get("steps", []):
        for code in st.get("parts", []):
            if code not in info:
                continue
            sels = [(s, lines) for l in chain(code) for s, lines in resolved[l]]
            rfs = refs_of(code)
            for rd in st.get("reads", []):
                doc, sec = rd.get("doc"), rd.get("section")
                ok = False
                if sec is None:
                    ok = any(r.get("doc") == doc and "section" not in r for r in rfs)
                else:
                    d = docs.get(doc)
                    wr = d.whole_range(sec) if d else None
                    if wr is None:
                        gen.errors.append(("C4", f"프로세스 맵 단계 {st.get('id')}의 reads 절이 없습니다: {doc} 「{sec}」"))
                        continue
                    target = set(range(*wr))
                    for s, lines in sels:
                        if s["doc"] != doc:
                            continue
                        if "items" not in s and "rows" not in s and target <= lines:
                            ok = True
                        if ("items" in s or "rows" in s) and s.get("section") == sec:
                            ok = True
                    for r in rfs:
                        if r.get("doc") != doc:
                            continue
                        if "section" not in r:
                            ok = True
                        else:
                            rr = d.whole_range(r["section"])
                            if rr and target <= set(range(*rr)):
                                ok = True
                if not ok:
                    missing.add((code, doc, sec or ""))
    for code, doc, sec in sorted(missing):
        where = f"{doc} 「{sec}」" if sec else f"{doc}(파일 refs)"
        gen.errors.append(("C4", f"배치 규칙 ④ 누락: 파트 {code}의 사슬에 프로세스 맵 reads {where}가 실리지 않습니다"))


def load_json(source, rel, gen, code):
    text = read_text(source, rel)
    if text is None:
        gen.errors.append((code, f"파일이 없습니다: {rel}"))
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        gen.errors.append((code, f"JSON으로 읽히지 않습니다: {rel} ({e.msg}, {e.lineno}행)"))
        return None


def generate(source, global_source=None):
    """원천으로 생성물 전체를 메모리에서 만든다. 형상통제 대조(C2·C4)도 이 함수를 쓴다."""
    gen = Generated()
    docs = Docs(source)
    gl = load_json(source, LAYERS_REL, gen, "C2")
    pm = load_json(source, PROCESS_MAP_REL, gen, "C4")
    if gl is None:
        return gen
    org = org_table(docs)
    info = dict(org)
    folders = dept_folders(docs)

    # 안전장치 핵심
    if global_source:
        safety_text = safety_from_global(global_source)
    else:
        safety_text = read_text(source, GEN_ROOT + SAFETY_REL)
        if safety_text is None:
            gen.errors.append(("C2", f"안전장치 핵심({GEN_ROOT}{SAFETY_REL})이 없습니다. 처음 만들 때는 --global-source를 준다"))
            return gen
    safety = parse_safety(safety_text)
    if safety is None:
        gen.errors.append(("C3", f"안전장치 핵심({GEN_ROOT}{SAFETY_REL})의 머리 표시 형식이 맞지 않습니다({SOURCE_RULE} 4항)"))
        return gen
    gen.safety = safety
    gen.files[SAFETY_REL] = safety_text.encode("utf-8")
    gen.budgets.append(("전역", "안전장치 핵심", len(safety["body"]), gl["budgets"]["global"]))

    std_text, std_chars = render_layer(docs, gl.get("standard", []), gen, "standard")
    gen.budgets.append(("표준", "공통", std_chars, gl["budgets"]["standard"]))
    gen.files[STANDARD_REL] = f"{MARKER}\n\n# 표준 공통: 표준 공통 핵심\n\n{std_text}\n".encode("utf-8")

    dept_body, team_body = {}, {}
    for dept, ent in gl.get("depts", {}).items():
        text, chars = render_layer(docs, ent.get("select", []), gen, f"부:{dept}")
        dept_body[dept] = f"# 부 지침: {dept}\n\n{text}"
        gen.budgets.append(("부", dept, chars, gl["budgets"]["dept"]))
        folder = folders.get(dept)
        if folder is None:
            gen.errors.append(("C4", f"부 {dept}의 폴더를 {AGENTS_REL} 「조직·구역과 권한 한계」 표에서 찾지 못했습니다"))
            continue
        gen.files[f"guides/depts/{folder}.md"] = f"{MARKER}\n\n{dept_body[dept]}\n".encode("utf-8")
    team_folder = {v["팀"]: v["팀 폴더"] for v in info.values() if v["팀"] != NO_TEAM}
    for team, ent in gl.get("teams", {}).items():
        text, chars = render_layer(docs, ent.get("select", []), gen, f"팀:{team}")
        team_body[team] = f"# 팀 지침: {team}\n\n{text}"
        gen.budgets.append(("팀", team, chars, gl["budgets"]["team"]))
        if team not in team_folder:
            gen.errors.append(("C4", f"구성표 teams의 {team}가 조직 표에 없습니다"))
            continue
        gen.files[f"guides/teams/{team_folder[team]}.md"] = f"{MARKER}\n\n{team_body[team]}\n".encode("utf-8")

    for code, v in org:
        ent = gl.get("parts", {}).get(code)
        if ent is None:
            continue
        text, chars = render_layer(docs, ent.get("select", []), gen, f"파트:{code}")
        gen.budgets.append(("파트", code, chars, gl["budgets"]["part"]))
        if v["부"] in dept_body:
            upper = [dept_body[v["부"]]]
            if v["팀"] in team_body:
                upper.append(team_body[v["팀"]])
            refs = (gl["depts"][v["부"]].get("refs", []) + gl.get("teams", {}).get(v["팀"], {}).get("refs", [])
                    + ent.get("refs", []))
        else:
            upper = [f"# 부 지침·팀 지침\n\n{X01_NOTE}"]
            refs = list(ent.get("refs", []))
        part_block = f"# 파트 지침: {code}\n\n{text}"
        tail = refs_text(refs)
        title = f"# 파트 지침 묶음: {code} {v['파트']}"
        body = "\n\n".join(upper + [part_block] + ([tail] if tail else []))
        gen.files[f"guides/parts/{code}.md"] = f"{MARKER}\n\n{title}\n\n{body}\n".encode("utf-8")
        if ent.get("card"):
            desc = f"{v['부']} {v['팀']} {code} {v['파트']}: {v['주요 업무']}"
            front = "\n".join(["---", f"name: part-{code.lower()}", f"description: {yaml_quote(desc)}", "model: inherit",
                               "disallowedTools: Agent", "omitClaudeMd: true", "---"])
            card = "\n\n".join([f"# 전역 공통: 안전장치 핵심\n\n{safety['block']}",
                                f"# 표준 공통: 표준 공통 핵심\n\n{std_text}"] + upper + [part_block]
                               + ([tail] if tail else []))
            gen.files[f"agents/part-{code.lower()}.md"] = f"{front}\n{MARKER}\n\n{card}\n".encode("utf-8")

    check_layout(docs, gl, org, pm, gen)
    return gen


# ---------------------------------------------------------------- 쓰기와 기준선

def governance_target(root, out):
    """--out이 저장소 안의 거버넌스 경로·CEO/·_archive/ 안이면 그 경로를, 아니면 None을 돌려준다."""
    p = Path(out)
    p = (Path.cwd() / p) if not p.is_absolute() else p
    try:
        rel = p.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return None
    for g in cs.GOVERNANCE_PATHS:
        if rel == g or rel.startswith(g + "/"):
            return rel
    return None


def now_kst():
    return datetime.now(KST).replace(microsecond=0).isoformat()


def baseline_record(root, source, gen, record):
    """기준선 기록(05 「형상통제 절차」 2항)의 내용."""
    import check_config  # 기준선의 check(형상통제 대조 요약)는 대조 함수로 구한다. 서로 가져오므로 여기서 가져온다

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True)
    generated = [{"path": GEN_ROOT + rel, "sha256": hashlib.sha256(data).hexdigest()}
                 for rel, data in sorted(gen.files.items())]
    manifest = "".join(f"{g['path']} {g['sha256']}\n" for g in generated)
    summary = check_config.summary_for_baseline(root, source)
    return {
        "recorded_at": now_kst(),
        "record": record,
        "head": head.stdout.decode("ascii", "replace").strip() if head.returncode == 0 else "",
        "manifest_sha256": hashlib.sha256(manifest.encode("utf-8")).hexdigest(),
        "sources": [{"doc": d, "section": s, "sha256": h, "selector": k}
                    for k, (d, s, h) in sorted(gen.sources.items())],
        "generated": generated,
        "global": {"update_mark": gen.safety["mark"], "extract_sha256": gen.safety["sha"]} if gen.safety else None,
        "budget": [{"layer": l, "name": n, "chars": c, "limit": lim, "over": c > lim} for l, n, c, lim in gen.budgets],
        "check": summary,
    }


def print_errors(errors):
    for code, msg in errors:
        print(f"[FAIL] 생성 오류({code}): {msg}")
    print(f"       조치: 계층 구성표({LAYERS_REL})나 원천 절을 {SOURCE_RULE} 3항의 규칙에 맞게 고친 뒤 다시 실행한다. "
          "생성물은 쓰지 않았습니다.")


def parse_args(argv):
    if len(argv) < 2 or argv[0] != "--out":
        raise ValueError("--out <경로>를 첫 인자로 둡니다")
    opts = {"out": argv[1], "overlay": [], "global": None, "baseline": False, "record": None}
    i = 2
    while i < len(argv):
        a = argv[i]
        if a == "--overlay" and i + 1 < len(argv):
            opts["overlay"].append(argv[i + 1])
            i += 2
        elif a == "--global-source" and i + 1 < len(argv):
            opts["global"] = argv[i + 1]
            i += 2
        elif a == "--record" and i + 1 < len(argv):
            opts["record"] = argv[i + 1]
            i += 2
        elif a == "--baseline":
            opts["baseline"] = True
            i += 1
        else:
            raise ValueError(f"알 수 없는 인자: {a}")
    if opts["baseline"] and not opts["record"]:
        raise ValueError("--baseline에는 --record <기록 이름>이 필요합니다")
    if opts["baseline"] and opts["global"]:
        raise ValueError("--baseline에는 --global-source를 함께 주지 않습니다")
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except ValueError as e:
        print(f"[FAIL] 사용법 오류: {e}")
        print("       사용법: python build_guides.py --out <폴더> [--overlay <폴더>]… [--global-source <파일>]")
        print("               python build_guides.py --out <파일> --baseline --record <기록 이름> [--overlay <폴더>]…")
        return 2
    try:
        root = repo_root()
        cs.ROOT_DIR = root
        bad = governance_target(root, opts["out"])
        if bad:
            print(f"[FAIL] --out이 거버넌스 경로·CEO/·_archive/ 안이어서 쓰지 않습니다: {bad}")
            print(f"       조치: 적용본 폴더나 형상통제팀 작업 폴더를 --out으로 준다({COMMAND_RULE} 1항).")
            return 1
        source = WorkTreeSource(root, opts["overlay"])
        gen = generate(source, opts["global"])
    except SourceError as e:
        print(f"[FAIL] 원천을 읽을 수 없습니다: {e}")
        print("       조치: 경로와 파일을 확인하고, 해결되지 않으면 멈춰 보고하십시오.")
        return 2
    if gen.errors:
        print_errors(gen.errors)
        return 1
    out = Path(opts["out"])
    if opts["baseline"]:
        if out.exists():
            print(f"[FAIL] 기준선 기록이 이미 있어 쓰지 않습니다(작성 뒤 고치지 않음): {out}")
            print("       조치: 새 시각으로 기록 이름을 정해 다시 실행한다.")
            return 1
        try:
            data = baseline_record(root, source, gen, opts["record"])
        except SourceError as e:
            print(f"[FAIL] 기준선 기록을 만들 수 없습니다: {e}")
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"[PASS] 기준선 기록을 썼습니다: {out} (생성물 {len(data['generated'])}개, 원천 {len(data['sources'])}개, "
              f"형상통제 대조 오류 {data['check']['errors']}건)")
        return 0
    for rel, data in sorted(gen.files.items()):
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"[INFO] 원천: {source.describe()}" + (f", 안전장치 핵심 원천 {opts['global']}" if opts["global"] else ""))
    for layer, name, chars, limit in gen.budgets:
        if chars > limit:
            print(f"[INFO] 예산 초과 {layer} {name} {chars}/{limit}")
    print(f"[PASS] 생성물 {len(gen.files)}개를 썼습니다: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
