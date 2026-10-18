# -*- coding: utf-8 -*-
"""REQ-028 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상
- 현행 check_standard.py: 개발 적용본 폴더(Departments/Development/workspace/REQ-028_적용본_vNN의 가장 높은 버전)의
  Departments/Development/assets/scripts.적용본/check_standard.py. 없으면 원본(REQ-028 5절 머리 안내 「현행 거버넌스 파일」).
- 현행 Workflow 문서: 개발 적용본, 설계 적용본(Departments/Design/workspace/REQ-028_적용본_vNN의 가장 높은 버전) 순으로
  Workflow.적용본/ 아래 같은 이름의 파일, 없으면 원본 Workflow/.
- 구현 단계 산출물: 종결 기록(Departments/Secretariat/assets/inbox/종결기록_*.md), 개발 결과서(DEV-028_vNN.md 가장 높은 버전).

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 임시 Git 저장소는 pytest tmp_path 아래에만 만든다.
종결 기록은 임시 저장소에 커밋해야 효력이 있다(EC-028 G3, 3.6절).
"""

import difflib
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]

SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"
APPLIED_GLOB = "REQ-028_적용본_v[0-9][0-9]"
APPLIED_SCRIPT_REL = "Departments/Development/assets/scripts.적용본/check_standard.py"
INBOX_REL = "Departments/Secretariat/assets/inbox"
REQ_DIR_REL = "Departments/Secretariat/docs/requests"
HOTFIX_DIR_REL = "Departments/Secretariat/results"
QUALITY_RESULTS_REL = "Departments/Quality/results"

# Workflow/07 적용본 2절 「종결 기록」 항의 파일명 형식(EC-028 G2)
CLOSE_NAME = re.compile(r"^종결기록_\d{8}_((?:REQ|HOTFIX)-\d{3}(?:-\d+)?)\.md$")
RECORD_FILE = re.compile(r"^(REQ|HOTFIX)-(\d{3}(?:-\d+)?)_v(\d{2})\.md$")
TIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$")
HEX40 = re.compile(r"\b[0-9a-f]{40}\b")
SUBJECT_TAG = re.compile(r"^[a-z]+: \[([^\]]+)\]")

# 체크리스트 4의 기간 시작(v04 초기화 커밋, REQ-028 D10)
BASE_COMMIT = "6c5d512be0c64f9fb9b9668819feb76e0ab2c8b9"
# 인수 시험 작성 때(2026-10-13) `git log --reverse --format=%H 6c5d512..HEAD`로 조회한 기간 안 커밋 32개(체크리스트 4 ⑤)
RANGE_COMMITS_AT_ACC = (
    "668914e4e2ee3724931b684d801db42091ce0432", "4d4ecb26305aef11cd31c1168ee9f6f3cc7b8fe0",
    "13ef61cdfc290ae8d7df0e251dbe79dd58005b4c", "53af6674750b3bb32123c1ca80b47af962366e05",
    "ce0ef19fce9ed0e7ea0b3586c54f93846696aad1", "8c5f245fc20a4b85955d5e1abb2a0d2962b660db",
    "22315d245d783e35589feae4d00006e5eb8fd626", "3801c6266af2af854a0963a1d5259fe918043956",
    "1044e1efe3cf521f507dd8bc589e474845917e1d", "9a52ebed5fefdaa8a2e187fdccc3a49cda929137",
    "5d21923cedc7a11006c91237fc5a574636c5997d", "c805713af9a26c1e574fbb91df2dc88f002fe706",
    "300437f55168e364f8719fd7b496979550d9f683", "5ff92a1fb242ce25acc5ea5127b62c9070744ee5",
    "610558bdedf80e94220076a04169169394df8fe2", "1ddbe58fc7fcdced9652daa6068a3ad4fc141908",
    "dc88268b4c5c511442c3112094a8f0a290ef8f7c", "69ba21dd513a0d9efec857120887424eb9e65e5d",
    "3a7b07ee29a37b62bc145f57d47b531c97688fc3", "ee95f5a3d6f2607a99cc1b7620a22cf4a4be0e71",
    "97262f32d902a0f64e78b1bb2c534f3617ce2a2b", "bdb70f7116745da556aad42dc8e50790bce97052",
    "67d278122fd0ba52213c574a26b6502dfd438375", "c9ecfa61aa0a4813b17ab5ad6a19bfefd0bab921",
    "574089373b52d5b927b0fb603ec30f39ca5a4974", "08e1ffcdb5dd9148fa443ae7fbfcc4fc65579c96",
    "2303486eb3bab9adcdc077339b2f9e1fa4397a5d", "09d735f3bd688d7790cd7f61e07e295591a5f42a",
    "5c8cd2156114b91167271e7224e18ff0c12b8705", "2d8de766c011de53d35b1b0b637e41173d705964",
    "cafc8d9f02a98228764f302c7eb724b7e0b5f995", "e956bab2bfe020510923ada212506ee975b87981",
)

# 체크리스트 3 ③의 기대값. 인수 시험 작성 때 커밋 이력으로 확인한 끝난 기록(ACC-028 2절 「3 ③ 기대값의 근거」)
EXPECTED_ENDED = frozenset(
    [f"REQ-{n:03d}" for n in range(7, 28)] + ["REQ-010-1"] + [f"HOTFIX-{n:03d}" for n in range(3, 7)]
)
NOT_ENDED = frozenset(["REQ-028", "REQ-029", "REQ-030"])
ABSORBED = frozenset(["REQ-011"])  # 커밋 없이 끝난 기록(흡수). REQ-028 체크리스트 3 ①, EC-028 3.4절 3번

