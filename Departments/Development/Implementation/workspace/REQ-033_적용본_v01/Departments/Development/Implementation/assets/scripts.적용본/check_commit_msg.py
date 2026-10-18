#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_commit_msg.py - 바이브 코딩 표준 커밋 메시지 검사기 (commit-msg 훅)

규칙의 원천은 Workflow/07_문서_서식_및_번호 「번호와 버전」의 「커밋 메시지」(제목 줄, 근거 줄, 같은 안건의 여러 커밋,
근거 줄의 키와 트레일러, 첫 커밋 예외)와 같은 문서 「문서 체계」(근거 줄 경로의 위치·파일명)다.
검사의 동작(대상, 예외, 실패 출력)은 Workflow/06_통제장치_및_배포 「커밋 메시지 검사」가 정한다.
이 스크립트는 그 구현이며 메시지 파일과 Git 저장소를 읽기만 한다.
근거 줄 Model-Effort(실행 모델·effort 줄)는 경로가 아니며, 있을 때만 값의 형식을 확인한다(REQ-033).

사용법: python check_commit_msg.py <메시지 파일>   # .githooks/commit-msg가 "$1"을 넘긴다
종료 코드: 0 통과, 1 실패
"""

import re
import subprocess
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard as cs  # noqa: E402  (공통 기록 이름·Git 조회 함수)

ROOT_DIR = cs.ROOT_DIR
SOURCE = "Workflow/07_문서_서식_및_번호 「커밋 메시지」"

# 근거 줄의 키(Workflow/07 「커밋 메시지」의 「근거 줄의 키와 트레일러」). 키 목록은 이 상수 하나에 둔다
EVIDENCE_KEYS = ("Approved-REQ", "Approved-RES", "Approval-Record", "Style-Check-RES", "Confirmed-HOTFIX",
                 "Request-Record", "Follows", "Model-Effort")
# 경로가 아닌 근거 줄(Workflow/07 「커밋 메시지」의 「같은 안건의 여러 커밋」·「실행 모델·effort 줄」)
NON_PATH_KEYS = ("Follows", "Model-Effort")
# Model-Effort 값: <모델> / <effort>. 있을 때만 형식을 확인한다(Workflow/06 「커밋 메시지 검사」 5번). (REQ-033)
MODEL_EFFORT_SEP = " / "
EVIDENCE_LINE = re.compile(r"^(" + "|".join(EVIDENCE_KEYS) + r"): (.*)$")
# 제목 줄: <유형>: [<기록 이름>] <요약>. 기록 이름에는 버전을 적지 않는다
SUBJECT = re.compile(r"^[a-z]+: \[(REQ-" + cs.RECORD_NUMBER + r"|HOTFIX-\d{3}|CEO)\] \S.*$")
SUBJECT_RECORD = re.compile(r"^[a-z]+: \[(REQ-" + cs.RECORD_NUMBER + r"|HOTFIX-\d{3})\] ")
TRAILER = re.compile(r"^co-authored-by:", re.IGNORECASE)
SCISSORS = re.compile(r"^# -+ >8 -+$")
SHORT_HASH = re.compile(r"^[0-9a-f]{7,40}$")

# 커밋 종류별로 쓸 수 있는 키와 반드시 있어야 하는 키(Workflow/07 「커밋 메시지」 표와 「같은 안건의 여러 커밋」)
# Model-Effort는 어느 종류에서든 쓸 수 있고 필수가 아니다. 커밋한 주체를 메시지만으로 가릴 수 없기 때문이다
KIND_KEYS = {
    "REQ": ({"Approved-REQ", "Approved-RES", "Approval-Record", "Style-Check-RES", "Follows", "Model-Effort"},
            ("Approved-REQ", "Approved-RES", "Approval-Record")),
    "HOTFIX": ({"Confirmed-HOTFIX", "Request-Record", "Follows", "Model-Effort"}, ("Confirmed-HOTFIX",)),
    "CEO": ({"Request-Record", "Follows", "Model-Effort"}, ()),
}


def model_effort_problem(value):
    """Model-Effort 값의 형식이 틀리면 사유를, 맞으면 None을 돌려준다(경로로 보지 않는다)."""
    parts = value.split(MODEL_EFFORT_SEP)
    if not value:
        return "값이 비어 있습니다"
    if "<" in value or ">" in value:
        return "자리 표시(<·>)가 남아 있습니다. 커밋한 세션의 모델과 effort로 채웁니다"
    if len(parts) != 2 or not all(p.strip() for p in parts):
        return f"「<모델 ID 또는 모델 이름>{MODEL_EFFORT_SEP}<effort 또는 「확인 불가」>」 형식(앞뒤 공백 한 칸씩인 / 로 두 부분)이 아닙니다"
    return None


def path_rule(key, number):
    """근거 줄 키마다 경로가 맞아야 하는 위치·파일명 정규식(Workflow/07 「문서 체계」)을 돌려준다."""
    n = re.escape(number) if number else cs.RECORD_NUMBER
    return {
        "Approved-REQ": rf"^{re.escape(cs.REQ_DIR_REL)}/REQ-{n}_v\d{{2}}\.md$",
        "Approved-RES": rf"^Departments/Quality/Review/results/RES-{n}_v\d{{2}}\.md$",
        "Approval-Record": rf"^{re.escape(cs.CLOSE_DIR_REL)}/승인기록_\d{{8}}_RES-{n}_v\d{{2}}\.md$",
        "Style-Check-RES": rf"^Departments/Quality/Review/results/RES-{n}(?:-[A-Z]+)?_v\d{{2}}\.md$",
        "Confirmed-HOTFIX": rf"^{re.escape(cs.HOTFIX_DIR_REL)}/HOTFIX-{n}_v\d{{2}}\.md$",
        "Request-Record": rf"^{re.escape(cs.CLOSE_DIR_REL)}/요청기록_\d{{8}}_[^/]+\.md$",
    }[key]


def read_message(path):
    """메시지 파일을 읽어 (줄 번호, 줄) 목록을 돌려준다. #으로 시작하는 줄과 끝의 빈 줄은 뺀다."""
    text = Path(path).read_text(encoding="utf-8-sig")
    lines = []
    for no, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        if SCISSORS.match(line):
            break
        if line.startswith("#"):
            continue
        lines.append((no, line))
    while lines and not lines[-1][1].strip():
        lines.pop()
    return lines


