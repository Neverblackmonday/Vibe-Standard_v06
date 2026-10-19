#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_process_map.py - 프로세스 맵 연결·누락 검사(모델 매트릭스 칸 대조 포함)

규칙의 원천은 Workflow/03_라이프사이클 「프로세스 맵」(형식, 관리, 검사)과 Workflow/04_모델_운용 「단계별 모델」
(모델 매트릭스의 칸, 분류 집합, 허용 값)이다. 명령과 규칙 P1~P6, 종료 코드는 Workflow/06_통제장치_및_배포
「커밋 전 검사」의 「프로세스 맵 검사(구현)」가 정한다. 이 스크립트는 그 구현이며 파일을 읽기만 한다
(커밋·삭제·이동·파일 쓰기·Git 설정 변경을 하지 않는다).

사용법: python check_process_map.py [--workflow-dir <폴더>]
  --workflow-dir: Workflow/<상대 경로>로 적힌 파일을 그 폴더에서 먼저 찾고, 없으면 저장소의 Workflow/에서 찾는다
                  (설계 적용본으로 시험하기 위한 옵션). 그 폴더의 변경 파일(<이름>.변경.md)은 apply_delta.py의 함수로
                  저장소의 원본에 적용해 읽는다(Workflow/06 「생성·반영 명령」 2항. REQ-034)
