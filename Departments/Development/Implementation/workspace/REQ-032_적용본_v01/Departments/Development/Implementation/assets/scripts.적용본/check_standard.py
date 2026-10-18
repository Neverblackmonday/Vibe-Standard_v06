#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_standard.py - 바이브 코딩 표준 v05 커밋 전 검사기

검사 순서와 규칙의 설명은 Workflow/06_통제장치_및_배포 「커밋 전 검사」에 있다.
작성 파트 대조의 쓰기 경로 원천은 Workflow/02_부서_구조_및_작업구역 「작업 구역」,
옛 경로 잔존 검사의 대응 원천은 같은 문서 「옛 이름과 새 이름의 대응」이다.
사용법: python check_standard.py              # 작업 트리 전체(git status)를 검사한다
        python check_standard.py --staged     # 커밋 대상(index)만 검사한다 (pre-commit 훅)
        python check_standard.py --scan-all   # 다른 검사 없이 추적 파일 전체와 커밋 이력 전체에서 비밀정보를 찾는다
                                              # (운영부의 보안 점검용. Workflow/06 「보안 점검」)
1. 초기 커밋 예외: .git이나 HEAD가 없으면 검사를 생략한다
2. Git 조회 실패 시 차단한다
3. CEO/ 아래 변경: 작업 트리 검사는 빼고, --staged 검사는 CEO/ 변경만 있으면 통과(4~9 생략), 그 밖의 변경과 섞이면 차단한다.
   Lab/ 아래 변경: 4의 검출을 받은 뒤, 작업 트리 검사는 빼고, --staged 검사는 Lab/ 변경만 있으면 통과(5~9 생략),
   그 밖의 변경과 섞이면 Lab/ 경로도 7·8의 대조를 받는다
4. 비밀정보 검출: 3의 CEO/ 처리 뒤 남은 경로(Lab/·대조 제외 경로 포함)의 내용에서 SECRET_RULES에 맞는 값을 찾으면
   차단한다(예외 목록 SECRET_ALLOWLIST_REL에 등록된 검출 제외). 값은 출력하지 않는다
5. 작성 파트 대조: Departments/ 아래 변경 파일의 머리말 작성 주체 칸(author·auditor의 agent)이 가리키는 파트의
   쓰기 경로(PART_WRITE_PATHS) 안에 그 파일이 있어야 한다. 머리말이나 작성 주체 칸이 없는 파일은 대조하지 않는다.
   HEAD에 이 스크립트(SCRIPTS_DIR_REL)가 없으면 생략한다(REQ-032 커밋 뒤의 커밋부터 적용)
6. 옛 경로 잔존 검사: 추적 파일(작업 트리 검사는 미추적 파일 포함)에서 뺄 범위를 뺀 파일에 옛 경로가 있으면 차단한다
7. 커밋 대상(작업 트리 검사는 작업 트리)에 있는 종결 기록(CLOSE_DIR_REL 아래에서 이름이 CLOSE_PREFIX로 시작하는 파일)이
   그 폴더 바로 아래에 있고 이름이 CLOSE_NAME 형식에 맞는지 확인한 뒤(틀리면 차단),
   scope 대조 제외 구역(WHITELIST_PREFIXES, 팀 직속 results/·workspace/)을 뺀다
8. 남은 변경 파일 전체가 승인되었고 끝나지 않은 REQ(최신 버전) 하나 또는 확인되었고 끝나지 않은 HOTFIX(최신 버전) 하나의
   scope에 들어가야 한다. 끝난 기록은 HEAD에 커밋된 종결 기록의 파일명으로 판단한다(Workflow/07 「종결 기록」).
   REQ는 REQ_DIR_REL, HOTFIX는 HOTFIX_DIR_REL에서 읽는다.
   HOTFIX로 통과하려면 남은 변경 파일이 HOTFIX_MAX_SCOPE개 이하여야 한다
