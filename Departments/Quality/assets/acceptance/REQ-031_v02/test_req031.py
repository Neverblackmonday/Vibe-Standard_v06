# -*- coding: utf-8 -*-
"""REQ-031 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상
- 현행 거버넌스 파일(REQ-031 5절 머리 안내): AGENTS.md, CLAUDE.md, Workflow/ 전체, .claude/ 전체, check_standard.py에서
  적용본이 있는 파일은 적용본, 없는 파일은 원본. 적용본은 개발 적용본(Departments/Development/workspace/REQ-031_적용본_vNN의
  가장 높은 버전), 설계 적용본(Departments/Design/workspace/REQ-031_적용본_vNN의 가장 높은 버전) 순으로 찾는다.
  적용본 안 경로는 Workflow/06 「거버넌스 파일 개정 절차」 2항의 이름 규칙(EC-031_v02 2.1절)을 따른다:
  AGENTS.md → AGENTS.md.적용본, Workflow/ → Workflow.적용본/, .claude/ → .claude.적용본/,
  Departments/Development/assets/scripts/ → Departments/Development/assets/scripts.적용본/.
- 「EC가 정한 위치」는 EC-031_v02 3.1절 표와 3.3절의 위치다.
- Grep 확인은 제목이 「개정 이력」인 절을 뺀다(REQ-031 5절 머리 안내).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 임시 Git 저장소는 pytest tmp_path 아래에만 만든다.
문장의 뜻(규정이 체크리스트의 뜻대로인지)은 최종 판정이 열람으로 본다(ACC-031 2절).
"""

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]

APPLIED_GLOB = "REQ-031_적용본_v[0-9][0-9]"
SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"
REQ_DIR_REL = "Departments/Secretariat/docs/requests"
HOTFIX_NEW_REL = "Departments/Development/results"
HOTFIX_OLD_REL = "Departments/Secretariat/results"

# 원본 경로 접두 → 적용본 안 경로 접두(EC-031_v02 2.1절, Workflow/06 「거버넌스 파일 개정 절차」 2항)
APPLIED_PREFIX = (
    ("AGENTS.md", "AGENTS.md.적용본"),
    ("CLAUDE.md", "CLAUDE.md.적용본"),
    ("Workflow/", "Workflow.적용본/"),
    (".claude/", ".claude.적용본/"),
    ("Departments/Development/assets/scripts/", "Departments/Development/assets/scripts.적용본/"),
)

AGENT_FILES = ("development.md", "engineering.md", "marketing.md", "operations.md", "quality.md")
DEPARTMENT_DIRS = {"Design", "Development", "Marketing", "Operations", "Quality", "Secretariat"}

# EC-031_v02 3.4절 1번의 PowerShell ask 규칙 13개(REQ-031 D18 ①)
POWERSHELL_ASK = (
    "PowerShell(git commit*)", "PowerShell(git push*)", "PowerShell(Remove-Item *)", "PowerShell(rm *)",
    "PowerShell(del *)", "PowerShell(erase *)", "PowerShell(rd *)", "PowerShell(rmdir *)", "PowerShell(ri *)",
    "PowerShell(Move-Item *)", "PowerShell(mv *)", "PowerShell(move *)", "PowerShell(mi *)",
)

# 조직 이름 검사 패턴. RPT-031_v02 4.5절 3번의 넓힌 패턴(EC-031_v02 3.5절 7번 패턴에 조사와 「:」을 더함)
OLD_ORG = re.compile(r"(?<![가-힣])(설계|개발|품질|운영|마케팅)(?=[이가은는을를의로와과에도만]|\s|·|\)|:|$)")
# EC-031_v02 G2의 「바꾸지 않는 것(조직이 아님)」과 비서실 「운영 방식」·「운영 기본값」(REQ-031 요구 항목 12)
ORG_ALLOWED = (
    "설계 단계", "설계 파라미터", "표준 자체의 설계", "기존 설계나", "세부 설계", "설계 결정",
    "품질 판정", "품질 평가", "항공 품질", "기능·품질",
    "운영 기록", "운영 중", "운영한다", "운영하는", "운영 방식", "운영 기본값", "운영 배포",
    "마케팅 전략",
)

SERVICE_NAMES = re.compile(r"코워크|Antigravity|채팅 서비스|claude\.ai 채팅")
OUTSIDE = "저장소 밖"
# 「저장소 밖」이 비서실을 가리키지 않는 문맥(EC-031_v02 3.9절 2번 「남기는 곳」, 3.3절 9번 ⑧)
OUTSIDE_ALLOWED = ("저장소 밖 세션", "저장소 밖이나", "저장소 밖에 있어")
MAIN_SESSION = "Claude Code 메인 세션"
MAIN_SESSION_DEF = "실행 명령으로 기동한 Claude Code 메인 세션"


# ---------------------------------------------------------------- 공통 도구