ITEM_LABELS = ("대상 기록", "종결 경로", "커밋 종류", "끝낸 커밋", "근거", "작성 주체", "작성 시각")


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


def git(cwd, *args, check=True):
    res = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false",
                          "-c", "core.quotepath=false", *args], cwd=cwd, capture_output=True, env=ENV)
    out = res.stdout.decode("utf-8", "replace")
    if check and res.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 실패({res.returncode}): "
                             f"{res.stderr.decode('utf-8', 'replace')}")
    return res.returncode, out


def _highest(folder, pattern):
    found = sorted(p for p in folder.glob(pattern) if p.is_dir() or p.is_file())
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


@pytest.fixture(scope="session")
def script_bytes(pytestconfig):
    opt = pytestconfig.getoption("--acc-script")
    if opt:
        path = _opt_path(opt)
    else:
        dev = dev_dir(pytestconfig)
        cand = dev / APPLIED_SCRIPT_REL if dev else None
        path = cand if cand is not None and cand.is_file() else REPO / SCRIPT_REL
    assert path.is_file(), f"검사 스크립트가 없습니다: {path}"
    print(f"[acc] check_standard.py: {path}")
    return path.read_bytes()


def current_doc(config, name):
    """Workflow 문서 name(예: 06_통제장치_및_배포.md)의 현행 내용."""
    for folder in (dev_dir(config), design_dir(config)):
        if folder is not None:
            cand = folder / "Workflow.적용본" / name
            if cand.is_file():
                return cand.read_text(encoding="utf-8")
    return (REPO / "Workflow" / name).read_text(encoding="utf-8")


def original_doc(name):
    return (REPO / "Workflow" / name).read_text(encoding="utf-8")


DOCS = ("01_표준_개요.md", "02_부서_구조_및_작업구역.md", "03_라이프사이클.md", "04_모델_운용.md",
        "05_인수인계_및_실행명령.md", "06_통제장치_및_배포.md", "07_문서_서식_및_번호.md")


def strip_history(text):
    """제목이 「개정 이력」인 절을 뺀다(REQ-028 5절 머리 「개정 이력 표는 Grep 확인에서 뺀다」)."""
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


def dev_result(config):
    opt = config.getoption("--acc-dev-result")
    path = _opt_path(opt) if opt else _highest(REPO / "Departments" / "Development" / "results", "DEV-028_v[0-9][0-9].md")
    if path is None or not path.is_file():
        pytest.fail("개발 결과서(Departments/Development/results/DEV-028_vNN.md)가 없습니다. 구현 단계 산출물이 있어야 합니다.")
    return path.read_text(encoding="utf-8")


def dev_section(config, keep, drop=()):
    """개발 결과서에서 제목에 keep이 들고 drop이 들지 않은 절들의 본문."""
    text = dev_result(config)
    lines = text.splitlines()
    parts = []
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and keep in m.group(2) and not any(d in m.group(2) for d in drop):
            parts.append(section("\n".join(lines[i:]), re.escape(line) + "$"))
    if not parts:
        pytest.fail(f"개발 결과서에 제목에 「{keep}」이 든 절이 없습니다.")
    return "\n".join(parts)


def close_records_in_repo(config):
    """작업 트리의 종결 기록 {기록 이름: 경로}. 같은 이름이 둘 이상이면 실패한다."""
    opt = config.getoption("--acc-close-dir")
    folder = _opt_path(opt) if opt else REPO / INBOX_REL
    found = {}
    dup = []
    for p in sorted(folder.glob("종결기록_*.md")):
        m = CLOSE_NAME.match(p.name)
        assert m, f"형식에 맞지 않는 종결 기록 이름: {p.name}"
        if m.group(1) in found:
            dup.append(m.group(1))
        found[m.group(1)] = p
    assert not dup, f"같은 기록 이름의 종결 기록이 둘 이상입니다: {dup}"
    return found


def require_close_records(config):
    found = close_records_in_repo(config)
    if not found:
        pytest.fail(f"종결 기록({INBOX_REL}/종결기록_*.md)이 작업 트리에 없습니다. 구현 단계 산출물이 있어야 합니다.")
    return found


def latest_records():
    """{기록 이름: 최신 버전 경로(저장소 기준)}."""
    latest = {}
    for rel_dir, kind in ((REQ_DIR_REL, "REQ"), (HOTFIX_DIR_REL, "HOTFIX")):
        for p in (REPO / rel_dir).glob(f"{kind}-*.md"):
            m = RECORD_FILE.match(p.name)
            if not m or m.group(1) != kind:
                continue
            name, ver = f"{kind}-{m.group(2)}", int(m.group(3))
            if name not in latest or ver > latest[name][0]:
                latest[name] = (ver, f"{rel_dir}/{p.name}")
    return {k: v[1] for k, v in latest.items()}


def line_value(text, label):
    """목록 항목 「- <label>: <값>」의 값. 항목이 없으면 None(Workflow/07 적용본 1.1절 4항 「목록으로 적고」)."""
    pat = re.compile(r"^\s*[-*]\s*(?:\*\*)?" + re.escape(label) + r"(?:\*\*)?\s*[:：]\s*(.*)$")
    for line in text.splitlines():
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return None


