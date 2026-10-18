# -*- coding: utf-8 -*-
"""REQ-032 인수 시험: 폴더와 작업 구역 재편(부 → 팀)과 검사 장치 재구성.

작성 기준은 Workflow/03_라이프사이클 「시험실」, 절차서는 Departments/Quality/results/ACC-032_v03.md다.

- 시험은 저장소 파일을 만들거나 고치지 않는다. 시험 저장소는 모두 pytest tmp_path 아래에 만든다.
- 「반영 뒤 상태」(REQ-032 5절 머리 안내)는 이 저장소를 tmp 아래로 복제하고, 작업 트리의 미추적 파일
  (.gitignore 무시 제외)을 읽기만 해서 같은 경로로 복사한 뒤, 결과서의 반영 명령(이동 포함)과 삭제 대상
  처리를 그 복제본에서 실행한 상태다(EC-032_v04 3.11절).
- 옛 경로·새 경로 대응, 이동하지 않는 파일, 옛 경로 패턴, 잔존 검사의 뺄 범위는 승인된 EC-032_v04
  3.3절 2~4번과 3.6절 2번에서 옮긴 기대값이다. 개발부 이동 명령·검사의 구현과 독립된 기대값으로 쓴다.
"""

import ast
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------- 기본값

BASE_COMMIT = "655a45d"  # EC-032_v04 1절 「변경 배경」의 원본 커밋
FIX_DATE = "20261020"  # 시험 저장소의 고정값(승인 기록·종결 기록 날짜)
SCRIPTS_NEW = "Departments/Development/Implementation/assets/scripts"
SCRIPTS_OLD = "Departments/Development/assets/scripts"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪"
TRUST_GUIDE = "폴더 신뢰 확인 화면"  # EC-032_v04 3.6절 4번 신뢰 처리 안내 문구의 일부

# EC-032_v04 3.3절 2번 표. 위에서부터 처음 맞는 행을 적용한다. (옛 폴더, 이름 조건, 새 폴더)
# 이름 조건이 있는 행은 그 폴더 바로 아래에서 이름이 조건으로 시작하는 파일만 맞는다.
# 운영부·마케팅부 행은 이동 명령이 쓰지 않으므로(3.3절 2번 표 아래 셋째 항목) 넣지 않는다.
MOVE_RULES = (
    ("Departments/Secretariat/assets/inbox/연락/", None, "Departments/Secretariat/Secretary/workspace/연락/"),
    ("Departments/Secretariat/assets/inbox/셸작업/", None, "Departments/Secretariat/Secretary/workspace/셸작업/"),
    ("Departments/Secretariat/assets/", None, "Departments/Secretariat/Secretary/assets/"),
    ("Departments/Secretariat/docs/", None, "Departments/Secretariat/PM/docs/"),
    ("Departments/Secretariat/workspace/", None, "Departments/Secretariat/PM/workspace/"),
    ("Departments/Secretariat/results/", "HOTFIX-", "Departments/Development/Hotfix/results/"),
    ("Departments/Design/docs/tad/", "EC-", "Departments/Design/EC/docs/"),
    ("Departments/Design/docs/", None, "Departments/Design/Spec/docs/"),
    ("Departments/Design/assets/", None, "Departments/Design/Spec/assets/"),
    ("Departments/Design/results/", None, "Departments/Design/EC/results/"),
    ("Departments/Design/workspace/", None, "Departments/Design/Spec/workspace/"),
    ("Departments/Development/assets/", None, "Departments/Development/Implementation/assets/"),
    ("Departments/Development/results/", "HOTFIX-", "Departments/Development/Hotfix/results/"),
    ("Departments/Development/results/", None, "Departments/Development/Implementation/results/"),
    ("Departments/Development/workspace/", None, "Departments/Development/Implementation/workspace/"),
    ("Departments/Quality/results/", "ACC-", "Departments/Quality/Test/results/"),
    ("Departments/Quality/results/", None, "Departments/Quality/Review/results/"),
    ("Departments/Quality/assets/", None, "Departments/Quality/Test/assets/"),
    ("Departments/Quality/docs/nonconformance/", None, "Departments/Quality/Nonconformance/docs/"),
    ("Departments/Quality/workspace/", None, "Departments/Quality/Review/workspace/"),
)

# EC-032_v04 3.3절 3번 「삭제」 행(17개)
DELETED_GITKEEPS = frozenset(
    ["Departments/Development/docs/.gitkeep", "Departments/Quality/docs/.gitkeep",
     "Departments/Secretariat/results/.gitkeep"]
    + [f"Departments/Operations/{p}/.gitkeep"
       for p in ("assets/live", "assets/logs", "assets/releases", "docs", "results", "workspace")]
    + [f"Departments/Marketing/{p}/.gitkeep"
       for p in ("assets/banners", "assets/fonts", "assets/icons", "assets/images", "assets/media",
                 "docs", "results", "workspace")])

# EC-032_v04 3.3절 3번 「새로 만듦」 행
NEW_GITKEEPS = ("Departments/Secretariat/ConfigControl/.gitkeep", "Departments/Operations/.gitkeep",
                "Departments/Marketing/.gitkeep")

# EC-032_v04 3.3절 1번 구조도(반영 뒤 활성 팀 폴더)
ACTIVE_TEAMS = {
    "Secretariat": {"Secretary", "PM", "ConfigControl"},
    "Design": {"EC", "Spec"},
    "Development": {"Implementation", "Hotfix"},
    "Quality": {"Review", "Nonconformance", "Test"},
}
DEPARTMENTS = {"Secretariat", "Design", "Development", "Quality", "Operations", "Marketing"}
COMMON_SUBFOLDERS = {"docs", "assets", "results", "workspace", ".gitkeep"}

# EC-032_v04 3.2절 G1(팀 이름, 팀 폴더 이름)
TEAM_FOLDERS = (
    ("비서팀", "Secretary"), ("PM팀", "PM"), ("형상통제팀", "ConfigControl"), ("EC팀", "EC"),
    ("명세팀", "Spec"), ("구현팀", "Implementation"), ("핫픽스팀", "Hotfix"), ("판정팀", "Review"),
    ("부적합관리팀", "Nonconformance"), ("시험팀", "Test"), ("배포팀", "Release"), ("보안팀", "Security"),
    ("디자인팀", "VisualDesign"), ("콘텐츠팀", "Content"), ("홍보팀", "Promotion"),
)

# EC-032_v04 3.6절 2번 ③ 옛 경로 패턴
OLD_PATH_PATTERNS = (
    re.compile(r"Departments/(Secretariat|Design|Development|Quality|Operations|Marketing|\*|<부서>)/"
               r"(assets|docs|results|workspace)\b"),
    re.compile(r"(?<![\w/.])(Secretariat|Design|Development|Quality|Operations|Marketing)/"
               r"(assets|docs|results|workspace)\b"),
)

# EC-032_v04 3.6절 2번 ② 뺄 범위
RESIDUAL_EXCLUDED_TOP = ("CEO/", "_archive/", "Lab/", "Audits/")
RESIDUAL_RECORD_PREFIXES = (
    "Departments/Secretariat/Secretary/assets/", "Departments/Secretariat/PM/docs/",
    "Departments/Design/EC/docs/", "Departments/Quality/Nonconformance/docs/",
    "Departments/Quality/Test/assets/acceptance/",
)

# EC-032_v04 3.5절 10행의 새 allow 규칙
NEW_ALLOW_RULES = tuple(
    f"Bash(python {SCRIPTS_NEW}/{n}*)" for n in ("check_env.py", "prepare_final_commit.py", "check_overlap.py")
) + tuple(
    f"PowerShell(python {SCRIPTS_NEW}/{n} *)" for n in ("check_env.py", "prepare_final_commit.py", "check_overlap.py")
)

NEW_COMMANDS = ("check_standard.py", "check_commit_msg.py", "check_env.py", "prepare_final_commit.py",
                "check_overlap.py")


# ---------------------------------------------------------------- 실행 도구

def _env(extra=None):
    env = dict(os.environ)
    for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY"):
        env.pop(key, None)
    env.update({
        "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "GIT_TERMINAL_PROMPT": "0",
        "GIT_AUTHOR_NAME": "acc-test", "GIT_AUTHOR_EMAIL": "acc-test@example.invalid",
        "GIT_COMMITTER_NAME": "acc-test", "GIT_COMMITTER_EMAIL": "acc-test@example.invalid",
    })
    if extra:
        env.update(extra)
    return env


def run(args, cwd, env=None, timeout=1800):
    res = subprocess.run([str(a) for a in args], cwd=str(cwd), capture_output=True,
                         env=env or _env(), timeout=timeout)
    return res.returncode, (res.stdout + res.stderr).decode("utf-8", "replace")


def git(cwd, *args, env=None):
    return run(["git", "-c", "core.quotepath=false", *args], cwd, env=env)


def git_ok(cwd, *args, env=None):
    code, out = git(cwd, *args, env=env)
    assert code == 0, f"git {' '.join(map(str, args))} 실패(종료 코드 {code}):\n{out}"
    return out


def git_z(cwd, *args):
    res = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=str(cwd), capture_output=True,
                         env=_env())
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    return [p for p in res.stdout.decode("utf-8").split("\0") if p]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tail(text, n=60):
    return "\n".join(text.splitlines()[-n:])


def _toplevel():
    res = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(Path(__file__).resolve().parent),
                         capture_output=True, env=_env())
    assert res.returncode == 0, "저장소 루트를 찾을 수 없습니다"
    return Path(res.stdout.decode("utf-8").strip())


REPO = _toplevel()


# ---------------------------------------------------------------- 입력 문서 찾기

def _versioned(folders, pattern, min_version=1):
    best = None
    for folder in folders:
        folder = REPO / folder
        if not folder.is_dir():
            continue
        for p in folder.glob("*"):
            m = re.fullmatch(pattern, p.name)
            if m and int(m.group(1)) >= min_version and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), p)
    return best[1] if best else None


# 이번 원스톱(REQ-032_v06 재승인 뒤)이 쓰는 산출물 버전의 하한(EC-032_v04 1절 「이전 버전과의 관계」 둘째 항목).
# 앞 원스톱의 적용본 v01·DEV-032_v02·v03·RPT-032_v02는 작성 파트 대조가 남은 입력이므로 읽지 않는다
# (EC-032_v04 3.12절 표 아래 항목, 4절 17행).
MIN_APPLIED = 2  # 설계·개발 적용본 폴더 REQ-032_적용본_v02 이상
MIN_DEV = 5      # DEV-032_v05 이상(DEV-032_v04는 이번 실험 결과서)
MIN_RPT = 4      # RPT-032_v04 이상(명세 결과서)


def design_dir(config):
    opt = config.getoption("--acc-design-dir")
    if opt:
        return (REPO / opt).resolve()
    return _versioned(["Departments/Design/workspace", "Departments/Design/Spec/workspace"],
                      r"REQ-032_적용본_v(\d{2})", min_version=MIN_APPLIED)


def dev_dir(config):
    opt = config.getoption("--acc-dev-dir")
    if opt:
        return (REPO / opt).resolve()
    return _versioned(["Departments/Development/workspace", "Departments/Development/Implementation/workspace"],
                      r"REQ-032_적용본_v(\d{2})", min_version=MIN_APPLIED)


def dev_result(config):
    opt = config.getoption("--acc-dev-result")
    if opt:
        return (REPO / opt).resolve()
    return _versioned(["Departments/Development/results", "Departments/Development/Implementation/results"],
                      r"DEV-032_v(\d{2})\.md", min_version=MIN_DEV)


def rpt_result(config):
    opt = config.getoption("--acc-rpt-result")
    if opt:
        return (REPO / opt).resolve()
    return _versioned(["Departments/Design/results", "Departments/Design/EC/results"], r"RPT-032_v(\d{2})\.md",
                      min_version=MIN_RPT)


def applied_path(config, rel):
    """현행 거버넌스 파일(REQ-032 5절 머리 안내): 적용본이 있으면 적용본, 없으면 원본."""
    for base in (dev_dir(config), design_dir(config)):
        if not base:
            continue
        if rel.startswith(SCRIPTS_NEW + "/"):
            cand = base / (SCRIPTS_NEW + ".적용본") / rel[len(SCRIPTS_NEW) + 1:]
        else:
            top, _, rest = rel.partition("/")
            cand = base / (top + ".적용본") / rest if rest else base / (rel + ".적용본")
        if cand.is_file():
            return cand
    if rel.startswith(SCRIPTS_NEW + "/"):
        old = REPO / SCRIPTS_OLD / rel[len(SCRIPTS_NEW) + 1:]
        return old if old.is_file() else None
    return REPO / rel if (REPO / rel).is_file() else None