9. 소스코드·테스트가 바뀌었으면 단위 테스트를 실행한다
"""

import os
import re
from collections import Counter
from datetime import datetime
import subprocess
import sys
from pathlib import Path

# Windows 콘솔에서 한국어 출력이 깨지지 않도록 출력 인코딩을 UTF-8로 고정한다
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# 이 파일은 <루트>/Departments/Development/Implementation/assets/scripts/ 아래에 있다(부 → 팀 두 단계. REQ-032)
ROOT_DIR = Path(__file__).resolve().parents[5]

# 이 스크립트 폴더(거버넌스 구역. AGENTS.md 「불변 원칙」 3항)
SCRIPTS_DIR_REL = "Departments/Development/Implementation/assets/scripts"
# 기록 위치(Workflow/07_문서_서식_및_번호 「문서 체계」)
REQ_DIR_REL = "Departments/Secretariat/PM/docs/requests"
HOTFIX_DIR_REL = "Departments/Development/Hotfix/results"
TEST_DIR_REL = "Departments/Development/Implementation/assets/tests"

# scope 대조에서 빼는 경로 (규정상 작업 구역은 Workflow/02 「작업 구역」이 원천이고, 이 목록은 커밋 검사용 구현이다)
# 품질보증부의 인수 시험·부적합 기록은 판정서(results/)처럼 안건 scope와 관계없이 커밋되어야 한다.
# 그 안건의 scope:에 품질보증부 폴더가 없거나, REQ 판정 fail로 생긴 부적합 기록이어도 막히지 않게 뺀다.
# 인수 시험의 통과는 구현 단계와 최종 판정이 확인하므로 커밋 때 다시 실행하지 않는다
# (이 경로는 순서 7에서 빠지므로 순서 9 run_tests()의 대상이 아니다) (REQ-017)
# 판정 전제 제외(AGENTS.md 「불변 원칙」 5항)와 달리 PM팀의 REQ 기록도 지금처럼 뺀다(REQ-032 D4)
WHITELIST_PREFIXES = (
    "Departments/Secretariat/PM/docs/requests/REQ-",  # REQ 기록 (승인 전 초안 포함)
    "Departments/Secretariat/Secretary/assets/",  # ORDER, 승인 기록, 종결 기록, 조사 자료, 보고 자료
    "Audits/",  # 외부감사실(외부 보고서)
    "Departments/Quality/Test/assets/acceptance/",  # 인수 시험(시험팀. Workflow/03 「시험실」)
    "Departments/Quality/Nonconformance/docs/",  # 부적합 기록(부적합관리팀. Workflow/03 「부적합 관리」)
)
# _archive/(지난 버전 기록)는 제외하지 않는다. 읽기 전용 구역이므로 변경은 scope 대조에서 차단된다

# 실험실 구역. 대조 제외 구역(WHITELIST_PREFIXES)이 아니다. 처리는 check_standard()의 순서 3을 따른다
LAB_PREFIX = "Lab/"

# 핫픽스 scope에 넣을 수 없는 경로 (AGENTS.md 「불변 원칙」 3항의 거버넌스 구역, CEO/, _archive/)
GOVERNANCE_PATHS = (
    "AGENTS.md",
    "CLAUDE.md",
    "setup.cmd",
    ".gitattributes",
    ".gitignore",
    ".claude",
    ".githooks",
    SCRIPTS_DIR_REL,
    "Workflow",
    "CEO",
    "_archive",
)
# 핫픽스 대상 조건 「수정 파일 3개 이하」(Workflow/03 「핫픽스 트랙」). scope 항목 수와 덮는 변경 파일 수에 함께 쓴다
HOTFIX_MAX_SCOPE = 3

# 공식 기록의 번호: <세 자리 번호>[-<파생 번호>]. 기록 파일명과 종결 기록 파일명이 같은 번호 형식을 쓰게 한 곳에 둔다
RECORD_NUMBER = r"\d{3}(?:-\d+)?"
# 공식 기록 파일명: <종류>-<세 자리 번호>[-<파생 번호>]_v<두 자리 버전>.md (Workflow/07 「번호와 버전」)
RECORD_NAME = re.compile(rf"^(REQ|HOTFIX)-({RECORD_NUMBER})_v(\d{{2}})\.md$")
# 종결 기록: <CLOSE_DIR_REL>/종결기록_<YYYYMMDD>_<기록 이름>.md (Workflow/07 「번호와 버전」의 「종결 기록」)
# 기록 이름은 끝난 기록의 파일명에서 _v<버전>.md를 뗀 것이다(REQ-xxx, REQ-xxx-n, HOTFIX-xxx)
CLOSE_DIR_REL = "Departments/Secretariat/Secretary/assets/inbox"
CLOSE_PREFIX = "종결기록_"
CLOSE_NAME = re.compile(rf"^{CLOSE_PREFIX}\d{{8}}_((?:REQ|HOTFIX)-{RECORD_NUMBER})\.md$")
CLOSE_SOURCE = "Workflow/07_문서_서식_및_번호 「번호와 버전」의 「종결 기록」"
# 승인·확인 시각 형식: YYYY-MM-DDTHH:MM:SS+09:00 (Workflow/07 「머리말」)
APPROVAL_TIME = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")

# ---------------------------------------------------------------- 작성 파트 대조 (순서 5)
# 파트별 쓰기 경로. 원천은 Workflow/02_부서_구조_및_작업구역 「작업 구역」 표이며, 이 상수는 그 표의 Departments/ 아래
# 고정 경로를 옮긴 구현 목록이다(두 목록의 대조는 Workflow/06 「거버넌스 파일 개정 절차」 3항).
# REQ scope:에 따라 달라지는 칸(「구현」·「실험」 행의 scope 경로, 운영부·마케팅부의 scope 경로)은 옮기지 않는다.
# 값은 경로 접두어이며, 폴더는 끝에 /를 붙이고 파일 이름 규칙(P02의 실행 기록)은 이름 앞부분까지 적는다
_SEC = "Departments/Secretariat/Secretary/"
_PMT = "Departments/Secretariat/PM/"
_EC = "Departments/Design/EC/"
_SPEC = "Departments/Design/Spec/"
_IMPL = "Departments/Development/Implementation/"
_REVIEW = ("Departments/Quality/Review/results/", "Departments/Quality/Review/workspace/",
           "Departments/Quality/Nonconformance/docs/")
_DESIGN_SPEC = (_SPEC + "workspace/", _SPEC + "docs/", _SPEC + "assets/", _EC + "results/")
PART_WRITE_PATHS = {
    "S01": (_SEC + "assets/inbox/", _SEC + "assets/planning/", _SEC + "workspace/셸작업/"),
    "S02": (_SEC + "assets/research/", _SEC + "assets/briefings/"),
    "S03": (),
    "C01": (),
    "C02": (_SEC + "assets/inbox/", _SEC + "workspace/셸작업/"),
    "C03": (),
    "P01": (_PMT + "docs/requests/", _PMT + "workspace/"),
    "P02": (_PMT + "workspace/실행기록_REQ-", _SEC + "assets/inbox/"),
    "E01": (_EC + "results/",),
    "E02": (_EC + "docs/", _EC + "workspace/"),
    "E03": _DESIGN_SPEC,
    "E04": _DESIGN_SPEC,
    "V01": (_IMPL + "results/", _IMPL + "workspace/"),
    "V02": (_IMPL + "results/", _IMPL + "workspace/"),
    "V03": ("Departments/Development/Hotfix/results/",),
    "Q01": _REVIEW,
    "Q02": _REVIEW,
    "Q03": _REVIEW,
    "Q04": _REVIEW,
    "Q05": _REVIEW,
    "Q06": ("Departments/Quality/Nonconformance/docs/",),
    "Q07": ("Departments/Quality/Test/assets/acceptance/", "Departments/Quality/Test/results/",
            "Departments/Quality/Test/workspace/"),
    "O01": ("Departments/Operations/Release/results/", "Departments/Operations/Release/workspace/"),
    "O02": ("Departments/Operations/Security/results/", "Departments/Operations/Security/workspace/"),
    "M01": ("Departments/Marketing/VisualDesign/results/", "Departments/Marketing/VisualDesign/workspace/"),
    "M02": ("Departments/Marketing/Content/results/", "Departments/Marketing/Content/workspace/"),
    "M03": ("Departments/Marketing/Content/results/", "Departments/Marketing/Content/workspace/"),
    "M04": ("Departments/Marketing/Promotion/results/", "Departments/Marketing/Promotion/workspace/"),
    "X01": (_EC + "results/", _IMPL + "results/", "Departments/Operations/Release/results/",
            "Departments/Operations/Security/results/", "Departments/Marketing/VisualDesign/results/",
            "Departments/Marketing/Content/results/", "Departments/Marketing/Promotion/results/"),
}
# 부 표기와 그 부의 파트(Workflow/06 「커밋 전 검사」의 「작성 파트 대조(구현)」 ③). 작성 주체 값의 원천은
# Workflow/07_문서_서식_및_번호 「머리말」이다. 파트별 서브에이전트 정의가 생기기 전에는 이 표로 부 단위 대조가 된다
DEPT_PARTS = {
    "Secretariat": ("S01", "S02", "S03", "C01", "C02", "C03"),
    "PM": ("P01", "P02"),
    "Design": ("E01", "E02", "E03", "E04"),
    "Development": ("V01", "V02", "V03"),
    "Quality": ("Q01", "Q02", "Q03", "Q04", "Q05", "Q06", "Q07"),
    "Operations": ("O01", "O02"),
    "Marketing": ("M01", "M02", "M03", "M04"),
}
PART_CODE = re.compile(r"^[SPCEVQOMX]\d{2}$")
AUTHOR_SOURCE = "Workflow/02_부서_구조_및_작업구역 「작업 구역」"

# ---------------------------------------------------------------- 옛 경로 잔존 검사 (순서 6)
# 옛 경로는 부서 폴더 바로 아래에 공통 하위 폴더 이름이 오는 경로다(대응의 원천: Workflow/02 「옛 이름과 새 이름의 대응」).
# 패턴을 낱말 목록으로 조립하는 이유는 이 파일 자신이 검사 대상(검사 스크립트 폴더)이어서,
# 옛 경로를 글자 그대로 적으면 이 파일이 패턴에 맞기 때문이다(SECRET_RULES와 같은 방식)
_OLD_DEPTS = "|".join(("Secretariat", "Design", "Development", "Quality", "Operations", "Marketing"))
_OLD_SUBS = "|".join(("assets", "docs", "results", "workspace"))
OLD_PATH_PATTERNS = (
    re.compile("Departments" + "/(" + _OLD_DEPTS + r"|\*|<부서>)/(" + _OLD_SUBS + r")\b"),
    re.compile(r"(?<![\w/.])(" + _OLD_DEPTS + ")/(" + _OLD_SUBS + r")\b"),
)
# 뺄 범위(Workflow/06 「커밋 전 검사」의 「옛 경로 잔존 검사(구현)」 ②, REQ-032 D12)
RESIDUAL_EXCLUDED_TOP = ("CEO/", "_archive/", "Lab/", "Audits/")
RESIDUAL_RECORD_PREFIXES = (
    "Departments/Secretariat/Secretary/assets/",
    "Departments/Secretariat/PM/docs/",
    "Departments/Design/EC/docs/",
    "Departments/Quality/Nonconformance/docs/",
    "Departments/Quality/Test/assets/acceptance/",
)
REVISION_HISTORY_HEADING = re.compile(r"^## .*개정 이력\s*$")
MAPPING_DOC_REL = "Workflow/02_부서_구조_및_작업구역.md"
MAPPING_HEADING = re.compile(r"^### 2\.3(?!\d)")
SECTION_HEADING = re.compile(r"^#{1,3} ")
RESIDUAL_SOURCE = "Workflow/02_부서_구조_및_작업구역 「옛 이름과 새 이름의 대응」"

# 비밀정보 검출 규칙(순서 4와 --scan-all). 규칙 목록의 원천은 이 상수다(Workflow/06 「비밀정보 검출」).
# 이 검사는 사고 이력 없이 대표님 결정으로 넣은 예방 검사이며(근거: Workflow/06 「비밀정보 검출」 ⑦ 도입 근거),
# AGENTS.md 「불변 원칙」 8항의 개별 예외다(REQ-018).
# 형식이 알려진 키·토큰·개인 키와, 따옴표로 감싼 값을 비밀번호·토큰 이름에 대입한 줄만 잡는다.
# 대입 규칙이 따옴표를 요구하는 이유는 표준 문서의 필드 이름 언급을 오탐하지 않기 위해서다.
# 형식이 없는 비밀정보는 놓칠 수 있으며 그 범위는 운영부의 보안 점검에서 사람이 확인한다.
# 각 정규식 문자열은 자기 자신과 맞지 않게 작성했으므로 이 파일은 검출되지 않는다
SECRET_RULES = (
    ("private-key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}|\bgithub_pat_[A-Za-z0-9_]{22,}")),
    ("anthropic-api-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("openai-api-key", re.compile(r"\bsk-(?!ant-)[A-Za-z0-9_-]{20,}")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}")),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("secret-assignment", re.compile(
        r"""\b(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b["']?\s*[:=]\s*["'][^"'\s]{8,}["']""",
        re.IGNORECASE)),
)
SECRET_RULE_NAMES = {name for name, _ in SECRET_RULES}