종료 코드: 0 오류 없음, 1 오류 있음, 2 파일을 읽지 못함
커밋 전 검사(check_standard.py 순서 9)는 run_checks()를 불러 쓰며 결과를 [WARN]으로 바꿔 출력한다(커밋을 막지 않음).
"""

import json
import re
import subprocess
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard  # noqa: E402,F401  (가져올 때 표준 출력·오류 인코딩을 UTF-8로 고정한다)

PROCESS_MAP_REL = "Workflow/data/process_map.json"
MODEL_MATRIX_REL = "Workflow/data/model_matrix.json"
ORG_DOC_REL = "Workflow/02_부서_구조_및_작업구역.md"
MAP_SOURCE = "Workflow/03_라이프사이클 「프로세스 맵」"
MATRIX_SOURCE = "Workflow/04_모델_운용 「단계별 모델」"

# 형식의 원천: 03 「프로세스 맵」 1항, 04 「단계별 모델」 2·3항
ROLES = ("작성", "판정", "기록")
CLASSES = ("Critical", "Major", "Minor")
NO_CLASS = "분류 없음"
CLASS_KEYS = CLASSES + (NO_CLASS,)
NA = "해당 없음"
MODEL_VALUES = ("고급", "중급", "중급(시범)", "제한 없음", "활성 때 정함", NA)
EFFORT_VALUES = ("low", "medium", "high", "xhigh", "max", "정하지 않음", NA)
EFFORT_MEANS = ("호출 인자", "실행 단위", "정하지 않음")
TRACK_KEYS = ("id", "name", "starts", "source")
STEP_KEYS = ("id", "track", "name", "parts", "classes", "optional", "condition", "inputs", "outputs", "next",
             "source", "reads")
ARTIFACT_KEYS = ("id", "name")
CELL_KEYS = ("part", "role", "effort_means") + CLASSES

# 절 제목 비교: H2·H3 제목에서 앞 번호와 리비전 태그를 뗀 글자(03 「프로세스 맵」 1항의 section 정의)
HEADING = re.compile(r"^#{2,3} (?:\d+(?:\.\d+)*\.? )?(.*?)\s*$")
REVISION_TAG = re.compile(r"\s*\((?:REQ|HOTFIX)-\d{3}(?:-\d+)?_v\d{2}\)$")
DELTA_SUFFIX = ".변경.md"

ACTIONS = {
    "P1": f"데이터 파일의 키와 값을 {MAP_SOURCE} 1항·{MATRIX_SOURCE} 3항의 형식대로 고친다",
    "P2": f"next·starts·end를 {MAP_SOURCE} 1항대로 고친다(끊긴 단계는 앞 단계의 next로 잇는다)",
    "P3": "그 산출물을 내놓는 단계의 outputs에 넣거나 artifacts에서 external로 둔다",
    "P4": "parts를 Workflow/02_부서_구조_및_작업구역 「조직 표」의 코드로 고치고, 활성 파트는 맡는 단계에 넣는다",
    "P5": "source·reads를 매뉴얼의 현행 절 제목(앞 번호·리비전 태그 제외)으로 고치고, 단계마다 source와 outputs를 둔다",
    "P6": f"모델 매트릭스 칸을 프로세스 맵의 (파트, 역할)·분류 집합과 맞춘다({MATRIX_SOURCE} 3항)",
}


class LoadError(Exception):
    """검사에 필요한 파일을 읽지 못함(종료 코드 2)."""


def repo_root():
    """저장소 루트(git rev-parse --show-toplevel). 조회에 실패하면 LoadError."""
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True)
    if res.returncode != 0:
        raise LoadError("저장소 루트를 조회할 수 없습니다(git rev-parse --show-toplevel 실패): "
                        + res.stderr.decode("utf-8", "replace").strip())
    return Path(res.stdout.decode("utf-8").strip())


def _read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise LoadError(f"파일을 읽을 수 없습니다: {path} ({type(e).__name__}: {e})")


def file_reader(root, workflow_dir=None):
    """저장소 루트 기준 경로를 받아 텍스트(없으면 None)를 돌려주는 함수를 만든다.

    workflow_dir를 주면 Workflow/ 아래 경로를 그 폴더에서 먼저 찾는다(설계 적용본 시험용).
    그 폴더에 원본 대신 변경 파일(<이름>.변경.md)이 있으면 저장소의 원본에 적용한 결과를 읽는다(REQ-034).
    """
    root = Path(root)
    wf = Path(workflow_dir) if workflow_dir else None

    def read(rel):
        if wf is not None and rel.startswith("Workflow/"):
            sub = rel[len("Workflow/"):]
            if (wf / sub).is_file():
                return _read_file(wf / sub)
            delta = wf / (sub[:-len(".md")] + DELTA_SUFFIX) if sub.endswith(".md") else None
            if delta is not None and delta.is_file():
                base = root / rel
                if not base.is_file():
                    raise LoadError(f"변경 파일의 원본이 없습니다: {delta} → {rel}")
                # 변경 파일을 읽을 때만 가져온다(변경 파일이 없는 실행에는 필요 없다)
                import apply_delta
                try:
                    text, _ = apply_delta.apply(_read_file(base).replace("\r\n", "\n"),
                                                _read_file(delta).replace("\r\n", "\n"))
                except apply_delta.DeltaError as e:
                    raise LoadError(f"변경 파일을 적용할 수 없습니다: {delta} ({e})")
                return text
        path = root / rel
        return _read_file(path) if path.is_file() else None

    return read


def headings(text):
    found = set()
    for line in text.split("\n"):
        m = HEADING.match(line.rstrip("\r"))
        if m:
            found.add(REVISION_TAG.sub("", m.group(1)).strip())
    return found


def org_table(text):
    """02 「조직 표」 제목 아래 첫 Markdown 표의 {코드: 상태}. 표를 찾지 못하면 None."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if re.match(r"^#{2,3} .*조직 표", ln)), None)
    if start is None:
        return None
    header, rows = None, []
    for line in lines[start + 1:]:
        s = line.strip()
        if re.match(r"^#{1,3} ", line):
            break
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if header is None:
                header = cells
            elif not re.fullmatch(r"[\s:|-]+", s):
                rows.append(cells)
        elif header is not None:
            break
    if not header or "코드" not in header or "상태" not in header:
        return None
    ci, si = header.index("코드"), header.index("상태")
    return {r[ci]: r[si] for r in rows if len(r) > max(ci, si)}


