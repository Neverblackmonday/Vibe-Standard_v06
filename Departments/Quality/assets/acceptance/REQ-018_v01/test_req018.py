# -*- coding: utf-8 -*-
"""REQ-018 인수 시험 (Workflow/03_라이프사이클 「시험실」).

대상은 개발 적용본의 커밋 전 검사 스크립트다.
  Departments/Development/workspace/REQ-018_적용본_vNN/Departments/Development/assets/scripts.적용본/check_standard.py
폴더 버전이 여럿이면 가장 높은 버전을 쓴다(REQ-018 5절 머리 안내 「적용본은 최신 버전」).
환경 변수 REQ018_ACC_TARGET에 스크립트 경로를 주면 그 파일을 대상으로 한다. 결함 사본(검출 없는 원본 등)으로
시험이 실제로 실패하는지(Red) 확인할 때만 쓴다.

시험은 이 저장소의 파일을 만들거나 고치지 않는다. 임시 Git 저장소는 pytest tmp_path 아래에만 만든다.
가짜 비밀정보는 EC-018 F12대로 실행 중에 문자열을 이어 붙여 만든다. 이 파일에는 검출 규칙에 맞는 문자열이 없다.
"""

import os
import random
import re
import string
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[5]
BASE_COMMIT = "dc88268"  # 적용본의 기준 커밋(EC-018 F11). 회귀 비교의 원본도 이 커밋에서 읽는다
SCRIPT_REL = "Departments/Development/assets/scripts/check_standard.py"
ALLOW_REL = "Departments/Development/assets/scripts/secret_allowlist.txt"
APPLIED_GLOB = "REQ-018_적용본_v[0-9][0-9]"
APPLIED_SCRIPTS_REL = "Departments/Development/assets/scripts.적용본"

SCOPE_DIR = "Departments/Design/docs/acc"  # 시험용 승인 REQ의 scope 안 경로
OUT_OF_SCOPE = "Departments/Operations/docs/acc-out.md"

REQ_TEXT = """---
task_id: "900"
approved: "2026-10-09T10:00:00+09:00"
scope:
  - Departments/Design/docs/acc
  - Departments/Development/assets/src
  - Departments/Development/assets/tests
  - Lab/acc-in-scope
---

# REQ-900: 인수 시험용 승인 REQ
"""


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
    })
    return env


ENV = _clean_env()


def _git(cwd, *args):
    res = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", *args],
                         cwd=cwd, capture_output=True, env=ENV)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패({res.returncode}): "
                           f"{res.stderr.decode('utf-8', 'replace')}")
    return res.stdout.decode("utf-8", "replace")


def applied_paths():
    """(검사 스크립트 적용본, 예외 목록 적용본 또는 None)을 돌려준다."""
    override = os.environ.get("REQ018_ACC_TARGET")
    if override:
        script = Path(override)
    else:
        folders = sorted((REPO / "Departments" / "Development" / "workspace").glob(APPLIED_GLOB))
        if not folders:
            pytest.fail("개발 적용본 폴더(Departments/Development/workspace/REQ-018_적용본_vNN)가 없습니다. "
                        "구현 단계 산출물이 있어야 합니다.")
        script = folders[-1] / APPLIED_SCRIPTS_REL / "check_standard.py"
    if not script.is_file():
        pytest.fail(f"검사 스크립트 적용본이 없습니다: {script}")
    allow = script.with_name("secret_allowlist.txt")
    return script, (allow if allow.is_file() else None)


def original_script_bytes():
    res = subprocess.run(["git", "show", f"{BASE_COMMIT}:{SCRIPT_REL}"], cwd=REPO,
                         capture_output=True, env=ENV)
    if res.returncode != 0:
        pytest.fail(f"기준 커밋 {BASE_COMMIT}의 check_standard.py를 읽지 못했습니다: "
                    f"{res.stderr.decode('utf-8', 'replace')}")
    return res.stdout