# 비밀정보 검출 예외 목록. 에이전트가 고칠 수 없는 거버넌스 구역(이 스크립트 폴더) 안에 두어
# 에이전트가 검사를 스스로 풀지 못하게 한다. 등록은 대표님 직접 또는 REQ로만 한다.
# 줄 번호가 아니라 경로와 규칙 이름으로 등록하는 이유는 문서를 고칠 때마다 줄 번호가 바뀌기 때문이다.
# 승인 기록과 같이 작업 트리에서 읽어, 대표님이 등록한 뒤 커밋 전에도 반영되게 한다
SECRET_ALLOWLIST_REL = SCRIPTS_DIR_REL + "/secret_allowlist.txt"
SECRET_SOURCE = "Workflow/06_통제장치_및_배포 「비밀정보 검출」"


def is_whitelisted(filepath):
    norm = filepath.replace("\\", "/")
    parts = norm.split("/")
    # 팀 직속 results/와 workspace/만 뺀다 (예: Departments/<부>/<팀>/results/...). 부서 직속 형태는 REQ-032 뒤
    # 그 위치에 파일이 없으므로 빼지 않는다
    if len(parts) >= 5 and parts[0] == "Departments" and parts[3] in ("results", "workspace"):
        return True
    return any(norm.startswith(p) for p in WHITELIST_PREFIXES)


def is_initial_commit():
    if not (ROOT_DIR / ".git").exists():
        return True
    res = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT_DIR, capture_output=True)
    return res.returncode != 0


def strip_value(raw):
    """YAML 한 줄 값에서 줄 끝 주석과 따옴표를 뗀다."""
    return raw.split(" #", 1)[0].strip().strip("'\"")


def parse_header(path, approval_key):
    """머리말에서 승인 필드(approval_key) 값과 scope 목록을 읽는다."""
    approved = None
    scope_lines = []
    in_scope = False
    for line in path.read_text(encoding="utf-8").splitlines():
        trimmed = line.strip()
        if trimmed.startswith(approval_key + ":"):
            val = strip_value(trimmed.split(":", 1)[1])
            if val and val.lower() not in ("null", "false"):
                approved = val
            continue
        if trimmed.startswith("scope:"):
            in_scope = True
            continue
        if in_scope:
            if line.startswith("  - ") or line.startswith("    - "):
                item = strip_value(line.split("-", 1)[1])
                scope_lines.append(item.replace("\\", "/").rstrip("/"))
            elif trimmed and not line.startswith(" ") and not line.startswith("#"):
                break
    return {"name": path.name, "scope": set(scope_lines), "approved": approved}


def load_latest(folder, kind):
    """폴더에서 kind(REQ 또는 HOTFIX) 기록의 번호별 최신 버전만 고른다."""
    if not folder.exists():
        return []
    latest = {}
    for f in folder.glob(f"{kind}-*.md"):
        m = RECORD_NAME.match(f.name)
        if not m or m.group(1) != kind:
            print(f"[INFO] {f.name}: 기록 파일명 형식(<종류>-<번호>_v<버전>.md)이 아니어서 검사에서 제외합니다.")
            continue
        number, version = m.group(2), int(m.group(3))
        if number not in latest or version > latest[number][0]:
            latest[number] = (version, f)
    return [latest[k][1] for k in sorted(latest)]


def is_governance_path(scope_item):
    # 거버넌스 경로 안의 항목만 보면, scope 대조(item_covers)로는 거버넌스 파일을 포함하는
    # 상위 폴더(Departments/Development/Implementation/assets)나 확장자를 뺀 이름(AGENTS)이 핫픽스 제외를 우회한다.
    # 제외 판단을 scope 대조와 같은 함수로 하여 두 규칙이 어긋나지 않게 한다
    return any(scope_item == g or scope_item.startswith(g + "/") or item_covers(scope_item, g)
               for g in GOVERNANCE_PATHS)


def approval_problem(rec, key):
    """승인 필드가 비었거나 형식이 틀리면 사유를, 정상이면 None을 돌려준다."""
    if not rec["approved"]:
        return f"{key}: 미기재"
    if not APPROVAL_TIME.match(rec["approved"]):
        return f"{key}: 형식 오류({rec['approved']}). YYYY-MM-DDTHH:MM:SS+09:00 형식이어야 합니다"
    try:
        datetime.fromisoformat(rec["approved"])
    except ValueError:
        return f"{key}: 실재하지 않는 일시({rec['approved']})"
    return None


def is_close_record_candidate(rel):
    """종결 기록 폴더 아래(하위 폴더 포함)에서 이름이 종결 기록 접두어로 시작하는 경로인지 판단한다."""
    return rel.startswith(CLOSE_DIR_REL + "/") and rel.rsplit("/", 1)[-1].startswith(CLOSE_PREFIX)


def close_record_name(rel):
    """종결 기록이 폴더 바로 아래에 있고 이름이 형식에 맞으면 기록 이름을, 아니면 None을 돌려준다."""
    parent, _, base = rel.rpartition("/")
    if parent != CLOSE_DIR_REL:
        return None
    m = CLOSE_NAME.match(base)
    return m.group(1) if m else None


# ---------------------------------------------------------------- 내용 읽기 (순서 4·5·6 공통)

