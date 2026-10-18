#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_final_commit.py - 최종 승인 커밋 준비 명령

규칙의 원천은 Workflow/05_인수인계_및_실행명령 「최종 판정서 승인과 커밋」(4번 반영, 5번 정리, 6번 스테이징 분류 ①~⑪,
8번 커밋)과 Workflow/07_문서_서식_및_번호 「커밋 메시지」(제목 줄, 근거 줄)다. 명령의 동작은
Workflow/06_통제장치_및_배포 「준비·판단 명령」이 정한다. 이 스크립트는 그 구현이며 저장소를 읽기만 한다
(커밋·삭제·이동·파일 쓰기·Git 설정 변경을 하지 않는다).

사용법: python prepare_final_commit.py <최종 판정서 경로>
출력: 1) 반영 목록 2) 삭제 목록 3) 스테이징 목록(경로마다 분류 번호 ①~⑪) 4) 분류하지 못한 변경 5) 커밋 메시지
      (근거 줄 끝, Follows 앞에 Model-Effort 자리 줄. C02가 채운다. REQ-033)
종료 코드: 0 준비 완료, 1 실패(읽을 기록이 없거나 형식이 맞지 않음, 판정 결과가 pass가 아님)
"""

import re
import subprocess
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard as cs  # noqa: E402  (기록 파일명, 머리말 읽기, scope 일치, 승인 필드 형식)

ROOT_DIR = cs.ROOT_DIR
SOURCE = "Workflow/05_인수인계_및_실행명령 「최종 판정서 승인과 커밋」"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪"
FINAL_RES_NAME = re.compile(r"^RES-(" + cs.RECORD_NUMBER + r")_v(\d{2})\.md$")
REVIEW_RESULTS_REL = "Departments/Quality/Review/results"
EC_DIR_REL = "Departments/Design/EC/docs"
ORDER_NAME = re.compile(r"^ORD-(\d{3})_v\d{2}\.md$")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
H1_TITLE = re.compile(r"^# (REQ-" + cs.RECORD_NUMBER + r"): (.+?)\s*$")
MODEL_EFFORT_PLACEHOLDER = "Model-Effort: <이 세션의 모델> / <effort>"


class PrepError(Exception):
    """읽을 기록이 없거나 형식이 맞지 않아 준비를 멈추는 사유."""


def read_text(rel):
    return (ROOT_DIR / rel).read_text(encoding="utf-8")


def rel_of(path):
    return path.relative_to(ROOT_DIR).as_posix()


def header_value(text, key):
    """머리말의 한 줄 값(key: value)을 돌려준다. 없으면 None."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith(key + ":"):
            return cs.strip_value(line.split(":", 1)[1])
    return None


def header_list(text, key):
    """머리말의 목록 필드(key:\n  - 항목) 값을 돌려준다."""
    items, inside = [], False
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return items
    for line in lines[1:]:
        line = line.rstrip("\r")
        if line.strip() == "---":
            break
        if line.startswith(key + ":"):
            inside = True
            continue
        if inside:
            if line.startswith("  - ") or line.startswith("    - "):
                items.append(cs.strip_value(line.split("-", 1)[1]))
            elif line.strip() and not line.startswith(" "):
                break
    return items


def versions(pattern, folders):
    """폴더들에서 이름이 pattern(버전 그룹 하나)에 맞는 파일을 [(버전, 저장소 루트 기준 경로)]로 돌려준다."""
    found = []
    for folder in folders:
        for p in sorted(ROOT_DIR.glob(folder)):
            if p.is_file():
                m = re.fullmatch(pattern, p.name)
                if m:
                    found.append((int(m.group(1)), rel_of(p)))
    return sorted(found)


def section_by_heading(text, keyword):
    """제목에 keyword가 있는 첫 절(같거나 높은 단계 제목 앞까지)의 줄 목록. 없으면 []."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and keyword in m.group(2):
            level, out = len(m.group(1)), []
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6}) ", nxt)
                if h and len(h.group(1)) <= level:
                    break
                out.append(nxt)
            return out
    return []


def section_by_number(text, number):
    """「## <번호>. 」 절의 줄 목록."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if line.startswith(f"## {number}. "):
            out = []
            for nxt in lines[i + 1:]:
                if re.match(r"^## ", nxt):
                    break
                out.append(nxt)
            return out
    return []


def split_cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def reflection_rows(text):
    """「## 4.」 절에서 머리 칸이 「적용본 경로 | 원본 경로 | 반영 명령」인 표의 행을 [(적용본, 원본, [명령])]로 돌려준다."""
    rows, in_table = [], False
    for line in section_by_number(text, "4"):
        if not line.startswith("|"):
            in_table = False
            continue
        cells = split_cells(line)
        if "적용본 경로" in cells[0] and len(cells) >= 3 and "반영 명령" in cells[2]:
            in_table = True
            continue
        if not in_table or re.match(r"^\|\s*:?-", line):
            continue
        if len(cells) < 3:
            continue
        src = INLINE_CODE.findall(cells[0])
        dst = INLINE_CODE.findall(cells[1])
        cmds = INLINE_CODE.findall(cells[2])
        rows.append((src[0] if src else cells[0], dst[0] if dst else cells[1], cmds))
    return rows