def as_list(value):
    return value if isinstance(value, list) else []


def load_json(read, rel, errors):
    text = read(rel)
    if text is None:
        raise LoadError(f"파일이 없습니다: {rel}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        errors.append(("P1", rel, f"JSON으로 읽히지 않습니다({e.msg}, {e.lineno}행 {e.colno}열)"))
        return None


def check_ids(items, kind, errors):
    seen = set()
    for i, item in enumerate(items):
        ident = item.get("id") if isinstance(item, dict) else None
        if not isinstance(ident, str) or not ident:
            errors.append(("P1", f"{kind}[{i}]", "id가 비어 있지 않은 문자열이 아닙니다"))
            continue
        if ident in seen:
            errors.append(("P1", f"{kind}[{ident}]", "id가 겹칩니다"))
        seen.add(ident)


def check_format(pm, mm, errors):
    """P1. 형식이 틀린 항목은 errors에 넣고, 뒤 규칙이 읽을 수 있게 dict 항목만 돌려준다."""
    tracks, steps, artifacts, cells = [], [], [], []
    if pm is not None:
        if not isinstance(pm, dict):
            errors.append(("P1", PROCESS_MAP_REL, "최상위가 객체가 아닙니다"))
        else:
            for key in ("tracks", "steps", "artifacts"):
                if not isinstance(pm.get(key), list):
                    errors.append(("P1", PROCESS_MAP_REL, f"최상위 키 {key}가 목록이 아닙니다"))
            tracks = [t for t in as_list(pm.get("tracks")) if isinstance(t, dict)]
            steps = [s for s in as_list(pm.get("steps")) if isinstance(s, dict)]
            artifacts = [a for a in as_list(pm.get("artifacts")) if isinstance(a, dict)]
            for kind, items, keys in (("tracks", tracks, TRACK_KEYS), ("steps", steps, STEP_KEYS),
                                      ("artifacts", artifacts, ARTIFACT_KEYS)):
                check_ids(as_list(pm.get(kind)), kind, errors)
                for item in items:
                    missing = [k for k in keys if k not in item]
                    if missing:
                        errors.append(("P1", f"{kind}[{item.get('id')}]", f"필수 키가 없습니다: {', '.join(missing)}"))
            for list_key in ("parts", "classes", "inputs", "outputs", "next", "source", "reads"):
                for st in steps:
                    if list_key in st and not isinstance(st[list_key], list):
                        errors.append(("P1", f"steps[{st.get('id')}]", f"{list_key}가 목록이 아닙니다"))
            for st in steps:
                classes = as_list(st.get("classes"))
                if "classes" in st and not classes:
                    errors.append(("P1", f"steps[{st.get('id')}]", "classes가 빈 목록입니다"))
                bad = [c for c in classes if c not in CLASS_KEYS]
                if bad:
                    errors.append(("P1", f"steps[{st.get('id')}]", f"classes의 허용 밖 값: {bad}"))
            for a in artifacts:
                if a.get("external") is True and "location" in a:
                    errors.append(("P1", f"artifacts[{a.get('id')}]", "external인데 location이 있습니다"))
                if a.get("external") is not True and not a.get("location"):
                    errors.append(("P1", f"artifacts[{a.get('id')}]", "external이 아닌데 location이 없습니다"))
    if mm is not None:
        if not isinstance(mm, dict) or not isinstance(mm.get("cells"), list):
            errors.append(("P1", MODEL_MATRIX_REL, "최상위 키 cells가 목록이 아닙니다"))
        else:
            for i, cell in enumerate(mm["cells"]):
                if not isinstance(cell, dict):
                    errors.append(("P1", f"cells[{i}]", "칸이 객체가 아닙니다"))
                    continue
                missing = [k for k in CELL_KEYS if k not in cell]
                if missing:
                    errors.append(("P1", f"cells[{cell.get('part')}, {cell.get('role')}]",
                                   f"필수 키가 없습니다: {', '.join(missing)}"))
                cells.append(cell)
            keys = [(c.get("part"), c.get("role")) for c in cells]
            for key in sorted({k for k in keys if keys.count(k) > 1}, key=str):
                errors.append(("P1", f"cells[{key[0]}, {key[1]}]", "같은 (파트, 역할) 칸이 겹칩니다"))
    return tracks, steps, artifacts, cells


def check_links(tracks, steps, errors):
    """P2."""
    step_by_id = {s.get("id"): s for s in steps}
    track_ids = {t.get("id") for t in tracks}
    for t in tracks:
        starts = as_list(t.get("starts"))
        if not starts:
            errors.append(("P2", f"tracks[{t.get('id')}]", "starts가 비어 있습니다"))
        for sid in starts:
            if sid not in step_by_id:
                errors.append(("P2", f"tracks[{t.get('id')}]", f"starts의 단계 「{sid}」가 없습니다"))
            elif step_by_id[sid].get("track") != t.get("id"):
                errors.append(("P2", f"tracks[{t.get('id')}]", f"starts의 단계 「{sid}」의 track이 이 트랙이 아닙니다"))
    for s in steps:
        if s.get("track") not in track_ids:
            errors.append(("P2", f"steps[{s.get('id')}]", f"track 「{s.get('track')}」가 없습니다"))
        nxt = as_list(s.get("next"))
        for n in nxt:
            if n not in step_by_id:
                errors.append(("P2", f"steps[{s.get('id')}]", f"next의 단계 「{n}」가 없습니다"))
        if not nxt and s.get("end") is not True:
            errors.append(("P2", f"steps[{s.get('id')}]", "next가 비었는데 \"end\": true가 없습니다(끊긴 단계)"))
        if nxt and "end" in s:
            errors.append(("P2", f"steps[{s.get('id')}]", "next가 있는데 end가 있습니다"))
    seen, todo = set(), [sid for t in tracks for sid in as_list(t.get("starts"))]
    while todo:
        cur = todo.pop()
        if cur in seen or cur not in step_by_id:
            continue
        seen.add(cur)
        todo.extend(as_list(step_by_id[cur].get("next")))
    for s in steps:
        if s.get("id") not in seen:
            errors.append(("P2", f"steps[{s.get('id')}]", "어느 트랙의 starts에서도 next를 따라 닿지 않습니다"))


def check_artifacts(steps, artifacts, errors):
    """P3."""
    art_by_id = {a.get("id"): a for a in artifacts}
    produced = {o for s in steps for o in as_list(s.get("outputs"))}
    for s in steps:
        for key in ("inputs", "outputs"):
            for aid in as_list(s.get(key)):
                if aid not in art_by_id:
                    errors.append(("P3", f"steps[{s.get('id')}]", f"{key}의 산출물 「{aid}」가 artifacts에 없습니다"))
        for aid in as_list(s.get("inputs")):
            if aid in art_by_id and aid not in produced and art_by_id[aid].get("external") is not True:
                errors.append(("P3", f"steps[{s.get('id')}]",
                               f"입력 「{aid}」를 outputs로 내놓는 단계가 없고 external도 아닙니다"))


def check_parts(steps, org, errors):
    """P4."""
    used = set()
    for s in steps:
        parts = as_list(s.get("parts"))
        for p in parts:
            used.add(p)
            if p not in org:
                errors.append(("P4", f"steps[{s.get('id')}]", f"파트 {p}가 {ORG_DOC_REL} 「조직 표」에 없습니다"))
        if parts:
            if s.get("role") not in ROLES:
                errors.append(("P4", f"steps[{s.get('id')}]", f"role 「{s.get('role')}」가 {'·'.join(ROLES)} 가운데 하나가 아닙니다"))
            if "actor" in s:
                errors.append(("P4", f"steps[{s.get('id')}]", "파트가 있는 단계에 actor가 있습니다"))
        elif not s.get("actor"):
            errors.append(("P4", f"steps[{s.get('id')}]", "파트가 없는 단계에 actor가 없습니다"))
    for code, state in org.items():
        if state == "활성" and code not in used:
            errors.append(("P4", "steps", f"활성 파트 {code}가 어느 단계의 parts에도 없습니다(누락)"))
    return used


def check_sources(tracks, steps, read, errors):
    """P5."""
    cache = {}

    def check_ref(owner, ref):
        if not isinstance(ref, dict) or not isinstance(ref.get("doc"), str):
            errors.append(("P5", owner, f"원천 항목의 형식이 틀립니다: {ref}"))
            return
        doc = ref["doc"]
        if doc not in cache:
            text = read(doc)
            cache[doc] = None if text is None else headings(text)
        if cache[doc] is None:
            errors.append(("P5", owner, f"문서 {doc}가 없습니다"))
            return
        if "section" in ref and ref["section"] not in cache[doc]:
            errors.append(("P5", owner, f"{doc}에 절 제목 「{ref['section']}」가 없습니다"))

    for t in tracks:
        for ref in as_list(t.get("source")):
            check_ref(f"tracks[{t.get('id')}]", ref)
    for s in steps:
        owner = f"steps[{s.get('id')}]"
        source, reads = as_list(s.get("source")), as_list(s.get("reads"))
        for ref in source + reads:
            check_ref(owner, ref)
        if not source:
            errors.append(("P5", owner, "source가 없습니다(누락)"))
        if not as_list(s.get("outputs")):
            errors.append(("P5", owner, "outputs가 없습니다(누락)"))
        missing = [r for r in source if r not in reads]
        if missing:
            errors.append(("P5", owner, f"reads가 source의 항목을 포함하지 않습니다: {missing}"))


def class_sets(steps):
    """(파트, 역할)마다 그 묶음이 든 모든 단계의 classes 합집합(04 「단계별 모델」 3항의 분류 집합)."""
    sets = {}
    for s in steps:
        for p in as_list(s.get("parts")):
            sets.setdefault((p, s.get("role")), set()).update(c for c in as_list(s.get("classes")) if isinstance(c, str))
    return sets


def check_cells(steps, cells, errors):
    """P6."""
    sets = class_sets(steps)
    by_key = {}
    for c in cells:
        by_key.setdefault((c.get("part"), c.get("role")), c)
    for key in sorted(set(sets) - set(by_key), key=str):
        errors.append(("P6", f"cells[{key[0]}, {key[1]}]", "프로세스 맵에 있는 (파트, 역할)의 칸이 모델 매트릭스에 없습니다"))
    for key in sorted(set(by_key) - set(sets), key=str):
        errors.append(("P6", f"cells[{key[0]}, {key[1]}]", "프로세스 맵에 없는 (파트, 역할)의 칸이 모델 매트릭스에 있습니다"))
    for key in sorted(set(by_key) & set(sets), key=str):
        cell, cs = by_key[key], sets[key]
        loc = f"cells[{key[0]}, {key[1]}]"
        if cell.get("effort_means") not in EFFORT_MEANS:
            errors.append(("P6", loc, f"effort_means 「{cell.get('effort_means')}」가 허용 값이 아닙니다"))
        if (NO_CLASS in cell) != (NO_CLASS in cs):
            errors.append(("P6", loc, f"「{NO_CLASS}」 키가 {'있지만' if NO_CLASS in cell else '없지만'} "
                                      f"분류 집합 {sorted(cs)}와 맞지 않습니다"))
        for cls in CLASS_KEYS:
            if cls not in cell:
                if cls in CLASSES:
                    errors.append(("P6", loc, f"{cls} 키가 없습니다"))
                continue
            val = cell[cls]
            if not isinstance(val, dict):
                errors.append(("P6", loc, f"{cls} 값이 {{model, effort}} 객체가 아닙니다"))
                continue
            model, effort = val.get("model"), val.get("effort")
            if model not in MODEL_VALUES or effort not in EFFORT_VALUES:
                errors.append(("P6", loc, f"{cls} 값 {val}에 허용 밖 값이 있습니다"))
            if cls in cs:
                if model == NA or effort == NA:
                    errors.append(("P6", loc, f"{cls}는 분류 집합에 든 분류인데 「{NA}」입니다"))
            elif cls in CLASSES and not (model == NA and effort == NA):
                errors.append(("P6", loc, f"{cls}는 분류 집합에 들지 않은 분류인데 model·effort가 「{NA}」가 아닙니다"))


def run_checks(read):
    """규칙 P1~P6을 실행해 (오류 목록, 통계)를 돌려준다. 오류는 (규칙, 위치, 원인)이다.

    read는 저장소 루트 기준 경로를 받아 텍스트(없으면 None)를 돌려주는 함수다.
    데이터 파일이나 조직 표 문서를 읽지 못하면 LoadError를 낸다.
    """
    errors = []
    pm = load_json(read, PROCESS_MAP_REL, errors)
    mm = load_json(read, MODEL_MATRIX_REL, errors)
    org_text = read(ORG_DOC_REL)
    if org_text is None:
        raise LoadError(f"파일이 없습니다: {ORG_DOC_REL}")
    org = org_table(org_text)
    if org is None:
        raise LoadError(f"{ORG_DOC_REL}에서 「조직 표」 제목 아래 「코드」·「상태」 열이 있는 표를 찾지 못했습니다")
    tracks, steps, artifacts, cells = check_format(pm, mm, errors)
    used = set()
    if pm is not None:
        check_links(tracks, steps, errors)
        check_artifacts(steps, artifacts, errors)
        used = check_parts(steps, org, errors)
        check_sources(tracks, steps, read, errors)
        if mm is not None:
            check_cells(steps, cells, errors)
    stats = {"tracks": len(tracks), "steps": len(steps), "parts": len(used), "cells": len(cells)}
    return errors, stats


def format_error(err):
    rule, loc, cause = err
    return f"{rule} {loc}: {cause}. 조치: {ACTIONS[rule]}"


def main(argv):
    workflow_dir = None
    args = list(argv)
    if args[:1] == ["--workflow-dir"] and len(args) == 2:
        workflow_dir = args[1]
    elif args:
        print("[FAIL] 사용법: python check_process_map.py [--workflow-dir <폴더>]")
        return 2
    try:
        root = repo_root()
        if workflow_dir and not Path(workflow_dir).is_dir():
            raise LoadError(f"--workflow-dir 폴더가 없습니다: {workflow_dir}")
        if workflow_dir:
            print(f"[INFO] Workflow/ 아래 파일을 {workflow_dir}에서 먼저 찾고(변경 파일은 원본에 적용해 읽음), "
                  "없으면 저장소의 Workflow/에서 찾습니다.")
        errors, stats = run_checks(file_reader(root, workflow_dir))
    except LoadError as e:
        print(f"[FAIL] 프로세스 맵 검사: 파일을 읽지 못했습니다: {e}")
        print("       조치: 경로와 파일을 확인하고, 해결되지 않으면 대표님께 보고하십시오.")
        return 2
    for err in errors:
        print("[FAIL] " + format_error(err))
    if errors:
        print(f"[FAIL] 프로세스 맵 검사 오류 {len(errors)}건(원천: {MAP_SOURCE}, {MATRIX_SOURCE}).")
        return 1
    print(f"[PASS] 프로세스 맵 검사: 오류 0건(트랙 {stats['tracks']}개, 단계 {stats['steps']}개, "
          f"파트 {stats['parts']}개, 칸 {stats['cells']}개).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