def index_entries():
    """index(스테이지 0)의 {경로: blob 해시}를 돌려준다. 조회에 실패하면 원인을 출력하고 None을 돌려준다."""
    cmd = ["git", "-c", "core.quotepath=false", "ls-files", "-s", "-z"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        print(f"[FAIL] 커밋 대상 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None
    entries = {}
    for rec in res.stdout.decode("utf-8", "replace").split("\0"):
        if not rec:
            continue
        meta, _, path = rec.partition("\t")
        fields = meta.split()
        # 병합 충돌 중의 스테이지 1~3 항목은 커밋 대상이 아니므로 스테이지 0만 쓴다
        if len(fields) == 3 and fields[2] == "0":
            entries[path] = fields[1]
    return entries


def index_paths():
    """index에 있는 경로 집합을 돌려준다. 조회에 실패하면 None을 돌려준다."""
    entries = index_entries()
    return None if entries is None else set(entries)


def read_blobs(shas):
    """blob 해시 목록의 내용을 {해시: bytes}로 돌려준다. 실패하면 원인을 출력하고 None을 돌려준다.

    파일마다 Git을 따로 부르면 이동이 많은 커밋(REQ-032)에서 수천 번 실행되므로 한 번의 --batch 호출로 읽는다.
    """
    unique = sorted(set(shas))
    if not unique:
        return {}
    cmd = ["git", "cat-file", "--batch"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, input=("\n".join(unique) + "\n").encode("ascii"))
    if res.returncode != 0:
        print(f"[FAIL] 커밋 대상의 내용을 읽을 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None
    out, pos, blobs = res.stdout, 0, {}
    for sha in unique:
        end = out.index(b"\n", pos)
        header = out[pos:end].decode("ascii", "replace").split()
        pos = end + 1
        if len(header) != 3:
            print(f"[FAIL] 커밋 대상의 내용을 읽을 수 없습니다: {sha} ({' '.join(header)})")
            print("       조치: git fsck로 저장소 상태를 확인한 뒤 다시 실행하십시오.")
            return None
        size = int(header[2])
        blobs[sha] = out[pos:pos + size]
        pos += size + 1
    return blobs


def read_contents(paths, staged):
    """경로 목록의 내용을 {경로: bytes}로 돌려준다. 커밋 대상(작업 트리 검사는 작업 트리)에 없는 경로는 빠진다.

    --staged는 커밋되는 내용인 index의 blob을, 작업 트리 검사는 작업 트리 파일을 읽는다.
    읽기에 실패하면 원인을 출력하고 None을 돌려준다.
    """
    contents = {}
    if staged:
        entries = index_entries()
        if entries is None:
            return None
        wanted = {p: entries[p] for p in paths if p in entries}
        blobs = read_blobs(wanted.values())
        if blobs is None:
            return None
        return {p: blobs[sha] for p, sha in wanted.items()}
    for rel in paths:
        path = ROOT_DIR / rel
        if not path.is_file():
            continue
        try:
            contents[rel] = path.read_bytes()
        except OSError as e:
            print(f"[FAIL] 파일을 읽을 수 없습니다: {rel}")
            print(f"       원인: {type(e).__name__}: {e}")
            print("       조치: 파일 권한과 잠금 상태를 확인한 뒤 다시 실행하십시오.")
            return None
    return contents


def check_close_record_names(files, staged):
    """순서 7 앞. 커밋 대상에 있는 종결 기록의 위치·이름이 형식에 맞으면 True, 아니면 False를 돌려준다.

    종결 기록은 대조 제외 구역(비서팀 assets/) 안에 있어 순서 8의 대조를 받지 않는다.
    이름이 틀린 종결 기록은 끝난 기록 판단에 쓰이지 않으므로, 확인하지 않으면 아무 출력 없이 효력을 잃고
    끝난 안건이 통과 근거로 남는다. 그래서 대조 제외와 Lab/ 처리보다 먼저 확인해
    종결 기록만 담은 커밋도 이 확인을 받게 한다 (REQ-028)
    """
    in_index = index_paths() if staged else None
    if staged and in_index is None:
        return False
    bad = []
    for rel in files:
        if not is_close_record_candidate(rel):
            continue
        # 지운 파일과 이름 변경의 원래 경로는 커밋 대상에 없으므로 대상이 아니다
        if staged and rel not in in_index:
            continue
        if not staged and not (ROOT_DIR / rel).is_file():
            continue
        if close_record_name(rel) is None:
            bad.append(rel)
    if bad:
        print("[FAIL] 종결 기록의 위치나 이름이 형식에 맞지 않습니다:")
        for rel in bad:
            print(f"  - {rel}")
        print(f"       원인: 종결 기록은 {CLOSE_DIR_REL}/ 바로 아래에 "
              f"{CLOSE_PREFIX}<YYYYMMDD>_<기록 이름>.md 형식(정규식 {CLOSE_NAME.pattern})으로 두어야 합니다.")
        print(f"       조치: {CLOSE_SOURCE} 형식으로 위치와 이름을 바꿔 다시 스테이징하십시오.")
        return False
    return True


def load_closed_records():
    """HEAD에 커밋된 종결 기록을 {기록 이름: 경로}로 돌려준다. 조회에 실패하면 None을 돌려준다.

    --staged 검사와 작업 트리 검사 모두 HEAD만 읽는다. 커밋된 종결 기록만 효력이 있으므로(Workflow/07 「종결 기록」),
    안건을 끝내는 커밋에 그 종결 기록을 함께 넣어도 그 커밋의 검사에서는 그 안건이 통과 근거로 남는다.
    index나 작업 트리를 읽으면 그 안건 자신의 커밋이 막히고, 두 검사의 판단이 어긋난다 (REQ-028)
    """
    cmd = ["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", "-z", "HEAD", "--",
           CLOSE_DIR_REL + "/"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        print(f"[FAIL] HEAD의 종결 기록 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None
    closed = {}
    for rel in res.stdout.decode("utf-8", "replace").split("\0"):
        # 판단 대상은 폴더 바로 아래의 파일뿐이다(Workflow/06 「끝난 기록(구현)」). 내용은 읽지 않는다
        if not rel or rel.rpartition("/")[0] != CLOSE_DIR_REL or not is_close_record_candidate(rel):
            continue
        name = close_record_name(rel)
        if name is None:
            print(f"[WARN] 형식에 맞지 않는 종결 기록이어서 끝난 기록 판단에 쓰지 않습니다: {rel}")
            print(f"       조치: {CLOSE_SOURCE} 형식의 종결 기록을 새로 만들어 커밋하고 대표님께 보고하십시오.")
            continue
        closed.setdefault(name, rel)
    return closed


def load_records(closed):
    """(승인되었고 끝나지 않은 기록 목록, 승인되지 않은 기록과 사유 목록, 끝난 기록과 종결 기록 경로 목록)을 돌려준다.

    closed는 load_closed_records()의 결과다. 판단 단위는 기록 이름이며 버전과 관계없다
    (REQ-010과 REQ-010-1은 다른 기록이다). HOTFIX는 한 위치(HOTFIX_DIR_REL)에서만 읽는다(REQ-032에서
    옛 두 위치의 HOTFIX를 이 위치로 옮겼다).
    """
    approved, rejected, ended = [], [], []
    for f in load_latest(ROOT_DIR / REQ_DIR_REL, "REQ"):
        rec = parse_header(f, "approved")
        rec["kind"] = "REQ"
        rec["record"] = f"REQ-{RECORD_NAME.match(f.name).group(2)}"
        problem = approval_problem(rec, "approved")
        (rejected if problem else approved).append((rec, problem))
    for f in load_latest(ROOT_DIR / HOTFIX_DIR_REL, "HOTFIX"):
        rec = parse_header(f, "confirmed")
        rec["kind"] = "HOTFIX"
        rec["record"] = f"HOTFIX-{RECORD_NAME.match(f.name).group(2)}"
        problem = approval_problem(rec, "confirmed")
        # 항목 수 검사는 기록만으로 판단할 수 있는 요건이다. 항목 하나가 폴더이면 여러 파일을 덮으므로
        # 실제 변경 파일 수는 변경 목록을 알아야 하며 hotfix_file_count_problem()이 따로 검사한다
        if not problem and not 1 <= len(rec["scope"]) <= HOTFIX_MAX_SCOPE:
            problem = f"scope 항목 {len(rec['scope'])}개(허용 1~{HOTFIX_MAX_SCOPE}개)"
        if not problem:
            governance = sorted(s for s in rec["scope"] if is_governance_path(s))
            if governance:
                problem = f"scope에 핫픽스 제외 경로 포함: {', '.join(governance)} - 거버넌스 파일·CEO/·_archive/는 핫픽스 대상이 아님"
        (rejected if problem else approved).append((rec, problem))
    # 승인 요건을 갖추지 못한 기록은 끝났어도 rejected에 사유와 함께 둔다(통과 근거가 아닌 것은 같다)
    still_open = []
    for rec, _ in approved:
        if rec["record"] in closed:
            ended.append((rec, closed[rec["record"]]))
        else:
            still_open.append(rec)
    if ended:
        print(f"[INFO] 끝난 기록 {len(ended)}건을 통과 근거에서 뺍니다(HEAD의 종결 기록): "
              f"{', '.join(rec['record'] for rec, _ in ended)}")
    return still_open, rejected, ended


def hotfix_file_count_problem(rec, files):
    """HOTFIX가 덮는 변경 파일이 허용 수를 넘으면 사유를, 아니면 None을 돌려준다.

    scope 항목 수만 세면 폴더 항목 하나로 「수정 파일 3개 이하」 조건을 넘을 수 있다.
    covers()가 참일 때만 부르므로 files 전체가 그 HOTFIX로 덮이는 파일이다.
    """
    if rec["kind"] == "HOTFIX" and len(files) > HOTFIX_MAX_SCOPE:
        return f"덮는 변경 파일 {len(files)}개(허용 {HOTFIX_MAX_SCOPE}개 이하)"
    return None


# 기록 문서의 버전 접미사(_vNN). scope에 버전 없이 적은 항목이 모든 버전을 포함하게 한다
VERSION_SUFFIX = re.compile(r"_v\d{2}$")


def item_covers(s, f):
    """scope 항목 s가 변경 파일 f를 포함하는지 판단한다."""
    if f == s or f.startswith(s + "/"):
        return True
    # 확장자·버전을 떼고 비교하는 규칙은 확장자 없이 적은 scope 항목에만 적용한다
    if os.path.splitext(s.rsplit("/", 1)[-1])[1]:
        return False
    f_no_ext = os.path.splitext(f)[0]
    return f_no_ext == s or VERSION_SUFFIX.sub("", f_no_ext) == s


def covers(rec, files):
    return all(any(item_covers(s, f) for s in rec["scope"]) for f in files)


def changed_files(staged):
    """변경 파일 목록을 돌려준다. Git 조회에 실패하면 None을 돌려준다."""
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ROOT_DIR,
                         capture_output=True, encoding="utf-8", errors="replace")
    if top.returncode != 0:
        print(f"[FAIL] Git 저장소 루트를 조회할 수 없습니다 (종료 코드 {top.returncode}).")
        print(f"       원인: {top.stderr.strip()}")
        print("       조치: 저장소 작업 트리에서 실행했는지와 .git 폴더 상태를 확인하십시오.")
        return None
    git_root = Path(top.stdout.strip())

    if staged:
        # 커밋 대상(index)만 조회한다. -z: 경로를 따옴표·이스케이프 없이 받는다
        cmd = ["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-status", "-M", "-z"]
    else:
        # -uall: 새 폴더 안의 파일을 폴더 한 줄이 아닌 파일 단위로 받는다
        cmd = ["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall", "-z"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[FAIL] Git 변경 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None

    # 이름 변경은 원래 경로와 새 경로를 모두 대조한다
    paths = []
    tokens = res.stdout.split("\0")
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if not tok:
            i += 1
            continue
        if staged:
            status = tok
            count = 2 if status[:1] in ("R", "C") else 1
            paths.extend(tokens[i + 1:i + 1 + count])
            i += 1 + count
        else:
            status, path = tok[:2], tok[3:]
            paths.append(path)
            if "R" in status or "C" in status:
                paths.append(tokens[i + 1])  # -z 형식은 새 경로 뒤에 원래 경로를 둔다
                i += 1
            i += 1

    result = []
    for target in paths:
        try:
            rel = (git_root / target).resolve().relative_to(ROOT_DIR.resolve())
            result.append(rel.as_posix())
        except ValueError:
            print(f"[INFO] 표준 루트 밖 경로를 검사에서 제외합니다: {target}")
    return result


def pure_rename_targets():
    """커밋 대상에서 내용이 같은 이름 변경(R100)의 새 경로 집합을 돌려준다. 조회에 실패하면 None을 돌려준다."""
    cmd = ["git", "-c", "core.quotepath=false", "diff", "--cached", "--name-status", "-M", "-z"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print(f"[FAIL] Git 변경 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None
    tokens, targets, i = res.stdout.split("\0"), set(), 0
    while i < len(tokens):
        status = tokens[i]
        if not status:
            i += 1
            continue
        count = 2 if status[:1] in ("R", "C") else 1
        if status == "R100":
            targets.add(tokens[i + 2])
        i += 1 + count
    return targets


# ---------------------------------------------------------------- 비밀정보 검출 (순서 4, --scan-all)

def load_secret_allowlist():
    """예외 목록을 {(규칙 이름, 경로)} 집합으로 돌려준다. 형식 오류나 읽기 실패면 None을 돌려준다."""
    path = ROOT_DIR / SECRET_ALLOWLIST_REL
    if not path.is_file():
        # 예외 없이 검사하는 쪽이 더 엄격하므로 실패로 처리하지 않는다
        print(f"[INFO] 비밀정보 검출 예외 목록이 없어 예외 없이 검사합니다: {SECRET_ALLOWLIST_REL}")
        return set()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        print(f"[FAIL] 비밀정보 검출 예외 목록을 읽을 수 없습니다: {SECRET_ALLOWLIST_REL}")
        print(f"       원인: {type(e).__name__}: {e}")
        print("       조치: 파일이 UTF-8 텍스트인지와 읽기 권한을 확인하고, 해결되지 않으면 대표님께 보고하십시오.")
        return None
    entries, problems = set(), []
    for line_no, raw in enumerate(text.split("\n"), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        rule = parts[0]
        rel = parts[1].strip().replace("\\", "/") if len(parts) > 1 else ""
        # 항목 내용은 출력하지 않는다. 잘못 적은 값이 비밀정보일 수 있기 때문이다
        if rule not in SECRET_RULE_NAMES:
            problems.append((line_no, "규칙 이름이 SECRET_RULES에 없습니다"))
        elif not rel:
            problems.append((line_no, "경로가 비어 있습니다"))
        else:
            entries.add((rule, rel))
    if problems:
        print(f"[FAIL] 비밀정보 검출 예외 목록에 잘못된 항목이 있습니다: {SECRET_ALLOWLIST_REL}")
        for line_no, reason in problems:
            print(f"  - {line_no}행: {reason}")
        print("       원인: 항목 줄은 「<규칙 이름> <저장소 루트 기준 상대 경로>」 형식이어야 합니다.")
        print(f"       조치: 예외 목록은 에이전트가 고치지 않습니다. 줄 번호를 대표님께 보고하십시오({SECRET_SOURCE}).")
        return None
    return entries


def find_secrets(data):
    """바이트 내용에서 (줄 번호, 규칙 이름)을 차례로 돌려준다. 한 줄에 여러 규칙이 맞으면 규칙마다 한 건이다."""
    text = data.decode("utf-8", errors="replace")
    # str.splitlines()는 \n 밖의 문자(\x0c 등)에서도 줄을 나눠 편집기의 줄 번호와 어긋나므로 \n으로만 나눈다
    for line_no, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        for name, pattern in SECRET_RULES:
            if pattern.search(line):
                yield line_no, name


def read_content(rel, staged):
    """대상 파일 하나의 내용을 bytes로 돌려준다. 읽기에 실패하면 원인을 출력하고 None을 돌려준다."""
    contents = read_contents([rel], staged)
    if contents is None:
        return None
    if rel not in contents:
        print(f"[FAIL] 비밀정보 검출: 파일을 읽을 수 없습니다: {rel}")
        print("       조치: 파일이 있는지 확인한 뒤 다시 실행하십시오.")
        return None
    return contents[rel]


def print_excluded(excluded):
    for (rel, rule), n in sorted(excluded.items()):
        print(f"[INFO] 예외 목록으로 뺀 검출: {rel} [{rule}] {n}건")


def print_secret_failure(lines, target_desc):
    print("[FAIL] 비밀정보로 보이는 값을 찾았습니다(값은 출력하지 않습니다).")
    for line in lines:
        print(f"  - {line}")
    print(f"       원인: 검출 규칙에 맞는 값이 {target_desc}에 있습니다.")
    print("       조치: 값을 지우고 비밀정보는 저장소 밖이나 .gitignore 대상 파일에 둔 뒤, 다시 스테이징하고 커밋하십시오.")
    print("             오탐으로 보이면 값을 고치거나 예외를 등록하지 말고 커밋을 멈춘 뒤, "
          f"대표님께 경로와 규칙 이름을 보고하십시오({SECRET_SOURCE}).")


def check_secrets(files, staged):
    """순서 4. 검출이 없으면 True, 검출이 있거나 읽기에 실패하면 False를 돌려준다."""
    allow = load_secret_allowlist()
    if allow is None:
        return False
    # 지운 파일과 이름 변경의 원래 경로는 커밋될 내용이 없으므로 read_contents()가 빼 준다
    contents = read_contents(files, staged)
    if contents is None:
        return False

    findings, excluded, scanned = [], Counter(), 0
    for rel in files:
        data = contents.get(rel)
        if data is None:
            continue
        if b"\0" in data:
            print(f"[INFO] 비밀정보 검출: 이진 파일이어서 뺍니다: {rel}")
            continue
        scanned += 1
        for line_no, rule in find_secrets(data):
            if (rule, rel) in allow:
                excluded[(rel, rule)] += 1
            else:
                findings.append(f"{rel}:{line_no} [{rule}]")

    print_excluded(excluded)
    if findings:
        print_secret_failure(findings, "커밋 대상" if staged else "변경 파일")
        return False
    if scanned:
        print(f"[PASS] 비밀정보 검출: 대상 파일 {scanned}개에서 검출 없음.")
    else:
        print("[PASS] 비밀정보 검출: 대상 파일 없음.")
    return True


def history_findings():
    """커밋 이력 전체의 추가 줄에서 [(커밋 짧은 해시, 경로, 규칙 이름)]을 돌려준다. 조회 실패면 None."""
    # \x01로 시작하는 줄을 커밋 머리로 쓴다. diff 본문 줄은 늘 +, -, 공백, \ 또는 머리 글자로 시작하므로 겹치지 않는다
    cmd = ["git", "-c", "core.quotepath=false", "log", "--all", "-p", "--no-color", "--no-ext-diff",
           "--no-textconv", "--format=%x01%h"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        print(f"[FAIL] 비밀정보 검출: 커밋 이력을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return None
    found, seen = [], set()
    commit, path, in_hunk = None, None, False
    for line in res.stdout.decode("utf-8", "replace").split("\n"):
        if line.startswith("\x01"):
            commit, path, in_hunk = line[1:].strip(), None, False
            continue
        if line.startswith("diff --git "):
            path, in_hunk = None, False
            continue
        if not in_hunk:
            if line.startswith("+++ "):
                # 공백이 든 경로는 Git이 줄 끝에 탭을 붙이므로 뗀다
                target = line[4:].rstrip("\t\r").strip('"')
                path = None if target == "/dev/null" else (target[2:] if target.startswith("b/") else target)
            elif line.startswith("@@"):
                in_hunk = True
            continue
        if path and line.startswith("+"):
            for _, rule in find_secrets(line[1:].encode("utf-8")):
                key = (commit, path, rule)
                if key not in seen:
                    seen.add(key)
                    found.append(key)
    return found


def scan_all():
    """--scan-all. 추적 파일 전체(CEO/ 포함)와 커밋 이력 전체를 검출한다. 커밋을 막지 않는 점검용이다."""
    allow = load_secret_allowlist()
    if allow is None:
        return False
    cmd = ["git", "-c", "core.quotepath=false", "ls-files", "-z"]
    res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True)
    if res.returncode != 0:
        print(f"[FAIL] 비밀정보 검출: 추적 파일 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
        print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
        print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
        return False
    tracked = [p for p in res.stdout.decode("utf-8", "replace").split("\0") if p]

    file_hits, excluded, scanned = [], Counter(), 0
    for rel in tracked:
        if not (ROOT_DIR / rel).is_file():
            print(f"[INFO] 비밀정보 검출: 작업 트리에 없는 추적 파일이어서 뺍니다: {rel}")
            continue
        data = read_content(rel, staged=False)
        if data is None:
            return False
        if b"\0" in data:
            print(f"[INFO] 비밀정보 검출: 이진 파일이어서 뺍니다: {rel}")
            continue
        scanned += 1
        for line_no, rule in find_secrets(data):
            if (rule, rel) in allow:
                excluded[(rel, rule)] += 1
            else:
                file_hits.append(f"{rel}:{line_no} [{rule}]")

    history = history_findings()
    if history is None:
        return False
    history_hits = []
    for commit, rel, rule in history:
        if (rule, rel) in allow:
            excluded[(rel, rule)] += 1
        else:
            history_hits.append(f"{commit} {rel} [{rule}]")

    print_excluded(excluded)
    print(f"[INFO] 비밀정보 검출(--scan-all): 추적 파일 {scanned}개, 커밋 이력 전체를 검사했습니다.")
    if file_hits or history_hits:
        print(f"[FAIL] 비밀정보로 보이는 값을 찾았습니다(값은 출력하지 않습니다). "
              f"추적 파일 {len(file_hits)}건, 커밋 이력 {len(history_hits)}건.")
        if file_hits:
            print("  추적 파일:")
            for line in file_hits:
                print(f"  - {line}")
        if history_hits:
            print("  커밋 이력:")
            for line in history_hits:
                print(f"  - {line}")
        print("       원인: 검출 규칙에 맞는 값이 추적 파일 또는 커밋 이력에 있습니다.")
        print(f"       조치: 보안 점검 결과서에 위험으로 적고 대표님의 조치 결정을 받으십시오({SECRET_SOURCE}).")
        return False
    print("[PASS] 비밀정보 검출(--scan-all): 검출 없음.")
    return True


# ---------------------------------------------------------------- 작성 파트 대조 (순서 5)

def header_agent(data):
    """머리말(---로 시작하는 YAML)의 author: 또는 auditor: 아래 agent: 값을 돌려준다. 없으면 None."""
    lines = data.decode("utf-8", errors="replace").lstrip("﻿").split("\n")
    if not lines or lines[0].rstrip("\r").strip() != "---":
        return None
    section = None
    for raw in lines[1:]:
        line = raw.rstrip("\r")
        if line.strip() == "---":
            break
        if line and not line[0].isspace():
            key = line.split(":", 1)[0].strip()
            section = key if key in ("author", "auditor") else None
            continue
        if section and line.strip().startswith("agent:"):
            return strip_value(line.strip()[len("agent:"):])
    return None


def parts_for_agent(agent):
    """작성 주체 값의 파트 목록을 돌려준다. 파트 코드도 부 표기도 아니면 None."""
    if PART_CODE.match(agent) and agent in PART_WRITE_PATHS:
        return (agent,)
    return DEPT_PARTS.get(agent)


def head_has_this_script():
    """HEAD에 이 스크립트가 새 위치로 커밋되어 있는지 돌려준다(작성 파트 대조의 적용 시점, REQ-032 D9)."""
    res = subprocess.run(["git", "cat-file", "-e", f"HEAD:{SCRIPTS_DIR_REL}/check_standard.py"],
                         cwd=ROOT_DIR, capture_output=True)
    return res.returncode == 0


def check_author_parts(files, staged):
    """순서 5. 대조에 맞으면 True, 맞지 않는 파일이 있거나 조회에 실패하면 False를 돌려준다."""
    if not head_has_this_script():
        print(f"[INFO] 작성 파트 대조: HEAD에 {SCRIPTS_DIR_REL}/check_standard.py가 없어 생략합니다"
              "(작성 파트 대조는 REQ-032 커밋 뒤의 커밋부터 적용).")
        return True
    targets = [f for f in files if f.startswith("Departments/")]
    if staged:
        # 내용이 같은 이름 변경은 작성이 아니므로 뺀다
        renamed = pure_rename_targets()
        if renamed is None:
            return False
        targets = [f for f in targets if f not in renamed]
    contents = read_contents(targets, staged)
    if contents is None:
        return False
    bad, checked = [], 0
    for rel in targets:
        data = contents.get(rel)
        if data is None or b"\0" in data:
            continue
        agent = header_agent(data)
        if agent is None:
            continue
        checked += 1
        parts = parts_for_agent(agent)
        if parts is None:
            bad.append((rel, agent, None))
            continue
        allowed = sorted({p for part in parts for p in PART_WRITE_PATHS[part]})
        if not any(rel.startswith(p) for p in allowed):
            bad.append((rel, agent, allowed))
    if bad:
        print("[FAIL] 작성 파트 대조: 작성 주체의 쓰기 경로 밖에 있는 파일이 있습니다:")
        for rel, agent, allowed in bad:
            print(f"  - {rel}")
            print(f"    작성 주체 값: {agent}")
            if allowed is None:
                print("    허용 경로: 없음(원인: 값이 Workflow/07_문서_서식_및_번호 「머리말」의 작성 주체 값"
                      "(부 표기나 파트 코드)이 아님)")
            else:
                print(f"    허용 경로: {', '.join(allowed) if allowed else '없음(이 파트의 고정 쓰기 경로 없음)'}")
        print(f"       조치: {AUTHOR_SOURCE}의 쓰기 경로로 파일을 옮기거나 머리말 작성 주체를 확인하십시오.")
        return False
    print(f"[PASS] 작성 파트 대조: 작성 주체 칸이 있는 파일 {checked}개가 쓰기 경로 안에 있습니다.")
    return True


# ---------------------------------------------------------------- 옛 경로 잔존 검사 (순서 6)

def residual_target(rel):
    """옛 경로 잔존 검사의 대상 파일인지 돌려준다(파일 단위로 뺄 범위를 뺀다)."""
    if rel.startswith(RESIDUAL_EXCLUDED_TOP):
        return False
    parts = rel.split("/")
    # 팀 폴더(Departments/<부>/<팀>/)의 results/·workspace/ 아래 전체는 이미 작성된 기록의 위치다
    if len(parts) >= 5 and parts[0] == "Departments" and parts[3] in ("results", "workspace"):
        return False
    return not rel.startswith(RESIDUAL_RECORD_PREFIXES)


def residual_lines(rel, text):
    """줄 단위로 뺄 범위(Markdown 개정 이력 H2부터 끝, 02의 2.3절)를 뺀 (줄 번호, 줄) 목록을 돌려준다."""
    keep, in_mapping = [], False
    for no, line in enumerate(text.split("\n"), 1):
        line = line.rstrip("\r")
        if rel.endswith(".md") and REVISION_HISTORY_HEADING.match(line):
            break
        if rel == MAPPING_DOC_REL:
            if MAPPING_HEADING.match(line):
                in_mapping = True
                continue
            if in_mapping and SECTION_HEADING.match(line):
                in_mapping = False
            if in_mapping:
                continue
        keep.append((no, line))
    return keep


def residual_candidates(staged):
    """대상 후보 경로 목록. --staged는 index의 추적 파일, 작업 트리 검사는 추적 파일과 미추적 파일이다."""
    if staged:
        entries = index_entries()
        return None if entries is None else sorted(entries)
    paths = []
    for extra in ([], ["--others", "--exclude-standard"]):
        cmd = ["git", "-c", "core.quotepath=false", "ls-files", "-z", *extra]
        res = subprocess.run(cmd, cwd=ROOT_DIR, capture_output=True)
        if res.returncode != 0:
            print(f"[FAIL] 옛 경로 잔존 검사: 파일 목록을 조회할 수 없습니다 (종료 코드 {res.returncode}).")
            print(f"       원인: {res.stderr.decode('utf-8', 'replace').strip()}")
            print(f"       조치: {' '.join(cmd)}를 직접 실행해 오류를 해결한 뒤 다시 실행하십시오.")
            return None
        paths += [p for p in res.stdout.decode("utf-8", "replace").split("\0") if p]
    return sorted(set(paths))


def check_old_paths(staged):
    """순서 6. 옛 경로가 없으면 True, 남았거나 조회에 실패하면 False를 돌려준다."""
    candidates = residual_candidates(staged)
    if candidates is None:
        return False
    targets = [p for p in candidates if residual_target(p)]
    print("[INFO] 옛 경로 잔존 검사: 뺀 범위 - 폴더 전체: " + ", ".join(RESIDUAL_EXCLUDED_TOP)
          + ", 팀 폴더(Departments/<부>/<팀>/)의 results/·workspace/, " + ", ".join(RESIDUAL_RECORD_PREFIXES)
          + f" / 줄 단위: Markdown 파일의 「개정 이력」 H2 제목부터 끝, {MAPPING_DOC_REL}의 2.3절."
          + f" 대상 파일 {len(targets)}개.")
    contents = read_contents(targets, staged)
    if contents is None:
        return False
    hits = []
    for rel in targets:
        data = contents.get(rel)
        if data is None or b"\0" in data:
            continue
        for no, line in residual_lines(rel, data.decode("utf-8", errors="replace")):
            for pattern in OLD_PATH_PATTERNS:
                m = pattern.search(line)
                if m:
                    hits.append(f"{rel}:{no}: {m.group(0)}")
                    break
    if hits:
        print("[FAIL] 옛 경로 잔존 검사: 옛 경로가 남은 줄이 있습니다:")
        for hit in hits:
            print(f"  - {hit}")
        print("       원인: REQ-032 커밋 전의 옛 경로(부서 폴더 바로 아래의 공통 하위 폴더)가 남아 있습니다.")
        print(f"       조치: {RESIDUAL_SOURCE}의 대응대로 새 경로로 고친 뒤 다시 스테이징하십시오.")
        return False
    print("[PASS] 옛 경로 잔존 검사: 대상 파일에 옛 경로가 없습니다.")
    return True


def run_tests(work_files):
    if not any("assets/src/" in f or "assets/tests/" in f for f in work_files):
        print("[PASS] 소스코드·테스트 변경 없음: 단위 테스트를 생략합니다.")
        return True
    test_dir = ROOT_DIR / TEST_DIR_REL
    if not (test_dir.exists() and list(test_dir.rglob("test_*.py"))):
        print(f"[WARN] 소스코드·테스트 변경이 있으나 테스트 파일(test_*.py)이 없습니다: {TEST_DIR_REL}")
        return True
    print("[CHECK] 소스코드·테스트 변경 감지: 단위 테스트를 실행합니다.")
    code = subprocess.run([sys.executable, "-m", "pytest", str(test_dir)], cwd=ROOT_DIR).returncode
    if code == 5:
        print("[WARN] 수집된 단위 테스트가 없습니다 (pytest 종료 코드 5).")
        return True
    if code != 0:
        print(f"[FAIL] 단위 테스트 실패 (종료 코드 {code})")
        return False
    print("[PASS] 단위 테스트 통과.")
    return True


def check_standard(staged=False):
    if is_initial_commit():
        print("[PASS] 초기화 커밋으로 확인되어 검사를 생략합니다.")
        return True

    files = changed_files(staged)
    if files is None:
        return False
    if not files:
        print("[PASS] 변경된 파일이 없습니다.")
        return True

    # 대표님이 CEO/를 커밋하지 않은 채 써도 파이프라인이 멈추지 않게 작업 트리 검사에서는 빼고,
    # 커밋 때는 CEO/ 변경과 다른 변경이 한 커밋에 섞이지 않게 막는다 (REQ-013).
    # 섞임 판단은 대조 제외(순서 7)보다 먼저 해야 제외 구역 경로와 섞인 커밋도 막힌다.
    # 이름 변경은 changed_files()가 두 경로를 따로 돌려주므로 경로마다 판별된다
    ceo = [f for f in files if f.startswith("CEO/")]
    others = [f for f in files if not f.startswith("CEO/")]
    if ceo and not staged:
        print("[INFO] CEO/ 아래 변경은 작업 트리 검사에서 뺍니다(대표님 구역):")
        for f in ceo:
            print(f"  - {f}")
        if not others:
            print("[PASS] 변경 파일이 모두 CEO/ 아래에 있습니다.")
            return True
    elif ceo and others:
        print("[FAIL] CEO/ 아래 변경과 그 밖의 변경이 한 커밋에 섞여 있습니다.")
        print("  CEO/ 아래 변경:")
        for f in ceo:
            print(f"  - {f}")
        print("  그 밖의 변경:")
        for f in others:
            print(f"  - {f}")
        print("       원인: CEO/ 변경은 그 밖의 변경과 따로 커밋해야 합니다(Workflow/06_통제장치_및_배포 「대표님 전용 구역의 커밋」).")
        print("       조치: git restore --staged <경로>로 한쪽을 스테이징에서 빼고 나눠 커밋하십시오.")
        return False
    elif ceo:
        print("[PASS] 커밋 대상이 모두 CEO/ 아래 변경입니다(대표님 구역). scope 대조를 생략합니다.")
        return True
    files = others

    # 파이프라인 밖 실험 커밋은 대조할 REQ가 없으므로 Lab/ 변경만 담은 커밋은 scope 대조 없이 통과시킨다.
    # 실험 파일이 다른 안건 커밋에 섞이는 것은 섞인 커밋만 scope로 막는다: Lab/ 경로를 빼지 않고
    # 순서 7·8로 넘겨 그 밖의 경로와 함께 승인되었고 끝나지 않은 REQ 하나의 scope 안에 있어야 통과하게 한다 (REQ-016).
    # 작업 트리 검사에서 빼는 이유는 CEO/와 같다(커밋하지 않은 실험 파일 때문에 다른 안건의 검사가 멈추지 않게 한다).
    # Lab/ 처리는 비밀정보 검출 대상을 줄이지 않으므로, 통과와 경로 제외는 순서 4를 마친 뒤에 한다 (REQ-018)
    lab = [f for f in files if f.startswith(LAB_PREFIX)]
    lab_only = bool(lab) and len(lab) == len(files)
    if lab and not staged:
        print("[INFO] Lab/ 아래 변경은 작업 트리 검사에서 뺍니다(실험실):")
        for f in lab:
            print(f"  - {f}")

    if not check_secrets(files, staged):
        return False

    # 순서 7 앞: 종결 기록의 위치·이름 확인. 이유는 check_close_record_names()의 설명 (REQ-028)
    if not check_close_record_names(files, staged):
        return False

    if lab_only:
        if staged:
            print("[PASS] 커밋 대상이 모두 Lab/ 아래 변경입니다(실험실). scope 대조를 생략합니다.")
        else:
            print("[PASS] CEO/·Lab/ 밖의 변경 파일이 없습니다.")
        return True
    if lab and not staged:
        files = [f for f in files if not f.startswith(LAB_PREFIX)]

    # 순서 5: 작성 파트 대조. 대조 제외 구역의 파일도 대상이므로 순서 7보다 먼저 한다 (REQ-032)
    if not check_author_parts(files, staged):
        return False

    # 순서 6: 옛 경로 잔존 검사. 변경 파일이 아니라 대상 범위 전체를 본다 (REQ-032)
    if not check_old_paths(staged):
        return False

    # 순서 7: 대조 제외
    work_files = [f for f in files if not is_whitelisted(f)]
    if not work_files:
        print("[PASS] 모든 변경 파일이 scope 대조 제외 구역 안에 있습니다.")
        return True

    # 순서 8: scope 대조와 승인
    closed = load_closed_records()
    if closed is None:
        return False
    approved, rejected, ended = load_records(closed)
    covering = [r for r in approved if covers(r, work_files)]
    # 파일 수를 넘은 HOTFIX는 건너뛰고, 같은 변경 파일을 덮는 승인되었고 끝나지 않은 REQ가 있으면 그 REQ로 통과시킨다
    matched = next((r for r in covering if not hotfix_file_count_problem(r, work_files)), None)
    if matched:
        print(f"[PASS] 변경 파일이 {matched['name']} (승인: {matched['approved']})의 scope 안에 있습니다.")
        # 순서 9: 조건부 테스트
        return run_tests(work_files)

    print("[FAIL] 변경 파일 전체를 포함하는 승인되었고 끝나지 않은 REQ 또는 확인되었고 끝나지 않은 HOTFIX가 없습니다. 대상 파일:")
    for f in work_files:
        print(f"  - {f}")
    for rec in covering:
        print(f"       참고: {rec['name']}의 scope는 대상 파일을 포함하지만 핫픽스 파일 수 조건을 넘습니다 "
              f"({hotfix_file_count_problem(rec, work_files)}).")
    for rec, problem in rejected:
        if covers(rec, work_files):
            print(f"       참고: {rec['name']}의 scope는 대상 파일을 포함하지만 승인 요건을 갖추지 못했습니다 ({problem}).")
    for rec, close_path in ended:
        if covers(rec, work_files):
            print(f"       참고: {rec['name']}의 scope는 대상 파일을 포함하지만 끝난 안건이어서 통과 근거로 쓰지 않습니다"
                  f"(종결 기록 {close_path}). 다시 할 일은 파생 안건이나 새 REQ로 진행하십시오"
                  "(Workflow/03_라이프사이클 「진행 중 변경과 파생 안건」).")
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--scan-all" in args:
        if not scan_all():
            sys.exit(1)
        print("[SUCCESS] 비밀정보 검출(--scan-all) 통과.")
        sys.exit(0)
    if not check_standard(staged="--staged" in args):
        sys.exit(1)
    print("[SUCCESS] 바이브 표준 v05 커밋 전 검사 통과.")
    sys.exit(0)
