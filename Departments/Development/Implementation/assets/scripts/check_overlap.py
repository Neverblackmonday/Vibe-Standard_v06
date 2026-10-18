#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_overlap.py - 겹침·착수 판단 명령

규칙의 원천은 Workflow/03_라이프사이클 「다른 안건이 진행 중일 때의 REQ 작성」 1~9항(req-save)과
「원스톱 착수 조건」 1~8항(onestop)이며, 명령의 사용과 실패 때의 처리는 같은 절 10항·9항, 동작은
Workflow/06_통제장치_및_배포 「준비·판단 명령」이 정한다. 이 스크립트는 그 구현이며 저장소를 읽기만 한다.

사용법: python check_overlap.py req-save --number <REQ 번호(예: REQ-101)> --scope <항목> [--scope <항목> ...]
        python check_overlap.py onestop <REQ 경로>
종료 코드: 0 겹침·실행 중 안건·대상 커밋 없음, 1 있음(멈춤 사유), 2 명령 실패(조회 실패, REQ 파일 형식 오류)
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard as cs  # noqa: E402  (기록 파일명, 머리말 읽기, scope 일치, 승인 필드 형식, 종결 기록 이름)

ROOT_DIR = cs.ROOT_DIR
SPECIAL_DOCS = ("Workflow/templates/REQ_TEMPLATE.md", "Workflow/03_라이프사이클.md")  # 3.1절 3항 끝 문장
REQ_ARG = re.compile(r"^REQ-(" + cs.RECORD_NUMBER + r")$")
SUBJECT_RECORD = re.compile(r"^[a-z]+: \[((?:REQ|HOTFIX)-" + cs.RECORD_NUMBER + r")\] ")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
SOURCE_SAVE = "Workflow/03_라이프사이클 「다른 안건이 진행 중일 때의 REQ 작성」"
SOURCE_ONESTOP = "Workflow/03_라이프사이클 「원스톱 착수 조건」"


class CommandError(Exception):
    """조회 실패나 REQ 파일 형식 오류(종료 코드 2)."""


def git_text(args):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        raise CommandError(f"git {' '.join(args)} 실패: {res.stderr.decode('utf-8', 'replace').strip()}")
    return res.stdout.decode("utf-8", "replace")


def closed_records():
    """끝난 안건의 기록 이름 집합(3.1절 4항 「끝난 안건」: 커밋된 종결 기록).

    git ls-files의 종결 기록 가운데 git status가 A로 시작하는 경로(스테이징만 하고 커밋하지 않은 파일)를 뺀다.
    """
    folder = cs.CLOSE_DIR_REL + "/"
    listed = [p for p in git_text(["ls-files", "-z", "--", folder]).split("\0") if p]
    staged_only = set()
    for tok in git_text(["status", "--porcelain", "-uall", "-z", "--", folder]).split("\0"):
        if tok.startswith("A"):
            staged_only.add(tok[3:])
    names = set()
    for rel in listed:
        if rel in staged_only:
            continue
        name = cs.close_record_name(rel)
        if name:
            names.add(name)
    return names


def req_versions():
    """REQ 폴더의 기록을 {번호: [(버전, 경로), ...]}로 돌려준다(버전 오름차순)."""
    folder = ROOT_DIR / cs.REQ_DIR_REL
    found = {}
    if not folder.is_dir():
        # REQ가 하나도 없는 저장소(배포본으로 시작한 직후 등)는 폴더 자리만 있거나 폴더가 없다. 진행 중인 안건 0건이다
        return found
    for p in folder.glob("REQ-*.md"):
        m = cs.RECORD_NAME.match(p.name)
        if m and m.group(1) == "REQ":
            found.setdefault(m.group(2), []).append((int(m.group(3)), p))
    return {k: sorted(v) for k, v in found.items()}


def in_progress(exclude_number):
    """진행 중인 안건(3.1절 2·4항)을 [(기록 이름, 대조 scope {항목: 그 항목이 있는 버전 파일명들})]로 돌려준다."""
    closed = closed_records()
    result = []
    for number, vers in sorted(req_versions().items()):
        if number == exclude_number:
            continue
        record = f"REQ-{number}"
        headers = [(p, cs.parse_header(p, "approved")) for _, p in vers]
        approved = [(p, h) for p, h in headers if cs.approval_problem(h, "approved") is None]
        if not approved or record in closed:
            continue
        scope = {}
        # 최신 버전과 승인된 모든 버전의 scope를 합쳐 읽는다(4항 「대조」)
        for p, h in approved + [headers[-1]]:
            for item in h["scope"]:
                scope.setdefault(item, set()).add(p.name)
        result.append((record, scope))
    return result