class Repo:
    """pytest tmp_path 아래의 임시 Git 저장소."""

    def __init__(self, root, script_bytes, allow_bytes):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        _git(root, "init", "-q")
        self.write(SCRIPT_REL, script_bytes)
        if allow_bytes is not None:
            self.write(ALLOW_REL, allow_bytes)
        self.write("Departments/Secretariat/docs/requests/REQ-900_v01.md", REQ_TEXT)
        self.git("add", "-A")
        self.commit("init")

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8") if isinstance(content, str) else content
        path.write_bytes(data)

    def append_allow(self, text):
        path = self.root / ALLOW_REL
        old = path.read_bytes() if path.exists() else b""
        if old and not old.endswith(b"\n"):
            old += b"\n"
        path.write_bytes(old + text.encode("utf-8"))

    def git(self, *args):
        return _git(self.root, *args)

    def stage(self, *rels):
        self.git("add", "--", *rels)

    def commit(self, msg):
        # 임시 저장소의 시험 준비 커밋이다. 사용자 전역 훅이 끼어들지 않게 --no-verify를 쓴다
        self.git("commit", "-q", "--no-verify", "-m", msg)

    def run(self, *args):
        res = subprocess.run([sys.executable, str(self.root / SCRIPT_REL), *args], cwd=self.root,
                             capture_output=True, env=ENV)
        out = res.stdout.decode("utf-8", "replace") + res.stderr.decode("utf-8", "replace")
        return res.returncode, out


@pytest.fixture
def repo(tmp_path):
    script, allow = applied_paths()
    return Repo(tmp_path / "repo", script.read_bytes(), allow.read_bytes() if allow else None)


# ---------------------------------------------------------------- 가짜 비밀정보 (EC-018 F1 규칙별)

_RNG = random.Random(20261009)
_ALNUM = string.ascii_letters + string.digits
_UPPER = string.ascii_uppercase + string.digits


def _fill(n, chars=_ALNUM):
    return "".join(_RNG.choice(chars) for _ in range(n))


def make_fakes():
    """규칙 이름 → (줄 내용, 출력에 나오면 안 되는 값 조각)."""
    fakes = {}
    fakes["private-key"] = ("-----BEGIN " + "RSA PRIVATE" + " KEY-----", "BEGIN " + "RSA PRIVATE")
    body = _fill(16, _UPPER)
    fakes["aws-access-key-id"] = ("AKIA" + body, body)
    body = _fill(40)
    fakes["github-token"] = ("gh" + "p_" + body, body)
    body = _fill(32)
    fakes["anthropic-api-key"] = ("sk-" + "ant-" + body, body)
    body = "proj" + _fill(28)
    fakes["openai-api-key"] = ("sk-" + body, body)
    body = _fill(35)
    fakes["google-api-key"] = ("AI" + "za" + body, body)
    body = _fill(24)
    fakes["slack-token"] = ("xo" + "xb-" + body, body)
    body = _fill(16)
    fakes["secret-assignment"] = ("client_secret" + " = " + '"' + body + '"', body)
    return fakes


def doc_with(line):
    """3행에 line을 둔 문서. 검출 줄 번호는 3이다."""
    return "# 인수 시험 파일\n설명 줄\n" + line + "\n끝 줄\n"


CLEAN_DOC = "# 인수 시험 파일\n비밀정보가 없는 변경이다.\n"


def assert_no_values(out, fakes):
    for rule, (line, fragment) in fakes.items():
        assert line not in out, f"출력에 {rule} 가짜 값 전체가 있습니다"
        assert fragment not in out, f"출력에 {rule} 가짜 값의 일부가 있습니다"


def detection(path, rule, line_no=3):
    return f"{path}:{line_no} [{rule}]"


# ---------------------------------------------------------------- 체크리스트 6 ⑧

def test_c6_8_each_rule_blocks_staged_commit_without_value(repo):
    fakes = make_fakes()
    paths = {}
    for rule, (line, _) in fakes.items():
        rel = f"{SCOPE_DIR}/{rule}.md"
        repo.write(rel, doc_with(line))
        paths[rule] = rel
    repo.stage(*paths.values())
    code, out = repo.run("--staged")
    assert code == 1, out
    assert "[FAIL]" in out
    for rule, rel in paths.items():
        assert detection(rel, rule) in out, f"{rule} 검출 줄이 없습니다\n{out}"
    assert_no_values(out, fakes)