def deletion_paths(text):
    """「삭제 대상」 절(없으면 「**삭제 대상**」 항목 줄)에서 지울 경로를 돌려준다.

    표의 행은 첫 인라인 코드(경로 칸)만, 표 밖의 줄은 Departments/로 시작하는 인라인 코드를 경로로 본다.
    근거 칸의 다른 경로를 지울 경로로 잘못 읽지 않기 위해서다.
    """
    lines = section_by_heading(text, "삭제 대상")
    if not lines:
        lines = [ln for ln in text.split("\n") if re.match(r"^\s*- \*\*삭제 대상\*\*", ln)]
    paths = []
    for line in lines:
        codes = INLINE_CODE.findall(line)
        if line.startswith("|"):
            codes = codes[:1]
        for code in codes:
            if code.startswith("Departments/") and not code.endswith("/") and code not in paths:
                paths.append(code)
    return paths


def changed_paths():
    """git status --porcelain -uall의 변경 경로와 상태를 [(상태, 경로)]로 돌려준다(이름 변경은 두 경로)."""
    res = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall", "-z"],
                         cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        raise PrepError(f"git status를 조회할 수 없습니다: {res.stderr.decode('utf-8', 'replace').strip()}")
    tokens, out, i = res.stdout.decode("utf-8", "replace").split("\0"), [], 0
    while i < len(tokens):
        tok = tokens[i]
        if not tok:
            i += 1
            continue
        status, path = tok[:2], tok[3:]
        out.append((status, path))
        if "R" in status or "C" in status:
            out.append((status, tokens[i + 1]))
            i += 1
        i += 1
    return out