def gov(config, rel):
    p = applied_path(config, rel)
    assert p is not None, f"현행 거버넌스 파일 {rel}이 없습니다(적용본·원본 모두 없음)"
    return p.read_text(encoding="utf-8")


def base_text(rel):
    res = subprocess.run(["git", "show", f"{BASE_COMMIT}:{rel}"], cwd=str(REPO), capture_output=True, env=_env())
    assert res.returncode == 0, f"원본 {BASE_COMMIT}:{rel}을 읽을 수 없습니다"
    return res.stdout.decode("utf-8")


def dev_scripts_dir(config):
    d = dev_dir(config)
    assert d is not None, "개발 적용본 폴더(REQ-032_적용본_vNN)가 없습니다(구현 단계 산출물)"
    p = d / (SCRIPTS_NEW + ".적용본")
    assert p.is_dir(), f"개발 적용본에 스크립트 폴더가 없습니다: {p}"
    return p


# ---------------------------------------------------------------- 문서 읽기

def without_history(text):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^## .*개정 이력\s*$", line):
            return "\n".join(lines[:i])
    return text


def section(text, num):
    """번호 절(예: "4" → "## 4. ", "3.1" → "### 3.1 ")의 제목 줄부터 같거나 높은 단계 제목 앞까지."""
    head = re.compile(rf"^(#{{1,6}}) {re.escape(num)}{r'\. ' if '.' not in num else ' '}")
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = head.match(line)
        if m:
            level = len(m.group(1))
            out = [line]
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6}) ", nxt)
                if h and len(h.group(1)) <= level:
                    break
                out.append(nxt)
            return "\n".join(out)
    return ""


def heading_section(text, keyword):
    """제목에 keyword가 있는 첫 절(같거나 높은 단계 제목 앞까지)."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6}) (.*)$", line)
        if m and keyword in m.group(2):
            level = len(m.group(1))
            out = [line]
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6}) ", nxt)
                if h and len(h.group(1)) <= level:
                    break
                out.append(nxt)
            return "\n".join(out)
    return ""


def item(sec, n):
    """절 안에서 줄 첫머리 「n. 」로 시작하는 번호 항목(다음 번호 항목 앞까지)."""
    lines = sec.splitlines()
    out, inside = [], False
    for line in lines:
        if re.match(rf"^{n}\. ", line):
            inside = True
            out.append(line)
            continue
        if inside:
            if re.match(r"^\d+\. ", line) or re.match(r"^#{1,6} ", line):
                break
            out.append(line)
    return "\n".join(out)


def must_contain(text, words, where):
    missing = [w for w in words if w not in text]
    assert not missing, f"{where}에 없는 문구: {missing}"


# ---------------------------------------------------------------- 대응표(기대값)

def expected_new_path(rel):
    for old, name_prefix, new in MOVE_RULES:
        if not rel.startswith(old):
            continue
        rest = rel[len(old):]
        if name_prefix is not None:
            if "/" in rest or not rest.startswith(name_prefix):
                continue
        return new + rest
    return None


def is_not_moved(rel):
    """EC-032_v04 3.3절 4번 ①② (③ 무시된 파일은 목록에 들어오지 않는다)."""
    if rel in DELETED_GITKEEPS:
        return True
    parts = rel.split("/")
    if len(parts) >= 4 and parts[0] == "Departments" and parts[2] == "workspace":
        name = parts[3]
        if name.startswith("REQ-032_") and not re.fullmatch(r"REQ-032_적용본_v\d{2}", name):
            return True
    return False


def residual_target(rel):
    if rel.startswith(RESIDUAL_EXCLUDED_TOP):
        return False
    parts = rel.split("/")
    if len(parts) >= 5 and parts[0] == "Departments" and parts[3] in ("results", "workspace"):
        return False
    return not rel.startswith(RESIDUAL_RECORD_PREFIXES)


def residual_lines(rel, text):
    """줄 단위로 뺄 범위(개정 이력 H2부터 끝, 02의 2.3절)를 뺀 (줄 번호, 줄) 목록."""
    lines = text.splitlines()
    keep = []
    skip_23 = False
    for no, line in enumerate(lines, 1):
        if rel.endswith(".md") and re.match(r"^## .*개정 이력\s*$", line):
            break
        if rel == "Workflow/02_부서_구조_및_작업구역.md":
            if re.match(r"^### 2\.3", line):
                skip_23 = True
                continue
            if skip_23 and re.match(r"^#{1,3} ", line):
                skip_23 = False
            if skip_23:
                continue
        keep.append((no, line))
    return keep


def old_path_hits(root, rels):
    hits = []
    for rel in rels:
        data = (root / rel).read_bytes()
        if b"\0" in data:
            continue
        for no, line in residual_lines(rel, data.decode("utf-8", "replace")):
            for pat in OLD_PATH_PATTERNS:
                m = pat.search(line)
                if m:
                    hits.append(f"{rel}:{no}: {m.group(0)}")
                    break
    return hits


# ---------------------------------------------------------------- 결과서 읽기

def inline_codes(text):
    return re.findall(r"`([^`\n]+)`", text)


def reflection_commands(text):
    """「## 4.」 절의 표 줄에서 반영 명령(cp, python -I)을 순서대로 꺼낸다."""
    sec = section(text, "4")
    cmds = []
    for line in sec.splitlines():
        if not line.startswith("|"):
            continue
        for code in inline_codes(line):
            if (code.startswith("cp ") or code.startswith("python -I ")) and code not in cmds:
                cmds.append(code)
    return cmds


def deletion_paths(text):
    sec = heading_section(text, "삭제 대상")
    return [c for c in inline_codes(sec) if c.startswith("Departments/")]


def commit_message_template(text):
    for block in re.findall(r"```[^\n]*\n(.*?)```", text, re.S):
        lines = [ln.rstrip() for ln in block.strip("\n").splitlines()]
        if lines and lines[0].startswith("feat: [REQ-032] "):
            return "\n".join(lines) + "\n"
    codes = inline_codes(text)
    subject = next((c for c in codes if c.startswith("feat: [REQ-032] ")), None)
    keys = {}
    for c in codes:
        m = re.match(r"^(Approved-REQ|Approved-RES|Approval-Record): (\S+)$", c)
        if m and m.group(1) not in keys:
            keys[m.group(1)] = c
    if subject and len(keys) == 3:
        return "\n".join([subject, ""] + [keys[k] for k in ("Approved-REQ", "Approved-RES", "Approval-Record")]) + "\n"
    return None


def fill_placeholders(msg, nn, date):
    msg = msg.replace("<NN>", nn).replace("<YYYYMMDD>", date)
    msg = re.sub(r"_vNN\b", f"_v{nn}", msg)
    return msg.replace("YYYYMMDD", date)


# ---------------------------------------------------------------- 시험 저장소

def mirror_worktree(dst):
    """이 저장소 작업 트리의 미추적 파일과 바뀐 추적 파일을 읽기만 해서 dst의 같은 경로로 옮겨 적는다."""
    for rel in git_z(REPO, "ls-files", "--others", "--exclude-standard", "-z"):
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, dst / rel)
    for rel in git_z(REPO, "ls-files", "-m", "-z"):
        if (REPO / rel).is_file():
            shutil.copyfile(REPO / rel, dst / rel)
    for rel in git_z(REPO, "ls-files", "-d", "-z"):
        if (dst / rel).is_file():
            (dst / rel).unlink()