def git_lines(args):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        return None, res.stderr.decode("utf-8", "replace").strip()
    return res.stdout.decode("utf-8", "replace"), None


def previous_commit(record, request_paths):
    """제목 줄 기록 이름이 같은 REQ·HOTFIX 커밋이나 Request-Record 경로가 같은 커밋 가운데 가장 최근 것의 해시.

    없으면 ""를, 조회에 실패하면 None을 돌려준다.
    """
    out, err = git_lines(["log", "--format=%H%x00%s%x00%b%x01", "HEAD"])
    if out is None:
        print(f"[FAIL] 이전 커밋을 조회할 수 없습니다: {err}")
        print("       조치: git log를 직접 실행해 오류를 해결한 뒤 다시 커밋하십시오.")
        return None
    for entry in out.split("\x01"):
        entry = entry.strip("\n")
        if not entry:
            continue
        sha, _, rest = entry.partition("\x00")
        subject, _, body = rest.partition("\x00")
        m = SUBJECT_RECORD.match(subject)
        if record and m and m.group(1) == record:
            return sha
        if request_paths:
            for line in body.split("\n"):
                em = EVIDENCE_LINE.match(line.rstrip("\r"))
                if em and em.group(1) == "Request-Record" and em.group(2).strip() in request_paths:
                    return sha
    return ""