def _clean_env():
    env = dict(os.environ)
    # 훅 안에서 pytest를 돌려도 바깥 저장소를 가리키지 않게 Git 위치 변수를 지운다
    for key in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
                "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_PREFIX"):
        env.pop(key, None)
    env.update({
        "GIT_AUTHOR_NAME": "acc", "GIT_AUTHOR_EMAIL": "acc@example.invalid",
        "GIT_COMMITTER_NAME": "acc", "GIT_COMMITTER_EMAIL": "acc@example.invalid",
        "PYTHONIOENCODING": "utf-8",
        # 저장소 조회가 .git/index를 고쳐 쓰지 않게 한다
        "GIT_OPTIONAL_LOCKS": "0",
    })
    return env


ENV = _clean_env()


def git(cwd, *args, check=True, env=None):
    res = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false",
                          "-c", "core.quotepath=false", *args], cwd=cwd, capture_output=True, env=env or ENV)
    out = res.stdout.decode("utf-8", "replace")
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 실패({res.returncode}): {res.stderr.decode('utf-8', 'replace')}")
    return res.returncode, out


def _highest(folder, pattern, want_dir=True):
    found = sorted(p for p in folder.glob(pattern) if (p.is_dir() if want_dir else p.is_file()))
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


def applied_rel(rel):
    for src, dst in APPLIED_PREFIX:
        if rel == src or (src.endswith("/") and rel.startswith(src)):
            return dst + rel[len(src):]
    return None


def current_path(config, rel):
    """원본 경로 rel의 현행 파일(개발 적용본, 설계 적용본, 원본 순)."""
    a_rel = applied_rel(rel)
    if a_rel is not None:
        for folder in (dev_dir(config), design_dir(config)):
            if folder is not None and (folder / a_rel).is_file():
                return folder / a_rel
    return REPO / rel


def current_doc(config, rel):
    return current_path(config, rel).read_text(encoding="utf-8")