def test_c6_8_all_detections_in_one_file_are_reported(repo):
    fakes = make_fakes()
    aws, gh, slack = (fakes[r][0] for r in ("aws-access-key-id", "github-token", "slack-token"))
    rel = f"{SCOPE_DIR}/multi.md"
    # 2행과 4행에 한 건씩, 5행 한 줄에 두 규칙
    repo.write(rel, "머리\n" + aws + "\n중간\n" + gh + "\n" + slack + " " + aws + "\n")
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 1, out
    for line_no, rule in ((2, "aws-access-key-id"), (4, "github-token"),
                          (5, "slack-token"), (5, "aws-access-key-id")):
        assert detection(rel, rule, line_no) in out, f"{line_no}행 {rule} 검출 줄이 없습니다\n{out}"
    assert_no_values(out, fakes)


def test_c6_8_allowlist_entry_excludes_only_that_file(repo):
    fakes = make_fakes()
    a = f"{SCOPE_DIR}/allowed.md"
    b = f"{SCOPE_DIR}/not-allowed.md"
    repo.write(a, doc_with(fakes["aws-access-key-id"][0]))
    repo.write(b, doc_with(fakes["github-token"][0]))
    repo.append_allow("# 2026-10-09 대표님 직접 인수 시험용 예외\n"
                      f"aws-access-key-id {a}\n")
    repo.stage(a, b)
    code, out = repo.run("--staged")
    assert code == 1, out
    assert detection(b, "github-token") in out, out
    assert detection(a, "aws-access-key-id") not in out, out
    assert_no_values(out, fakes)

    repo.git("restore", "--staged", "--", b)
    code, out = repo.run("--staged")
    assert code == 0, out
    assert any(l.startswith("[INFO]") and a in l and "aws-access-key-id" in l for l in out.splitlines()), out
    assert_no_values(out, fakes)


def test_c6_8_removing_value_and_restaging_passes(repo):
    fakes = make_fakes()
    rel = f"{SCOPE_DIR}/fix.md"
    repo.write(rel, doc_with(fakes["anthropic-api-key"][0]))
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 1, out
    repo.write(rel, CLEAN_DOC)
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 0, out


@pytest.mark.parametrize("rel", [
    "Departments/Design/workspace/REQ-900_acc.md",       # 부서 직속 workspace/
    "Departments/Design/results/RPT-900_v01.md",         # 부서 직속 results/
    "Departments/Secretariat/assets/inbox/ORD-900_v01.md",  # WHITELIST_PREFIXES
    "Departments/Quality/assets/acceptance/REQ-900_v01/test_x.py",  # 품질 인수 시험 경로
])
def test_c6_8_scope_excluded_paths_are_detected(repo, rel):
    fakes = make_fakes()
    repo.write(rel, doc_with(fakes["google-api-key"][0]))
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 1, out
    assert detection(rel, "google-api-key") in out, out
    assert_no_values(out, fakes)


def test_c6_8_ceo_only_commit_with_value_passes(repo):
    fakes = make_fakes()
    rel = "CEO/raw-note.md"
    repo.write(rel, doc_with(fakes["openai-api-key"][0]))
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 0, out
    assert_no_values(out, fakes)


@pytest.mark.parametrize("entry", ["no-such-rule Departments/Design/docs/acc/x.md", "aws-access-key-id"])
def test_c6_8_invalid_allowlist_entry_fails(repo, entry):
    repo.append_allow("# 2026-10-09 대표님 직접 잘못된 항목\n" + entry + "\n")
    rel = f"{SCOPE_DIR}/clean.md"
    repo.write(rel, CLEAN_DOC)
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 1, out
    assert "[FAIL]" in out


# ---------------------------------------------------------------- 체크리스트 6 ⑤ (실행 부분: 검사 대상과 처리)

def test_c6_5_deleted_file_is_not_target(repo):
    fakes = make_fakes()
    rel = f"{SCOPE_DIR}/old.md"
    repo.write(rel, doc_with(fakes["aws-access-key-id"][0]))
    repo.stage(rel)
    repo.commit("prepare")
    repo.git("rm", "-q", "--", rel)
    code, out = repo.run("--staged")
    assert code == 0, out
    assert f"{rel}:" not in out


