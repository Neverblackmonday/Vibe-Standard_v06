#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
resolve_model.py - 모델 매트릭스와 CEO 설정을 합친 유효 값 계산과 CEO 설정 검증

규칙의 원천은 Workflow/04_모델_운용 「단계별 모델」(4항 값의 읽는 법, 5항 분류, 6항 유효 값)과 「CEO 설정」
(파일 형식, 쓸 수 없는 칸, 하향 확인)이다. 등급의 모델 ID는 같은 문서 「모델 등급과 기본 모델」 표,
「활성 때 정함」 칸의 등급은 Workflow/03_라이프사이클 「분류별 단계」 표의 기본 모델 등급에서 읽는다.
명령의 동작(옵션, 출력, 종료 코드)은 Workflow/06_통제장치_및_배포 「준비·판단 명령」 4번이 정한다.
이 스크립트는 그 구현이며 파일을 읽기만 한다(커밋·삭제·이동·파일 쓰기·Git 설정 변경을 하지 않는다).

사용법: python resolve_model.py (--class <Critical|Major|Minor> | --hotfix) [--escalated]
                                [--approved-model <모델 ID>] [--approved-effort <값>] [--part <코드>] [--settings <경로>]
종료 코드: 0 계산 완료, 1 CEO 설정 오류(잘못된 옵션 포함), 2 모델 매트릭스·매뉴얼 표를 읽지 못함
"""

import argparse
import json
import re
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard as cs  # noqa: E402  (출력 인코딩 고정, 시각 형식 판단 approval_problem)
import check_process_map as cpm  # noqa: E402  (저장소 루트, 분류·값 상수)

SETTINGS_REL = "CEO/settings/model_settings.json"
MODEL_DOC_REL = "Workflow/04_모델_운용.md"
CLASS_DOC_REL = "Workflow/03_라이프사이클.md"
SOURCE = "Workflow/04_모델_운용 「단계별 모델」 6항과 「CEO 설정」"

# CEO 설정 파일 칸의 허용 값(04 「CEO 설정」 1항)
CEO_KEYS = {"part", "role", "class", "model", "model_id", "effort", "downgrade_confirmed_at"}
CEO_MODELS = ("최고급", "고급", "중급")
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# 등급의 높낮이. 격상(6항 ③)과 하향 판단(1.4절 4항)에 쓴다
GRADE_RANK = {"중급": 1, "고급": 2, "최고급": 3}
UNLIMITED = "제한 없음"
TRIAL = "중급(시범)"
LATER = "활성 때 정함"
# 6항 ④: 최종 판정(Q05)은 이 effort일 때만 승인 effort를 쓰고, REQ 작성 파이프라인 파트에는 쓰지 않는다
FINAL_JUDGE = "Q05"
FINAL_JUDGE_EFFORTS = ("high", "xhigh", "max")
REQ_PIPELINE_PARTS = ("P01", "Q01")


class ReadError(Exception):
    """모델 매트릭스나 매뉴얼 표를 읽지 못함(종료 코드 2)."""


class SettingsError(Exception):
    """CEO 설정 오류(종료 코드 1)."""


def table_after_heading(text, keyword):
    """제목에 keyword가 있는 H2·H3 절의 첫 Markdown 표를 (머리 칸, 행 목록)으로 돌려준다. 없으면 None."""
    lines = text.split("\n")
    start = next((i for i, ln in enumerate(lines) if re.match(r"^#{2,3} ", ln) and keyword in ln), None)
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
    return (header, rows) if header else None


def read_doc(root, rel):
    path = Path(root) / rel
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise ReadError(f"{rel}을 읽을 수 없습니다({type(e).__name__}: {e})")


def load_model_ids(root):
    """04 1.1절 표의 {등급: 기본 모델 ID}(최고급은 기본 모델이 없어 빠진다)."""
    table = table_after_heading(read_doc(root, MODEL_DOC_REL), "모델 등급과 기본 모델")
    ids = {}
    if table:
        for row in table[1]:
            m = re.search(r"`([^`]+)`", row[-1])
            if m:
                ids[row[0]] = m.group(1)
    if "고급" not in ids or "중급" not in ids:
        raise ReadError(f"{MODEL_DOC_REL} 「모델 등급과 기본 모델」 표에서 고급·중급의 기본 모델 ID를 읽지 못했습니다")
    return ids


def load_class_grades(root):
    """03 「분류별 단계」 표의 {분류: 기본 모델 등급}."""
    table = table_after_heading(read_doc(root, CLASS_DOC_REL), "분류별 단계")
    grades = {}
    if table and "분류" in table[0] and "기본 모델 등급" in table[0]:
        ci, gi = table[0].index("분류"), table[0].index("기본 모델 등급")
        grades = {r[ci]: r[gi] for r in table[1] if len(r) > max(ci, gi)}
    if any(grades.get(c) not in GRADE_RANK for c in cpm.CLASSES):
        raise ReadError(f"{CLASS_DOC_REL} 「분류별 단계」 표에서 분류별 기본 모델 등급을 읽지 못했습니다")
    return grades


def load_matrix(root):
    path = Path(root) / cpm.MODEL_MATRIX_REL
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ReadError(f"{cpm.MODEL_MATRIX_REL}을 읽을 수 없습니다({type(e).__name__}: {e})")
    cells = data.get("cells") if isinstance(data, dict) else None
    if not isinstance(cells, list) or not all(isinstance(c, dict) and "part" in c and "role" in c for c in cells):
        raise ReadError(f"{cpm.MODEL_MATRIX_REL}의 cells 형식이 틀립니다(check_process_map.py로 확인하십시오)")
    return cells


def valid_time(value):
    """YYYY-MM-DDTHH:MM:SS+09:00 형식의 실재하는 시각인지. 승인 필드와 같은 판단(check_standard.approval_problem)을 쓴다."""
    return isinstance(value, str) and cs.approval_problem({"approved": value}, "time") is None


def is_unusable(cell, cls):
    """쓸 수 없는 칸: 비서실 세션 파트(「제한 없음」)와 「해당 없음」 칸(04 「CEO 설정」 1항)."""
    val = cell.get(cls) or {}
    return cell.get("effort_means") == "정하지 않음" or val.get("model") in (UNLIMITED, cpm.NA)


def load_settings(path):
    """CEO 설정 파일을 읽는다. 없으면 None. JSON으로 읽히지 않으면 SettingsError."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise SettingsError(f"CEO 설정 파일이 JSON으로 읽히지 않습니다({type(e).__name__}: {e})")
    return data