def original_doc(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def governance_rels(config):
    """현행 거버넌스 파일의 원본 경로 목록(REQ-031 5절 머리 안내). 적용본에만 있는 파일도 넣는다."""
    rels = {"AGENTS.md", "CLAUDE.md", SCRIPT_REL}
    _, out = git(REPO, "ls-files", "-z", "--", "Workflow", ".claude")
    rels.update(p for p in out.split("\0") if p)
    for folder in (dev_dir(config), design_dir(config)):
        if folder is None:
            continue
        for p in folder.rglob("*"):
            if not p.is_file():
                continue
            a = p.relative_to(folder).as_posix()
            for src, dst in APPLIED_PREFIX:
                if a == dst or (dst.endswith("/") and a.startswith(dst)):
                    rels.add(src + a[len(dst):])
    return sorted(r for r in rels if current_path(config, r).is_file())


def strip_history(text):
    """제목이 「개정 이력」인 절을 뺀 줄 목록 [(줄 번호, 줄)]."""
    out, skip = [], False
    for i, line in enumerate(text.splitlines(), 1):
        if re.match(r"^## (\d+\. )?개정 이력\s*$", line):
            skip = True
            continue
        if skip and re.match(r"^#{1,2} ", line):
            skip = False
        if not skip:
            out.append((i, line))
    return out


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


def item(text, label):
    """목록 항목 「- **label**: …」이나 번호 항목 「n. **label**: …」 한 줄."""
    pat = re.compile(r"^\s*(?:[-*]|\d+\.)\s+\*\*" + re.escape(label) + r"\*\*")
    for line in text.splitlines():
        if pat.match(line):
            return line
    raise AssertionError(f"항목을 찾지 못했습니다: **{label}**")


def table_row(text, first_cell):
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells and cells[0] == first_cell:
            return line
    raise AssertionError(f"표 행을 찾지 못했습니다: | {first_cell} |")


def require(text, words, where):
    missing = [w for w in words if w not in text]
    assert not missing, f"{where}에 없는 문구: {missing}"


def dev_result(config):
    opt = config.getoption("--acc-dev-result")
    path = _opt_path(opt) if opt else _highest(REPO / "Departments" / "Development" / "results",
                                               "DEV-031_v[0-9][0-9].md", want_dir=False)
    if path is None or not path.is_file():
        pytest.fail("개발 결과서(Departments/Development/results/DEV-031_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
    return path.read_text(encoding="utf-8")


def dev_section(config, keyword):
    """개발 결과서에서 제목에 keyword가 든 절들의 본문."""
    text = dev_result(config)
    lines = text.splitlines()
    parts = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and keyword in m.group(2):
            parts.append(section("\n".join(lines[i:]), re.escape(line) + "$"))
    if not parts:
        pytest.fail(f"개발 결과서에 제목에 「{keyword}」이 든 절이 없습니다.")
    return "\n".join(parts)


def current_settings(config):
    return json.loads(current_doc(config, ".claude/settings.json"))


def original_settings():
    return json.loads(original_doc(".claude/settings.json"))


# ---------------------------------------------------------------- 임시 저장소

APPROVED = "2026-10-20T10:00:00+09:00"


def req_text(name, scope):
    return (f'---\ntask_id: "{name.split("-", 1)[1]}"\napproved: "{APPROVED}"\nscope:\n'
            + "".join(f"  - {s}\n" for s in scope) + f"---\n\n# {name}: 인수 시험용 기록\n")


def hotfix_text(name, scope):
    return (f'---\nhotfix_id: "{name.split("-", 1)[1]}"\nconfirmed: "{APPROVED}"\nscope:\n'
            + "".join(f"  - {s}\n" for s in scope) + f"---\n\n# {name}: 인수 시험용 기록\n")


@pytest.fixture(scope="session")
def script_bytes(pytestconfig):
    opt = pytestconfig.getoption("--acc-script")
    path = _opt_path(opt) if opt else current_path(pytestconfig, SCRIPT_REL)
    assert path.is_file(), f"검사 스크립트가 없습니다: {path}"
    print(f"[acc] check_standard.py: {path}")
    return path.read_bytes()


class TempRepo:
    """pytest tmp_path 아래의 임시 Git 저장소."""

    def __init__(self, root, script):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        git(root, "init", "-q")
        self.write(SCRIPT_REL, script)

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)

    def commit_all(self, msg, date=None):
        env = dict(ENV)
        if date:
            env["GIT_AUTHOR_DATE"] = date
            env["GIT_COMMITTER_DATE"] = date
        git(self.root, "add", "-A", env=env)
        # 임시 저장소의 시험 준비 커밋이다. 사용자 전역 훅이 끼어들지 않게 --no-verify를 쓴다
        git(self.root, "commit", "-q", "--no-verify", "-m", msg, env=env)

    def run_staged(self, rel, content="# 인수 시험 변경\n"):
        self.write(rel, content)
        git(self.root, "add", "--", rel)
        res = subprocess.run([sys.executable, str(self.root / SCRIPT_REL), "--staged"], cwd=self.root,
                             capture_output=True, env=ENV)
        return res.returncode, res.stdout.decode("utf-8", "replace") + res.stderr.decode("utf-8", "replace")


# 인수 시험용 기록: 이름 → (기록 경로, 내용, 그 기록만 덮는 변경 파일)
RECORDS = {
    "REQ-101": (f"{REQ_DIR_REL}/REQ-101_v01.md", req_text("REQ-101", ["Departments/Design/docs/acc101"]),
                "Departments/Design/docs/acc101/a.md"),
    "HOTFIX-101": (f"{HOTFIX_NEW_REL}/HOTFIX-101_v01.md",
                   hotfix_text("HOTFIX-101", ["Departments/Operations/assets/live101"]),
                   "Departments/Operations/assets/live101/a.md"),
    "HOTFIX-003": (f"{HOTFIX_OLD_REL}/HOTFIX-003_v01.md",
                   hotfix_text("HOTFIX-003", ["Departments/Operations/assets/live003"]),
                   "Departments/Operations/assets/live003/a.md"),
}


@pytest.fixture
def record_repo(tmp_path, script_bytes):
    repo = TempRepo(tmp_path / "repo", script_bytes)
    for rel, text, _ in RECORDS.values():
        repo.write(rel, text)
    repo.write("README.md", "acc\n")
    repo.commit_all("init")
    return repo


def assert_pass_by(result, name):
    rc, out = result
    assert rc == 0, f"--staged 검사가 통과하지 않았습니다(종료 코드 {rc}, 기대 0):\n{out}"
    assert f"{name}_v01.md" in out, f"통과 근거가 {name}이 아닙니다:\n{out}"
    assert "기록 파일명 형식" not in out, f"기록 파일명 형식 [INFO]가 나왔습니다:\n{out}"


# ---------------------------------------------------------------- 체크리스트 1 (v05 번호 규칙)

def test_c1_1_start_number_exception(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/07_문서_서식_및_번호.md"), r"^## 2\. ")
    line = item(sec, "시작 번호")
    require(line, ["v05", "`101`", "`REQ-031` 커밋 전에 받은 번호", "그대로 쓴다", "ORDER 번호", "「ORDER」 항"],
            "07 2절 「시작 번호」")


def test_c1_2_req101_read_as_record(record_repo):
    assert_pass_by(record_repo.run_staged(RECORDS["REQ-101"][2]), "REQ-101")


def test_c1_2_hotfix101_read_as_record(record_repo):
    assert_pass_by(record_repo.run_staged(RECORDS["HOTFIX-101"][2]), "HOTFIX-101")


def test_c1_2_dev_result_records_comparison(pytestconfig):
    body = dev_section(pytestconfig, "대조")
    require(body, ["check_standard.py", "RECORD_NAME"], "개발 결과서 「대조」 절")


# ---------------------------------------------------------------- 체크리스트 2 (조직 개편)

def _org_rows(config):
    sec = section(current_doc(config, "Workflow/02_부서_구조_및_작업구역.md"), r"^### 2\.2 ")
    rows = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 6 and re.fullmatch(r"[A-Z]\d{2}", cells[2]):
            rows.append(cells)
    return rows


def test_c2_2_every_part_in_team_except_x01(pytestconfig):
    rows = _org_rows(pytestconfig)
    assert len(rows) == 29, f"02 2.2절 조직 표의 파트 행이 {len(rows)}개입니다(기대 29)"
    teamless = [r[2] for r in rows if r[1] in ("", "—", "-")]
    assert teamless == ["X01"], f"팀이 없는 파트: {teamless}(기대 X01 하나)"


def test_c2_3_mapping_only_in_02(pytestconfig):
    # 02 2.3절 대응 표의 부 이름 행(「| 설계 | 설계부 |」 등)이 다른 문서에 다시 적히지 않았는지 본다
    doc02 = current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md")
    sec = section(doc02, r"^### 2\.3 ")
    pairs = [("설계", "설계부"), ("개발", "개발부"), ("품질", "품질보증부"), ("운영", "운영부"), ("마케팅", "마케팅부")]
    for old, new in pairs:
        assert re.search(rf"^\|\s*{old}\s*\|\s*{new}\s*\|", sec, re.M), f"02 2.3절에 대응 행 「| {old} | {new} |」이 없습니다"
    found = []
    for rel in governance_rels(pytestconfig):
        if rel == "Workflow/02_부서_구조_및_작업구역.md":
            continue
        for no, line in strip_history(current_doc(pytestconfig, rel)):
            if any(re.search(rf"^\|\s*{o}\s*\|\s*{n}\s*\|", line) for o, n in pairs):
                found.append(f"{rel}:{no}")
    assert not found, f"대응 표 행이 02 밖에 있습니다: {found}"
    term = table_row(current_doc(pytestconfig, "Workflow/01_표준_개요.md"), "조직")
    require(term, ["옛 이름과 새 이름의 대응"], "01 「용어」 「조직」 행")


def _old_org_hits(config, rels):
    hits = []
    for rel in rels:
        text = current_doc(config, rel)
        lines = strip_history(text)
        if rel == "Workflow/02_부서_구조_및_작업구역.md":
            # 2.3절 대응 표는 옛 이름을 적는 곳이다(D2)
            sec = section(text, r"^### 2\.3 ").splitlines()
            start = text.splitlines().index(sec[0]) + 1
            skip = set(range(start, start + len(sec)))
            lines = [(n, l) for n, l in lines if n not in skip]
        for no, line in lines:
            masked = line
            for phrase in ORG_ALLOWED:
                masked = masked.replace(phrase, "■")
            for m in OLD_ORG.finditer(masked):
                hits.append(f"{rel}:{no}: 「{masked[max(0, m.start() - 12):m.end() + 6]}」")
    return hits


def test_c2_4_no_old_org_names_in_manuals(pytestconfig):
    rels = [r for r in governance_rels(pytestconfig)
            if r == "AGENTS.md" or (r.startswith("Workflow/") and r.endswith(".md"))]
    hits = _old_org_hits(pytestconfig, rels)
    assert not hits, "조직을 가리키는 옛 부 이름이 남았습니다:\n" + "\n".join(hits)
    agents = current_doc(pytestconfig, "AGENTS.md")
    org_table = section(agents, r"^## 1\. ")
    for name in ("설계부", "개발부", "품질보증부", "운영부", "마케팅부"):
        table_row(org_table, name)


def test_c2_5_department_folders_not_renamed():
    _, tracked = git(REPO, "ls-files", "-z", "--", "Departments")
    tracked_dirs = {p.split("/")[1] for p in tracked.split("\0") if p.count("/") >= 2}
    assert tracked_dirs == DEPARTMENT_DIRS, f"추적되는 부서 폴더: {sorted(tracked_dirs)}"
    on_disk = {p.name for p in (REPO / "Departments").iterdir() if p.is_dir()}
    assert on_disk == DEPARTMENT_DIRS, f"작업 트리의 부서 폴더: {sorted(on_disk)}"
    _, status = git(REPO, "status", "--porcelain", "-uall", "--", "Departments")
    renamed = []
    for line in status.splitlines():
        if line[:2].strip().startswith("R") and " -> " in line:
            src, dst = line[3:].split(" -> ", 1)
            if src.split("/")[1:2] != dst.split("/")[1:2]:
                renamed.append(line)
    assert not renamed, f"부서 폴더가 바뀐 이름 변경: {renamed}"


def test_c2_6_agent_definitions_kept_and_renamed(pytestconfig):
    _, tracked = git(REPO, "ls-files", "-z", "--others", "--cached", "--exclude-standard", "--", ".claude/agents")
    originals = sorted(Path(p).name for p in tracked.split("\0") if p)
    assert originals == sorted(AGENT_FILES), f".claude/agents 파일: {originals}"
    dev = dev_dir(pytestconfig)
    if dev is not None and (dev / ".claude.적용본" / "agents").is_dir():
        applied = sorted(p.name for p in (dev / ".claude.적용본" / "agents").iterdir())
        assert applied == sorted(AGENT_FILES), f"개발 적용본 agents 파일: {applied}(새 정의 파일이 생기면 안 됨)"
    rels = [f".claude/agents/{n}" for n in AGENT_FILES]
    for rel in rels:
        cur, orig = current_doc(pytestconfig, rel), original_doc(rel)
        for key in ("name:", "model:", "disallowedTools:"):
            c = [l for l in cur.splitlines() if l.startswith(key)]
            o = [l for l in orig.splitlines() if l.startswith(key)]
            assert c == o, f"{rel}의 머리말 {key}가 바뀌었습니다: {o} → {c}"
    hits = _old_org_hits(pytestconfig, rels)
    assert not hits, "정의 파일에 조직을 가리키는 옛 부 이름이 남았습니다:\n" + "\n".join(hits)


# ---------------------------------------------------------------- 체크리스트 3 (구조 변경 세 건)

def test_c3_1_hotfix_roles(pytestconfig):
    sec03 = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^## 9\. ")
    require(sec03, ["S01", "핫픽스팀(V03)", "핫픽스 실행 명령", "`Departments/Development/results/`"], "03 9절")
    sec04 = section(current_doc(pytestconfig, "Workflow/04_모델_운용.md"), r"^### 1\.2 ")
    v03 = next((l for l in sec04.splitlines() if l.startswith("|") and "V03" in l), None)
    assert v03, "04 1.2절 표에 핫픽스팀(V03) 행이 없습니다"
    require(v03, ["고급 기본 모델", "`medium`"], "04 1.2절 V03 행")
    sec02 = section(current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), r"^### 2\.1 ")
    require(sec02, ["(S01) 핫픽스의 사전 승인", "핫픽스팀(V03)"], "02 2.1절")


@pytest.mark.parametrize("name", ["HOTFIX-101", "HOTFIX-003"], ids=["development_results", "secretariat_results"])
def test_c3_2_hotfix_read_from_both_locations(record_repo, name):
    assert_pass_by(record_repo.run_staged(RECORDS[name][2]), name)


def test_c3_2_hotfix_location_in_07(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/07_문서_서식_및_번호.md"), r"^## 1\. ")
    require(table_row(sec, "HOTFIX"), ["`Departments/Development/results/HOTFIX-xxx_vNN.md`"], "07 1절 HOTFIX 행")


def test_c3_3_commit_subject_c02(pytestconfig):
    doc05 = current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md")
    for heading in (r"^## 1\. ", r"^### 1\.1 ", r"^### 8\.3 "):
        require(section(doc05, heading), ["형상통제팀(C02)"], f"05 {heading}")
    sec83 = section(doc05, r"^### 8\.3 ")
    for proc in ("최종 승인 커밋", "요청 커밋", "요청 푸시"):
        row = next((l for l in sec83.splitlines() if l.startswith("|") and f"| {proc} |" in l), None)
        assert row and "형상통제팀(C02" in row, f"05 8.3절 표 「{proc}」 행의 수행 주체가 C02가 아닙니다: {row}"
    sec02 = section(current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), r"^### 2\.1 ")
    require(sec02, ["⑦ (C02)", "⑩ (C02)"], "02 2.1절")
    agents = section(current_doc(pytestconfig, "AGENTS.md"), r"^## 2\. ")
    require(item(agents, "커밋·푸시"), ["형상통제팀(C02)"], "AGENTS.md 2절 5항")


def test_c3_4_configuration_team(pytestconfig):
    rows = {r[2]: r for r in _org_rows(pytestconfig)}
    for code in ("C01", "C02", "C03"):
        assert code in rows and rows[code][0] == "비서실" and rows[code][1] == "형상통제팀", \
            f"02 2.2절 표에 비서실 형상통제팀 {code} 행이 없습니다: {rows.get(code)}"
    sec02 = section(current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), r"^### 2\.1 ")
    require(sec02, ["형상통제팀(C01~C03)은 두 가지를 모두 할 수 있는 비서실 세션이 맡는다",
                    "(C01·C03) 형상통제팀은", "뒤 안건이 정한다"], "02 2.1절")