def test_c6_5_rename_checks_new_path_only(repo):
    fakes = make_fakes()
    old = f"{SCOPE_DIR}/old.md"
    new = f"{SCOPE_DIR}/new.md"
    repo.write(old, doc_with(fakes["aws-access-key-id"][0]))
    repo.stage(old)
    repo.commit("prepare")
    repo.git("mv", old, new)
    code, out = repo.run("--staged")
    assert code == 1, out
    assert detection(new, "aws-access-key-id") in out, out
    assert f"{old}:" not in out, out
    assert_no_values(out, fakes)


def test_c6_5_staged_check_reads_index_content(repo):
    fakes = make_fakes()
    rel = f"{SCOPE_DIR}/index.md"
    repo.write(rel, doc_with(fakes["slack-token"][0]))
    repo.stage(rel)
    repo.write(rel, CLEAN_DOC)  # 작업 트리에서만 지우고 다시 스테이징하지 않는다
    code, out = repo.run("--staged")
    assert code == 1, out
    assert detection(rel, "slack-token") in out, out
    assert_no_values(out, fakes)


def test_c6_5_worktree_check_reads_worktree_content(repo):
    fakes = make_fakes()
    rel = f"{SCOPE_DIR}/worktree.md"
    repo.write(rel, doc_with(fakes["secret-assignment"][0]))
    code, out = repo.run()
    assert code == 1, out
    assert detection(rel, "secret-assignment") in out, out
    assert_no_values(out, fakes)


def test_c6_5_worktree_ceo_value_is_not_detected(repo):
    fakes = make_fakes()
    repo.write("CEO/raw-note.md", doc_with(fakes["aws-access-key-id"][0]))
    repo.write(f"{SCOPE_DIR}/clean.md", CLEAN_DOC)
    code, out = repo.run()
    assert code == 0, out
    assert "CEO/raw-note.md:" not in out
    assert_no_values(out, fakes)


def test_c6_5_lab_only_staged(repo):
    fakes = make_fakes()
    bad = "Lab/exp1/note.md"
    repo.write(bad, doc_with(fakes["github-token"][0]))
    repo.stage(bad)
    code, out = repo.run("--staged")
    assert code == 1, out
    assert detection(bad, "github-token") in out, out
    assert_no_values(out, fakes)

    repo.git("rm", "-q", "--cached", "--", bad)
    good = "Lab/exp1/clean.md"
    repo.write(good, CLEAN_DOC)
    repo.stage(good)
    code, out = repo.run("--staged")
    assert code == 0, out


def test_c6_5_lab_value_in_worktree_check_fails(repo):
    fakes = make_fakes()
    rel = "Lab/exp1/note.md"
    repo.write(rel, doc_with(fakes["github-token"][0]))
    code, out = repo.run()
    assert code == 1, out
    assert detection(rel, "github-token") in out, out
    assert_no_values(out, fakes)


def test_c6_5_lab_path_removed_before_scope_check_in_worktree(repo):
    lab = "Lab/exp1/clean.md"
    repo.write(lab, CLEAN_DOC)
    repo.write(OUT_OF_SCOPE, CLEAN_DOC)
    code, out = repo.run()
    assert code == 1, out
    marker = "[FAIL] 변경 파일 전체를 포함하는"
    assert marker in out, out
    tail = out.split(marker, 1)[1]
    assert OUT_OF_SCOPE in tail, out
    assert lab not in tail, out


def test_c6_5_binary_file_is_skipped_with_info(repo):
    fakes = make_fakes()
    rel = f"{SCOPE_DIR}/blob.dat"
    repo.write(rel, b"abc\x00def\n" + fakes["aws-access-key-id"][0].encode("ascii") + b"\n")
    repo.stage(rel)
    code, out = repo.run("--staged")
    assert code == 0, out
    assert any(l.startswith("[INFO]") for l in out.splitlines()), out
    assert rel in out, out
    assert_no_values(out, fakes)


# ---------------------------------------------------------------- 체크리스트 6 ⑨ (기존 검사 회귀)

def _write_stage(r, *rels):
    for rel in rels:
        r.write(rel, CLEAN_DOC)
    r.stage(*rels)


def sc_no_change_staged(r):
    return ["--staged"]