def items_overlap(a, b):
    """3.1절 3항: 두 scope 항목이 같거나, 어느 한쪽 방향으로 scope 일치 규칙상 포함되면 겹친다."""
    return a == b or cs.item_covers(a, b) or cs.item_covers(b, a)


def cmd_req_save(argv):
    number_arg, scopes, i = None, [], 0
    while i < len(argv):
        if argv[i] == "--number" and i + 1 < len(argv):
            number_arg = argv[i + 1]
            i += 2
        elif argv[i] == "--scope" and i + 1 < len(argv):
            scopes.append(argv[i + 1].replace("\\", "/").split(" #", 1)[0].strip().rstrip("/"))
            i += 2
        else:
            raise CommandError(f"알 수 없는 인자: {argv[i]}")
    m = REQ_ARG.match(number_arg or "")
    if not m or not scopes:
        raise CommandError("사용법: req-save --number <REQ 번호(예: REQ-101)> --scope <항목> [--scope <항목> ...]")
    own = m.group(1)
    print(f"[INFO] REQ 저장 전 겹침 판단: {number_arg}, scope {', '.join(scopes)}. 원천: {SOURCE_SAVE} 1~9항")
    progress = in_progress(own)
    if progress:
        print(f"[INFO] 진행 중인 안건 {len(progress)}건: {', '.join(r for r, _ in progress)}")
    else:
        print("[INFO] 진행 중인 안건 0건")
    overlaps = []
    for record, scope in progress:
        for item, files in sorted(scope.items()):
            for new in scopes:
                if items_overlap(item, new):
                    overlaps.append(f"{record}: 진행 중 scope `{item}`({', '.join(sorted(files))}) ↔ 새 REQ scope `{new}`")
            for doc in SPECIAL_DOCS:
                if cs.item_covers(item, doc):
                    overlaps.append(f"{record}: 진행 중 scope `{item}`({', '.join(sorted(files))})가 `{doc}`를 포함"
                                    "(3항 끝 문장. 새 REQ의 scope와 관계없이 겹침)")
    if overlaps:
        print("[FAIL] 겹침이 있습니다. REQ 파일을 저장하지 않고 멈춥니다(7절 11항):")
        for o in overlaps:
            print(f"  - {o}")
        return 1
    print("[PASS] 진행 중인 안건과 겹치지 않습니다.")
    return 0


def base_time(header_text, req_name):
    """4.1절 5항의 기준 시각: created_at, 없으면 created 날짜 0시."""
    values = {}
    for line in header_text.split("\n")[1:]:
        if line.strip() == "---":
            break
        for key in ("created_at", "created"):
            if line.startswith(key + ":"):
                values[key] = cs.strip_value(line.split(":", 1)[1])
    if values.get("created_at"):
        return values["created_at"]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", values.get("created", "")):
        return values["created"] + "T00:00:00+09:00"
    raise CommandError(f"{req_name} 머리말에 created_at도 created(YYYY-MM-DD)도 없습니다.")


def pathspecs(items):
    """확장자 없는 항목은 끝에 *를 붙여 적는다(4.1절 5항 「겹침」)."""
    out = []
    for item in items:
        name = item.rsplit("/", 1)[-1]
        out.append(item if Path(name).suffix else item + "*")
    return out


def target_commits(since, specs, closed):
    """기준 시각 뒤에 specs 경로를 바꾼 커밋 가운데 제목 줄 기록 이름이 끝난 안건인 커밋."""
    try:
        since_dt = datetime.fromisoformat(since)
    except ValueError:
        raise CommandError(f"기준 시각이 YYYY-MM-DDTHH:MM:SS+09:00 형식이 아닙니다: {since}")
    out = git_text(["log", f"--since={since}", "--format=%H %cI %s", "HEAD", "--", *specs])
    found = []
    for line in out.split("\n"):
        if not line.strip():
            continue
        sha, cdate, subject = (line.split(" ", 2) + ["", ""])[:3]
        m = SUBJECT_RECORD.match(subject)
        # --since는 커밋 시각 기준이며, 같은 기준을 출력 값(시간대 포함)으로 한 번 더 확인한다
        if m and m.group(1) in closed and datetime.fromisoformat(cdate) >= since_dt:
            found.append((sha, cdate, subject, m.group(1)))
    return found