# ---------------------------------------------------------------- 체크리스트 12 (비서실을 역할과 능력으로)

def test_c12_1_secretariat_definition(pytestconfig):
    row01 = table_row(current_doc(pytestconfig, "Workflow/01_표준_개요.md"), "비서실")
    require(row01, ["대표님과 대화하며 요구를 모아", "대표님이", "Claude Code 세션도 비서실이 될 수 있다"], "01 「용어」 비서실 행")
    row_a = table_row(section(current_doc(pytestconfig, "AGENTS.md"), r"^## 1\. "), "비서실")
    require(row_a, ["대표님과 대화하며 요구를 모으는 세션", "대표님이 정한다", "Claude Code 세션 포함"],
            "AGENTS.md 1절 비서실 행")
    assert "저장소 밖 서비스" not in row_a, "AGENTS.md 1절 비서실 행에 「저장소 밖 서비스」가 남았습니다"


def test_c12_2_capability_subjects(pytestconfig):
    doc05 = current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md")
    sec2 = section(doc05, r"^## 2\. ")
    require(sec2, ["셸을 실행할 수 있는 비서실 세션", "셸을 실행할 수 없는 비서실 세션"], "05 2절")
    sec82 = section(doc05, r"^### 8\.2 ")
    require(sec82, ["셸을 실행할 수 없는 비서실 세션"], "05 8.2절")
    sec03 = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^## 9\. ")
    require(sec03, ["셸을 실행할 수 있는 비서실 세션", "셸을 실행할 수 없는 비서실 세션"], "03 9절")