def sc_ceo_only_staged(r):
    _write_stage(r, "CEO/memo.md")
    return ["--staged"]


def sc_ceo_mixed_staged(r):
    _write_stage(r, "CEO/memo.md", f"{SCOPE_DIR}/a.md")
    return ["--staged"]


def sc_ceo_mixed_whitelist_staged(r):
    _write_stage(r, "CEO/memo.md", "Departments/Design/results/RPT-900_v01.md")
    return ["--staged"]


def sc_ceo_only_worktree(r):
    r.write("CEO/memo.md", CLEAN_DOC)
    return []


def sc_ceo_and_scope_worktree(r):
    r.write("CEO/memo.md", CLEAN_DOC)
    r.write(f"{SCOPE_DIR}/a.md", CLEAN_DOC)
    return []


def sc_lab_only_staged(r):
    _write_stage(r, "Lab/exp1/a.md")
    return ["--staged"]


def sc_lab_in_scope_staged(r):
    _write_stage(r, "Lab/acc-in-scope/a.md", f"{SCOPE_DIR}/a.md")
    return ["--staged"]


def sc_lab_out_of_scope_staged(r):
    _write_stage(r, "Lab/exp1/a.md", f"{SCOPE_DIR}/a.md")
    return ["--staged"]


def sc_lab_only_worktree(r):
    r.write("Lab/exp1/a.md", CLEAN_DOC)
    return []


def sc_lab_and_out_of_scope_worktree(r):
    r.write("Lab/exp1/a.md", CLEAN_DOC)
    r.write(OUT_OF_SCOPE, CLEAN_DOC)
    return []


def sc_whitelist_only_staged(r):
    _write_stage(r, "Departments/Design/results/RPT-900_v01.md",
                 "Departments/Secretariat/assets/inbox/ORD-900_v01.md",
                 "Departments/Quality/assets/acceptance/REQ-900_v01/test_x.py",
                 "Departments/Quality/docs/nonconformance/NCR-900_01.md")
    return ["--staged"]


def sc_in_scope_one_staged(r):
    _write_stage(r, f"{SCOPE_DIR}/a.md")
    return ["--staged"]


def sc_in_scope_many_staged(r):
    _write_stage(r, f"{SCOPE_DIR}/a.md", f"{SCOPE_DIR}/b.md", f"{SCOPE_DIR}/sub/c.md")
    return ["--staged"]


def sc_out_of_scope_staged(r):
    _write_stage(r, OUT_OF_SCOPE)
    return ["--staged"]


def sc_unapproved_req_staged(r):
    r.write("Departments/Secretariat/docs/requests/REQ-901_v01.md",
            '---\ntask_id: "901"\napproved: ""\nscope:\n  - Departments/Marketing/docs\n---\n')
    _write_stage(r, "Departments/Marketing/docs/a.md")
    r.stage("Departments/Secretariat/docs/requests/REQ-901_v01.md")
    return ["--staged"]


def sc_hotfix_over_count_staged(r):
    r.write("Departments/Secretariat/results/HOTFIX-902_v01.md",
            '---\ntask_id: "902"\nconfirmed: "2026-10-09T11:00:00+09:00"\nscope:\n'
            '  - Departments/Operations/assets/live\n---\n')
    r.stage("Departments/Secretariat/results/HOTFIX-902_v01.md")
    _write_stage(r, *(f"Departments/Operations/assets/live/p{i}.md" for i in range(4)))
    return ["--staged"]


def sc_src_and_tests_staged(r):
    r.write("Departments/Development/assets/src/acc_mod.py", "VALUE = 1\n")
    r.write("Departments/Development/assets/tests/test_acc_mod.py", "def test_ok():\n    assert 1 + 1 == 2\n")
    r.stage("Departments/Development/assets/src/acc_mod.py",
            "Departments/Development/assets/tests/test_acc_mod.py")
    return ["--staged"]