def validate_settings(data, matrix):
    """CEO 설정을 검증해 {(파트, 역할, 분류): 칸 설정}을 돌려준다. 쓸 수 없는 칸은 [WARN]을 출력하고 뺀다."""
    problems = []
    if not isinstance(data, dict):
        raise SettingsError("CEO 설정 파일의 최상위가 객체가 아닙니다")
    if not valid_time(data.get("saved_at")):
        problems.append(f"saved_at 「{data.get('saved_at')}」가 YYYY-MM-DDTHH:MM:SS+09:00 형식의 실재하는 시각이 아닙니다")
    cells = data.get("cells")
    if not isinstance(cells, list):
        raise SettingsError("CEO 설정 파일의 cells가 목록이 아닙니다; " + "; ".join(problems))
    by_key = {(c["part"], c["role"]): c for c in matrix}
    usable, warnings = {}, []
    for i, item in enumerate(cells):
        loc = f"cells[{i}]"
        if not isinstance(item, dict):
            problems.append(f"{loc}: 칸이 객체가 아닙니다")
            continue
        loc = f"cells[{i}]({item.get('part')} {item.get('role')} {item.get('class')})"
        extra = sorted(set(item) - CEO_KEYS)
        if extra:
            problems.append(f"{loc}: 허용 밖 키 {extra}")
        cell = by_key.get((item.get("part"), item.get("role")))
        if cell is None:
            problems.append(f"{loc}: 모델 매트릭스에 없는 파트·역할입니다")
            continue
        cls = item.get("class")
        if cls not in cpm.CLASS_KEYS or cls not in cell:
            problems.append(f"{loc}: 그 칸에 없는 분류입니다")
            continue
        model, effort = item.get("model"), item.get("effort")
        if model is None and effort is None:
            problems.append(f"{loc}: model과 effort가 모두 없습니다")
        if model is not None and model not in CEO_MODELS:
            problems.append(f"{loc}: model 「{model}」가 허용 값({'·'.join(CEO_MODELS)})이 아닙니다")
        if effort is not None and effort not in EFFORTS:
            problems.append(f"{loc}: effort 「{effort}」가 허용 값({'·'.join(EFFORTS)})이 아닙니다")
        if model == "최고급" and not (isinstance(item.get("model_id"), str) and item["model_id"].strip()):
            problems.append(f"{loc}: 「최고급」에 model_id가 없습니다(최고급에는 기본 모델이 없음)")
        confirmed = item.get("downgrade_confirmed_at")
        if confirmed is not None and not valid_time(confirmed):
            problems.append(f"{loc}: downgrade_confirmed_at 「{confirmed}」가 시각 형식이 아닙니다")
        needs_confirm = model == "중급" and (cell.get("role") == "판정" or cls == "Critical")
        if needs_confirm and confirmed is None:
            problems.append(f"{loc}: 판정 역할이나 Critical 칸을 중급으로 두면서 downgrade_confirmed_at(확인 창의 확인 시각)이 없습니다")
        if is_unusable(cell, cls):
            warnings.append(f"{loc}: 쓸 수 없는 칸(비서실 세션 파트 또는 「해당 없음」 칸)이어서 이 설정을 쓰지 않습니다")
            continue
        usable[(cell["part"], cell["role"], cls)] = item
    if problems:
        raise SettingsError("; ".join(problems))
    for w in warnings:
        print(f"[WARN] {w}")
    return usable