def test_c12_3_service_names_only_in_allowed_places(pytestconfig):
    bad = []
    for rel in governance_rels(pytestconfig):
        text = current_doc(pytestconfig, rel)
        allowed_lines = set()
        if rel == "Workflow/05_인수인계_및_실행명령.md":
            all_lines = text.splitlines()
            sec85 = section(text, r"^### 8\.5 ").splitlines()
            s = all_lines.index(sec85[0]) + 1
            allowed_lines.update(range(s, s + len(sec85)))
            sec84 = section(text, r"^### 8\.4 ").splitlines()
            s84 = all_lines.index(sec84[0]) + 1
            in2 = False
            for off, line in enumerate(sec84):
                if re.match(r"^2\. ", line):
                    in2 = True
                elif re.match(r"^\d+\. ", line):
                    in2 = False
                if in2:
                    allowed_lines.add(s84 + off)
        for no, line in strip_history(text):
            if SERVICE_NAMES.search(line) and no not in allowed_lines:
                bad.append(f"{rel}:{no}: 서비스 이름 「{SERVICE_NAMES.search(line).group(0)}」")
            masked = line
            for phrase in OUTSIDE_ALLOWED:
                masked = masked.replace(phrase, "■")
            if OUTSIDE in masked:
                i = masked.index(OUTSIDE)
                bad.append(f"{rel}:{no}: 「{masked[max(0, i - 15):i + 15]}」")
    assert not bad, "허용 위치 밖의 서비스 이름·「저장소 밖」:\n" + "\n".join(bad)