def write(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")
    return p


def res_fixture(task, result="pass"):
    return (f'---\ntask_id: "{task}"\ngate: "FINAL"\nresult: "{result}"\n'
            f'completed_at: "2026-10-20T09:00:00+09:00"\nauditor:\n  agent: "Quality"\n'
            f'  model: "acc-test"\n  effort: "medium"\n---\n\n# RES-{task}: 판정서(시험 저장소 고정값)\n\n'
            f'## 1. 판정 요약\n- **판정 결과**: `{result}`\n\n## 7. 삭제 대상 (최종 판정만)\n없음\n')


def approval_fixture(name, target):
    return (f"# 승인 기록: {name}\n\n- **승인 문구 원문**: {name} 승인\n"
            f"- **문구를 받은 시각**: 2026-10-20T09:10:00+09:00\n- **대상 파일 경로**: {target}\n"
            f"- **대상 버전**: v01\n- **기재 세션**: acc-test\n- **기재 모델**: acc-test\n")


@pytest.fixture(scope="session")
def reflected(tmp_path_factory, pytestconfig):
    """반영 뒤 상태(커밋 전). EC-032_v04 3.9절 4번 ②~⑤를 시험 저장소에서 실행한다."""
    dev = dev_result(pytestconfig)
    rpt = rpt_result(pytestconfig)
    if dev is None:
        pytest.fail("DEV-032_v05 이상 결과서가 없어 반영 뒤 상태를 만들 수 없습니다(구현 단계 산출물)")
    if rpt is None:
        pytest.fail("RPT-032_v04 이상 결과서가 없습니다")
    dev_text = dev.read_text(encoding="utf-8")
    rpt_text = rpt.read_text(encoding="utf-8")
    tmp = tmp_path_factory.mktemp("reflected")
    root = tmp / "repo"
    git_ok(tmp, "clone", "-q", "--no-hardlinks", str(REPO), str(root))
    mirror_worktree(root)
    snapshot = {rel: sha256(root / rel)
                for rel in git_z(root, "ls-files", "-co", "--exclude-standard", "-z", "--", "Departments")}

    dev_cmds = reflection_commands(dev_text)
    moves = [c for c in dev_cmds if c.startswith("python -I ") and "--apply" in c]
    if not moves:
        pytest.fail(f"{dev.name} 4절 표에서 `python -I … --apply` 이동 명령을 찾지 못했습니다")
    tokens = shlex.split(moves[0])
    code, out = run([sys.executable] + tokens[1:], root)
    if code != 0:
        pytest.fail(f"이동 명령 `{moves[0]}` 실패(종료 코드 {code}):\n{tail(out)}")
    move_out = out

    overwritten = set()
    copies = [c for c in reflection_commands(rpt_text) if c.startswith("cp ")] + \
             [c for c in dev_cmds if c.startswith("cp ")]
    if not copies:
        pytest.fail("결과서 4절 표에서 cp 반영 명령을 찾지 못했습니다")
    for cmd in copies:
        args = shlex.split(cmd)
        if len(args) != 3:
            pytest.fail(f"cp \"<적용본>\" \"<원본>\" 형태가 아닌 반영 명령: {cmd}")
        src, dst = root / args[1], root / args[2]
        if not src.is_file():
            pytest.fail(f"반영 명령의 적용본이 반영 뒤 상태에 없습니다: {cmd}")
        if not dst.parent.is_dir():
            pytest.fail(f"반영 명령의 원본 폴더가 반영 뒤 상태에 없습니다: {cmd}")
        shutil.copyfile(src, dst)
        overwritten.add(args[2])

    deleted = []
    for rel in deletion_paths(dev_text):
        p = root / rel
        if p.is_dir():
            shutil.rmtree(p)
        elif p.is_file():
            p.unlink()
        else:
            pytest.fail(f"{dev.name} 「삭제 대상」의 경로가 이동 뒤에 없습니다: {rel}")
        deleted.append(rel)
    # Workflow/03_라이프사이클 최종 판정 기준 7의 일회성 파일(최종 판정서 「삭제 대상」이 옛 경로로 적는 것)
    for dept in sorted((root / "Departments").iterdir()):
        ws = dept / "workspace"
        if ws.is_dir():
            for p in sorted(ws.iterdir()):
                if p.name.startswith("REQ-032_") and not re.fullmatch(r"REQ-032_적용본_v\d{2}", p.name):
                    shutil.rmtree(p) if p.is_dir() else p.unlink()
                    deleted.append(p.relative_to(root).as_posix())
    return {"root": root, "snapshot": snapshot, "overwritten": overwritten, "deleted": deleted,
            "move_out": move_out, "dev_text": dev_text}


@pytest.fixture(scope="session")
def committed(reflected):
    """반영 뒤 상태에서 EC-032_v04 3.9절 4번 ⑥⑦과 ⑧ 표대로 스테이징하고 결과서 메시지로 커밋한 상태."""
    root = reflected["root"]
    template = commit_message_template(reflected["dev_text"])
    if template is None:
        pytest.fail("DEV 결과서에서 이 REQ의 커밋 메시지(제목 줄 `feat: [REQ-032] …`와 근거 줄 세 줄)를 찾지 못했습니다")
    existing = [int(m.group(1)) for p in (root / "Departments/Quality/Review/results").glob("RES-032_v*.md")
                if (m := re.fullmatch(r"RES-032_v(\d{2})\.md", p.name))]
    nn = f"{(max(existing) + 1) if existing else 1:02d}"
    msg = fill_placeholders(template, nn, FIX_DATE)
    fields = dict(re.findall(r"^(Approved-REQ|Approved-RES|Approval-Record): (\S+)$", msg, re.M))
    if len(fields) != 3:
        pytest.fail(f"커밋 메시지 근거 줄을 읽지 못했습니다:\n{msg}")
    if not (root / fields["Approved-REQ"]).is_file():
        pytest.fail(f"Approved-REQ 경로가 반영 뒤 상태에 없습니다: {fields['Approved-REQ']}")
    res_rel, appr_rel = fields["Approved-RES"], fields["Approval-Record"]
    if not (root / res_rel).exists():
        write(root, res_rel, res_fixture("032"))
    if not (root / appr_rel).exists():
        write(root, appr_rel, approval_fixture(Path(res_rel).stem, res_rel))
    close_rel = f"Departments/Secretariat/Secretary/assets/inbox/종결기록_{FIX_DATE}_REQ-032.md"
    write(root, close_rel,
          f"- 대상 기록: {fields['Approved-REQ']}\n- 종결 경로: 커밋\n- 커밋 종류: 최종 승인 커밋\n"
          f"- 끝낸 커밋: 이 기록을 더한 커밋\n- 근거: 최종 판정서 {res_rel}, 승인 기록 {appr_rel}\n"
          f"- 작성 주체: acc-test\n- 작성 시각: 2026-10-20T09:20:00+09:00\n")
    # 스테이징은 05 1.1절 6번 분류로만 한다(EC-032_v04 3.9절 4번 ⑥). 이 안건의 변경은 모두 REQ scope 안
    # (①~⑪의 기록·산출물도 Departments 아래)이므로 scope 항목을 pathspec으로 쓴다. 저장소 루트의 다른 미추적
    # 파일(예: 미추적 폴더 `Claude outputs/`)은 분류할 수 없는 변경이며 스테이징하지 않는다(ACC-032_v03 2절 「반영 뒤 상태 만들기」 7번).
    req_text = (root / fields["Approved-REQ"]).read_text(encoding="utf-8")
    scope_block = re.search(r"^scope:\n((?:  - .+\n)+)", req_text, re.M)
    if not scope_block:
        pytest.fail(f"{fields['Approved-REQ']}에서 scope를 읽지 못했습니다")
    specs = [ln[4:].split(" #")[0].strip() for ln in scope_block.group(1).splitlines()]
    specs = [s for s in specs if (root / s).exists()]
    git_ok(root, "add", "-A", "--", *specs)
    if not (root / ".githooks/commit-msg").is_file():
        pytest.fail("반영 뒤 상태에 .githooks/commit-msg가 없습니다")
    git_ok(root, "add", "--chmod=+x", "--", ".githooks/commit-msg")
    head_before = git_ok(root, "rev-parse", "HEAD").strip()
    msg_file = root.parent / "commit_msg.txt"
    msg_file.write_text(msg, encoding="utf-8", newline="\n")
    code, out = git(root, "-c", "core.hooksPath=.githooks", "commit", "-q", "-F", str(msg_file))
    if code != 0:
        pytest.fail(f"반영 뒤 상태의 커밋이 새 훅을 통과하지 못했습니다(종료 코드 {code}):\n{tail(out, 80)}")
    head_after = git_ok(root, "rev-parse", "HEAD").strip()
    return {"root": root, "msg": msg, "commit_out": out, "head_before": head_before, "head_after": head_after,
            "fields": fields, "close_rel": close_rel}


@pytest.fixture
def clone(committed, tmp_path):
    """커밋된 반영 뒤 상태의 복제본(시험마다 새로 만든다)."""
    dst = tmp_path / "work"
    git_ok(tmp_path, "clone", "-q", "--no-hardlinks", str(committed["root"]), str(dst))
    return dst


def staged_check(root, files):
    """files({경로: 내용})를 쓰고 스테이징해 새 커밋 전 검사(--staged)를 실행한 뒤 되돌린다."""
    for rel, text in files.items():
        write(root, rel, text)
    git_ok(root, "add", "--", *files)
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_standard.py", "--staged"], root)
    git_ok(root, "reset", "-q", "--", *files)
    for rel in files:
        (root / rel).unlink()
    return code, out


# ================================================================ 체크리스트 18

def test_c18_1_team_folder_rule(pytestconfig):
    t02 = gov(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md")
    s3 = section(t02, "3")
    must_contain(s3, ["「부 → 팀」", "파트 폴더는 두지 않는다", "용도 이름", "`docs/`", "`assets/`", "`results/`",
                      "`workspace/`", "대기 팀 폴더는 만들지 않"], "02 3절")
    s22 = section(t02, "2.2")
    assert re.search(r"^\| 부 \| 팀 \| 팀 폴더 \|", s22, re.M), "02 2.2절 표에 「팀 폴더」 열이 없습니다"
    missing = [f"{team} `{folder}`" for team, folder in TEAM_FOLDERS
               if not re.search(rf"\| {re.escape(team)} \| `{folder}` \|", s22)]
    assert not missing, f"02 2.2절 표에서 팀 폴더 이름(EC G1)이 다른 행: {missing}"


def test_c18_2_folder_composition(reflected, committed):
    root = reflected["root"]
    files = [r for r in git_z(root, "ls-files", "-z", "--", "Departments")]
    children = {}
    for rel in files:
        parts = rel.split("/")
        children.setdefault(parts[1], set()).add(parts[2] if len(parts) > 2 else "")
    assert set(children) == DEPARTMENTS, f"부서 폴더가 여섯 개 그대로가 아닙니다: {sorted(children)}"
    for dept in ("Operations", "Marketing"):
        under = [r for r in files if r.startswith(f"Departments/{dept}/")]
        assert under == [f"Departments/{dept}/.gitkeep"], f"{dept} 아래가 폴더 자리 하나가 아닙니다: {under}"
    for dept, teams in ACTIVE_TEAMS.items():
        assert children[dept] == teams, f"{dept} 아래 폴더가 활성 팀 폴더와 다릅니다: {sorted(children[dept])}"
    bad = sorted({"/".join(r.split("/")[:4]) for r in files
                  if len(r.split("/")) > 4 and r.split("/")[1] in ACTIVE_TEAMS
                  and r.split("/")[3] not in COMMON_SUBFOLDERS})
    assert not bad, f"팀 폴더 바로 아래에 공통 하위 폴더 밖의 폴더(파트 폴더 등)가 있습니다: {bad}"
    missing = [g for g in NEW_GITKEEPS if g not in files]
    assert not missing, f"새로 만들 폴더 자리가 없습니다: {missing}"


def test_c18_3_moved_files_unchanged(reflected):
    """체크리스트 18 ③과 ⑪(이동 뒤 기록 내용 불변)."""
    root, snap, overwritten = reflected["root"], reflected["snapshot"], reflected["overwritten"]
    unmapped, missing, changed, left = [], [], [], []
    for rel, digest in sorted(snap.items()):
        if is_not_moved(rel):
            if (root / rel).exists():
                left.append(f"{rel}(이동하지 않는 파일이 정리 뒤에도 남음)")
            continue
        new = expected_new_path(rel)
        if new is None:
            unmapped.append(rel)
            continue
        if (root / rel).exists():
            left.append(rel)
        if not (root / new).is_file():
            missing.append(f"{rel} → {new}")
        elif new not in overwritten and sha256(root / new) != digest:
            changed.append(f"{rel} → {new}")
    assert not unmapped, f"EC 3.3절 2번 표에 맞지 않는 파일(기대값 오류이거나 새 파일): {unmapped[:20]}"
    assert not missing, f"대응표의 새 경로에 없는 파일 {len(missing)}개: {missing[:20]}"
    assert not changed, f"이동 전후 해시가 다른 파일 {len(changed)}개: {changed[:20]}"
    assert not left, f"옛 경로에 남은 파일 {len(left)}개: {left[:20]}"


def test_c18_4_work_zone_table(pytestconfig):
    s4 = section(gov(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), "4")
    # 표를 지키는지 보는 방법과 한계(EC-032_v04 3.4절 머리 문장, G6)
    must_contain(s4, ["수정 주체(파트)", "REQ `scope:` 대조", "PM의 단계별 확인", "판정의 범위 대조",
                      "기계가 잡지 않는다"], "02 4절")
    rows = {
        "REQ 작성": ("`Departments/Secretariat/PM/docs/requests/`", "P01"),
        "EC 판단": ("`Departments/Design/EC/results/`", "E01"),
        "인수 시험": ("`Departments/Quality/Test/assets/acceptance/`", "Q07"),
        "부적합 기록": ("`Departments/Quality/Nonconformance/docs/`", "Q06"),
        "핫픽스": ("`Departments/Development/Hotfix/results/`", "V03"),
        "셸 작업 지시": ("`Departments/Secretariat/Secretary/workspace/셸작업/`", "S01"),
    }
    for name, (path, code) in rows.items():
        line = next((ln for ln in s4.splitlines() if ln.startswith(f"| {name} |")), "")
        assert path in line and code in line, f"02 4절 「{name}」 행에 {path}·{code}가 없습니다: {line}"


def _hdr(key, agent):
    return f'---\ntask_id: "950"\n{key}:\n  agent: "{agent}"\n  model: "acc-test"\n---\n\n# 시험 문서\n'


def _author_mismatch_files():
    """머리말 작성 주체 값이 놓인 위치의 부서·팀·파트와 다른 파일들(작성 파트 대조가 있으면 실패할 경우).

    RES-032_v01 결함 D1의 경우(명세팀 workspace 적용본 폴더 안 서식 사본의 견본 값)와, 같은 scope 안에서
    다른 부서·팀·파트의 위치에 쓴 파일(02 4절 머리 문장의 「기계가 잡지 않는다」)을 함께 둔다.
    REQ-950은 승인된 시험 REQ이며 PRD 위치를 scope로 가져, 대조 제외 밖 변경의 통과 근거가 된다."""
    spec_ws = "Departments/Design/Spec/workspace/REQ-950_적용본_v01/Workflow.적용본/templates"
    return {
        "Departments/Secretariat/PM/docs/requests/REQ-950_v01.md":
            ('---\ntask_id: "950"\napproved: "2026-10-20T09:00:00+09:00"\nauthor:\n  agent: "PM"\n'
             'scope:\n  - Departments/Design/Spec/docs/prd\n---\n\n# REQ-950: 시험\n'),
        "Departments/Design/Spec/docs/prd/PRD-950_v01.md": _hdr("author", "Quality"),
        f"{spec_ws}/RES_TEMPLATE.md": _hdr("auditor", "Quality"),
        f"{spec_ws}/REQ_TEMPLATE.md": _hdr("author", "PM"),
        "Departments/Quality/Review/results/RES-950-REQ_v01.md": _hdr("auditor", "Design"),
        "Departments/Quality/Test/results/ACC-950_v01.md": _hdr("author", "Q01"),
        "Departments/Quality/Review/workspace/memo950.md": _hdr("author", "External"),
    }


def test_c18_4_no_author_part_check_staged(clone):
    """작성 파트 대조가 없다(ORDER 3절 45항, EC-032_v04 G6·3.11절 18 ④): 머리말 작성 주체 값이 위치와 다른
    파일을 REQ scope 안의 변경과 함께 스테이징해도 새 커밋 전 검사(--staged)가 통과한다."""
    files = _author_mismatch_files()
    code, out = staged_check(clone, files)
    assert code == 0, f"작성 주체 값이 위치와 다른 파일 때문에 커밋 전 검사가 실패했습니다(종료 코드 {code}):\n{tail(out, 30)}"


def test_c18_4_no_author_part_check_worktree(clone):
    """같은 경우의 작업 트리 검사(옵션 없음). 반영 뒤 커밋된 상태라 작업 트리 변경은 이 파일들뿐이다."""
    files = _author_mismatch_files()
    for rel, text in files.items():
        write(clone, rel, text)
    try:
        code, out = run([sys.executable, SCRIPTS_NEW + "/check_standard.py"], clone)
    finally:
        for rel in files:
            (clone / rel).unlink()
    assert code == 0, f"작성 주체 값이 위치와 다른 파일 때문에 작업 트리 검사가 실패했습니다(종료 코드 {code}):\n{tail(out, 30)}"


def test_c18_4_no_author_part_check_code(pytestconfig):
    """코드 Grep 부분: 개발 적용본 스크립트에 작성 파트 대조의 상수·문구가 없고(EC-032_v04 3.6절 1번),
    규정(설계 적용본 02·06)에 작성 파트 대조를 정하는 문구가 없다. 남은 author.agent·auditor.agent 줄이
    대조인지는 열람 부분(최종 판정, DEV 「대조」 ⑤)이다."""
    d = dev_scripts_dir(pytestconfig)
    hits = []
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.suffix in (".py", ".md", ".txt"):
            for no, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"PART_WRITE_PATHS|작성 파트", ln):
                    hits.append(f"{p.relative_to(d).as_posix()}:{no}: {ln.strip()[:100]}")
    for rel in ("Workflow/02_부서_구조_및_작업구역.md", "Workflow/06_통제장치_및_배포.md"):
        for no, ln in residual_lines(rel, gov(pytestconfig, rel)):
            if "작성 파트" in ln:
                hits.append(f"{rel}:{no}: {ln.strip()[:100]}")
    assert not hits, "작성 파트 대조의 코드·규정 문구가 남아 있습니다:\n" + "\n".join(hits[:30])


def test_c18_5_mapping_only_in_02(pytestconfig):
    t02 = gov(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md")
    s23 = section(t02, "2.3")
    pairs = [(old + (p or ""), new) for old, p, new in MOVE_RULES]
    missing = [f"{o} → {n}" for o, n in pairs
               if not any(f"`{o}" in ln and f"`{n}" in ln for ln in s23.splitlines())]
    assert not missing, f"02 2.3절에 없는 대응 행: {missing}"
    docs = ["AGENTS.md", "CLAUDE.md"] + sorted(
        p.relative_to(REPO).as_posix() for p in (REPO / "Workflow").rglob("*") if p.is_file()) + sorted(
        p.relative_to(REPO).as_posix() for p in (REPO / ".claude/agents").glob("*.md"))
    hits = []
    for rel in docs:
        text = gov(pytestconfig, rel)
        for no, line in residual_lines(rel, text):
            if any(p.search(line) for p in OLD_PATH_PATTERNS):
                hits.append(f"{rel}:{no}: {line.strip()[:120]}")
    assert not hits, f"02 2.3절·개정 이력 밖에 옛 경로(대응의 다시 적기 포함)가 있는 줄 {len(hits)}개:\n" + "\n".join(hits[:30])


def test_c18_6_no_old_paths_in_target_range(committed):
    root = committed["root"]
    rels = [r for r in git_z(root, "ls-files", "-z") if residual_target(r)]
    assert rels, "대상 범위의 추적 파일이 없습니다"
    hits = old_path_hits(root, rels)
    assert not hits, f"D12 대상 범위에 옛 경로 {len(hits)}건:\n" + "\n".join(hits[:40])


def _insert_before_revision_history(original, line):
    """개정 이력 H2 줄 바로 앞(D12의 대상 범위)에 한 줄을 넣은 바이트와 그 줄 번호(1부터)를 돌려준다.
    ACC-032_v02 6절 1번: 파일 끝은 개정 이력 H2 아래라 EC 3.6절 2번 ②의 뺄 범위이기 때문이다."""
    lines = original.decode("utf-8").splitlines(keepends=True)
    idx = next((i for i, ln in enumerate(lines) if re.match(r"^## .*개정 이력\s*$", ln)), None)
    assert idx is not None, "Workflow/01_표준_개요.md에 개정 이력 H2 줄이 없습니다"
    new = "".join(lines[:idx]) + line + "\n\n" + "".join(lines[idx:])
    return new.encode("utf-8"), idx + 1


def test_c18_6_old_path_blocks_commit(clone):
    target = "Workflow/01_표준_개요.md"
    original = (clone / target).read_bytes()
    try:
        changed, lineno = _insert_before_revision_history(original, "시험 줄: `Departments/Quality/results/`")
        (clone / target).write_bytes(changed)
        git_ok(clone, "add", "--", target)
        code, out = run([sys.executable, SCRIPTS_NEW + "/check_standard.py", "--staged"], clone)
        git_ok(clone, "reset", "-q", "--", target)
        changed_ok, _ = _insert_before_revision_history(original, "시험 줄: `Departments/Quality/Review/results/`")
        (clone / target).write_bytes(changed_ok)
        git_ok(clone, "add", "--", target)
        code_ok, out_ok = run([sys.executable, SCRIPTS_NEW + "/check_standard.py", "--staged"], clone)
        git_ok(clone, "reset", "-q", "--", target)
    finally:
        (clone / target).write_bytes(original)
    assert code != 0 and re.search(rf"{re.escape(target)}:{lineno}\b", out), \
        f"옛 경로를 넣은 대상 범위 파일의 스테이징이 막히지 않았습니다(종료 코드 {code}):\n{tail(out, 20)}"
    for word in ("[INFO]",) + RESIDUAL_EXCLUDED_TOP + ("Departments/Secretariat/Secretary/assets/",):
        assert word in out, f"옛 경로 잔존 검사 출력에 뺀 범위 「{word}」가 없습니다:\n{tail(out, 30)}"
    assert code_ok == 0 and not re.search(rf"{re.escape(target)}:\d+", out_ok), \
        f"새 경로만 넣은 같은 변경이 통과하지 않았습니다(종료 코드 {code_ok}):\n{tail(out_ok, 20)}"


def test_c18_7_archive_excludes(committed):
    root = committed["root"]
    res = subprocess.run(["git", "-c", "core.quotepath=false", "archive", "--format=tar", "HEAD"],
                         cwd=str(root), capture_output=True, env=_env())
    assert res.returncode == 0, res.stderr.decode("utf-8", "replace")
    names = [m.name for m in tarfile.open(fileobj=io.BytesIO(res.stdout)).getmembers() if m.isfile()]
    zones = (
        (r"^Departments/[^/]+/[^/]+/results/", "팀 직속 results/"),
        (r"^Departments/[^/]+/[^/]+/workspace/", "팀 직속 workspace/(연락·셸 작업 포함)"),
        (r"^Departments/Secretariat/Secretary/assets/[^/]+/", "비서팀 assets/"),
        (r"^Departments/Quality/Test/assets/acceptance/", "인수 시험"),
        (r"^Departments/Quality/Nonconformance/docs/", "부적합 기록"),
    )
    leaked = [n for n in names for pat, _ in zones if re.match(pat, n) and not n.endswith("/.gitkeep")]
    leaked += [n for n in names if re.search(r"/(REQ|EC)-\d{3}[^/]*\.md$", n) and n.startswith("Departments/")]
    assert not leaked, f"배포본(git archive)에 들어간 내부 기록 {len(leaked)}개: {leaked[:20]}"
    tracked = git_z(root, "ls-files", "-z", "--", "Departments")
    for pat, label in zones:
        assert any(re.match(pat, t) and not t.endswith("/.gitkeep") for t in tracked), \
            f"{label}에 추적 파일이 없어 제외를 확인할 수 없습니다"
    must = [SCRIPTS_NEW + "/check_standard.py", "Workflow/02_부서_구조_및_작업구역.md",
            "Departments/Quality/Review/results/.gitkeep"]
    absent = [m for m in must if m not in names]
    assert not absent, f"배포본에 있어야 할 파일이 없습니다: {absent}"


def test_c18_7_scope_exclusion_staged(clone):
    """체크리스트 18 ⑦의 대조 제외, ⑧의 PM팀 REQ·실행 기록, ⑩의 연락·셸 작업 폴더."""
    excluded = {
        "Departments/Quality/Review/results/memo950.md": "메모\n",
        "Departments/Development/Implementation/workspace/memo950.md": "메모\n",
        "Departments/Secretariat/PM/docs/requests/REQ-950_v01.md":
            '---\ntask_id: "950"\napproved: ""\nauthor:\n  agent: "PM"\nscope:\n  - Lab/x\n---\n\n# REQ-950: 시험\n',
        "Departments/Secretariat/PM/workspace/실행기록_REQ-950.md": "실행 기록\n",
        "Departments/Secretariat/Secretary/assets/research/조사_20261020_시험_v01.md": "조사\n",
        "Departments/Quality/Test/assets/acceptance/REQ-950_v01/test_x.py": "def test_x():\n    pass\n",
        "Departments/Quality/Nonconformance/docs/NCR-950_01.md": "부적합\n",
        "Departments/Secretariat/Secretary/workspace/연락/memo950.md": "연락\n",
        "Departments/Secretariat/Secretary/workspace/셸작업/memo950.md": "셸 작업\n",
    }
    code, out = staged_check(clone, excluded)
    assert code == 0, f"대조 제외 구역의 변경만 스테이징했는데 실패했습니다(종료 코드 {code}):\n{tail(out, 30)}"
    control = {"Departments/Design/Spec/docs/prd/PRD-950_v01.md": "명세\n"}
    code_c, out_c = staged_check(clone, control)
    assert code_c != 0, f"대조 제외 밖(명세 위치) 변경이 승인 scope 없이 통과했습니다:\n{tail(out_c, 20)}"


def test_c18_7_rule_paths_text(pytestconfig):
    agents = gov(pytestconfig, "AGENTS.md")
    s2 = section(agents, "2")
    must_contain(item(s2, 3), [f"`{SCRIPTS_NEW}/`"], "AGENTS.md 2절 3항")
    must_contain(item(s2, 5), ["`Departments/Secretariat/Secretary/assets/`"], "AGENTS.md 2절 5항")


def test_c18_8_pm_not_in_judgment_exclusion(pytestconfig):
    s5 = item(section(gov(pytestconfig, "AGENTS.md"), "2"), 5)
    assert s5, "AGENTS.md 2절 5항을 찾지 못했습니다"
    assert "Departments/Secretariat/PM" not in s5, "판정 전제 제외(AGENTS.md 2절 5항)에 PM팀 폴더가 들어 있습니다"


def test_c18_10_contact_shell_locations(pytestconfig):
    new_shell = "Departments/Secretariat/Secretary/workspace/셸작업/"
    new_contact = "Departments/Secretariat/Secretary/workspace/연락/"
    s07 = section(gov(pytestconfig, "Workflow/07_문서_서식_및_번호.md"), "1")
    assert any("셸 작업" in ln and new_shell in ln for ln in s07.splitlines()), "07 1절 표 셸 작업 행에 새 위치가 없습니다"
    s4 = section(gov(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), "4")
    assert any(ln.startswith("| 연락 기록 |") and new_contact in ln for ln in s4.splitlines()), \
        "02 4절 「연락 기록」 행에 새 위치가 없습니다"
    s5 = item(section(gov(pytestconfig, "AGENTS.md"), "2"), 5)
    must_contain(s5, [new_contact.rstrip("/"), new_shell.rstrip("/")], "AGENTS.md 2절 5항(판정 전제 제외)")


def test_c18_11_records_unchanged_in_worktree():
    """이미 작성된 기록(추적 파일)의 내용이 이 저장소 작업 트리에서 바뀌지 않았다."""
    lines = git_z(REPO, "status", "--porcelain", "-z", "--", "Departments")
    changed = [ln for ln in lines if ln[:2].strip() and not ln.startswith("??")]
    assert not changed, f"Departments 아래 추적 파일의 변경: {changed[:20]}"


def test_c18_12_application_timing(pytestconfig):
    """체크리스트 18 ⑫과 20 ⑩의 규정 부분(02 2절 표 아래 REQ-032 적용 시점 항목)."""
    s2 = section(gov(pytestconfig, "Workflow/02_부서_구조_및_작업구역.md"), "2")
    line = next((ln for ln in s2.splitlines() if "`REQ-032`가 바꾼 규정과 경로" in ln), "")
    # EC-032_v04 3.8절 3번 ⑤의 문안 요소(작성 파트 대조의 적용 시점은 v04에서 빠졌다)
    must_contain(line, ["`REQ-032` 커밋 뒤에 기동하는 세션", "자신의 최종 승인 커밋에도 실행",
                        "`--no-verify`를 쓰지 않고 멈춰 보고", "`setup.cmd`를 실행할 때부터",
                        "이미 실행 중인 세션은 기동 때의 규정으로 진행", "2.3절로 읽는다"],
                 "02 2절 표 아래 REQ-032 적용 시점 항목")
    assert "작성 파트" not in line, "02 2절 REQ-032 적용 시점 항목에 작성 파트 대조가 남아 있습니다"


# ================================================================ 체크리스트 20

def _msg_case(root, text):
    f = root.parent / "msg_case.txt"
    f.write_text(text, encoding="utf-8", newline="\n")
    return run([sys.executable, SCRIPTS_NEW + "/check_commit_msg.py", str(f)], root)


def test_c20_1_commit_msg_cases(committed, clone):
    head = committed["head_after"][:7]
    f = committed["fields"]
    good = (f"docs: [REQ-032] 최종 판정서 추가\n\nApproved-REQ: {f['Approved-REQ']}\n"
            f"Approved-RES: {f['Approved-RES']}\nApproval-Record: {f['Approval-Record']}\n")
    hotfix = "Departments/Development/Hotfix/results/HOTFIX-901_v01.md"
    request = "Departments/Secretariat/Secretary/assets/inbox/요청기록_20261020_시험.md"
    write(clone, hotfix, '---\ntask_id: "901"\nconfirmed: "2026-10-20T09:00:00+09:00"\nscope:\n  - x\n---\n')
    write(clone, request, "- 요청 문구 원문: 시험\n")
    git_ok(clone, "add", "--", hotfix, request)
    old_req = f["Approved-REQ"].replace("Departments/Secretariat/PM/docs/", "Departments/Secretariat/docs/")
    cases = [
        ("제목 줄에 기록 이름 없음", "feat: 기록 이름 없는 제목\n", False),
        ("REQ 커밋, Follows 맞음", good + f"Follows: {head}\n", True),
        ("REQ 커밋, Follows 없음(같은 REQ 이전 커밋 있음)", good, False),
        ("REQ 커밋, Follows 해시 틀림", good + "Follows: 0000000\n", False),
        ("REQ 커밋, 근거 줄 경로가 index에 없음(옛 경로)",
         good.replace(f["Approved-REQ"], old_req) + f"Follows: {head}\n", False),
        ("REQ 커밋, 근거 줄 누락(Approval-Record 없음)",
         "\n".join(ln for ln in good.splitlines() if not ln.startswith("Approval-Record")) + f"\nFollows: {head}\n", False),
        ("REQ 커밋, 근거 줄이 아닌 줄", good + f"Follows: {head}\nNote: 메모\n", False),
        ("REQ 커밋, Co-Authored-By 트레일러", good + f"Follows: {head}\nCo-Authored-By: acc <acc@example.invalid>\n", True),
        ("[CEO] 근거 줄 없음", "docs: [CEO] 시험 커밋\n\n본문 문장\n", True),
        ("[CEO] 07 밖 키의 줄", "docs: [CEO] 시험 커밋\n\nRefs: 시험\nNote: 메모\n", True),
        ("[CEO] Approved-REQ 키", f"docs: [CEO] 시험 커밋\n\nApproved-REQ: {f['Approved-REQ']}\n", False),
        ("[CEO] Request-Record 없이 Follows", f"docs: [CEO] 시험 커밋\n\nFollows: {head}\n", False),
        ("[CEO] Request-Record", f"docs: [CEO] 시험 커밋\n\nRequest-Record: {request}\n", True),
        ("[CEO] Request-Record, 이전 커밋 없는데 Follows", f"docs: [CEO] 시험 커밋\n\nRequest-Record: {request}\nFollows: {head}\n", False),
        ("HOTFIX 커밋", f"fix: [HOTFIX-901] 시험 수정\n\nConfirmed-HOTFIX: {hotfix}\n", True),
        ("HOTFIX 커밋, Confirmed-HOTFIX 없음", "fix: [HOTFIX-901] 시험 수정\n", False),
    ]
    problems = []
    for name, text, ok in cases:
        code, out = _msg_case(clone, text)
        if (code == 0) != ok:
            problems.append(f"[{name}] 기대 {'통과' if ok else '실패'}, 종료 코드 {code}:\n{tail(out, 10)}")
    assert not problems, "\n".join(problems)


def test_c20_1_first_commit_skipped(pytestconfig, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    git_ok(empty, "init", "-q")
    shutil.copytree(dev_scripts_dir(pytestconfig), empty / SCRIPTS_NEW)
    msg = tmp_path / "m.txt"
    msg.write_text("기록 이름 없는 첫 커밋 메시지\n", encoding="utf-8")
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_commit_msg.py", str(msg)], empty)
    assert code == 0, f"첫 커밋(HEAD 없음)을 검사했습니다(종료 코드 {code}):\n{tail(out)}"


def test_c20_1_hook_blocks_bad_message(clone):
    rel = "Departments/Quality/Review/workspace/memo950.md"
    write(clone, rel, "메모\n")
    git_ok(clone, "add", "--", rel)
    head = git_ok(clone, "rev-parse", "HEAD").strip()
    msg = clone.parent / "bad.txt"
    msg.write_text("feat: 기록 이름 없는 제목\n", encoding="utf-8")
    code, out = git(clone, "-c", "core.hooksPath=.githooks", "commit", "-q", "-F", str(msg))
    assert code != 0, f"commit-msg 훅이 틀린 메시지의 커밋을 막지 않았습니다:\n{tail(out)}"
    assert git_ok(clone, "rev-parse", "HEAD").strip() == head, "막힌 커밋 뒤 HEAD가 바뀌었습니다"
    msg.write_text("docs: [CEO] 시험 메모\n", encoding="utf-8")
    code_ok, out_ok = git(clone, "-c", "core.hooksPath=.githooks", "commit", "-q", "-F", str(msg))
    assert code_ok == 0, f"맞는 메시지의 커밋이 훅을 통과하지 못했습니다:\n{tail(out_ok)}"


def _home(tmp_path, root, trust):
    home = tmp_path / f"home_{trust}"
    home.mkdir(exist_ok=True)
    top = git_ok(root, "rev-parse", "--show-toplevel").strip()
    state = home / ".claude.json"
    if trust == "true":
        state.write_text(json.dumps({"projects": {top: {"hasTrustDialogAccepted": True}}}), encoding="utf-8")
    elif trust == "false":
        state.write_text(json.dumps({"projects": {top: {"hasTrustDialogAccepted": False}}}), encoding="utf-8")
    elif trust == "nokey":
        state.write_text(json.dumps({"projects": {}}), encoding="utf-8")
    return home, state


def _check_env(root, home, *opts):
    env = _env({"HOME": str(home), "USERPROFILE": str(home)})
    return run([sys.executable, SCRIPTS_NEW + "/check_env.py", *opts], root, env=env)


def test_c20_2_check_env_cases(clone, tmp_path):
    problems = []
    home_t, state_t = _home(tmp_path, clone, "true")
    code_s, out_s = _check_env(clone, home_t, "--setup")
    code_n, out_n = _check_env(clone, home_t)
    if code_s == 0 or code_n == 0:
        problems.append(f"[훅 경로 미설정] 두 모드 모두 실패해야 함: --setup {code_s}, 옵션 없음 {code_n}\n{tail(out_s, 8)}")
    git_ok(clone, "config", "core.hooksPath", ".githooks")
    before = sha256(state_t)
    code_s, out_s = _check_env(clone, home_t, "--setup")
    code_n, out_n = _check_env(clone, home_t)
    if code_s != 0 or code_n != 0 or TRUST_GUIDE in out_s + out_n:
        problems.append(f"[모두 충족] 두 모드 모두 통과, 안내 없음이어야 함: --setup {code_s}, 옵션 없음 {code_n}\n{tail(out_n, 8)}")
    if sha256(state_t) != before:
        problems.append("[모두 충족] 신뢰 상태 파일이 바뀌었습니다")
    for trust in ("false", "nokey", "nofile"):
        home, state = _home(tmp_path, clone, trust)
        before = sha256(state) if state.exists() else None
        code_s, out_s = _check_env(clone, home, "--setup")
        code_n, out_n = _check_env(clone, home)
        if code_s != 0 or "[WARN]" not in out_s or TRUST_GUIDE not in out_s:
            problems.append(f"[신뢰 {trust}] --setup은 [WARN]·안내·종료 코드 0이어야 함: {code_s}\n{tail(out_s, 8)}")
        if code_n == 0 or "[FAIL]" not in out_n:
            problems.append(f"[신뢰 {trust}] 옵션 없음은 [FAIL]·실패여야 함: {code_n}\n{tail(out_n, 8)}")
        after = sha256(state) if state.exists() else None
        if before != after:
            problems.append(f"[신뢰 {trust}] 신뢰 상태 파일이 바뀌었습니다")
    hook = clone / ".githooks/commit-msg"
    saved = hook.read_bytes()
    hook.unlink()
    try:
        code_s, out_s = _check_env(clone, home_t, "--setup")
    finally:
        hook.write_bytes(saved)
    if code_s == 0:
        problems.append(f"[commit-msg 훅 없음] --setup이 실패해야 함\n{tail(out_s, 8)}")
    assert not problems, "\n".join(problems)


@pytest.mark.skipif(os.name != "nt", reason="setup.cmd는 Windows 명령 파일이다")
def test_c20_2_setup_cmd(clone, tmp_path):
    problems = []
    for trust, guide in (("true", False), ("nokey", True)):
        home, state = _home(tmp_path, clone, trust)
        before = sha256(state)
        env = _env({"HOME": str(home), "USERPROFILE": str(home)})
        # 경로를 붙인다. NoDefaultCurrentDirectoryInExePath가 설정된 환경에서 cmd.exe가 작업 폴더의
        # 파일을 이름만으로 찾지 않기 때문이다(ACC-032_v02 6절 2번).
        code, out = run(["cmd", "/c", ".\\setup.cmd"], clone, env=env)
        if code != 0:
            problems.append(f"[신뢰 {trust}] setup.cmd 종료 코드 {code}\n{tail(out, 12)}")
        if (TRUST_GUIDE in out) != guide:
            problems.append(f"[신뢰 {trust}] 신뢰 처리 안내 {'없음' if guide else '있음'}\n{tail(out, 12)}")
        if sha256(state) != before:
            problems.append(f"[신뢰 {trust}] 신뢰 상태 파일이 바뀌었습니다")
        hooks = git(clone, "config", "--get", "core.hooksPath")[1].strip()
        if hooks != ".githooks":
            problems.append(f"[신뢰 {trust}] core.hooksPath가 .githooks가 아님: {hooks}")
    assert not problems, "\n".join(problems)


def test_c20_2_pm_launch_rule(pytestconfig):
    s83 = section(gov(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), "8.3")
    line = next((ln for ln in s83.splitlines() if "2-1)" in ln), "")
    must_contain(line, ["check_env.py", "PM을 기동하지 않고"], "05 8.3절 「PM 기동」 2-1)")


def _scenario_901(root):
    """REQ-901 최종 승인 커밋 직전의 작업 트리(05 1.1절 6번 ①~⑪마다 한 경로, 분류 못 할 변경)."""
    ws = "Departments/Development/Implementation/workspace"
    applied = f"{ws}/REQ-901_적용본_v01/Workflow.적용본/04_모델_운용.md"
    cp = f'cp "{applied}" "Workflow/04_모델_운용.md"'
    files = {
        "Departments/Secretariat/PM/docs/requests/REQ-901_v01.md":
            ('---\ntask_id: "901"\nclassification: "Major"\ncreated: "2026-10-20"\n'
             'created_at: "2026-10-20T09:00:00+09:00"\n'
             'source_order: "Departments/Secretariat/Secretary/assets/inbox/ORD-901_v01.md"\n'
             'approved: "2026-10-20T09:30:00+09:00"\nauthor:\n  agent: "PM"\n  model: "acc-test"\n'
             '  effort: "medium"\nworkflow:\n  - "Development: 구현"\n  - "Quality: 최종 판정"\nscope:\n'
             '  - Departments/Development/Implementation/assets/src/app901.py\n---\n\n# REQ-901: 시험 안건\n'),
        "Departments/Development/Implementation/results/DEV-901_v01.md":
            ('---\ntask_id: "901"\ncreated: "2026-10-20"\nauthor:\n  agent: "Development"\n  model: "acc-test"\n'
             '  effort: "medium"\n---\n\n# DEV-901: 개발부 결과서\n\n## 1. 입력 문서\n'
             '- REQ: `Departments/Secretariat/PM/docs/requests/REQ-901_v01.md`\n\n## 2. 변경 파일\n'
             '| 번호 | 경로 | 변경 내용 | 근거 |\n| :---: | :--- | :--- | :--- |\n'
             '| 1 | `Departments/Development/Implementation/assets/src/listed901.py` | 새 파일 | 시험 |\n\n'
             '## 3. 검증 결과\n없음\n\n## 4. 적용본 (거버넌스 파일을 바꾼 경우만)\n'
             '| 적용본 경로 | 원본 경로 | 반영 명령 |\n| :--- | :--- | :--- |\n'
             f'| `{applied}` | `Workflow/04_모델_운용.md` | `{cp}` |\n\n## 5. 확인하지 못한 항목\n없음\n\n'
             '## 8. 삭제 대상\n| 번호 | 경로 | 추적 여부 |\n| :---: | :--- | :--- |\n'
             f'| 1 | `{ws}/REQ-901_dev_20261020a.py` | 미추적 |\n'),
        "Departments/Quality/Review/results/RES-901_v01.md":
            res_fixture("901").replace("## 7. 삭제 대상 (최종 판정만)\n없음\n",
                                       "## 7. 삭제 대상 (최종 판정만)\n| 번호 | 경로 | 추적 여부 | 근거 |\n"
                                       "| :---: | :--- | :--- | :--- |\n"
                                       f"| 1 | `{ws}/REQ-901_tmp_20261020a.py` | 미추적 | 시험 |\n"),
        "Departments/Secretariat/Secretary/assets/inbox/승인기록_20261020_REQ-901_v01.md":
            approval_fixture("REQ-901_v01", "Departments/Secretariat/PM/docs/requests/REQ-901_v01.md"),
        "Departments/Secretariat/Secretary/assets/inbox/승인기록_20261020_RES-901_v01.md":
            approval_fixture("RES-901_v01", "Departments/Quality/Review/results/RES-901_v01.md"),
        "Departments/Secretariat/Secretary/assets/inbox/ORD-901_v01.md":
            ('---\norder_id: "901"\ncreated: "2026-10-20"\nceo_checked_at: ""\nclassification_proposal: "Major"\n'
             'related_req:\n  - REQ-901\n---\n\n# ORD-901: 시험 오더\n\n- 담당 세션: acc-test\n- 출처 기획안: 없음\n'
             '- 근거 자료: `Departments/Secretariat/Secretary/assets/research/조사_20261020_시험_v01.md`\n'),
        applied: "# 04 적용본(시험)\n",
        "Departments/Development/Implementation/assets/src/listed901.py": "LISTED = 1\n",
        "Departments/Development/Implementation/assets/src/app901.py": "APP = 1\n",
        "Departments/Secretariat/PM/workspace/실행기록_REQ-901.md": "# 실행 기록\n",
        "Departments/Quality/Test/assets/acceptance/REQ-901_v01/test_req901.py": "def test_x():\n    pass\n",
        "Departments/Secretariat/Secretary/assets/briefings/브리핑_20261020_REQ-901_최종승인_v01.html": "<p>시험</p>\n",
        "Departments/Secretariat/Secretary/assets/research/조사_20261020_시험_v01.md": "# 조사\n",
        "Departments/Secretariat/Secretary/assets/inbox/종결기록_20261020_REQ-901.md": "- 대상 기록: REQ-901\n",
        "Departments/Development/Implementation/assets/src/unrelated902.py": "OTHER = 1\n",
        "Departments/Quality/Review/results/RES-902-REQ_v01.md": res_fixture("902"),
        f"{ws}/REQ-901_tmp_20261020a.py": "TMP = 1\n",
        f"{ws}/REQ-901_dev_20261020a.py": "TMP = 2\n",
    }
    for rel, text in files.items():
        write(root, rel, text)
    expected = {
        "Departments/Secretariat/PM/docs/requests/REQ-901_v01.md": "①",
        "Departments/Development/Implementation/results/DEV-901_v01.md": "①",
        "Departments/Quality/Review/results/RES-901_v01.md": "①",
        "Departments/Secretariat/Secretary/assets/inbox/승인기록_20261020_REQ-901_v01.md": "②",
        "Departments/Secretariat/Secretary/assets/inbox/승인기록_20261020_RES-901_v01.md": "②",
        "Departments/Secretariat/Secretary/assets/inbox/ORD-901_v01.md": "③",
        applied: "④",
        "Departments/Development/Implementation/assets/src/listed901.py": "⑤",
        "Departments/Development/Implementation/assets/src/app901.py": "⑥",
        "Departments/Secretariat/PM/workspace/실행기록_REQ-901.md": "⑦",
        "Departments/Quality/Test/assets/acceptance/REQ-901_v01/test_req901.py": "⑧",
        "Departments/Secretariat/Secretary/assets/briefings/브리핑_20261020_REQ-901_최종승인_v01.html": "⑨",
        "Departments/Secretariat/Secretary/assets/research/조사_20261020_시험_v01.md": "⑩",
        "Departments/Secretariat/Secretary/assets/inbox/종결기록_20261020_REQ-901.md": "⑪",
    }
    unclassified = ["Departments/Development/Implementation/assets/src/unrelated902.py",
                    "Departments/Quality/Review/results/RES-902-REQ_v01.md"]
    deletions = [f"{ws}/REQ-901_tmp_20261020a.py", f"{ws}/REQ-901_dev_20261020a.py"]
    return {"cp": cp, "applied": applied, "expected": expected, "unclassified": unclassified,
            "deletions": deletions, "res": "Departments/Quality/Review/results/RES-901_v01.md"}


def _prepare(root, res):
    return run([sys.executable, SCRIPTS_NEW + "/prepare_final_commit.py", res], root)


def test_c20_3_prepare_final_commit(clone):
    sc = _scenario_901(clone)
    code1, out1 = _prepare(clone, sc["res"])
    assert code1 == 0, f"반영 전 실행 실패(종료 코드 {code1}):\n{tail(out1, 30)}"
    assert sc["cp"] in out1 or (sc["applied"] in out1 and "Workflow/04_모델_운용.md" in out1), \
        f"반영 목록에 DEV-901 4절 행이 없습니다:\n{tail(out1, 40)}"
    for rel in sc["deletions"]:
        assert rel in out1, f"삭제 목록에 {rel}가 없습니다:\n{tail(out1, 40)}"
        (clone / rel).unlink()
    code2, out2 = _prepare(clone, sc["res"])
    assert code2 == 0, f"스테이징 전 재실행 실패(종료 코드 {code2}):\n{tail(out2, 30)}"
    lines = out2.splitlines()
    wrong = [f"{rel} ({mark})" for rel, mark in sc["expected"].items()
             if not any(rel in ln and mark in ln for ln in lines)]
    assert not wrong, f"분류 번호가 붙은 스테이징 목록 줄이 없는 경로: {wrong}\n{tail(out2, 60)}"
    start = next((i for i, ln in enumerate(lines) if "분류하지 못한" in ln), None)
    assert start is not None, f"「분류하지 못한 변경」 출력이 없습니다:\n{tail(out2, 60)}"
    for rel in sc["unclassified"]:
        assert any(rel in ln for ln in lines[start:]), f"분류하지 못한 변경에 {rel}가 없습니다:\n{tail(out2, 60)}"
    stripped = [ln.strip() for ln in lines]
    must = ["feat: [REQ-901] 시험 안건",
            "Approved-REQ: Departments/Secretariat/PM/docs/requests/REQ-901_v01.md",
            "Approved-RES: Departments/Quality/Review/results/RES-901_v01.md",
            "Approval-Record: Departments/Secretariat/Secretary/assets/inbox/승인기록_20261020_RES-901_v01.md"]
    absent = [m for m in must if m not in stripped]
    assert not absent, f"커밋 메시지 줄이 없습니다: {absent}\n{tail(out2, 30)}"
    assert not any(s.startswith(("Follows:", "Style-Check-RES:")) for s in stripped), "필요 없는 근거 줄이 있습니다"
    write(clone, sc["res"], res_fixture("901", result="fail"))
    code3, out3 = _prepare(clone, sc["res"])
    assert code3 == 1 and "[FAIL]" in out3, f"result가 pass가 아닌 판정서로 실패하지 않았습니다(종료 코드 {code3}):\n{tail(out3, 20)}"


def test_c20_3_rule_text(pytestconfig):
    s11 = section(gov(pytestconfig, "Workflow/05_인수인계_및_실행명령.md"), "1.1")
    must_contain(item(s11, 4), ["`prepare_final_commit.py`", "멈춰"], "05 1.1절 4번")
    must_contain(item(s11, 6), ["`prepare_final_commit.py`", "그대로 쓰고", "분류하지 못한 변경", "멈춰"], "05 1.1절 6번")
    must_contain(item(s11, 8), ["`prepare_final_commit.py`"], "05 1.1절 8번")


# ---------------------------------------------------------------- 겹침·착수 판단(시험 저장소)

def _req(num, approved, scope, version="01", created="2026-10-19", created_at=None):
    lines = ["---", f'task_id: "{num}"', f'created: "{created}"']
    if created_at:
        lines.append(f'created_at: "{created_at}"')
    lines += [f'approved: "{approved}"', "author:", '  agent: "PM"', "scope:"] + [f"  - {s}" for s in scope]
    lines += ["---", "", f"# REQ-{num}: 시험 {num}", ""]
    return f"Departments/Secretariat/PM/docs/requests/REQ-{num}_v{version}.md", "\n".join(lines)


APPROVED = "2026-10-19T10:00:00+09:00"
INBOX = "Departments/Secretariat/Secretary/assets/inbox"


def _ov_repo(tmp_path, scripts, reqs=(), closed=(), staged_closed=(), files=(), commits=()):
    root = tmp_path / "ov"
    root.mkdir()
    git_ok(root, "init", "-q")
    shutil.copytree(scripts, root / SCRIPTS_NEW)
    write(root, f"{INBOX}/.gitkeep", "")
    for rel, text in reqs:
        write(root, rel, text)
    for num in closed:
        write(root, f"{INBOX}/종결기록_20261018_REQ-{num}.md", f"- 대상 기록: REQ-{num}\n")
    early = {"GIT_AUTHOR_DATE": "2026-10-18T09:00:00+09:00", "GIT_COMMITTER_DATE": "2026-10-18T09:00:00+09:00"}
    git_ok(root, "add", "-A")
    git_ok(root, "commit", "-q", "--no-verify", "-m", "chore: [CEO] 시험 저장소 초기화", env=_env(early))
    for date, subject, rel in commits:
        write(root, rel, f"{subject}\n")
        git_ok(root, "add", "--", rel)
        git_ok(root, "commit", "-q", "--no-verify", "-m", subject,
               env=_env({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}))
    for num in staged_closed:
        rel = f"{INBOX}/종결기록_20261020_REQ-{num}.md"
        write(root, rel, f"- 대상 기록: REQ-{num}\n")
        git_ok(root, "add", "--", rel)
    for rel in files:
        write(root, rel, "산출물\n")
    return root


REQ_SAVE_CASES = [
    ("진행 중 0건", {}, ["Workflow"], 0, None),
    ("1건 겹침(폴더 항목 안의 파일)", {"reqs": [_req("901", APPROVED, ["Workflow"])]}, ["Workflow/02_x.md"], 1, "REQ-901"),
    ("1건 겹침(반대 방향)", {"reqs": [_req("901", APPROVED, ["Workflow/02_x.md"])]}, ["Workflow"], 1, "REQ-901"),
    ("1건 겹침 없음", {"reqs": [_req("901", APPROVED, ["Lab/a"])]}, ["Workflow"], 0, None),
    ("여러 건(겹침·비겹침·끝남·미승인)",
     {"reqs": [_req("901", APPROVED, ["Lab/a"]), _req("902", APPROVED, ["Departments/Design/Spec/docs"]),
               _req("903", APPROVED, ["Departments/Design/Spec/docs"]), _req("904", "", ["Departments/Design/Spec/docs"])],
      "closed": ["903"]}, ["Departments/Design/Spec/docs/prd"], 1, "REQ-902"),
    ("여러 건 모두 끝남·미승인",
     {"reqs": [_req("903", APPROVED, ["Workflow"]), _req("904", "", ["Workflow"])], "closed": ["903"]}, ["Workflow"], 0, None),
    ("승인된 이전 버전의 scope",
     {"reqs": [_req("905", APPROVED, ["Workflow"], "01"), _req("905", "", ["Lab/x"], "02")]}, ["Workflow/01.md"], 1, "REQ-905"),
    ("서식 특례", {"reqs": [_req("906", APPROVED, ["Workflow/templates"])]}, ["Lab/zzz"], 1, "REQ-906"),
    ("03 특례", {"reqs": [_req("907", APPROVED, ["Workflow/03_라이프사이클.md"])]}, ["Lab/zzz"], 1, "REQ-907"),
    ("스테이징만 한 종결 기록", {"reqs": [_req("903", APPROVED, ["Workflow"])], "staged_closed": ["903"]}, ["Workflow"], 1, "REQ-903"),
    ("자기 번호 제외", {"reqs": [_req("950", APPROVED, ["Workflow"])]}, ["Workflow"], 0, None),
    ("scope 여러 항목", {"reqs": [_req("901", APPROVED, ["Workflow/02_x.md"])]}, ["Lab/a", "Workflow/02_x.md"], 1, "REQ-901"),
]


@pytest.mark.parametrize("name,setup,scopes,expect,mention", REQ_SAVE_CASES, ids=[c[0] for c in REQ_SAVE_CASES])
def test_c20_4_req_save(pytestconfig, tmp_path, name, setup, scopes, expect, mention):
    root = _ov_repo(tmp_path, dev_scripts_dir(pytestconfig), **setup)
    args = ["req-save", "--number", "REQ-950"]
    for s in scopes:
        args += ["--scope", s]
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_overlap.py", *args], root)
    assert code == expect, f"[{name}] 종료 코드 {code}, 기대 {expect}:\n{tail(out, 20)}"
    if mention:
        assert mention in out, f"[{name}] 겹친 안건 {mention}가 출력에 없습니다:\n{tail(out, 20)}"


TARGET = _req("950", APPROVED, ["Workflow/02_x.md"], created="2026-10-20", created_at="2026-10-20T10:00:00+09:00")
TARGET_NO_AT = _req("950", APPROVED, ["Workflow/02_x.md"], created="2026-10-20")
AFTER, BEFORE, EARLY_DAY = "2026-10-20T11:00:00+09:00", "2026-10-20T09:00:00+09:00", "2026-10-20T01:00:00+09:00"

ONESTOP_CASES = [
    ("다른 안건·대상 커밋 없음", {"reqs": [TARGET]}, 0, None),
    ("실행 중인 다른 안건(EC 산출물)", {"reqs": [TARGET, _req("901", APPROVED, ["Lab/a"])],
                                   "files": ["Departments/Design/EC/docs/EC-901_v01.md"]}, 1, "REQ-901"),
    ("실행 중인 다른 안건(DEV 산출물)", {"reqs": [TARGET, _req("901", APPROVED, ["Lab/a"])],
                                    "files": ["Departments/Development/Implementation/results/DEV-901_v01.md"]}, 1, "REQ-901"),
    ("REQ 판정서만 있는 다른 안건", {"reqs": [TARGET, _req("901", APPROVED, ["Lab/a"])],
                                 "files": ["Departments/Quality/Review/results/RES-901-REQ_v01.md"]}, 0, None),
    ("끝난 안건의 커밋(작성 시각 뒤, scope 경로)", {"reqs": [TARGET, _req("902", APPROVED, ["Workflow"])], "closed": ["902"],
                                            "commits": [(AFTER, "feat: [REQ-902] 시험 변경", "Workflow/02_x.md")]}, 1, "REQ-902"),
    ("끝난 안건의 커밋(작성 시각 앞)", {"reqs": [TARGET, _req("902", APPROVED, ["Workflow"])], "closed": ["902"],
                                  "commits": [(BEFORE, "feat: [REQ-902] 시험 변경", "Workflow/02_x.md")]}, 0, None),
    ("끝난 안건의 커밋(작성 시각 뒤, 다른 경로)", {"reqs": [TARGET, _req("902", APPROVED, ["Workflow"])], "closed": ["902"],
                                          "commits": [(AFTER, "feat: [REQ-902] 시험 변경", "Workflow/05_y.md")]}, 0, None),
    ("끝난 안건의 커밋(03 특례 경로)", {"reqs": [TARGET, _req("902", APPROVED, ["Workflow"])], "closed": ["902"],
                                  "commits": [(AFTER, "feat: [REQ-902] 시험 변경", "Workflow/03_라이프사이클.md")]}, 1, "REQ-902"),
    ("created_at 없는 버전(created 0시부터)", {"reqs": [TARGET_NO_AT, _req("902", APPROVED, ["Workflow"])], "closed": ["902"],
                                          "commits": [(EARLY_DAY, "feat: [REQ-902] 시험 변경", "Workflow/02_x.md")]}, 1, "REQ-902"),
    ("끝나지 않은 안건의 커밋", {"reqs": [TARGET, _req("903", APPROVED, ["Workflow"])],
                             "commits": [(AFTER, "feat: [REQ-903] 시험 변경", "Workflow/02_x.md")]}, 0, None),
]


@pytest.mark.parametrize("name,setup,expect,mention", ONESTOP_CASES, ids=[c[0] for c in ONESTOP_CASES])
def test_c20_4_onestop(pytestconfig, tmp_path, name, setup, expect, mention):
    root = _ov_repo(tmp_path, dev_scripts_dir(pytestconfig), **setup)
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_overlap.py", "onestop", TARGET[0]], root)
    assert code == expect, f"[{name}] 종료 코드 {code}, 기대 {expect}:\n{tail(out, 20)}"
    if mention:
        assert mention in out, f"[{name}] {mention}가 출력에 없습니다:\n{tail(out, 20)}"


def test_c20_4_onestop_command_failure(pytestconfig, tmp_path):
    root = _ov_repo(tmp_path, dev_scripts_dir(pytestconfig), reqs=[TARGET])
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_overlap.py", "onestop",
                     "Departments/Secretariat/PM/docs/requests/REQ-999_v01.md"], root)
    assert code == 2, f"없는 REQ 경로에서 종료 코드 2가 아닙니다({code}):\n{tail(out, 10)}"


def test_c20_4_criteria_unchanged_and_rule(pytestconfig):
    new03 = gov(pytestconfig, "Workflow/03_라이프사이클.md")
    old03 = base_text("Workflow/03_라이프사이클.md")
    changed = []
    for num, nos in (("3.1", (1, 2, 3, 5, 6, 7, 8, 9)), ("4.1", (1, 3, 4, 5, 6, 7, 8))):
        for n in nos:
            before, after = item(section(old03, num), n), item(section(new03, num), n)
            if not before or before != after:
                changed.append(f"{num}절 {n}항")
    assert not changed, f"판단 기준 문장이 바뀌었습니다: {changed}"
    must_contain(item(section(new03, "3.1"), 10), ["`check_overlap.py req-save`", "종료 코드가 2", "멈춘다"], "03 3.1절 10항")
    must_contain(item(section(new03, "4.1"), 9), ["`check_overlap.py onestop`", "종료 코드가 2", "멈춘다"], "03 4.1절 9항")
    must_contain(item(section(new03, "7"), 13), ["겹침·착수 판단 명령"], "03 7절 13항")


# ---------------------------------------------------------------- 정리(하위 요구 ⑤)

def _settings(config):
    p = applied_path(config, ".claude/settings.json")
    return json.loads(p.read_text(encoding="utf-8"))["permissions"]


def test_c20_5_settings_not_narrowed(pytestconfig):
    """체크리스트 20 ⑤(막는 범위를 좁히지 않음), 20 ⑦(ask 불변), 18 ⑦(권한 규칙의 새 범위)."""
    old = json.loads(base_text(".claude/settings.json"))["permissions"]
    new = _settings(pytestconfig)

    def moved(rule):
        rule = rule.replace(SCRIPTS_OLD + "/", SCRIPTS_NEW + "/")
        return "Bash(python Departments/*/*/workspace/*)" if rule == "Bash(python Departments/*/workspace/*)" else rule

    expected_allow = {moved(r) for r in old["allow"]} | set(NEW_ALLOW_RULES)
    assert set(new["allow"]) == expected_allow, (
        f"allow 차이 - 빠짐: {sorted(expected_allow - set(new['allow']))}, 더함: {sorted(set(new['allow']) - expected_allow)}")
    expected_deny = {moved(r) for r in old["deny"]}
    assert set(new["deny"]) == expected_deny, (
        f"deny 차이 - 빠짐: {sorted(expected_deny - set(new['deny']))}, 더함: {sorted(set(new['deny']) - expected_deny)}")
    assert new["ask"] == old["ask"], "ask 규칙이 바뀌었습니다(커밋·푸시·삭제·이동 규칙은 그대로여야 함)"


def test_c20_5_no_v04_and_first_commit_message(pytestconfig):
    files = {rel: applied_path(pytestconfig, rel) for rel in
             (SCRIPTS_NEW + "/check_standard.py", ".githooks/pre-commit", ".githooks/commit-msg", "setup.cmd")}
    absent = [rel for rel, p in files.items() if p is None]
    assert not absent, f"현행 파일이 없습니다: {absent}"
    # 「v04」 표기는 표준 버전 표기(「표준 v04」)다. check_standard.py 주석의 기록 이름 `ORD-005_v04`는
    # 이미 작성된 기록의 이름이므로 남는다(EC-032_v04 G12 ③, 5절 15행).
    hits = [f"{rel}:{no}" for rel, p in files.items()
            for no, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if re.search(r"표준 v04", ln)]
    assert not hits, f"「v04」 표기(표준 v04)가 남아 있습니다: {hits}"
    setup = files["setup.cmd"].read_text(encoding="utf-8")
    m = re.search(r'git commit -m "([^"]+)"', setup)
    assert m, "setup.cmd에서 첫 커밋 메시지를 찾지 못했습니다"
    s2 = section(gov(pytestconfig, "Workflow/07_문서_서식_및_번호.md"), "2")
    m07 = re.search(r"`setup\.cmd`가 만드는 첫 커밋\(`([^`]+)`\)", s2)
    assert m07, "07 2절에서 첫 커밋 예외 문구를 찾지 못했습니다"
    assert m.group(1) == m07.group(1), f"setup.cmd 「{m.group(1)}」와 07 2절 「{m07.group(1)}」가 다릅니다"


def test_c20_5_duplicate_check_removed(pytestconfig):
    t05 = gov(pytestconfig, "Workflow/05_인수인계_및_실행명령.md")
    i7 = item(section(t05, "1.1"), 7)
    must_contain(i7, ["따로 실행하지 않는다", "훅"], "05 1.1절 7번")
    s83 = section(t05, "8.3")
    assert "커밋 전 검사는 따로 실행하지 않는다" in s83, "05 8.3절 「요청 커밋」 5)가 커밋 전 검사를 따로 실행하지 않는다고 적지 않았습니다"
    # 「요청 커밋」 예외 (나)(마)(바)가 없앤 5)의 검사를 가리키지 않는다(EC-032_v04 3.8절 6번 ④)
    left = [w for w in ("5)를 실행하지 않고", "5)의 실패", "5)의 검사") if w in s83]
    assert not left, f"05 8.3절에 없앤 커밋 직전 검사(5))를 가리키는 문구가 남아 있습니다: {left}"
    assert not re.search(r"`python [^`]*check_standard\.py --staged`", i7), "05 1.1절 7번에 커밋 직전 실행 명령이 남아 있습니다"


def test_c20_5_eol_rule_and_hash(pytestconfig, committed):
    p = applied_path(pytestconfig, ".gitattributes")
    rules = [ln.strip() for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.startswith("#")]
    assert rules and rules[0] == "* text=auto eol=lf", f".gitattributes 첫 규칙이 `* text=auto eol=lf`가 아닙니다: {rules[:1]}"
    assert "* text=auto eol=lf" in section(gov(pytestconfig, "Workflow/06_통제장치_및_배포.md"), "4.5"), "06 4.5절에 줄바꿈 규칙 서술이 없습니다"
    root = committed["root"]
    recorded = {}
    for acc in git_z(REPO, "ls-files", "-z", "--", "Departments/Quality/results"):
        if re.search(r"/ACC-\d{3}_v\d{2}\.md$", acc):
            for path, digest in re.findall(r"^\| `(Departments/Quality/assets/acceptance/[^`]+)` \| `([0-9a-f]{40})` \|",
                                           (REPO / acc).read_text(encoding="utf-8"), re.M):
                recorded[path] = digest
    assert recorded, "커밋된 ACC에서 시험 파일 해시를 찾지 못했습니다"
    wrong = []
    for old_path, digest in sorted(recorded.items()):
        new_path = expected_new_path(old_path)
        for autocrlf in ("true", "false"):
            code, out = git(root, "-c", f"core.autocrlf={autocrlf}", "diff", "--no-index", "--full-index",
                            "/dev/null", new_path)
            m = re.search(r"^index [0-9a-f]+\.\.([0-9a-f]{40})", out, re.M)
            if not m or m.group(1) != digest:
                wrong.append(f"{new_path} (core.autocrlf={autocrlf}): {m.group(1) if m else '해시 없음'} ≠ {digest}")
    assert not wrong, "반영 뒤 상태에서 인수 시험 해시 대조가 맞지 않습니다:\n" + "\n".join(wrong[:20])


def test_c20_5_unmeasured_rules_known_issues(pytestconfig):
    s7 = section(gov(pytestconfig, "Workflow/06_통제장치_및_배포.md"), "7")
    must_contain(s7, ["`Write(...)` 규칙 자체의 효력", "`ask` 규칙의 효력", "신뢰 처리 전", "확인 불가"], "06 7절")
    # 이번 원스톱의 실험 결과서는 DEV-032_v04다(EC-032_v04 1절 「실험 결과 인용」)
    exp = _versioned(["Departments/Development/results", "Departments/Development/Implementation/results"],
                     r"DEV-032_v(04)\.md")
    assert exp is not None, "실험 결과서 DEV-032_v04가 없습니다"
    must_contain(section(exp.read_text(encoding="utf-8"), "6"), ["확인 불가", "N1"], "DEV-032_v04 6절")


# ---------------------------------------------------------------- 대장(하위 요구 ⑥)

def test_c20_6_ledger(pytestconfig):
    p = applied_path(pytestconfig, SCRIPTS_NEW + "/검사장치대장.md")
    assert p is not None and p.parent.name.endswith(".적용본"), "개발 적용본에 검사장치대장.md가 없습니다"
    text = p.read_text(encoding="utf-8")
    header = next((ln for ln in text.splitlines() if ln.startswith("|") and "규정 원천 절" in ln), None)
    assert header, "대장 표 머리에 「규정 원천 절」 열이 없습니다"
    cols = [c.strip() for c in header.strip("|").split("|")]
    src_col = cols.index("규정 원천 절")
    rows = {}
    for ln in text.splitlines():
        if ln.startswith("|") and not re.match(r"^\|\s*:?-", ln) and ln != header:
            cells = [c.strip() for c in ln.strip("|").split("|")]
            rows[cells[0].strip("`* ")] = cells
    need = [f"M{i}" for i in range(1, 12)] + [f"F{i}" for i in range(1, 5)]
    missing = [k for k in need if k not in rows]
    p_rows = [k for k in rows if re.fullmatch(r"P\d(~P\d)?", k)]
    if not ("P1~P9" in rows or all(f"P{i}" in rows for i in range(1, 10))):
        missing.append("P1~P9")
    assert not missing, f"대장에 없는 행: {missing}"
    empty = [k for k in need + p_rows if k in rows and (len(rows[k]) <= src_col or not rows[k][src_col])]
    assert not empty, f"규정 원천 절이 빈 행: {empty}"
    assert "M3b" in text, "없앤 장치 M3b의 기재가 없습니다"
    s44 = section(gov(pytestconfig, "Workflow/06_통제장치_및_배포.md"), "4.4")
    must_contain(s44, ["검사장치대장.md", "중복", "대장을 고친다"], "06 4.4절")


# ---------------------------------------------------------------- 새 명령의 성질(하위 요구 ⑦)

FORBIDDEN_GIT = {"commit", "push", "rm", "mv", "add", "reset", "checkout", "restore", "stash", "update-index",
                 "update-ref", "tag", "merge", "rebase", "clean", "apply", "am", "cherry-pick", "revert", "init",
                 "clone", "fetch", "pull"}
FORBIDDEN_ATTRS = {"unlink", "write_text", "write_bytes", "rmdir", "touch", "rename", "symlink_to", "hardlink_to"}
FORBIDDEN_MODULE_CALLS = {"os": {"remove", "unlink", "rmdir", "removedirs", "rename", "renames", "replace", "system",
                                 "popen", "truncate"},
                          "shutil": {"move", "rmtree", "copy", "copy2", "copyfile", "copytree", "copyfileobj"}}


def _git_violation(tokens):
    if not tokens or tokens[0] != "git":
        return None
    i = 1
    while i < len(tokens) and tokens[i].startswith("-"):
        i += 2 if tokens[i] in ("-c", "-C") else 1
    if i >= len(tokens):
        return None
    sub = tokens[i]
    if sub in FORBIDDEN_GIT:
        return f"git {sub}"
    if sub == "config" and not ({"--get", "--get-all", "--get-regexp", "--list", "-l"} & set(tokens[i:])):
        return "git config(설정 변경)"
    return None


def _violations(source):
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Attribute):
            if isinstance(f.value, ast.Name) and f.attr in FORBIDDEN_MODULE_CALLS.get(f.value.id, ()):
                found.append(f"{f.value.id}.{f.attr} (줄 {node.lineno})")
            elif f.attr in FORBIDDEN_ATTRS:
                found.append(f".{f.attr}() (줄 {node.lineno})")
        is_open = (isinstance(f, ast.Name) and f.id == "open") or (isinstance(f, ast.Attribute) and f.attr == "open")
        if is_open:
            mode = node.args[1] if len(node.args) > 1 else next((k.value for k in node.keywords if k.arg == "mode"), None)
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str) and set(mode.value) & set("wax+"):
                found.append(f"open(..., {mode.value!r}) (줄 {node.lineno})")
        if node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
            tokens = [e.value for e in node.args[0].elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            v = _git_violation(tokens)
            if v:
                found.append(f"{v} (줄 {node.lineno})")
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            v = _git_violation(node.args[0].value.split())
            if v:
                found.append(f"{v} (줄 {node.lineno})")
    return found


def test_c20_7_new_commands_static(pytestconfig):
    d = dev_scripts_dir(pytestconfig)
    problems = []
    for name in NEW_COMMANDS:
        p = d / name
        if not p.is_file():
            problems.append(f"{name}: 없음")
            continue
        src = p.read_text(encoding="utf-8")
        doc = ast.get_docstring(ast.parse(src)) or ""
        if "Workflow/" not in doc:
            problems.append(f"{name}: 첫머리 설명에 규칙의 원천(Workflow 절)이 없음")
        problems += [f"{name}: {v}" for v in _violations(src)]
    assert not problems, "\n".join(problems)


def _repo_state(root):
    files = git_z(root, "ls-files", "-co", "--exclude-standard", "-z")
    return (git_ok(root, "rev-parse", "HEAD").strip(), git_z(root, "status", "--porcelain", "-uall", "-z"),
            git_z(root, "ls-files", "-s", "-z"), {f: sha256(root / f) for f in files if (root / f).is_file()},
            git(root, "config", "--list", "--local")[1])


def test_c20_7_new_commands_do_not_change_repo(clone, tmp_path):
    sc = _scenario_901(clone)
    git_ok(clone, "add", "--", "Departments/Quality/Review/results/RES-901_v01.md")
    home, _ = _home(tmp_path, clone, "true")
    msg = tmp_path / "m.txt"
    msg.write_text("docs: [CEO] 시험\n", encoding="utf-8")
    before = _repo_state(clone)
    py = sys.executable
    runs = [
        [py, SCRIPTS_NEW + "/check_env.py"], [py, SCRIPTS_NEW + "/check_env.py", "--setup"],
        [py, SCRIPTS_NEW + "/prepare_final_commit.py", sc["res"]],
        [py, SCRIPTS_NEW + "/check_overlap.py", "req-save", "--number", "REQ-950", "--scope", "Workflow"],
        [py, SCRIPTS_NEW + "/check_overlap.py", "onestop", "Departments/Secretariat/PM/docs/requests/REQ-901_v01.md"],
        [py, SCRIPTS_NEW + "/check_commit_msg.py", str(msg)],
        [py, SCRIPTS_NEW + "/check_standard.py", "--staged"],
    ]
    for args in runs:
        run(args, clone, env=_env({"HOME": str(home), "USERPROFILE": str(home)}))
    after = _repo_state(clone)
    labels = ("HEAD", "git status", "index", "작업 트리 파일 해시", "로컬 Git 설정")
    diff = [lab for lab, b, a in zip(labels, before, after) if b != a]
    assert not diff, f"새 명령 실행 뒤 바뀐 것: {diff}"


# ---------------------------------------------------------------- allow 완화(D15)

def test_c20_9_allow_rule_and_wrapper_rule(pytestconfig):
    assert "Bash(python Departments/*/*/workspace/*)" in _settings(pytestconfig)["allow"], \
        "allow에 Bash(python Departments/*/*/workspace/*)가 없습니다"
    s21 = section(gov(pytestconfig, "Workflow/06_통제장치_및_배포.md"), "2.1")
    line = next((ln for ln in s21.splitlines() if "`ask` 대상인 명령" in ln), "")
    must_contain(line, ["`allow` 밖", "실행하지 않는다", "tmp_path", "결함"], "06 2.1절 스크립트 감싸기 금지 항목")


# ---------------------------------------------------------------- 이 REQ 자신의 커밋(D13·D14)

def test_c20_10_reflection_commit_passes_new_hooks(committed):
    assert committed["head_after"] != committed["head_before"], "반영 커밋이 만들어지지 않았습니다"
    subject = git_ok(committed["root"], "log", "-1", "--format=%s").strip()
    assert subject == committed["msg"].splitlines()[0], f"커밋 제목 줄이 결과서 메시지와 다릅니다: {subject}"
    out = committed["commit_out"]
    for word in RESIDUAL_EXCLUDED_TOP:
        assert word in out, f"반영 커밋 때 새 pre-commit(옛 경로 잔존 검사)의 뺀 범위 출력에 {word}가 없습니다:\n{tail(out, 30)}"


def test_c20_10_req032_ended_after_commit(clone):
    """반영 커밋 다음 커밋에서 REQ-032가 끝난 안건으로 판단된다(D14). setup.cmd는 승인되었고 끝나지 않은
    다른 REQ의 scope에 없으므로(승인된 REQ-033_v02의 scope에 없고, REQ-034는 v01~v04 모두 미승인. 2026-10-18
    머리말 조회), REQ-032가 끝났으면 통과 근거가 없다."""
    target = "setup.cmd"
    original = (clone / target).read_bytes()
    (clone / target).write_bytes(original + b"rem acc-test\r\n")
    git_ok(clone, "add", "--", target)
    code, out = run([sys.executable, SCRIPTS_NEW + "/check_standard.py", "--staged"], clone)
    git_ok(clone, "reset", "-q", "--", target)
    (clone / target).write_bytes(original)
    assert code != 0 and "REQ-032" in out, \
        f"다음 커밋에서 REQ-032가 끝난 안건으로 판단되지 않았습니다(종료 코드 {code}):\n{tail(out, 20)}"
