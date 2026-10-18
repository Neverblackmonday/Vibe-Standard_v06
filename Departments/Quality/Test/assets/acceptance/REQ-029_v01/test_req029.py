# -*- coding: utf-8 -*-
"""REQ-029 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상
- 현행 거버넌스 파일(REQ-029 5절 머리 안내): Workflow/ 전체와 check_standard.py에서, 적용본이 있는 파일은 적용본,
  없는 파일은 원본. 적용본은 개발 적용본(Departments/Development/workspace/REQ-029_적용본_vNN의 가장 높은 버전),
  설계 적용본(Departments/Design/workspace/REQ-029_적용본_vNN의 가장 높은 버전) 순으로 찾는다.
  적용본 안 경로는 경로 조각 끝의 `.적용본`을 떼어 원본 경로로 본다(Workflow/06 「거버넌스 파일 개정 절차」 2항).
- 규정의 위치는 EC-029_v02 3.1절이 정한 Workflow/03 3.1절 「다른 안건이 진행 중일 때의 REQ 작성」과
  4.1절 「원스톱 착수 조건」이다.
- Grep 확인은 제목이 「개정 이력」인 절을 뺀다(REQ-029 5절 머리 안내).

시험은 파일을 읽고 Git을 조회만 한다. 저장소 파일을 만들거나 고치지 않는다.
문장의 뜻(규정이 체크리스트의 뜻대로인지)은 최종 판정이 열람으로 본다(ACC-029 2절).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]

APPLIED_GLOB = "REQ-029_적용본_v[0-9][0-9]"
WORKFLOW = "Workflow"
SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"
INBOX_REL = "Departments/Secretariat/assets/inbox"
RUN_LOG_REL = "Departments/Secretariat/workspace/실행기록_REQ-029.md"

SEC_REQ = "다른 안건이 진행 중일 때의 REQ 작성"
SEC_ONESTOP = "원스톱 착수 조건"

# REQ-029 D13, 4절 「착수 조건」
REQ028_COMMIT = "a7d7c5605df2466c2bb14f8bbd05b4e4133a2df3"
REQ028_VERSION = "REQ-028_v04"

ORDER_NAME = re.compile(r"^ORD-\d{3}(?:-\d+)?_v\d{2}\.md$")
# 인수 시험 작성 때(2026-10-14T17:31:38+09:00 무렵) 이미 있던 ORDER 변경과 그 파일의 해시
# (`git diff --no-index --full-index /dev/null <파일>`의 index 줄 `..` 뒤 값). EC-029_v02 3.6절이 이 안건의 변경이 아니라고 본 것이다.
ORDER_BASELINE = {
    "ORD-007_v01.md": "6d6e6a23b0f3ea4e39a6b8b9cc34969ad5672724",
    "ORD-012_v06.md": "92319c5349664ba7affad3fbc4ea26af49ba2054",
}


# ---------------------------------------------------------------- 공통 도구

def _env():
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_PREFIX"):
        env.pop(key, None)
    # 조회가 .git/index를 고쳐 쓰지 않게 한다
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


ENV = _env()


def git(*args, check=True):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=REPO, capture_output=True, env=ENV)
    out = res.stdout.decode("utf-8", "replace")
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 실패({res.returncode}): {res.stderr.decode('utf-8', 'replace')}")
    return res.returncode, out


def _highest(folder, pattern):
    found = sorted(p for p in folder.glob(pattern) if p.is_dir())
    return found[-1] if found else None


def _opt_path(value):
    p = Path(value)
    return p if p.is_absolute() else REPO / p


def dev_dir(config):
    opt = config.getoption("--acc-dev-dir")
    if opt:
        return _opt_path(opt)
    return _highest(REPO / "Departments" / "Development" / "workspace", APPLIED_GLOB)


def design_dir(config):
    opt = config.getoption("--acc-design-dir")
    if opt:
        return _opt_path(opt)
    return _highest(REPO / "Departments" / "Design" / "workspace", APPLIED_GLOB)


def _applied_candidate(folder, rel):
    first, _, rest = rel.partition("/")
    return folder / (first + ".적용본") / rest


def current_path(config, rel):
    """원본 경로 rel(예: Workflow/03_라이프사이클.md)의 현행 파일."""
    for folder in (dev_dir(config), design_dir(config)):
        if folder is not None:
            cand = _applied_candidate(folder, rel)
            if cand.is_file():
                return cand
    return REPO / rel


def current_doc(config, rel):
    return current_path(config, rel).read_text(encoding="utf-8")


def original_doc(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def current_governance(config):
    """{원본 경로: 현행 내용}. Workflow/ 전체(적용본이 있으면 적용본)와 AGENTS.md(사본 대조 범위, EC-029 3.3절 6번)."""
    rels = sorted(p.relative_to(REPO).as_posix() for p in (REPO / WORKFLOW).rglob("*") if p.is_file())
    for folder in (dev_dir(config), design_dir(config)):
        if folder is None:
            continue
        base = folder / (WORKFLOW + ".적용본")
        if base.is_dir():
            for p in base.rglob("*"):
                if p.is_file():
                    rel = WORKFLOW + "/" + p.relative_to(base).as_posix()
                    if rel not in rels:
                        rels.append(rel)
    docs = {rel: current_path(config, rel).read_text(encoding="utf-8", errors="replace") for rel in rels}
    docs["AGENTS.md"] = original_doc("AGENTS.md")
    return docs


def strip_history(text):
    """제목이 「개정 이력」인 절을 뺀다."""
    out, skip = [], False
    for line in text.splitlines():
        if re.match(r"^## (\d+\. )?개정 이력\s*$", line):
            skip = True
            continue
        if skip and re.match(r"^#{1,2} ", line):
            skip = False
        if not skip:
            out.append(line)
    return "\n".join(out)


def section(text, heading_re):
    """heading_re에 맞는 제목부터 같은 수준 이상의 다음 제목 앞까지."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) ", line)
        if m and re.match(heading_re, line):
            level = len(m.group(1))
            body = [line]
            for nxt in lines[i + 1:]:
                m2 = re.match(r"^(#{1,6}) ", nxt)
                if m2 and len(m2.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    raise AssertionError(f"제목을 찾지 못했습니다: {heading_re}")


def item(sec_text, label):
    """번호 목록 항목 「N. **label**: …」과 그 아래 들여 쓴 줄."""
    lines = sec_text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^\d+\. \*\*" + re.escape(label) + r"\*\*", line):
            body = [line]
            for nxt in lines[i + 1:]:
                if re.match(r"^\d+\. ", nxt) or nxt.startswith("#") or (nxt and not nxt.startswith(" ")):
                    break
                body.append(nxt)
            return "\n".join(body)
    raise AssertionError(f"항목 「{label}」을 찾지 못했습니다")


def sec_req(config):
    d03 = strip_history(current_doc(config, "Workflow/03_라이프사이클.md"))
    return section(d03, r"^### 3\.1 " + re.escape(SEC_REQ))


def sec_onestop(config):
    d03 = strip_history(current_doc(config, "Workflow/03_라이프사이클.md"))
    return section(d03, r"^### 4\.1 " + re.escape(SEC_ONESTOP))


def must_contain(text, words, where):
    missing = [w for w in words if w not in text]
    assert not missing, f"{where}에 없는 문구: {missing}\n--- {where} ---\n{text[:1500]}"


# ---------------------------------------------------------------- 체크리스트 5 ①

def test_c5_1_overlap_rule_for_req_writing(pytestconfig):
    sec = sec_req(pytestconfig)
    must_contain(sec.splitlines()[0] + "\n" + "\n".join(sec.splitlines()[1:4]), ["이 절이 원천이다"], "03 3.1절 첫 문단")
    must_contain(item(sec, "대상"), ["REQ 작성 명령", "REQ 새 버전 명령"], "03 3.1절 「대상」 항")
    result = item(sec, "결과")
    must_contain(result, ["겹치지 않으면", "저장", "겹치면", "저장하지 않고"], "03 3.1절 「결과」 항")
    must_contain(item(sec, "재개"), ["진행 중이던 안건이 끝난 뒤"], "03 3.1절 「재개」 항")
    # 3절 1항이 3.1절을 가리킨다(EC-029 3.3절 2번)
    d03 = strip_history(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"))
    sec3 = section(d03, r"^## 3\. REQ 작성 파이프라인")
    first = [l for l in sec3.splitlines() if l.startswith("1. PM이 ORDER 경로를 받아")]
    assert len(first) == 1, first
    must_contain(first[0], ["저장하기 전에 3.1절"], "03 3절 1항 첫 문단")


# ---------------------------------------------------------------- 체크리스트 5 ②

def test_c5_2_in_progress_period(pytestconfig):
    body = item(sec_req(pytestconfig), "진행 중인 안건")
    must_contain(body, [
        "승인된 버전", "하나라도 생긴 때부터",
        "중단 조건으로 멈춰 대표님 결정을 기다리는 동안",
        "최종 판정 `pass` 뒤 승인·커밋을 기다리는 동안",
        "「문체 반영」으로 다시 실행하는 동안",
        "승인 뒤 원스톱 착수 전",
        "`Workflow/07_문서_서식_및_번호` 「종결 기록」",
    ], "03 3.1절 「진행 중인 안건」 항")
    # 2항이 가리키는 「승인 요건(구현)」이 현행 06에 있다
    d06 = strip_history(current_doc(pytestconfig, "Workflow/06_통제장치_및_배포.md"))
    assert "승인 요건(구현)" in d06


DEFINITION_PHRASES = ("가운데 하나에 해당하고 그 종결 기록이 커밋된 REQ·HOTFIX다",)


def test_c5_2_ended_definition_single_source(pytestconfig):
    hits = []
    for rel, text in current_governance(pytestconfig).items():
        for n, line in enumerate(strip_history(text).splitlines(), 1):
            for phrase in DEFINITION_PHRASES:
                if phrase in line:
                    hits.append((rel, n))
    assert len(hits) == 1 and hits[0][0] == "Workflow/07_문서_서식_및_번호.md", \
        f"「끝난」의 정의 문장은 Workflow/07 한 곳에만 있어야 합니다: {hits}"


# ---------------------------------------------------------------- 체크리스트 5 ③

def test_c5_3_judgement_stop_and_resume(pytestconfig):
    sec = sec_req(pytestconfig)
    must_contain(item(sec, "판단"), ["PM", "저장하기 전에", "`scope:`"], "03 3.1절 「판단」 항")
    must_contain(item(sec, "결과"), [
        "저장하지 않고", "`related_req`", "멈", "보고",
        "REQ마다 판단", "겹치지 않는 REQ는 저장",
    ], "03 3.1절 「결과」 항")
    must_contain(item(sec, "재개"), [
        "멈춘 명령과 같은 명령", "REQ 새 버전 명령", "같은 대상 REQ와 근거 파일",
        "REQ 작성 명령", "이미 저장된 REQ", "건너뛰",
        "저장할 때", "「번호」 항",
    ], "03 3.1절 「재개」 항")


# ---------------------------------------------------------------- 체크리스트 5 ④⑤

def test_c5_4_file_unit_overlap(pytestconfig):
    body = item(sec_req(pytestconfig), "겹침")
    must_contain(body, [
        "파일 단위", "「scope 일치 규칙」",
        "한쪽 폴더 항목 안에 다른 쪽 파일·폴더 항목이 있는 경우",
        "폴더 항목끼리 같거나 한쪽이 다른 쪽을 포함하는 경우",
    ], "03 3.1절 「겹침」 항")
    d06 = strip_history(current_doc(pytestconfig, "Workflow/06_통제장치_및_배포.md"))
    assert "**scope 일치 규칙**" in d06, "3.1절이 가리키는 06 「scope 일치 규칙」이 없습니다"


def test_c5_5_template_and_lifecycle_always_overlap(pytestconfig):
    body = item(sec_req(pytestconfig), "겹침")
    must_contain(body, ["`Workflow/templates/REQ_TEMPLATE.md`", "`Workflow/03_라이프사이클.md`",
                        "관계없이 겹친 것으로 본다"], "03 3.1절 「겹침」 항")


# ---------------------------------------------------------------- 체크리스트 5 ⑥

def test_c5_6_compare_with_ended_cases(pytestconfig):
    body = item(sec_onestop(pytestconfig), "끝난 안건과의 대조")
    must_contain(body, [
        "첫 단계 전", "작성한 뒤 끝난 안건",
        "`scope:`", "절의 제목이나 인용한 문구",
        "시작하지 않고 멈춰", "보고",
        "ORDER 새 버전", "REQ 새 버전 명령",
    ], "03 4.1절 「끝난 안건과의 대조」 항")


# ---------------------------------------------------------------- 체크리스트 5 ⑦

def test_c5_7_no_applied_check_standard(pytestconfig):
    found = []
    for folder in (dev_dir(pytestconfig), design_dir(pytestconfig)):
        if folder is not None and folder.is_dir():
            found += [p.relative_to(REPO).as_posix() if p.is_relative_to(REPO) else str(p)
                      for p in folder.rglob("check_standard.py")]
    assert not found, f"적용본 폴더에 check_standard.py가 있습니다(D6 권고안과 다름): {found}"


def test_c5_7_original_check_standard_unchanged():
    _, out = git("status", "--porcelain", "-uall", "--", SCRIPT_REL)
    assert not out.strip(), f"원본 check_standard.py가 바뀌었습니다:\n{out}"


def dev_result(config):
    opt = config.getoption("--acc-dev-result")
    path = _opt_path(opt) if opt else None
    if path is None:
        found = sorted((REPO / "Departments" / "Development" / "results").glob("DEV-029_v[0-9][0-9].md"))
        path = found[-1] if found else None
    if path is None or not path.is_file():
        pytest.fail("개발 결과서(Departments/Development/results/DEV-029_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
    return path.read_text(encoding="utf-8")


def test_c5_7_dev_result_records_comparison(pytestconfig):
    # EC-029_v02 5절 완료 기준 2(체크리스트 ⑦): DEV 「대조」 절에 check_standard.py·settings.json 대조가 있다
    text = dev_result(pytestconfig)
    lines = text.splitlines()
    parts = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and "대조" in m.group(2) and not any(d in m.group(2) for d in ("범위 대조", "사본 대조")):
            parts.append(section("\n".join(lines[i:]), re.escape(line) + "$"))
    assert parts, "개발 결과서에 제목에 「대조」가 든 절(범위 대조·사본 대조 제외)이 없습니다"
    must_contain("\n".join(parts), ["check_standard.py", "settings.json"], "개발 결과서 「대조」 절")


# ---------------------------------------------------------------- 체크리스트 5 ⑧

def test_c5_8_onestop_one_at_a_time(pytestconfig):
    sec = sec_onestop(pytestconfig)
    must_contain(sec.splitlines()[0] + "\n" + "\n".join(sec.splitlines()[1:4]), ["이 절이 원천이다"], "03 4.1절 첫 문단")
    must_contain(item(sec, "하나씩 실행"), [
        "하나씩 실행한다", "원스톱 실행 명령으로 첫 단계를 시작한 때부터", "끝날 때",
        "겹치든 겹치지 않든", "착수하지 않",
    ], "03 4.1절 「하나씩 실행」 항")
    must_contain(item(sec, "착수 순서"), [
        "승인되었고 착수하지 않은 안건", "서로의 착수를 막지 않",
        "ORDER 5절의 순서", "`approved:` 시각 순서",
    ], "03 4.1절 「착수 순서」 항")
    must_contain(item(sec, "클라우드 세션"), [
        "로컬 세션의 원스톱과 합쳐 하나씩 실행",
        "클라우드 Claude Code 도입 ORDER의 조사 결과로 다시 정할 때까지",
    ], "03 4.1절 「클라우드 세션」 항")
    # 4절 1항이 4.1절을 가리킨다(EC-029 3.3절 2번)
    d03 = strip_history(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"))
    sec4 = section(d03, r"^## 4\. 원스톱 파이프라인")
    first = [l for l in sec4.splitlines() if l.startswith("1. 오케스트레이터가 REQ 머리말")]
    assert len(first) == 1, first
    must_contain(first[0], ["4.1절의 착수 조건"], "03 4절 1항")


# ---------------------------------------------------------------- 체크리스트 5 ⑨

def _criterion2(text):
    sec5 = section(strip_history(text), r"^## 5\. ")
    rows = [l for l in sec5.splitlines() if l.startswith("2. **범위 대조**")]
    assert len(rows) == 1, rows
    return rows[0]


def _staging_item(text):
    sec11 = section(strip_history(text), r"^### 1\.1 ")
    lines = sec11.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("6. **스테이징**"):
            block = [line]
            for nxt in lines[i + 1:]:
                if re.match(r"^\d+\. ", nxt):
                    break
                block.append(nxt)
            return "\n".join(block).rstrip()
    raise AssertionError("05 1.1절 6번 「스테이징」을 찾지 못했습니다")


def test_c5_9_final_criterion2_unchanged(pytestconfig):
    rel = "Workflow/03_라이프사이클.md"
    assert _criterion2(current_doc(pytestconfig, rel)) == _criterion2(original_doc(rel)), \
        "03 5절 최종 판정 기준 2가 원본과 다릅니다(D8 권고안)"


def test_c5_9_staging_rule_unchanged(pytestconfig):
    rel = "Workflow/05_인수인계_및_실행명령.md"
    cur, orig = _staging_item(current_doc(pytestconfig, rel)), _staging_item(original_doc(rel))
    assert cur == orig, "05 1.1절 6번(②를 포함한 「스테이징」)이 원본과 다릅니다(D8 권고안)"


# ---------------------------------------------------------------- 체크리스트 5 ⑩

def test_c5_10_order_section5_relation(pytestconfig):
    must_contain(item(sec_req(pytestconfig), "ORDER 5절과의 관계"),
                 ["ORDER 5절의 착수 조건", "늦은 쪽", "바꾸지 않는다"], "03 3.1절 「ORDER 5절과의 관계」 항")
    tpl = current_doc(pytestconfig, "Workflow/templates/ORDER_TEMPLATE.md")
    sec5 = section(tpl, r"^## 5\. ")
    must_contain(sec5, [f"「{SEC_REQ}」", f"「{SEC_ONESTOP}」", "늦은 쪽"], "ORDER 서식 5절 안내")


def _blob(rel):
    _, out = git("diff", "--no-index", "--full-index", "/dev/null", rel, check=False)
    m = re.search(r"^index [0-9a-f]+\.\.([0-9a-f]{40})", out, re.M)
    assert m, f"{rel}의 해시를 얻지 못했습니다:\n{out[:300]}"
    return m.group(1)


def test_c5_10_issued_orders_unchanged(pytestconfig):
    baseline = {} if pytestconfig.getoption("--acc-no-order-baseline") else ORDER_BASELINE
    _, out = git("status", "--porcelain", "-uall", "--", INBOX_REL)
    problems = []
    for line in out.splitlines():
        if not line:
            continue
        code, paths = line[:2], line[3:]
        for rel in paths.split(" -> "):
            rel = rel.strip().strip('"')
            parent, _, name = rel.rpartition("/")
            if parent != INBOX_REL or not ORDER_NAME.match(name):
                continue
            if name in baseline:
                if not (REPO / rel).is_file():
                    problems.append(f"{code} {rel}: 기준값이 있는 ORDER가 없어졌습니다")
                elif _blob(rel) != baseline[name]:
                    problems.append(f"{code} {rel}: 인수 시험 작성 때의 내용과 다릅니다")
            elif code != "??":
                # 미추적 새 ORDER는 이미 발행된 ORDER의 변경이 아니다
                problems.append(f"{code} {rel}: 이미 발행된 ORDER가 바뀌었습니다")
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 5 ⑪⑫

def test_c5_11_own_new_version_excluded(pytestconfig):
    must_contain(item(sec_req(pytestconfig), "대상"),
                 ["진행 중인 안건 자신의 REQ 새 버전", "이 절의 대상이 아니"], "03 3.1절 「대상」 항")


def test_c5_12_application_timing_split(pytestconfig):
    must_contain(item(sec_req(pytestconfig), "적용 시점"), [
        "`REQ-029` 커밋 뒤에 REQ 작성 명령이나 REQ 새 버전 명령으로 기동하는 PM 세션부터",
        "소급해 판단하지 않는다", "이미 실행 중인 PM 세션은 기동 때의 규정으로 진행한다",
    ], "03 3.1절 「적용 시점」 항")
    must_contain(item(sec_onestop(pytestconfig), "적용 시점"), [
        "`REQ-029` 커밋 뒤에 원스톱 실행 명령으로 기동하는 PM 세션부터",
        "작성한 시점과 관계없이", "이미 실행 중인 PM 세션은 기동 때의 규정으로 진행한다",
    ], "03 4.1절 「적용 시점」 항")


# ---------------------------------------------------------------- 체크리스트 5 ⑬

POINTER_WORDS = ("REQ 작성 명령", "REQ 새 버전 명령", "원스톱 실행 명령", f"「{SEC_REQ}」", f"「{SEC_ONESTOP}」")
# 3.1·4.1절에만 있어야 할 규칙 문장의 조각(EC-029 3.3절 6번)
RULE_PHRASES = ("하나라도 생긴 때부터", "파일 단위로 보며", "겹치든 겹치지 않든",
                "이미 저장된 REQ를 확인해", "로컬 세션의 원스톱과 합쳐")


def test_c5_13_pm_pointers_in_02_and_05(pytestconfig):
    d02 = strip_history(current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"))
    rows = [l for l in section(d02, r"^### 2\.1 ").splitlines() if l.startswith("| PM ")]
    assert len(rows) == 1, rows
    pm6 = rows[0].split("⑥", 1)
    assert len(pm6) == 2, "02 2.1절 PM 책무에 ⑥이 없습니다"
    must_contain(pm6[1], POINTER_WORDS, "02 2.1절 PM 책무 ⑥")
    d05 = strip_history(current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"))
    lines = [l for l in section(d05, r"^## 3\. ").splitlines() if l.startswith("- PM은") and f"「{SEC_REQ}」" in l]
    assert len(lines) == 1, lines
    must_contain(lines[0], POINTER_WORDS, "05 3절의 PM 항목")
    # 가리키는 절이 현행 03에 있다
    sec_req(pytestconfig)
    sec_onestop(pytestconfig)


def test_c5_13_rule_sentences_single_source(pytestconfig):
    hits = {p: [] for p in RULE_PHRASES}
    for rel, text in current_governance(pytestconfig).items():
        for n, line in enumerate(strip_history(text).splitlines(), 1):
            for p in RULE_PHRASES:
                if p in line:
                    hits[p].append((rel, n))
    problems = [f"{p}: {h}" for p, h in hits.items()
                if not h or any(rel != "Workflow/03_라이프사이클.md" for rel, _ in h)]
    assert not problems, "규칙 문장이 없거나 Workflow/03 밖에 있습니다:\n" + "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 5 ⑭

def test_c5_14_run_log_records_req028_commit(pytestconfig):
    opt = pytestconfig.getoption("--acc-run-log")
    path = _opt_path(opt) if opt else REPO / RUN_LOG_REL
    assert path.is_file(), f"PM 실행 기록이 없습니다: {path}"
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 3 and cells[1] == "원스톱 시작":
            rows.append(cells[2])
    assert rows, "PM 실행 기록에 「원스톱 시작」 행이 없습니다"
    assert any(REQ028_COMMIT in r and REQ028_VERSION in r for r in rows), \
        f"「원스톱 시작」 행 「사건」 칸에 {REQ028_COMMIT}와 {REQ028_VERSION}가 함께 있는 행이 없습니다: {rows}"
    # 적힌 사실이 커밋 이력과 맞다(REQ-029 4절 「착수 조건」)
    _, msg = git("log", "-1", "--format=%B", REQ028_COMMIT)
    assert re.search(r"^Approved-REQ: Departments/Secretariat/docs/requests/" + REQ028_VERSION + r"\.md\s*$",
                     msg, re.M), msg