def test_c12_4_capability_check(pytestconfig):
    sec81 = section(current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), r"^### 8\.1 ")
    line = item(sec81, "능력 확인")
    require(line, ["시작할 때마다", "스스로 확인", "셸 작업 지시 파일", "대표님께 제시", "핫픽스", "사전 승인까지만",
                   "「승인 기록」 예외 (마)"], "05 8.1절 「능력 확인」")


def test_c12_5_session_id_includes_claude_code(pytestconfig):
    sec84 = section(current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), r"^### 8\.4 ")
    block, in2 = [], False
    for line in sec84.splitlines():
        if re.match(r"^2\. ", line):
            in2 = True
        elif re.match(r"^\d+\. ", line):
            in2 = False
        if in2:
            block.append(line)
    assert block, "05 8.4절 2항이 없습니다"
    require("\n".join(block), ["`Claude Code`"], "05 8.4절 2항")


def test_c12_6_operation_and_shell_instruction(pytestconfig):
    doc05 = current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md")
    sec85 = section(doc05, r"^### 8\.5 ")
    require(sec85, ["비서실은 하나다", "운영 기본값", "Antigravity"], "05 8.5절")
    sec86 = section(doc05, r"^### 8\.6 ")
    require(sec86, ["지시 파일", "결과 파일", "한 번 입력하면 지시 파일 하나를 처리한다", "REQ 작성 명령",
                    "REQ 새 버전 명령", "「없음」", "「승인 필요」", "바로 실행한다", "「진행」",
                    "승인 문구 원문은 적지 않는다"], "05 8.6절")


# ---------------------------------------------------------------- 체크리스트 13 (비서실 세션과 PM·부서의 경계)

def test_c13_1_boundary_rule(pytestconfig):
    sec02 = section(current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), r"^### 2\.1 ")
    require(sec02, ["셸을 실행할 수 있어도", "부서 서브에이전트 기동", "직접 하지 않고", "PM 지시문"], "02 2.1절")


def test_c13_2_pm_notation(pytestconfig):
    bad = []
    for rel in governance_rels(pytestconfig):
        for no, line in strip_history(current_doc(pytestconfig, rel)):
            if MAIN_SESSION in line.replace(MAIN_SESSION_DEF, "■"):
                bad.append(f"{rel}:{no}")
    assert not bad, f"정의 형태가 아닌 「{MAIN_SESSION}」: {bad}"
    agents = section(current_doc(pytestconfig, "AGENTS.md"), r"^## 1\. ")
    doc02 = current_doc(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md")
    places = {
        "AGENTS.md 1절 비서실 행": table_row(agents, "비서실"),
        "02 2절 표 비서실 행": table_row(section(doc02, r"^## 2\. "), "비서실"),
        "02 2.1절 표 PM 행": next((l for l in section(doc02, r"^### 2\.1 ").splitlines() if l.startswith("| PM")), ""),
    }
    sec05 = section(current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), r"^## 1\. ")
    for mark in ("③", "⑥"):
        places[f"05 1절 {mark}"] = next((l for l in sec05.splitlines() if l.startswith(mark)), "")
    missing = [k for k, v in places.items() if MAIN_SESSION_DEF not in v]
    assert not missing, f"PM 정의 표기가 없는 위치: {missing}"