def name_pattern(name):
    return re.compile(r"(?<![A-Za-z0-9-])" + re.escape(name) + r"(?![0-9]|-[0-9])")


# ---------------------------------------------------------------- 임시 저장소

REQ_APPROVED = "2026-10-13T10:00:00+09:00"
CLOSE_DATE = "20261013"


def req_text(name, scope, approved=REQ_APPROVED):
    return (f'---\ntask_id: "{name.split("-", 1)[1]}"\napproved: "{approved}"\nscope:\n'
            + "".join(f"  - {s}\n" for s in scope) + f"---\n\n# {name}: 인수 시험용 기록\n")


def hotfix_text(name, scope):
    return (f'---\ntask_id: "{name.split("-", 1)[1]}"\nconfirmed: "{REQ_APPROVED}"\nscope:\n'
            + "".join(f"  - {s}\n" for s in scope) + f"---\n\n# {name}: 인수 시험용 기록\n")


def close_rel(name, date=CLOSE_DATE, folder=INBOX_REL):
    return f"{folder}/종결기록_{date}_{name}.md"


ROUTES = {"REQ-901": "커밋", "REQ-902": "흡수", "REQ-903": "중단 뒤 종료", "HOTFIX-904": "커밋",
          "REQ-905": "커밋", "REQ-907": "커밋", "REQ-907-1": "커밋"}


def close_text(name, record_rel):
    route = ROUTES.get(name, "커밋")
    return (f"- 대상 기록: {record_rel}\n- 종결 경로: `{route}`\n"
            f"- 커밋 종류: {'최종 승인 커밋' if route == '커밋' else '해당 없음'}\n"
            f"- 끝낸 커밋: {'이 기록을 더한 커밋' if route == '커밋' else '해당 없음'}\n"
            "- 근거: 인수 시험용\n- 작성 주체: 인수 시험\n- 작성 시각: 2026-10-13T10:00:00+09:00\n")


# 인수 시험용 기록. 이름 → (기록 경로, 기록 내용, 그 기록만 덮는 변경 파일)
def _records():
    d = "Departments/Design/docs"
    o = "Departments/Operations/assets"
    recs = {
        "REQ-901": (f"{REQ_DIR_REL}/REQ-901_v01.md", req_text("REQ-901", [f"{d}/acc901"]), f"{d}/acc901/a.md"),
        "REQ-902": (f"{REQ_DIR_REL}/REQ-902_v01.md", req_text("REQ-902", [f"{d}/acc902"]), f"{d}/acc902/a.md"),
        "REQ-903": (f"{REQ_DIR_REL}/REQ-903_v01.md", req_text("REQ-903", [f"{d}/acc903"]), f"{d}/acc903/a.md"),
        "HOTFIX-904": (f"{HOTFIX_DIR_REL}/HOTFIX-904_v01.md", hotfix_text("HOTFIX-904", [f"{o}/live904"]),
                       f"{o}/live904/a.md"),
        # 판정 fail 뒤 고쳐서 계속하는 안건: 같은 번호의 새 버전이 있다
        "REQ-905": (f"{REQ_DIR_REL}/REQ-905_v02.md", req_text("REQ-905", [f"{d}/acc905"]), f"{d}/acc905/a.md"),
        "HOTFIX-906": (f"{HOTFIX_DIR_REL}/HOTFIX-906_v01.md", hotfix_text("HOTFIX-906", [f"{o}/live906"]),
                       f"{o}/live906/a.md"),
        "REQ-907": (f"{REQ_DIR_REL}/REQ-907_v01.md", req_text("REQ-907", [f"{d}/acc907"]), f"{d}/acc907/a.md"),
        "REQ-907-1": (f"{REQ_DIR_REL}/REQ-907-1_v01.md", req_text("REQ-907-1", [f"{d}/acc9071"]),
                      f"{d}/acc9071/a.md"),
    }
    return recs


RECORDS = _records()
ENDED_MANY = ("REQ-901", "REQ-902", "REQ-903", "HOTFIX-904")


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

    def remove(self, rel):
        (self.root / rel).unlink()

    def stage(self, *rels):
        git(self.root, "add", "--", *rels)

    def commit_all(self, msg):
        # 임시 저장소의 시험 준비 커밋이다. 사용자 전역 훅이 끼어들지 않게 --no-verify를 쓴다
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "--no-verify", "-m", msg)

    def reset(self):
        git(self.root, "reset", "-q")

    def run(self, *args):
        res = subprocess.run([sys.executable, str(self.root / SCRIPT_REL), *args], cwd=self.root,
                             capture_output=True, env=ENV)
        return res.returncode, res.stdout.decode("utf-8", "replace") + res.stderr.decode("utf-8", "replace")

    def both(self, rel, content="# 인수 시험 변경\n"):
        """rel을 바꾸고 작업 트리 검사와 --staged 검사를 차례로 실행한 뒤 변경을 되돌린다."""
        self.write(rel, content)
        wt = self.run()
        self.stage(rel)
        st = self.run("--staged")
        self.reset()
        self.remove(rel)
        return wt, st


def build_repo(tmp_path, script, ended=(), close_msg="records closed"):
    """인수 시험용 기록을 커밋하고, ended의 종결 기록을 다음 커밋에 넣는다."""
    repo = TempRepo(tmp_path / "repo", script)
    for name, (rel, text, _) in RECORDS.items():
        repo.write(rel, text)
    repo.write(f"{REQ_DIR_REL}/REQ-905_v01.md", req_text("REQ-905", ["Departments/Design/docs/acc905"]))
    repo.commit_all("init")
    if ended:
        for name in ended:
            repo.write(close_rel(name), close_text(name, RECORDS[name][0]))
        repo.commit_all(close_msg)
    return repo