REGRESSION_SCENARIOS = [
    sc_no_change_staged, sc_ceo_only_staged, sc_ceo_mixed_staged, sc_ceo_mixed_whitelist_staged,
    sc_ceo_only_worktree, sc_ceo_and_scope_worktree, sc_lab_only_staged, sc_lab_in_scope_staged,
    sc_lab_out_of_scope_staged, sc_lab_only_worktree, sc_lab_and_out_of_scope_worktree,
    sc_whitelist_only_staged, sc_in_scope_one_staged, sc_in_scope_many_staged, sc_out_of_scope_staged,
    sc_unapproved_req_staged, sc_hotfix_over_count_staged, sc_src_and_tests_staged,
]


def comparable(out):
    """검사기의 판정 줄만 남긴다.

    pytest 하위 실행의 출력(경로·소요 시간)은 저장소마다 달라 비교에서 뺀다. 적용본에 더해진
    비밀정보 검출 줄(검출 결과, 예외 목록 안내)은 원본에 없으므로 뺀다(EC-018 3.4절 T11).
    """
    keep = []
    for line in out.splitlines():
        if not (line.startswith("[") or line.startswith(" ")):
            continue
        if "비밀정보" in line or "예외 목록" in line:
            continue
        keep.append(line)
    return keep


@pytest.mark.parametrize("scenario", REGRESSION_SCENARIOS, ids=lambda f: f.__name__[3:])
def test_c6_9_existing_checks_match_original(tmp_path, scenario):
    script, allow = applied_paths()
    allow_bytes = allow.read_bytes() if allow else None
    original = Repo(tmp_path / "original", original_script_bytes(), allow_bytes)
    applied = Repo(tmp_path / "applied", script.read_bytes(), allow_bytes)
    args_o = scenario(original)
    args_a = scenario(applied)
    code_o, out_o = original.run(*args_o)
    code_a, out_a = applied.run(*args_a)
    assert code_a == code_o, f"종료 코드가 다릅니다(원본 {code_o}, 적용본 {code_a})\n원본:\n{out_o}\n적용본:\n{out_a}"
    assert comparable(out_a) == comparable(out_o), f"원본:\n{out_o}\n적용본:\n{out_a}"


# ---------------------------------------------------------------- 체크리스트 6 ⑩ (실측에 쓰는 --scan-all의 실행 부분)

def test_c6_10_scan_all_reports_tracked_files_and_history_without_values(repo):
    fakes = make_fakes()
    tracked = f"{SCOPE_DIR}/tracked.md"
    gone = f"{SCOPE_DIR}/gone.md"
    ceo = "CEO/raw-note.md"
    repo.write(tracked, doc_with(fakes["aws-access-key-id"][0]))
    repo.write(ceo, doc_with(fakes["slack-token"][0]))
    repo.stage(tracked, ceo)
    repo.commit("tracked")
    repo.write(gone, doc_with(fakes["github-token"][0]))
    repo.stage(gone)
    repo.commit("add gone")
    added = repo.git("rev-parse", "HEAD").strip()
    repo.git("rm", "-q", "--", gone)
    repo.commit("remove gone")

    code, out = repo.run("--scan-all")
    assert code == 1, out
    assert detection(tracked, "aws-access-key-id") in out, out
    assert detection(ceo, "slack-token") in out, out  # 추적 파일 검출은 CEO/를 포함한다(EC-018 F7)
    hist = re.findall(r"\b([0-9a-f]{7,40}) " + re.escape(gone) + r" \[github-token\]", out)
    assert hist, f"커밋 이력 검출 줄(<커밋 짧은 해시> <경로> [<규칙 이름>])이 없습니다\n{out}"
    assert any(added.startswith(h) for h in hist), out
    assert_no_values(out, fakes)


def test_c6_10_scan_all_clean_repository_exits_zero(repo):
    repo.write(f"{SCOPE_DIR}/clean.md", CLEAN_DOC)
    repo.stage(f"{SCOPE_DIR}/clean.md")
    repo.commit("clean")
    code, out = repo.run("--scan-all")
    assert code == 0, out


# ---------------------------------------------------------------- 체크리스트 6 ⑫

def test_c6_12_no_new_files_under_operations():
    res = subprocess.run(["git", "-c", "core.quotepath=false", "status", "--porcelain", "-uall",
                          "--", "Departments/Operations"], cwd=REPO, capture_output=True, env=ENV)
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    assert res.stdout.decode("utf-8", "replace").strip() == ""