def check_message(msg_path):
    """메시지를 검사해 실패 사유 목록을 돌려준다(빈 목록이면 통과). 조회 실패는 사유로 넣는다."""
    lines = read_message(msg_path)
    if not lines:
        return ["메시지가 비어 있습니다."]
    problems = []
    subject_no, subject = lines[0]
    m = SUBJECT.match(subject)
    if not m:
        return [f"{subject_no}행(제목 줄): 「<유형>: [<기록 이름>] <요약>」 형식이 아닙니다"
                "(기록 이름은 REQ-xxx, REQ-xxx-n, HOTFIX-xxx, CEO이며 버전을 적지 않습니다)."]
    record = m.group(1)
    kind = "CEO" if record == "CEO" else record.split("-", 1)[0]
    number = None if kind == "CEO" else record.split("-", 1)[1]
    body = lines[1:]
    if body and body[0][1].strip():
        problems.append(f"{body[0][0]}행: 제목 줄 다음 줄은 빈 줄이어야 합니다.")

    evidence, others = [], []
    for no, line in body:
        if not line.strip() or TRAILER.match(line):
            continue
        em = EVIDENCE_LINE.match(line)
        if em:
            evidence.append((no, em.group(1), em.group(2).strip()))
        else:
            others.append(no)

    # [CEO] 커밋은 근거 줄이 아닌 줄을 확인하지 않는다. 대표님 직접 커밋과 요청 커밋을 메시지로 가릴 수 없기 때문이다
    if kind != "CEO" and others:
        problems.append(f"{', '.join(map(str, others))}행: {kind} 커밋의 본문에는 근거 줄만 둡니다"
                        "(빈 줄과 Co-Authored-By 줄 제외).")

    allowed, required = KIND_KEYS[kind]
    seen = {}
    for no, key, value in evidence:
        if key not in allowed:
            problems.append(f"{no}행 {key}: {kind} 커밋에 쓰지 않는 근거 줄 키입니다(쓸 수 있는 키: {', '.join(sorted(allowed))}).")
            continue
        if key in seen:
            problems.append(f"{no}행 {key}: 같은 키가 {seen[key][0]}행에도 있습니다.")
            continue
        seen[key] = (no, value)
    for key in required:
        if key not in seen:
            problems.append(f"근거 줄 {key}가 없습니다({kind} 커밋의 필수 근거 줄).")
    if kind == "CEO" and "Follows" in seen and "Request-Record" not in seen:
        problems.append(f"{seen['Follows'][0]}행 Follows: [CEO] 커밋의 Follows는 Request-Record와 함께 씁니다.")

    in_index = cs.index_paths()
    if in_index is None:
        problems.append("index(커밋될 트리)를 조회할 수 없어 근거 줄 경로를 확인하지 못했습니다.")
        in_index = set()
    for key, (no, value) in seen.items():
        if key == "Model-Effort":
            problem = model_effort_problem(value)
            if problem:
                problems.append(f"{no}행 {key}: {problem}.")
            continue
        if key in NON_PATH_KEYS:
            continue
        if not value or " " in value or "\\" in value or value.startswith(("/", "..")):
            problems.append(f"{no}행 {key}: {value} - 저장소 루트 기준 상대 경로(/로 나눔)여야 합니다.")
            continue
        if not re.match(path_rule(key, number), value):
            problems.append(f"{no}행 {key}: {value} - 위치·파일명이 Workflow/07_문서_서식_및_번호 「문서 체계」 형식과 다릅니다.")
            continue
        if value not in in_index:
            problems.append(f"{no}행 {key}: {value} - 커밋될 트리(index)에 없는 경로입니다.")

    # Follows: 같은 REQ·HOTFIX·요청 기록의 이전 커밋이 있으면 그 가운데 가장 최근 커밋을 가리켜야 한다.
    # 근거 줄이 없는 [CEO] 커밋에는 요구하지 않는다
    if kind != "CEO" or seen:
        request_paths = {seen["Request-Record"][1]} if "Request-Record" in seen else set()
        prev = previous_commit(None if kind == "CEO" else record, request_paths)
        if prev is None:
            problems.append("이전 커밋을 조회하지 못해 Follows를 확인하지 못했습니다.")
        elif prev and "Follows" not in seen:
            problems.append(f"근거 줄 Follows가 없습니다(같은 안건의 이전 커밋 {prev[:7]}이 있습니다).")
        elif not prev and "Follows" in seen:
            problems.append(f"{seen['Follows'][0]}행 Follows: 같은 안건의 이전 커밋이 없으므로 Follows를 적지 않습니다.")
        elif prev and "Follows" in seen:
            no, value = seen["Follows"]
            if not SHORT_HASH.match(value) or not prev.startswith(value):
                problems.append(f"{no}행 Follows: {value} - 같은 안건 직전 커밋 {prev[:7]}의 해시 앞부분"
                                "(7자 이상)이어야 합니다.")
    return problems


def main(argv):
    if len(argv) != 1:
        print("[FAIL] 사용법: python check_commit_msg.py <메시지 파일>")
        return 1
    if cs.is_initial_commit():
        # setup.cmd가 만드는 첫 커밋은 예외다(Workflow/07 「커밋 메시지」)
        print("[PASS] 첫 커밋(HEAD 없음)이어서 커밋 메시지 검사를 생략합니다.")
        return 0
    try:
        problems = check_message(argv[0])
    except (OSError, UnicodeDecodeError) as e:
        print(f"[FAIL] 커밋 메시지 파일을 읽을 수 없습니다: {argv[0]}")
        print(f"       원인: {type(e).__name__}: {e}")
        print("       조치: 메시지 파일이 UTF-8 텍스트인지 확인한 뒤 다시 커밋하십시오.")
        return 1
    if problems:
        # 근거 줄 밖의 문장(본문)은 출력하지 않는다. 줄 번호만 적는다
        print("[FAIL] 커밋 메시지가 규칙과 맞지 않습니다:")
        for p in problems:
            print(f"  - {p}")
        print(f"       원인: 제목 줄이나 근거 줄이 {SOURCE}의 형식과 다릅니다.")
        print(f"       조치: {SOURCE}대로 메시지를 고쳐 다시 커밋하십시오.")
        return 1
    print("[PASS] 커밋 메시지 검사 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
