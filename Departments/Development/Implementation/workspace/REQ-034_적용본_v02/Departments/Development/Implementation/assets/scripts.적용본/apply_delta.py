#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_delta.py - 변경 파일 적용본의 반영·출력·대조

규칙의 원천은 Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항(변경 파일, 블록과 지시)이고,
명령의 동작은 같은 문서 「생성·반영 명령」 2항이 정한다. 이 스크립트는 그 구현이다.
리비전 태그의 정규식은 Workflow/07_문서_서식_및_번호 「개정 이력과 리비전 태그」 절차 2를 따른다.

사용법: python apply_delta.py --print "<변경 파일>" "<원본>"   # 반영 결과를 출력만 한다
        python apply_delta.py --check "<변경 파일>" "<원본>"   # 바꾸지 않은 블록이 원본과 같은지 확인한다(종료 코드 0·1)
        python apply_delta.py --write "<변경 파일>" "<원본>"   # 원본에 쓴다(반영 명령 표에는 python -I 형태로 적는다)
종료 코드: 0 성공, 1 지시 오류·대조 불일치(원본을 쓰지 않음), 2 사용법 오류·파일을 읽지 못함
쓰는 곳은 --write의 원본 파일 하나뿐이다. 커밋·삭제·이동·Git 설정 변경을 하지 않는다.
"""

import re
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SOURCE = "Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항"
TAG_RE = re.compile(r"\s*\((REQ|HOTFIX)-\d{3}(-\d+)?_v\d{2}\)")
HEADING_RE = re.compile(r"^(#{1,6}) (.*)$")
NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
TABLE_SEP_RE = re.compile(r"^\|[\s:|-]+\|\s*$")
DIRECTIVE_RE = re.compile(r"^<!-- 변경: (?:(교체|뒤에 추가|삭제) 「(.+?)」|(머리)|(이력 추가)) -->\s*$")
HISTORY_BLOCK = "개정 이력"


class DeltaError(Exception):
    """변경 파일의 지시를 적용할 수 없는 사유(원본을 쓰지 않는다)."""


def block_name(title):
    """제목 글자에서 앞 번호와 리비전 태그를 뗀 블록 이름."""
    return NUMBER_RE.sub("", TAG_RE.sub("", title).strip()).strip()


def strip_tag(line):
    return TAG_RE.sub("", line)


def split_blocks(text):
    """원본을 [(블록 이름 또는 None(머리), 줄 목록)]으로 나눈다. 코드 울타리 안의 # 줄은 제목이 아니다."""
    lines = text.split("\n")
    heads, fence = [], False
    for i, line in enumerate(lines):
        if line.startswith("```"):
            fence = not fence
            continue
        m = HEADING_RE.match(line)
        if m and not fence and len(m.group(1)) <= 3:
            heads.append((i, len(m.group(1)), block_name(m.group(2))))
    first_h2 = next((i for i, lv, _ in heads if lv >= 2), len(lines))
    blocks = [[None, lines[:first_h2]]]
    starts = [(i, name) for i, _, name in heads if i >= first_h2]
    for n, (i, name) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        blocks.append([name, lines[i:end]])
    return blocks


def parse_delta(text):
    """변경 파일을 [(지시, 블록 이름, 내용 줄 목록)]으로 읽는다."""
    out, cur = [], None
    for line in text.split("\n"):
        m = DIRECTIVE_RE.match(line)
        if m:
            if cur:
                out.append(cur)
            if m.group(3):
                cur = ("머리", None, [])
            elif m.group(4):
                cur = ("이력 추가", None, [])
            else:
                cur = (m.group(1), m.group(2), [])
            continue
        if cur is None:
            if line.strip():
                raise DeltaError(f"첫 지시 줄 앞에 내용이 있습니다: {line[:60]}")
            continue
        cur[2].append(line)
    if cur:
        out.append(cur)
    if not out:
        raise DeltaError("변경 파일에 지시 줄(<!-- 변경: … -->)이 없습니다")
    return out


def trim(lines):
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def as_block(content, action, name):
    """교체·추가 내용을 블록 목록으로 나눈다. 제목 줄(H1~H3)로 시작하지 않으면 오류다."""
    body = trim(content)
    if not body:
        raise DeltaError(f"{action} 「{name}」의 내용이 비어 있습니다")
    m = HEADING_RE.match(body[0])
    if not m or len(m.group(1)) > 3:
        raise DeltaError(f"{action} 「{name}」의 내용이 제목 줄(H1~H3)로 시작하지 않습니다: {body[0][:60]}")
    parsed = split_blocks("\n".join(body))
    if any(parsed[0][1]):
        raise DeltaError(f"{action} 「{name}」의 내용이 제목 줄로 시작하지 않습니다")
    out = []
    for bname, blines in parsed[1:]:
        out.append([bname, trim(blines) + [""]])
    return out


def find_block(blocks, name):
    hits = [i for i, (bname, _) in enumerate(blocks) if bname == name]
    if not hits:
        raise DeltaError(f"원본에 블록 「{name}」이 없습니다")
    if len(hits) > 1:
        raise DeltaError(f"원본에 같은 이름의 블록 「{name}」이 {len(hits)}개 있습니다")
    return hits[0]