@pytest.fixture
def make_repo(tmp_path, script_bytes):
    def _make(ended=(), close_msg="records closed"):
        return build_repo(tmp_path, script_bytes, ended, close_msg)
    return _make


def assert_code(result, code, what):
    rc, out = result
    assert rc == code, f"{what}: 종료 코드 {rc}(기대 {code})\n{out}"


# ---------------------------------------------------------------- 체크리스트 1 ①~⑥ (임시 저장소 시험)

MODES = ("one", "many")


def _ended(mode, target):
    return (target,) if mode == "one" else ENDED_MANY


@pytest.mark.parametrize("mode", MODES)
def test_c1_1_committed_req_change_blocked(make_repo, mode):
    repo = make_repo(_ended(mode, "REQ-901"))
    wt, st = repo.both(RECORDS["REQ-901"][2])
    assert_code(wt, 1, "작업 트리 검사")
    assert_code(st, 1, "--staged 검사")
    # 실패 출력의 참고에 그 종결 기록 경로(Workflow/06 적용본 4절 순서 6 「실패 시」)
    assert f"종결기록_{CLOSE_DATE}_REQ-901.md" in st[1], st[1]


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("target", ["REQ-902", "REQ-903"], ids=["absorbed", "stopped"])
def test_c1_2_closed_without_commit_req_change_blocked(make_repo, mode, target):
    repo = make_repo(_ended(mode, target))
    wt, st = repo.both(RECORDS[target][2])
    assert_code(wt, 1, "작업 트리 검사")
    assert_code(st, 1, "--staged 검사")


@pytest.mark.parametrize("mode", MODES)
def test_c1_3_closed_hotfix_change_blocked(make_repo, mode):
    repo = make_repo(_ended(mode, "HOTFIX-904"))
    wt, st = repo.both(RECORDS["HOTFIX-904"][2])
    assert_code(wt, 1, "작업 트리 검사")
    assert_code(st, 1, "--staged 검사")


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("target", ["REQ-905", "HOTFIX-906"], ids=["req_new_version", "hotfix"])
def test_c1_4_open_records_still_pass(make_repo, mode, target):
    repo = make_repo(_ended(mode, "REQ-901"))
    wt, st = repo.both(RECORDS[target][2])
    assert_code(wt, 0, "작업 트리 검사")
    assert_code(st, 0, "--staged 검사")


def test_c1_4_derived_record_judged_separately(make_repo):
    # REQ-907이 끝나도 파생 안건 REQ-907-1은 통과 근거로 남는다(Workflow/07 적용본 1.1절 1항)
    repo = make_repo(("REQ-907",))
    wt, st = repo.both(RECORDS["REQ-907-1"][2])
    assert_code(wt, 0, "REQ-907-1 작업 트리 검사")
    assert_code(st, 0, "REQ-907-1 --staged 검사")
    wt, st = repo.both(RECORDS["REQ-907"][2])
    assert_code(wt, 1, "REQ-907 작업 트리 검사")
    assert_code(st, 1, "REQ-907 --staged 검사")


def test_c1_4_derived_close_does_not_end_parent(make_repo):
    repo = make_repo(("REQ-907-1",))
    wt, st = repo.both(RECORDS["REQ-907"][2])
    assert_code(wt, 0, "REQ-907 작업 트리 검사")
    assert_code(st, 0, "REQ-907 --staged 검사")
    wt, st = repo.both(RECORDS["REQ-907-1"][2])
    assert_code(wt, 1, "REQ-907-1 작업 트리 검사")
    assert_code(st, 1, "REQ-907-1 --staged 검사")


def test_c1_5_own_closing_commit_passes_then_blocks(make_repo):
    repo = make_repo(("REQ-901",))
    change = RECORDS["REQ-905"][2]
    close = close_rel("REQ-905")
    repo.write(change, "# 인수 시험 변경\n")
    repo.write(close, close_text("REQ-905", RECORDS["REQ-905"][0]))
    # 커밋하지 않은 종결 기록은 효력이 없다(작업 트리 검사)
    assert_code(repo.run(), 0, "종결 기록이 작업 트리에만 있을 때의 작업 트리 검사")
    repo.stage(change, close)
    assert_code(repo.run("--staged"), 0, "종결 기록을 함께 넣는 그 안건 자신의 커밋의 --staged 검사")
    repo.commit_all("REQ-905 closing commit")
    after = "Departments/Design/docs/acc905/b.md"
    wt, st = repo.both(after)
    assert_code(wt, 1, "종결 커밋 뒤 작업 트리 검사")
    assert_code(st, 1, "종결 커밋 뒤 --staged 검사")


def test_c1_6_zero_closed_records_all_pass(make_repo):
    repo = make_repo(())
    for name in ("REQ-901", "REQ-902", "REQ-903", "HOTFIX-904", "REQ-905", "HOTFIX-906"):
        wt, st = repo.both(RECORDS[name][2])
        assert_code(wt, 0, f"{name} 작업 트리 검사")
        assert_code(st, 0, f"{name} --staged 검사")


# ---------------------------------------------------------------- 체크리스트 1 ⑦ (실행 부분: Workflow/06 문장)