def tracked_paths():
    res = subprocess.run(["git", "-c", "core.quotepath=false", "ls-files", "-z"], cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        raise PrepError(f"git ls-files를 조회할 수 없습니다: {res.stderr.decode('utf-8', 'replace').strip()}")
    return {p for p in res.stdout.decode("utf-8", "replace").split("\0") if p}


def previous_record_commit(record):
    """제목 줄 기록 이름이 같은 가장 최근 커밋의 해시(없으면 "")."""
    res = subprocess.run(["git", "log", "--format=%H%x00%s", "HEAD"], cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        raise PrepError(f"git log를 조회할 수 없습니다: {res.stderr.decode('utf-8', 'replace').strip()}")
    for line in res.stdout.decode("utf-8", "replace").split("\n"):
        sha, _, subject = line.partition("\x00")
        m = re.match(r"^[a-z]+: \[([^\]]+)\] ", subject)
        if m and m.group(1) == record:
            return sha
    return ""


class Case:
    """최종 판정서 하나로 정해지는 안건의 기록과 분류 기준."""

    def __init__(self, res_rel):
        self.res_rel = res_rel.replace("\\", "/")
        m = FINAL_RES_NAME.match(Path(self.res_rel).name)
        if not m or not (ROOT_DIR / self.res_rel).is_file():
            raise PrepError(f"최종 판정서 경로가 아니거나 파일이 없습니다: {self.res_rel} "
                            "(형식 Departments/Quality/Review/results/RES-xxx_vNN.md)")
        self.number, self.res_version = m.group(1), int(m.group(2))
        self.record = f"REQ-{self.number}"
        res_text = read_text(self.res_rel)
        result = header_value(res_text, "result")
        if result != "pass":
            raise PrepError(f"최종 판정서의 result가 pass가 아닙니다(값: {result or '없음'}): {self.res_rel}")

        reqs = versions(rf"REQ-{re.escape(self.number)}_v(\d{{2}})\.md", [cs.REQ_DIR_REL + "/*"])
        if not reqs:
            raise PrepError(f"{self.record}가 {cs.REQ_DIR_REL}/에 없습니다.")
        self.req_rel = reqs[-1][1]
        req_rec = cs.parse_header(ROOT_DIR / self.req_rel, "approved")
        problem = cs.approval_problem(req_rec, "approved")
        if problem:
            raise PrepError(f"REQ 최신 버전의 승인 필드가 형식에 맞지 않습니다({problem}): {self.req_rel}")
        self.req_scope = req_rec["scope"]
        req_text = read_text(self.req_rel)
        title = next((t for t in (H1_TITLE.match(ln) for ln in req_text.split("\n")) if t), None)
        if not title or title.group(1) != self.record:
            raise PrepError(f"REQ 최신 버전에서 「# {self.record}: <제목>」 줄을 찾지 못했습니다: {self.req_rel}")
        self.title = title.group(2)

        stem = Path(self.res_rel).stem
        approvals = sorted(p for p in (ROOT_DIR / cs.CLOSE_DIR_REL).glob(f"승인기록_*_{stem}.md")
                           if re.fullmatch(rf"승인기록_\d{{8}}_{re.escape(stem)}\.md", p.name))
        if len(approvals) != 1:
            raise PrepError(f"최종 판정서 승인 기록(승인기록_<YYYYMMDD>_{stem}.md)이 {cs.CLOSE_DIR_REL}/에 "
                            f"하나가 아닙니다({len(approvals)}개).")
        self.approval_rel = rel_of(approvals[0])

        # 「문체 반영」 대조 판정서: 승인한 최종 판정서보다 높은 버전 가운데 「문체 반영 대조」를 적은 것
        later = versions(rf"RES-{re.escape(self.number)}_v(\d{{2}})\.md", [REVIEW_RESULTS_REL + "/*"])
        checks = [rel for ver, rel in later if ver > self.res_version and "문체 반영 대조" in read_text(rel)]
        self.style_check_rel = checks[-1] if checks else None

        ecs = versions(rf"EC-{re.escape(self.number)}_v(\d{{2}})\.md", [EC_DIR_REL + "/*"])
        self.ec_scope = cs.parse_header(ROOT_DIR / ecs[-1][1], "status")["scope"] if ecs else set()

        self.results = {}
        for kind in ("RPT", "DEV"):
            found = versions(rf"{kind}-{re.escape(self.number)}_v(\d{{2}})\.md", ["Departments/*/*/results/*"])
            self.results[kind] = [rel for _, rel in found]
        self.reflections = []
        for kind in ("RPT", "DEV"):
            if self.results[kind]:
                latest = self.results[kind][-1]
                for row in reflection_rows(read_text(latest)):
                    self.reflections.append((Path(latest).stem, *row))
        self.deletions = []
        for kind in ("RPT", "DEV"):
            if self.results[kind]:
                latest = self.results[kind][-1]
                for p in deletion_paths(read_text(latest)):
                    self.deletions.append((p, Path(latest).stem))
        for p in deletion_paths(res_text):
            self.deletions.append((p, Path(self.res_rel).stem))

        self.listed = set()
        for kind in ("RPT", "DEV"):
            for rel in self.results[kind]:
                for line in section_by_number(read_text(rel), "2"):
                    if line.startswith("|"):
                        cells = split_cells(line)
                        if len(cells) >= 2:
                            self.listed.update(INLINE_CODE.findall(cells[1]))

        self.orders, self.research = set(), set()
        inbox = ROOT_DIR / cs.CLOSE_DIR_REL
        order_files = sorted(p for p in inbox.glob("ORD-*.md") if ORDER_NAME.match(p.name))
        for p in order_files:
            if self.record in header_list(p.read_text(encoding="utf-8"), "related_req"):
                self.orders.add(ORDER_NAME.match(p.name).group(1))
        for p in order_files:
            if ORDER_NAME.match(p.name).group(1) in self.orders:
                for line in p.read_text(encoding="utf-8").split("\n"):
                    if "근거 자료" in line:
                        self.research.update(INLINE_CODE.findall(line))

    def classify(self, rel):
        """경로의 분류 번호(①~⑪ 가운데 처음 맞는 것)를 돌려준다. 맞는 것이 없으면 None."""
        n = re.escape(self.number)
        name = rel.rsplit("/", 1)[-1]
        parts = rel.split("/")
        records = (rf"(?:REQ|EC|DEV|RPT|ACC)-{n}_v\d{{2}}\.md", rf"RES-{n}(?:-(?:REQ|EC|SPEC|DESIGN))?_v\d{{2}}\.md",
                   rf"NCR-{n}_\d{{2}}\.md")
        if rel.startswith("Departments/") and any(re.fullmatch(p, name) for p in records):
            return 1
        if rel.startswith(cs.CLOSE_DIR_REL + "/") and re.fullmatch(rf"승인기록_\d{{8}}_(?:REQ|RES)-{n}_v\d{{2}}\.md", name):
            return 2
        m = ORDER_NAME.match(name)
        if rel.startswith(cs.CLOSE_DIR_REL + "/") and m and m.group(1) in self.orders:
            return 3
        if (len(parts) >= 6 and parts[0] == "Departments" and parts[3] == "workspace"
                and re.fullmatch(rf"REQ-{n}_적용본_v\d{{2}}", parts[4])):
            return 4
        if rel in self.listed:
            return 5
        reflected = {dst.rstrip("/") for _, _, dst, _ in self.reflections if dst}
        deleted = {p for p, _ in self.deletions}
        if (any(cs.item_covers(s, rel) for s in self.req_scope | self.ec_scope)
                or rel in reflected or rel in deleted):
            return 6
        if rel == f"Departments/Secretariat/PM/workspace/실행기록_{self.record}.md":
            return 7
        if re.match(rf"^Departments/Quality/Test/assets/acceptance/{re.escape(self.record)}_v\d{{2}}/", rel):
            return 8
        if re.match(rf"^Departments/Secretariat/Secretary/assets/briefings/브리핑_\d{{8}}_{re.escape(self.record)}_", rel):
            return 9
        if rel.startswith("Departments/Secretariat/Secretary/assets/research/") and rel in self.research:
            return 10
        if rel.startswith(cs.CLOSE_DIR_REL + "/") and re.fullmatch(rf"종결기록_\d{{8}}_{re.escape(self.record)}\.md", name):
            return 11
        return None

    def message(self):
        lines = [f"feat: [{self.record}] {self.title}", "",
                 f"Approved-REQ: {self.req_rel}",
                 f"Approved-RES: {self.res_rel}",
                 f"Approval-Record: {self.approval_rel}"]
        if self.style_check_rel:
            lines.append(f"Style-Check-RES: {self.style_check_rel}")
        # 실행 모델·effort 줄은 근거 줄 끝(Follows 앞)에 둔다. 이 명령은 커밋할 세션의 모델을 알 수 없으므로 자리만 만들고
        # C02가 채운다. 채우지 않으면 <·> 때문에 커밋 메시지 검사가 실패한다(Workflow/07 「커밋 메시지」) (REQ-033)
        lines.append(MODEL_EFFORT_PLACEHOLDER)
        prev = previous_record_commit(self.record)
        if prev:
            lines.append(f"Follows: {prev[:7]}")
        return lines


def main(argv):
    if len(argv) != 1:
        print("[FAIL] 사용법: python prepare_final_commit.py <최종 판정서 경로>")
        return 1
    try:
        case = Case(argv[0])
        changes = changed_paths()
        tracked = tracked_paths()
        message = case.message()
    except (PrepError, OSError, UnicodeDecodeError) as e:
        print(f"[FAIL] 최종 승인 커밋 준비를 할 수 없습니다: {e}")
        print(f"       조치: 손으로 대신하지 않고 멈춰 상세 보고하십시오({SOURCE} 4·6번).")
        return 1

    print(f"[INFO] 최종 승인 커밋 준비: {case.res_rel} (안건 {case.record}, REQ {case.req_rel}). 원천: {SOURCE}")
    print("1) 반영 목록(결과서 「적용본」 표의 순서 그대로)")
    if not case.reflections:
        print("  - 없음")
    for i, (doc, src, dst, cmds) in enumerate(case.reflections, 1):
        print(f"  {i}. [{doc}] 적용본: {src} | 원본: {dst}")
        for cmd in cmds:
            print(f"     반영 명령: {cmd}")
    print("2) 삭제 목록(결과서·최종 판정서 「삭제 대상」)")
    if not case.deletions:
        print("  - 없음")
    for rel, doc in case.deletions:
        state = "추적" if rel in tracked else ("미추적" if (ROOT_DIR / rel).exists() else "없음")
        print(f"  - {rel} ({state}, 출처: {doc})")

    staged, unclassified, seen = [], [], set()
    for status, rel in changes:
        if rel in seen:
            continue
        seen.add(rel)
        num = case.classify(rel)
        (staged if num else unclassified).append((num, status, rel))
    print(f"3) 스테이징 목록({SOURCE} 6번 ①~⑪. 이 목록을 그대로 스테이징한다)")
    if not staged:
        print("  - 없음")
    for num, status, rel in sorted(staged, key=lambda x: (x[0], x[2])):
        print(f"  {CIRCLED[num - 1]} {rel} [{status.strip()}]")
    print("4) 분류하지 못한 변경(스테이징하지 않고 보고에 적는다)")
    if not unclassified:
        print("  - 없음")
    for _, status, rel in sorted(unclassified, key=lambda x: x[2]):
        print(f"  - {rel} [{status.strip()}]")
    print("5) 커밋 메시지(Workflow/07_문서_서식_및_번호 「커밋 메시지」. 아래 줄을 그대로 쓰고, "
          "Model-Effort 줄의 <…> 자리만 이 세션의 모델과 effort로 채운다)")
    print("----- 커밋 메시지 시작 -----")
    for line in message:
        print(line)
    print("----- 커밋 메시지 끝 -----")
    print(f"[PASS] 준비 완료: 반영 {len(case.reflections)}행, 삭제 {len(case.deletions)}개, "
          f"스테이징 {len(staged)}개, 분류하지 못한 변경 {len(unclassified)}개.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