def approved_grade(model_id, ids):
    """REQ 「결정」 열이 승인한 모델 ID의 등급. 1.1절 표의 기본 모델 ID가 아니면 최고급으로 본다."""
    for grade, mid in ids.items():
        if mid == model_id:
            return grade
    return "최고급"


def resolve_cell(cell, cls, args, ids, class_grades, settings):
    """칸 하나와 분류 하나의 (등급, 모델 ID, effort, 출처, 하향 확인 시각)을 04 1.2절 6항 순서로 구한다."""
    base = cell[cls]
    grade, effort, source, confirmed, model_id = base.get("model"), base.get("effort"), "기본값", None, None
    # ① 값의 읽는 법(4항)
    if grade == TRIAL:
        grade = "고급"
    elif grade == LATER:
        grade = class_grades[cls]
    # ② CEO 설정
    item = settings.get((cell["part"], cell["role"], cls))
    if item is not None:
        if item.get("model") is not None:
            grade = item["model"]
            model_id = item.get("model_id") if grade == "최고급" else None
            confirmed = item.get("downgrade_confirmed_at")
        if item.get("effort") is not None:
            effort = item["effort"]
        source = "CEO 설정"
    # ③ 격상: 고급 아래인 칸을 고급으로 올린다
    if args.escalated and GRADE_RANK.get(grade, 99) < GRADE_RANK["고급"]:
        grade, model_id, confirmed, source = "고급", None, None, "격상"
    # ④ REQ 「결정」 열의 승인(원스톱 파이프라인 세션. REQ 작성 파이프라인·비서실 세션·핫픽스에는 쓰지 않는다)
    applies = (cls in cpm.CLASSES and cell["part"] not in REQ_PIPELINE_PARTS
               and cell.get("effort_means") != "정하지 않음" and grade != UNLIMITED)
    if applies and args.approved_model:
        a_grade = approved_grade(args.approved_model, ids)
        final_ok = cell["part"] != FINAL_JUDGE or a_grade == "최고급"
        # 1.3절 5항: REQ 「결정」 열로는 Critical·Major를 중급으로 낮추지 않는다
        lowers = cls in ("Critical", "Major") and GRADE_RANK[a_grade] < GRADE_RANK["고급"]
        if final_ok and not lowers:
            grade, model_id, confirmed, source = a_grade, args.approved_model, None, "REQ 결정"
    if applies and args.approved_effort:
        if cell["part"] != FINAL_JUDGE or args.approved_effort in FINAL_JUDGE_EFFORTS:
            effort, source = args.approved_effort, "REQ 결정"
    if grade in ("고급", "중급") and model_id is None:
        model_id = ids[grade]
    return grade, model_id or "—", effort, source, confirmed