OLD_LIMIT = "종결된 안건의 승인으로 같은 경로를 다시 커밋하는 것을 막지 못한다"


def test_c1_7_layer3_limit_and_mitigation(pytestconfig):
    doc = strip_history(current_doc(pytestconfig, "06_통제장치_및_배포.md"))
    assert OLD_LIMIT not in doc, "현행 Workflow/06에 지울 문장이 남아 있습니다"
    sec1 = section(doc, r"^## 1\. ")
    rows = [l for l in sec1.splitlines() if l.startswith("| 3 |")]
    assert len(rows) == 1, rows
    assert "없이 승인 필드를 기재하는 것" in rows[0] and "막지 못한다" in rows[0], rows[0]
    sec21 = section(doc, r"^### 2\.1 ")
    lines = [l for l in sec21.splitlines() if "위험을 줄인다" in l and "커밋 전 검사" in l]
    assert len(lines) == 1, lines
    assert "끝나지 않은" in lines[0], lines[0]


# ---------------------------------------------------------------- 체크리스트 1 ⑧ (실행 부분: 개발 결과서 「대조」 절)

def test_c1_8_dev_result_records_comparison(pytestconfig):
    body = dev_section(pytestconfig, "대조", drop=("범위 대조",))
    for word in ("check_standard.py", "settings.json"):
        assert word in body, f"개발 결과서 「대조」 절에 {word}가 없습니다"


# ---------------------------------------------------------------- 체크리스트 2

def test_c2_1_rule_location_name_and_items(pytestconfig):
    doc = strip_history(current_doc(pytestconfig, "07_문서_서식_및_번호.md"))
    sec1 = section(doc, r"^## 1\. ")
    rows = [l for l in sec1.splitlines()
            if l.startswith("| 종결 기록 |") and f"`{INBOX_REL}/종결기록_YYYYMMDD_<기록 이름>.md`" in l]
    assert len(rows) == 1, "07 1절 문서 체계 표에 종결 기록 행(위치·파일명)이 하나 있어야 합니다"
    assert "버전 없음" in rows[0], rows[0]
    sec11 = section(doc, r"^### 1\.1 종결 기록")
    for label in ITEM_LABELS:
        assert f"- {label}:" in sec11, f"07 1.1절 항목에 「{label}」이 없습니다"
    sec2 = section(doc, r"^## 2\. ")
    items = [l for l in sec2.splitlines() if l.startswith("- **종결 기록**")]
    assert len(items) == 1, items
    assert CLOSE_NAME.pattern in items[0], items[0]
    assert "바로 아래" in items[0] and "작성 뒤 고치지 않는다" in items[0], items[0]


@pytest.mark.parametrize("bad", [
    f"{INBOX_REL}/종결기록_2026101_REQ-901.md",          # 날짜 7자리
    f"{INBOX_REL}/종결기록_{CLOSE_DATE}_REQ-901_v01.md",  # 버전 포함
    f"{INBOX_REL}/sub/종결기록_{CLOSE_DATE}_REQ-901.md",  # 폴더 바로 아래가 아님
], ids=["date7", "version", "subfolder"])
def test_c2_1_bad_close_name_blocked(make_repo, bad):
    # 07 적용본 2절 「종결 기록」 항: 커밋 전 검사가 이 형식을 확인한다(06 적용본 4절 순서 5)
    repo = make_repo(())
    repo.write(bad, close_text("REQ-901", RECORDS["REQ-901"][0]))
    assert_code(repo.run(), 1, "작업 트리 검사")
    repo.stage(bad)
    assert_code(repo.run("--staged"), 1, "--staged 검사")


def test_c2_1_close_records_findable(pytestconfig):
    found = require_close_records(pytestconfig)
    latest = latest_records()
    problems = []
    for name, path in sorted(found.items()):
        text = path.read_text(encoding="utf-8")
        for label in ITEM_LABELS:
            if line_value(text, label) is None:
                problems.append(f"{name}: 항목 「{label}」 없음")
        if name in latest and latest[name] not in text:
            problems.append(f"{name}: 대상 기록 {latest[name]} 없음")
        when = line_value(text, "작성 시각")
        if when is not None and not TIME_RE.match(when.strip("` ")):
            problems.append(f"{name}: 작성 시각 형식 {when}")
        route = line_value(text, "종결 경로") or ""
        if name in ABSORBED:
            if "흡수" not in route:
                problems.append(f"{name}: 종결 경로가 흡수가 아님({route})")
            # 근거 기록(EC-028 3.4절 3번): AGENTS.md 개정 이력, Workflow/07 2절 「시작 번호」, 커밋 300437f
            for marker in ("AGENTS.md", "Workflow/07", "300437f"):
                if marker not in text:
                    problems.append(f"{name}: 근거에 {marker} 없음")
        else:
            hexes = HEX40.findall(line_value(text, "끝낸 커밋") or "")
            if len(hexes) != 1:
                problems.append(f"{name}: 끝낸 커밋 40자리 해시가 하나가 아님({hexes})")
                continue
            rc, kind = git(REPO, "cat-file", "-t", hexes[0], check=False)
            if rc != 0 or kind.strip() != "commit":
                problems.append(f"{name}: 끝낸 커밋 {hexes[0]}이 저장소의 커밋이 아님")
    assert not problems, "\n".join(problems)