def apply(original, delta):
    """원본 글자에 변경 파일 글자를 적용한 결과와 (교체·추가된 블록 이름, 지운 블록 이름, 넣은 이력 행)을 돌려준다."""
    blocks = split_blocks(original)
    directives = parse_delta(delta)
    touched, deleted, history_rows = set(), set(), []
    head_replaced = False
    for action, name, content in directives:
        if action == "머리":
            body = trim(content)
            if body and HEADING_RE.match(body[0]) and len(HEADING_RE.match(body[0]).group(1)) >= 2:
                raise DeltaError("머리 내용이 H2 이하 제목으로 시작합니다(머리는 첫 H2 앞이다)")
            blocks[0][1] = body + [""]
            head_replaced = True
        elif action == "교체":
            i = find_block(blocks, name)
            new = as_block(content, action, name)
            blocks[i:i + 1] = new
            touched.update(b[0] for b in new)
        elif action == "뒤에 추가":
            i = find_block(blocks, name)
            new = as_block(content, action, name)
            if blocks[i][1] and blocks[i][1][-1].strip():
                blocks[i][1] = blocks[i][1] + [""]
            blocks[i + 1:i + 1] = new
            touched.update(b[0] for b in new)
        elif action == "삭제":
            if trim(content):
                raise DeltaError(f"삭제 「{name}」 뒤에 내용이 있습니다(삭제 지시에는 내용을 두지 않는다)")
            i = find_block(blocks, name)
            del blocks[i]
            deleted.add(name)
        else:  # 이력 추가
            rows = trim(content)
            if not rows or not all(r.strip().startswith("|") for r in rows):
                raise DeltaError("이력 추가 내용이 표의 행(|로 시작하는 줄)이 아닙니다")
            i = find_block(blocks, HISTORY_BLOCK)
            lines = blocks[i][1]
            sep = next((k for k, ln in enumerate(lines) if TABLE_SEP_RE.match(ln.strip())), None)
            if sep is None:
                raise DeltaError(f"블록 「{HISTORY_BLOCK}」에 표의 구분 줄이 없습니다")
            blocks[i][1] = lines[:sep + 1] + rows + lines[sep + 1:]
            history_rows.extend(rows)
    # 교체·추가하지 않은 블록의 제목 줄에서 리비전 태그를 지운다(이전 태그 제거. 07 절차 2)
    for k, (bname, lines) in enumerate(blocks):
        if bname is None:
            if not head_replaced:
                blocks[k][1] = [strip_tag(ln) if HEADING_RE.match(ln) else ln for ln in lines]
            continue
        if bname not in touched and lines:
            lines[0] = strip_tag(lines[0])
    result_lines = [ln for _, lines in blocks for ln in lines]
    while len(result_lines) > 1 and result_lines[-1] == "" and result_lines[-2] == "":
        result_lines.pop()
    result = "\n".join(result_lines)
    if not result.endswith("\n"):
        result += "\n"
    return result, (touched, deleted, history_rows)


def norm(lines):
    return trim([ln.rstrip() for ln in lines])


def check_untouched(original, result, info):
    """교체·추가·삭제하지 않은 블록이 결과에서 제목 줄의 리비전 태그를 뺀 나머지까지 원본과 같은지 대조한다."""
    touched, deleted, history_rows = info
    got = {}
    for name, lines in split_blocks(result):
        got.setdefault(name, []).append(lines)
    problems = []
    for name, lines in split_blocks(original):
        if name is None or name in touched or name in deleted:
            continue
        exp = norm([strip_tag(lines[0])] + lines[1:]) if lines else []
        cands = got.get(name, [])
        if len(cands) != 1:
            problems.append(f"블록 「{name}」이 결과에 {len(cands)}개 있습니다")
            continue
        have = norm(cands[0])
        if name == HISTORY_BLOCK:
            have = [ln for ln in have if ln not in [r.rstrip() for r in history_rows]] if history_rows else have
        if have != exp:
            problems.append(f"바꾸지 않은 블록 「{name}」이 원본과 다릅니다")
    return problems


def read_text(path):
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n")


def main(argv):
    if len(argv) != 3 or argv[0] not in ("--print", "--check", "--write"):
        print('[FAIL] 사용법: python apply_delta.py (--print | --check | --write) "<변경 파일>" "<원본>"')
        return 2
    mode, delta_path, orig_path = argv
    try:
        delta, original = read_text(delta_path), read_text(orig_path)
    except (OSError, UnicodeDecodeError) as e:
        print(f"[FAIL] 파일을 읽을 수 없습니다: {type(e).__name__}: {e}")
        print("       조치: 변경 파일과 원본의 경로를 확인하고 다시 실행하십시오.")
        return 2
    try:
        result, info = apply(original, delta)
    except DeltaError as e:
        print(f"[FAIL] 변경 파일을 반영할 수 없습니다: {delta_path} → {orig_path}")
        print(f"       원인: {e}")
        print(f"       조치: 변경 파일의 지시와 블록 이름을 원본의 현행 제목에 맞춰 고친다({SOURCE}). 원본은 쓰지 않았습니다.")
        return 1
    if mode == "--print":
        sys.stdout.write(result)
        return 0
    problems = check_untouched(original, result, info)
    if problems:
        print(f"[FAIL] 반영 결과의 대조가 맞지 않습니다: {delta_path} → {orig_path}")
        for p in problems:
            print(f"  - {p}")
        print(f"       조치: 변경 파일을 확인하고 멈춰 보고하십시오({SOURCE}). 원본은 쓰지 않았습니다.")
        return 1
    touched, deleted, rows = info
    if mode == "--check":
        print(f"[PASS] 변경 파일 대조: 바꾸지 않은 블록이 원본과 같습니다(교체·추가 {len(touched)}개, 삭제 {len(deleted)}개, "
              f"이력 행 {len(rows)}개). {delta_path} → {orig_path}")
        return 0
    Path(orig_path).write_text(result, encoding="utf-8", newline="\n")
    print(f"[PASS] 변경 파일을 반영했습니다: {delta_path} → {orig_path}(교체·추가 {len(touched)}개, 삭제 {len(deleted)}개, "
          f"이력 행 {len(rows)}개)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