def test_c13_4_no_subagent_block_device(pytestconfig):
    cur, orig = current_settings(pytestconfig), original_settings()
    assert set(cur) == set(orig), f"settings.json 최상위 키가 바뀌었습니다: {sorted(orig)} → {sorted(cur)}"
    cp, op = cur.get("permissions", {}), orig.get("permissions", {})
    assert set(cp) == set(op), f"permissions 키가 바뀌었습니다: {sorted(op)} → {sorted(cp)}"
    assert cp.get("allow") == op.get("allow"), "allow 목록이 바뀌었습니다"
    assert cp.get("deny") == op.get("deny"), "deny 목록이 바뀌었습니다"
    added = [r for r in cp.get("ask", []) if r not in op.get("ask", [])]
    odd = [r for r in added if not r.startswith("PowerShell(") or re.search(r"Agent|Task", r)]
    assert not odd, f"ask에 PowerShell 규칙 밖의 새 규칙: {odd}"


# ---------------------------------------------------------------- 체크리스트 14 (권한 설정)

def test_c14_1_layer1_limit(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/06_통제장치_및_배포.md"), r"^## 1\. ")
    row = table_row(sec, "1")
    require(row, ["Claude Code로 연 비서실 세션", "핫픽스팀(V03) 세션", "2.2절"], "06 1절 계층 1 행")
    assert "저장소 밖 서비스" not in row, "06 1절 계층 1 행에 「저장소 밖 서비스」가 남았습니다"


def test_c14_2_6_permission_relation_section(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/06_통제장치_및_배포.md"), r"^### 2\.2 ")
    require(sec, ["형상통제팀(C02)", "`deny`는 그대로 둔다", "반영 명령", "계층 3(scope 대조)",
                  "`CLAUDE.md`", "`.claude/agents/`", "`settings.json`"], "06 2.2절")


def test_c14_3_v03_deny_paths(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^## 9\. ")
    require(sec, ["`deny` 경로", "고치지 않고", "HOTFIX 2절", "수정안", "대표님이 직접 고치게"], "03 9절")


def test_c14_4_commit_confirmation(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), r"^### 8\.3 ")
    require(item(sec, "권한 확인 화면"), ["형상통제팀(C02)의 커밋·푸시", "`ask`", "대표님이 다시 승인"],
            "05 8.3절 「권한 확인 화면」")
    ask = current_settings(pytestconfig)["permissions"]["ask"]
    missing = [r for r in ("Bash(git commit*)", "Bash(git push*)") if r not in ask]
    assert not missing, f"ask에 없는 커밋·푸시 규칙: {missing}"


def test_c14_5_no_pm_launch_in_allow(pytestconfig):
    allow = current_settings(pytestconfig)["permissions"].get("allow", [])
    bad = [r for r in allow if re.match(r"^\w+\(\s*claude\b", r)]
    assert not bad, f"allow에 PM 기동 명령(claude …) 규칙: {bad}"


def test_c14_7_powershell_ask_rules(pytestconfig):
    ask = current_settings(pytestconfig)["permissions"]["ask"]
    missing = [r for r in POWERSHELL_ASK if r not in ask]
    assert not missing, f"ask에 없는 PowerShell 규칙: {missing}"


def test_c14_7_dev_result_permission_measurement(pytestconfig):
    body = dev_section(pytestconfig, "권한 실측")
    require(body, ["PowerShell(git commit*)", "PowerShell(Remove-Item *)", "PowerShell(Move-Item *)"],
            "개발 결과서 「권한 실측」 절")


def test_c14_8_ask_and_command_tool_docs(pytestconfig):
    doc06 = current_doc(pytestconfig, "Workflow/06_통제장치_및_배포.md")
    require(item(section(doc06, r"^## 2\. "), "`ask`"),
            ["PowerShell 도구", "`Remove-Item`", "`Move-Item`", "`erase`", "`rd`", "`rmdir`", "`ri`", "`mi`",
             "`git commit`", "`git push`"], "06 2절 「`ask`」")
    sec21 = section(doc06, r"^### 2\.1 ")
    require(item(sec21, "명령 도구"), ["`PowerShell(...)` 규칙으로 `ask`에 따로 등록"], "06 2.1절 「명령 도구」")
    require(sec21, ["`ask`를 거치지 않으므로", "대표님 승인"], "06 2.1절")


def test_c14_9_dev_result_settings_comparison(pytestconfig):
    body = dev_section(pytestconfig, "대조")
    require(body, ["settings.json", "check_standard.py"], "개발 결과서 「대조」 절")


# ---------------------------------------------------------------- 체크리스트 19 (원스톱 착수 대조의 시각 기준)

def _onestop_item5(config):
    sec = section(current_doc(config, "Workflow/03_라이프사이클.md"), r"^### 4\.1 ")
    return item(sec, "끝난 안건과의 대조"), sec


def _target_commit_line(config):
    sec = section(current_doc(config, "Workflow/03_라이프사이클.md"), r"^### 4\.1 ")
    line = next((l for l in sec.splitlines() if l.strip().startswith("- 대상 커밋:")), None)
    assert line, "03 4.1절 5항에 「대상 커밋」 항목이 없습니다"
    return line, sec


def test_c19_1_compare_from_creation_time(pytestconfig):
    line, sec = _target_commit_line(pytestconfig)
    require(line, ["--since=<기준 시각>", "`created_at`", "`T00:00:00+09:00`"], "03 4.1절 5항 「대상 커밋」")
    pointer = next((l for l in sec.splitlines() if l.strip().startswith("- 가리키는 절·문구:")), "")
    require(pointer, ["같은 `<기준 시각>`"], "03 4.1절 5항 「가리키는 절·문구」")


def test_c19_2_created_at_field(pytestconfig):
    tpl = current_doc(pytestconfig, "Workflow/templates/REQ_TEMPLATE.md")
    head = tpl.split("---", 2)[1] if tpl.startswith("---") else ""
    assert re.search(r"^created_at:", head, re.M), "REQ 서식 머리말에 created_at 칸이 없습니다"
    sec07 = section(current_doc(pytestconfig, "Workflow/07_문서_서식_및_번호.md"), r"^## 3\. ")
    require(table_row(sec07, "REQ"), ["`created_at`", "`YYYY-MM-DDTHH:MM:SS+09:00`", "처음 저장할 때"],
            "07 3절 표 REQ 행")
    sec03 = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^## 3\. ")
    require(sec03, ["머리말 `created_at`", "처음 저장하기 직전"], "03 3절")


def test_c19_3_versions_without_created_at(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^### 4\.1 ")
    line = item(sec, "작성 시각 기준의 적용 시점")
    require(line, ["`created_at`이 없는 REQ 버전", "나중에 `created_at`을 적지 않고", "0시부터 대조"],
            "03 4.1절 8항")


def _base_time(header):
    """03 4.1절 5항의 <기준 시각>: created_at, 없거나 비면 created에 T00:00:00+09:00을 붙인 값."""
    m = re.search(r'^created_at:\s*"([^"]*)"', header, re.M)
    if m and m.group(1):
        return m.group(1)
    return re.search(r'^created:\s*"([^"]+)"', header, re.M).group(1) + "T00:00:00+09:00"


def _log_args(template, base, path):
    cmd = template.replace("<기준 시각>", base).replace("<경로 목록>", path)
    args = shlex.split(cmd)
    assert args[:2] == ["git", "log"], f"「대상 커밋」 명령 형태가 git log가 아닙니다: {cmd}"
    return args[1:]  # git() 도우미가 "git"과 -c 옵션을 붙이므로 하위 명령 "log"부터 넘긴다


@pytest.mark.parametrize("with_time", [True, False], ids=["created_at", "created_only"])
def test_c19_4_query_by_creation_time(pytestconfig, tmp_path, with_time):
    line, _ = _target_commit_line(pytestconfig)
    m = re.search(r"`(git log --since=<기준 시각>[^`]*)`", line)
    assert m, "03 4.1절 5항 「대상 커밋」에 `git log --since=<기준 시각> …` 명령이 없습니다"
    template = m.group(1)
    repo = TempRepo(tmp_path / "repo", b"# acc\n")
    path = "Workflow/acc_target.md"
    repo.write(path, "base\n")
    repo.commit_all("chore: base", date="2026-10-19T12:00:00+09:00")
    repo.write(path, "before\n")
    repo.commit_all("feat: [REQ-901] ended before creation", date="2026-10-20T09:00:00+09:00")
    repo.write(path, "after\n")
    repo.commit_all("feat: [REQ-902] ended after creation", date="2026-10-20T11:00:00+09:00")
    header = 'created: "2026-10-20"\n' + ('created_at: "2026-10-20T10:00:00+09:00"\n' if with_time else "")
    _, out = git(repo.root, *_log_args(template, _base_time(header), path))
    subjects = out
    if with_time:
        assert "[REQ-902]" in subjects and "[REQ-901]" not in subjects, \
            f"작성 시각 뒤 커밋만 나와야 합니다:\n{out}"
    else:
        assert "[REQ-902]" in subjects and "[REQ-901]" in subjects, f"두 커밋이 모두 나와야 합니다:\n{out}"
    assert "chore: base" not in subjects, f"앞 날짜 커밋이 나왔습니다:\n{out}"


def test_c19_6_application_timing(pytestconfig):
    sec = section(current_doc(pytestconfig, "Workflow/03_라이프사이클.md"), r"^### 4\.1 ")
    line = item(sec, "작성 시각 기준의 적용 시점")
    require(line, ["`REQ-031` 커밋 뒤에 기동하는 PM 세션", "`REQ-031` 커밋 뒤에 원스톱 실행 명령으로 기동하는 PM 세션",
                   "작성한 시점과 관계없이", "이미 실행 중인 PM 세션은 기동 때의 규정으로 진행한다"], "03 4.1절 8항")