def test_c2_2_recording_procedures(pytestconfig):
    d07 = strip_history(current_doc(pytestconfig, "07_문서_서식_및_번호.md"))
    sec11 = section(d07, r"^### 1\.1 종결 기록")
    for first in ("| 최종 승인 커밋 |", "| 핫픽스 커밋", "| 대표님 직접 커밋 |", "| PM 커밋", "| 흡수, 중단 뒤 종료 |"):
        # 1.1절 6항의 표는 번호 목록 안에 들여 쓴다
        rows = [l.strip() for l in sec11.splitlines() if l.strip().startswith(first)]
        assert len(rows) == 1, f"07 1.1절 기록 주체 표에 「{first}」 행이 하나 있어야 합니다: {rows}"
        if "커밋" in first and "흡수" not in first:
            assert "그 커밋에 넣는다" in rows[0], rows[0]
    d05 = strip_history(current_doc(pytestconfig, "05_인수인계_및_실행명령.md"))
    sec1 = section(d05, r"^## 1\. ")
    assert "REQ·HOTFIX를 끝내는 커밋에는 그 안건의 종결 기록을 함께 넣는다" in sec1
    sec1_1 = section(d05, r"^### 1\.1 ")
    assert "⑪ 그 안건의 종결 기록" in sec1_1
    assert "①~⑩" not in sec1_1, "05 1.1절에 바뀌기 전 범위 「①~⑩」이 남아 있습니다"
    sec83 = section(d05, r"^### 8\.3 ")
    rows = [l for l in sec83.splitlines() if l.startswith("| 요청 커밋 |")]
    assert len(rows) == 1 and "종결 기록" in rows[0], rows
    d03 = strip_history(current_doc(pytestconfig, "03_라이프사이클.md"))
    sec9 = section(d03, r"^## 9\. ")
    assert re.search(r"\*\*종결\*\*: 핫픽스 커밋에 그 HOTFIX의 종결 기록을 함께 넣는다", sec9), sec9


def test_c2_3_closing_without_commit_decided_by_ceo(pytestconfig):
    d07 = strip_history(current_doc(pytestconfig, "07_문서_서식_및_번호.md"))
    sec11 = section(d07, r"^### 1\.1 종결 기록")
    assert "흡수와 중단 뒤 종료는 대표님이 정한다" in sec11
    d03 = strip_history(current_doc(pytestconfig, "03_라이프사이클.md"))
    sec7 = section(d03, r"^## 7\. ")
    assert "흡수할지는 대표님이 정하며" in sec7, sec7[-400:]


def test_c2_4_closed_records_not_reopened(pytestconfig):
    d03 = strip_history(current_doc(pytestconfig, "03_라이프사이클.md"))
    sec6 = section(d03, r"^## 6\. ")
    assert "| 종결된 안건의 사후 결함 | 파생 안건으로 진행한다 |" not in sec6
    rows = [l for l in sec6.splitlines() if l.startswith("| 끝난 안건")]
    assert len(rows) == 1, rows
    assert "다시 열지 않는다" in rows[0] and "파생 안건" in rows[0] and "새 REQ" in rows[0], rows[0]
    d07 = strip_history(current_doc(pytestconfig, "07_문서_서식_및_번호.md"))
    assert "다시 열지 않" in section(d07, r"^### 1\.1 종결 기록")


def test_c2_5_official_status_uses_close_records(pytestconfig):
    d05 = strip_history(current_doc(pytestconfig, "05_인수인계_및_실행명령.md"))
    sec1 = section(d05, r"^## 1\. ")
    lines = [l for l in sec1.splitlines() if "공식 진행 상태는" in l]
    assert len(lines) == 1, lines
    assert "종결 기록" in lines[0] and "커밋된 종결 기록으로 판단한다" in lines[0], lines[0]


@pytest.mark.parametrize("where", ["regulated", "other_folder", "subfolder"])
def test_c2_5_checker_reads_regulated_location_only(tmp_path, script_bytes, where):
    repo = TempRepo(tmp_path / "repo", script_bytes)
    for name, (rel, text, _) in RECORDS.items():
        repo.write(rel, text)
    repo.commit_all("init")
    folder = {"regulated": INBOX_REL, "other_folder": "Departments/Secretariat/docs",
              "subfolder": f"{INBOX_REL}/old"}[where]
    repo.write(close_rel("REQ-901", folder=folder), close_text("REQ-901", RECORDS["REQ-901"][0]))
    repo.commit_all("close elsewhere")
    wt, st = repo.both(RECORDS["REQ-901"][2])
    expected = 1 if where == "regulated" else 0
    assert_code(wt, expected, f"{where} 작업 트리 검사")
    assert_code(st, expected, f"{where} --staged 검사")


def test_c2_6_judgement_without_commit_message_tag(make_repo):
    # 종결 기록을 안건 표기도 기록 이름도 없는 메시지로 커밋해도 끝난 것으로 판단한다(D4)
    repo = make_repo(("REQ-902",), close_msg="x")
    wt, st = repo.both(RECORDS["REQ-902"][2])
    assert_code(wt, 1, "작업 트리 검사")
    assert_code(st, 1, "--staged 검사")