def running_others(own):
    """4.1절 2항: 진행 중인 다른 안건 가운데 단계 산출물이 작업 트리에 있는 안건 {기록 이름: [산출물]}."""
    running = {}
    for record, _ in in_progress(own):
        n = record[len("REQ-"):]
        patterns = [f"Departments/Design/EC/docs/EC-{n}_*"]
        for kind in ("RPT", "DEV", "ACC", "RES"):
            patterns.append(f"Departments/*/*/results/{kind}-{n}_*")
        for suffix in ("EC", "SPEC", "DESIGN"):
            patterns.append(f"Departments/*/*/results/RES-{n}-{suffix}_*")
        hits = sorted({p.relative_to(ROOT_DIR).as_posix() for pat in patterns for p in ROOT_DIR.glob(pat) if p.is_file()})
        if hits:
            running[record] = hits
    return running


def cmd_onestop(argv):
    if len(argv) != 1:
        raise CommandError("사용법: onestop <REQ 경로>")
    rel = argv[0].replace("\\", "/")
    m = cs.RECORD_NAME.match(Path(rel).name)
    if not m or m.group(1) != "REQ" or not (ROOT_DIR / rel).is_file():
        raise CommandError(f"REQ 파일이 없거나 이름이 REQ-xxx_vNN.md 형식이 아닙니다: {rel}")
    own, record = m.group(2), f"REQ-{m.group(2)}"
    latest = req_versions()[own][-1][1]
    latest_rel = latest.relative_to(ROOT_DIR).as_posix()
    text = latest.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise CommandError(f"REQ 머리말이 없습니다: {latest_rel}")
    since = base_time(text, latest.name)
    scope = sorted(cs.parse_header(latest, "approved")["scope"])
    print(f"[INFO] 원스톱 착수 판단: {record}(최신 버전 {latest_rel}), 기준 시각 {since}. 원천: {SOURCE_ONESTOP} 1·2·5항")
    stop = False

    running = running_others(own)
    if running:
        stop = True
        print("[FAIL] 실행 중인 다른 안건이 있습니다(1·2항. 7절 12항으로 멈춤):")
        for rec, hits in running.items():
            print(f"  - {rec}: {', '.join(hits)}")
    else:
        print("[PASS] 실행 중인 다른 안건이 없습니다(1·2항).")

    closed = closed_records()
    specs = pathspecs(scope) + list(SPECIAL_DOCS)
    commits = target_commits(since, specs, closed)
    if commits:
        stop = True
        print(f"[FAIL] 끝난 안건의 커밋이 이 REQ의 scope·특례 문서를 바꿨습니다(5항 「겹침」. 경로 {', '.join(specs)}):")
        for sha, cdate, subject, rec in commits:
            print(f"  - {rec}: {sha[:7]} {cdate} {subject}")
    else:
        print("[PASS] 기준 시각 뒤에 scope·특례 문서를 바꾼 끝난 안건의 커밋이 없습니다(5항 「겹침」).")

    # 5항 「가리키는 절·문구」: REQ 본문이 백틱으로 가리킨 scope 밖 파일과 그 파일을 바꾼 대상 커밋. 절 제목·인용 문구가
    # 바뀌었는지는 PM이 git show로 판단한다(기계로 하지 않는 부분)
    body = text.split("---", 2)[-1]
    referred = []
    for code in INLINE_CODE.findall(body):
        path = code.strip().rstrip("/")
        if (" " in path or path.startswith(("/", "..")) or path in referred or not (ROOT_DIR / path).is_file()
                or any(cs.item_covers(s, path) for s in scope)):
            continue
        referred.append(path)
    pm_items = []
    for path in referred:
        for sha, cdate, subject, rec in target_commits(since, [path], closed):
            pm_items.append(f"{path}: {rec} {sha[:7]} {cdate} {subject}")
    if pm_items:
        print("[WARN] PM 판단 대상(5항 「가리키는 절·문구」. git show <커밋> -- <문서>로 절 제목·인용 문구가 바뀌었는지 판단):")
        for item in pm_items:
            print(f"  - {item}")
    else:
        print("[INFO] PM 판단 대상 없음(REQ 본문이 가리킨 scope 밖 문서를 바꾼 끝난 안건의 커밋 없음).")
    return 1 if stop else 0


def main(argv):
    if not argv or argv[0] not in ("req-save", "onestop"):
        print("[FAIL] 명령 실패: 사용법은 req-save 또는 onestop입니다.")
        return 2
    try:
        return cmd_req_save(argv[1:]) if argv[0] == "req-save" else cmd_onestop(argv[1:])
    except (CommandError, OSError, UnicodeDecodeError) as e:
        print(f"[FAIL] 명령 실패: {e}")
        print("       조치: 손으로 대신 판단하지 않고 멈춰 보고하십시오(Workflow/03_라이프사이클 「중단 조건」 13항).")
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