class OptionParser(argparse.ArgumentParser):
    """잘못된 옵션을 종료 코드 1로 끝낸다. argparse 기본값 2는 「모델 매트릭스·매뉴얼 표를 읽지 못함」과 겹치기 때문이다."""

    def error(self, message):
        self.print_usage(sys.stdout)
        print(f"[FAIL] 옵션 오류: {message}")
        print("       조치: Workflow/06_통제장치_및_배포 「준비·판단 명령」 4번의 사용법대로 다시 실행하십시오.")
        sys.exit(1)


def parse_args(argv):
    parser = OptionParser(prog="resolve_model.py", description="모델 매트릭스와 CEO 설정의 유효 값을 출력한다.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--class", dest="cls", choices=cpm.CLASSES)
    group.add_argument("--hotfix", action="store_true")
    parser.add_argument("--escalated", action="store_true")
    parser.add_argument("--approved-model")
    parser.add_argument("--approved-effort", choices=EFFORTS)
    parser.add_argument("--part")
    parser.add_argument("--settings")
    return parser.parse_args(argv)


def main(argv):
    args = parse_args(argv)
    cls = cpm.NO_CLASS if args.hotfix else args.cls
    try:
        root = cpm.repo_root()
        matrix = load_matrix(root)
        ids = load_model_ids(root)
        class_grades = load_class_grades(root)
    except (ReadError, cpm.LoadError) as e:
        print(f"[FAIL] 유효 값을 계산할 수 없습니다: {e}")
        print("       조치: 세션을 기동하지 말고 대표님께 보고하십시오.")
        return 2
    settings_path = Path(args.settings) if args.settings else root / SETTINGS_REL
    try:
        data = load_settings(settings_path)
        if data is None:
            print(f"[INFO] CEO 설정 파일: {settings_path} 없음(기본값)")
            settings = {}
        else:
            saved = data.get("saved_at") if isinstance(data, dict) else None
            print(f"[INFO] CEO 설정 파일: {settings_path} saved_at {saved if saved is not None else '없음'}")
            settings = validate_settings(data, matrix)
        if args.part and args.part not in {c["part"] for c in matrix}:
            raise SettingsError(f"--part {args.part}: 모델 매트릭스에 없는 파트입니다")
    except SettingsError as e:
        print(f"[FAIL] CEO 설정 오류: {e}")
        print(f"       원인: CEO 설정이 {SOURCE}의 형식·조건과 맞지 않습니다.")
        print("       조치: 세션을 기동하지 말고 대표님께 보고하십시오(대시보드에서 다시 저장하거나 새로고침).")
        return 1

    shown = skipped = 0
    for cell in matrix:
        if args.part and cell["part"] != args.part:
            continue
        if cls not in cell:
            continue  # --hotfix: 「분류 없음」 키가 없는 칸은 읽지 않는다
        if (cell[cls] or {}).get("model") == cpm.NA:
            skipped += 1
            continue
        grade, model_id, effort, source, confirmed = resolve_cell(cell, cls, args, ids, class_grades, settings)
        line = f"[INFO] {cell['part']} {cell['role']} {cls} 모델 {grade} {model_id} effort {effort} 출처 {source}"
        if confirmed:
            line += f" 하향 확인 {confirmed}"
        print(line)
        shown += 1
    if skipped:
        print(f"[INFO] 그 분류로 실행되지 않는 「{cpm.NA}」 칸 {skipped}개는 출력하지 않습니다.")
    print(f"[PASS] 유효 값 {shown}칸(분류 {cls}{', 격상' if args.escalated else ''}). 원천: {SOURCE}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