def _commit_message_block(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("- **커밋 메시지**"):
            block = [line]
            for nxt in lines[i + 1:]:
                if not nxt.strip() or nxt.startswith("#") or nxt.startswith("- **"):
                    break
                block.append(nxt)
            return block
    raise AssertionError("「커밋 메시지」 항을 찾지 못했습니다")


def test_c2_6_no_index_and_no_new_message_rule(pytestconfig):
    cur07 = current_doc(pytestconfig, "07_문서_서식_및_번호.md")
    assert _commit_message_block(cur07) == _commit_message_block(original_doc("07_문서_서식_및_번호.md")), \
        "07 2절 「커밋 메시지」 항이 원본과 다릅니다(새 근거 줄 없음, D4)"
    added = []
    for name in DOCS:
        cur = strip_history(current_doc(pytestconfig, name)).splitlines()
        orig = set(strip_history(original_doc(name)).splitlines())
        added += [f"{name}: {l[:80]}" for l in cur if l not in orig and "색인" in l]
    assert not added, "RT 색인을 정한 줄이 더해졌습니다(D3):\n" + "\n".join(added)


def test_c2_7_close_records_export_ignored(pytestconfig):
    found = require_close_records(pytestconfig)
    problems = []
    for name, path in sorted(found.items()):
        rel = path.relative_to(REPO).as_posix()
        _, out = git(REPO, "check-attr", "export-ignore", "--", rel)
        if not out.strip().endswith(": export-ignore: set"):
            problems.append(f"{rel}: {out.strip()}")
    assert not problems, "\n".join(problems)


# ---------------------------------------------------------------- 체크리스트 3

def test_c3_1_dev_result_lists_every_record(pytestconfig):
    body = dev_section(pytestconfig, "종결 확인")
    names = sorted(latest_records())
    missing = [n for n in names if not name_pattern(n).search(body)]
    assert not missing, f"개발 결과서 「종결 확인」 절에 없는 기록: {missing}"
    for must in ("REQ-010-1", "REQ-011"):
        assert must in names


def _tag(subject):
    m = SUBJECT_TAG.match(subject)
    return m.group(1) if m else None


def test_c3_2_end_commits_follow_rule(pytestconfig):
    found = require_close_records(pytestconfig)
    problems = []
    for name, path in sorted(found.items()):
        if name in ABSORBED:
            continue
        hexes = HEX40.findall(line_value(path.read_text(encoding="utf-8"), "끝낸 커밋") or "")
        if len(hexes) != 1:
            problems.append(f"{name}: 끝낸 커밋 40자리 해시가 하나가 아님")
            continue
        h = hexes[0]
        rc, _ = git(REPO, "merge-base", "--is-ancestor", BASE_COMMIT, h, check=False)
        rc2, _ = git(REPO, "merge-base", "--is-ancestor", h, "HEAD", check=False)
        if rc != 0 or rc2 != 0 or h == BASE_COMMIT:
            problems.append(f"{name}: {h[:7]}이 {BASE_COMMIT[:7]} 다음부터 HEAD까지의 커밋이 아님")
            continue
        _, subject = git(REPO, "log", "-1", "--format=%s", h)
        tag = _tag(subject.strip())
        if tag is not None and tag != name:
            problems.append(f"{name}: 끝낸 커밋 {h[:7]}의 제목 줄 표기가 [{tag}]임")
        _, later = git(REPO, "log", "--format=%h%x09%s", f"{h}..HEAD")
        for line in later.splitlines():
            short, _, subj = line.partition("\t")
            if _tag(subj) == name:
                problems.append(f"{name}: 끝낸 커밋 {h[:7]} 뒤에 표기가 [{name}]인 커밋 {short}이 있음")
        # 최종 판정서(REQ) 또는 확인된 HOTFIX가 끝낸 커밋의 트리에 있어야 한다
        kind, num = name.split("-", 1)
        if kind == "REQ":
            _, listing = git(REPO, "ls-tree", "--name-only", h, "--", f"{QUALITY_RESULTS_REL}/")
            ok = False
            for p in listing.splitlines():
                if re.fullmatch(rf"{re.escape(QUALITY_RESULTS_REL)}/RES-{re.escape(num)}_v\d{{2}}\.md", p):
                    _, body = git(REPO, "show", f"{h}:{p}")
                    if re.search(r'^result:\s*"?pass"?', body, re.M):
                        ok = True
            if not ok:
                problems.append(f"{name}: 끝낸 커밋 {h[:7]}의 트리에 result pass인 RES-{num}_vNN.md가 없음")
        else:
            _, listing = git(REPO, "ls-tree", "--name-only", h, "--", f"{HOTFIX_DIR_REL}/")
            if not any(re.fullmatch(rf"{re.escape(HOTFIX_DIR_REL)}/{re.escape(name)}_v\d{{2}}\.md", p)
                       for p in listing.splitlines()):
                problems.append(f"{name}: 끝낸 커밋 {h[:7]}의 트리에 HOTFIX 기록이 없음")
    assert not problems, "\n".join(problems)


def test_c3_3_close_records_match_ended_set(pytestconfig):
    found = set(require_close_records(pytestconfig))
    assert not (found & NOT_ENDED), f"끝나지 않은 기록의 종결 기록: {sorted(found & NOT_ENDED)}"
    assert found == EXPECTED_ENDED, (f"빠진 기록: {sorted(EXPECTED_ENDED - found)}, "
                                     f"기대 밖 기록: {sorted(found - EXPECTED_ENDED)}")


def test_c3_4_existing_records_unchanged():
    _, out = git(REPO, "status", "--porcelain", "-uall", "--", REQ_DIR_REL, HOTFIX_DIR_REL)
    bad = [l for l in out.splitlines() if l and not l.startswith("?? ")]
    assert not bad, "이미 있는 REQ·HOTFIX 파일이 바뀌었습니다:\n" + "\n".join(bad)


def _parse_header(text, key):
    value, scope, in_scope = None, [], False
    for line in text.splitlines():
        t = line.strip()
        if t.startswith(key + ":"):
            value = t.split(":", 1)[1].split(" #", 1)[0].strip().strip("'\"")
            continue
        if t.startswith("scope:"):
            in_scope = True
            continue
        if in_scope:
            if line.startswith("  - ") or line.startswith("    - "):
                scope.append(line.split("-", 1)[1].split(" #", 1)[0].strip().strip("'\"").replace("\\", "/").rstrip("/"))
            elif t and not line.startswith(" ") and not line.startswith("#"):
                break
    return value, scope


def _covers(s, f):
    if f == s or f.startswith(s + "/"):
        return True
    if os.path.splitext(s.rsplit("/", 1)[-1])[1]:
        return False
    no_ext = os.path.splitext(f)[0]
    return no_ext == s or re.sub(r"_v\d{2}$", "", no_ext) == s


def _excluded_path(f):
    parts = f.split("/")
    if len(parts) >= 3 and parts[0] == "Departments" and parts[2] in ("results", "workspace"):
        return True
    prefixes = ("Departments/Secretariat/docs/requests/REQ-", "Departments/Secretariat/assets/", "Audits/",
                "Departments/Quality/assets/acceptance/", "Departments/Quality/docs/nonconformance/", "CEO/", "Lab/")
    return f.startswith(prefixes)


def test_c3_5_real_records_ended_only_path_blocked(pytestconfig, tmp_path, script_bytes):
    found = require_close_records(pytestconfig)
    latest = latest_records()
    ended = set(found)
    active, ended_scopes = [], {}
    for name, rel in latest.items():
        key = "approved" if name.startswith("REQ") else "confirmed"
        value, scope = _parse_header((REPO / rel).read_text(encoding="utf-8"), key)
        if name in ended:
            ended_scopes[name] = scope
        elif value and TIME_RE.match(value):
            active.append(scope)  # 승인·확인 요건의 나머지(HOTFIX 조건)는 보지 않는다. 덮는 기록을 넓게 잡는 쪽이다
    candidates = set()
    for name, scope in ended_scopes.items():
        for s in scope:
            f = s if os.path.splitext(s.rsplit("/", 1)[-1])[1] else f"{s}/acc_c3_5_probe.md"
            if _excluded_path(f) or any(_covers(a, f) for sc in active for a in sc):
                continue
            candidates.add(f)
    assert candidates, "끝난 기록만 덮는 경로를 기록 파일에서 찾지 못했습니다"
    picked = sorted(candidates)[:3]
    print(f"[acc] 3 ⑤ 대상 경로: {picked}")

    repo = TempRepo(tmp_path / "repo", script_bytes)
    for rel_dir, pattern in ((REQ_DIR_REL, "REQ-*.md"), (HOTFIX_DIR_REL, "HOTFIX-*.md")):
        for p in (REPO / rel_dir).glob(pattern):
            repo.write(f"{rel_dir}/{p.name}", p.read_bytes())
    for name, p in found.items():
        repo.write(f"{INBOX_REL}/{p.name}", p.read_bytes())
    repo.commit_all("records")
    for f in picked:
        repo.write(f, "# 인수 시험 변경\n")
        rc, out = repo.run()
        repo.remove(f)
        assert rc == 1, f"{f}: 작업 트리 검사 종료 코드 {rc}(기대 1)\n{out}"
        assert "종결기록_" in out, f"{f}: 실패 출력에 종결 기록 경로가 없습니다\n{out}"


# ---------------------------------------------------------------- 체크리스트 4

def test_c4_1_3_dev_result_scope_comparison_covers_range(pytestconfig):
    body = dev_section(pytestconfig, "범위 대조")
    row_hashes = []
    for line in body.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and re.fullmatch(r"[0-9a-f]{7,40}", cells[1]):
            row_hashes.append(cells[1])
    tried = []
    for head in sorted(set(HEX40.findall(body))):
        rc, _ = git(REPO, "merge-base", "--is-ancestor", BASE_COMMIT, head, check=False)
        if rc != 0 or head == BASE_COMMIT:
            continue
        _, out = git(REPO, "log", "--format=%H", f"{BASE_COMMIT}..{head}")
        expected = out.split()
        matched = all(any(e.startswith(r) for r in row_hashes) for e in expected)
        tried.append(f"{head[:7]}: 기간 커밋 {len(expected)}개, 표 행 {len(row_hashes)}개, 모두 있음 {matched}")
        if matched and len(row_hashes) == len(expected) and len(set(row_hashes)) == len(row_hashes):
            return
    pytest.fail("개발 결과서 「범위 대조」 절에서 HEAD 커밋과, 그 기간의 커밋마다 한 행을 찾지 못했습니다:\n"
                + "\n".join(tried))


def test_c4_5_range_commits_not_rewritten(pytestconfig):
    head = pytestconfig.getoption("--acc-head")
    missing = []
    for h in RANGE_COMMITS_AT_ACC:
        rc, _ = git(REPO, "merge-base", "--is-ancestor", h, head, check=False)
        if rc != 0:
            missing.append(h[:7])
    assert not missing, f"{head}의 조상이 아닌 기간 안 커밋(고쳐 쓴 커밋 메시지 등): {missing}"
