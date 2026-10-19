#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_config.py - 형상통제 대조(옛 경로 잔존, 생성물 대조, 안전장치 핵심 무결성, 파트 대조, 이관 검사, 분량)

명령과 검사 C1~C6의 동작은 Workflow/06_통제장치_및_배포 「형상통제 대조」가 원천이다. 계층과 생성물의 규칙은
Workflow/04_모델_운용 「계층형 지침」, 전수 대응표의 형식·단위는 Workflow/05_인수인계_및_실행명령 「형상통제 절차」 3항,
옛 경로의 대응은 Workflow/02_부서_구조_및_작업구역 「옛 이름과 새 이름의 대응」이 원천이며, 이 스크립트는 그 구현이다.

사용법: python check_config.py [--overlay <폴더>]… [--owner <기록 이름>]… [--global-source <파일>] [--units | --placement <코드>]
  옵션 없음: C1~C6을 모든 행에 대해 실행한다(C01의 전환 전 전체 확인).
  --owner: C5를 그 기록 이름이 담당인 행만 본다. --global-source: C2~C6과 함께 안전장치 핵심을 그 파일과 대조한다(C1 생략).
  --units: 기준본 대상 문서의 단위 목록만 출력한다. --placement: 전수 대응표에서 그 파트의 사슬에 실리는 행만 출력한다.
종료 코드: 0 오류 없음, 1 오류 있음, 2 사용법 오류·읽기 실패
커밋 전 검사 순서 5(check_standard.py)는 run_commit_check()를 부른다. 읽기만 하고 파일을 쓰지 않는다.
"""

import json
import re
import subprocess
import sys

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import build_guides as bg  # noqa: E402  (생성물을 같은 함수로 다시 만들어 대조한다. 06 「형상통제 대조」 C2)
import check_standard as cs  # noqa: E402  (출력 인코딩 고정, index 내용 읽기, 공통 처리)

RULE = "Workflow/06_통제장치_및_배포 「형상통제 대조」"
MAP_REL = "Workflow/data/migration_map.json"
MAP_RULE = "Workflow/05_인수인계_및_실행명령 「형상통제 절차」 3항"
LAYER_RULE = "Workflow/04_모델_운용 「계층형 지침」"
GEN_PREFIX = ".claude/guides/"
CARD_RE = re.compile(r"^\.claude/agents/part-[^/]+\.md$")
DEFAULT_OWNER = "REQ-034"  # 행이 없는 단위의 담당(대응표를 만든 안건. 05 「형상통제 절차」 3항 「owner」)
KINDS = {"규정", "비규정"}
ACTIONS_RULE = {"이관", "개정", "통합", "안전장치 핵심으로 대체", "삭제"}
ACTIONS_NONRULE = {"보관", "정리"}
OWNERS = {"REQ-031", "REQ-032", "REQ-033", "REQ-034", "ORD-012-9", "ORD-012-10"}
STATUSES = {"완료", "개정 예정"}

ACTIONS = {
    "C1": "Workflow/02_부서_구조_및_작업구역 「옛 이름과 새 이름의 대응」대로 새 경로로 고친 뒤 다시 스테이징한다",
    "C2": ("원천을 바꾼 안건의 구현 단계에서 생성 명령으로 다시 만든다(Workflow/06_통제장치_및_배포 「거버넌스 파일 개정 절차」 2항). "
           "전역 지침이 원천이면 형상통제팀(C01)의 지침 재생성 반영(Workflow/05_인수인계_및_실행명령 「형상통제 절차」 1항). "
           "대표님이 REQ 없이 원천 절을 고쳐 어긋났으면 처리는 대표님이 정한다"),
    "C3": "안전장치 핵심은 손으로 고치지 않는다. 형상통제팀(C01)의 지침 재생성 반영으로 다시 만든다",
    "C4": f"계층 구성표와 조직 표·프로세스 맵을 {LAYER_RULE} 3항의 배치 규칙에 맞게 고치고 생성물을 다시 만든다",
    "C5": f"전수 대응표의 그 행을 {MAP_RULE}의 형식대로 고친다(그 행을 맡은 안건의 설계 적용본)",
    "G": "형상통제팀(C01)의 지침 재생성 반영(Workflow/05_인수인계_및_실행명령 「형상통제 절차」 1항)",
}

# ---------------------------------------------------------------- C1 옛 경로 잔존 (REQ-032 D8로 check_standard.py에서 옮김)
# 옛 경로는 부서 폴더 바로 아래에 공통 하위 폴더 이름이 오는 경로다. 패턴을 낱말 목록으로 조립하는 이유는 이 파일 자신이
# 검사 대상(검사 스크립트 폴더)이어서, 옛 경로를 글자 그대로 적으면 이 파일이 패턴에 맞기 때문이다
_OLD_DEPTS = "|".join(("Secretariat", "Design", "Development", "Quality", "Operations", "Marketing"))
_OLD_SUBS = "|".join(("assets", "docs", "results", "workspace"))
OLD_PATH_PATTERNS = (
    re.compile("Departments" + "/(" + _OLD_DEPTS + r"|\*|<부서>)/(" + _OLD_SUBS + r")\b"),
    re.compile(r"(?<![\w/.])(" + _OLD_DEPTS + ")/(" + _OLD_SUBS + r")\b"),
)
RESIDUAL_EXCLUDED_TOP = ("CEO/", "_archive/", "Lab/", "Audits/")
RESIDUAL_RECORD_PREFIXES = (
    "Departments/Secretariat/Secretary/assets/",
    "Departments/Secretariat/PM/docs/",
    "Departments/Design/EC/docs/",
    "Departments/Quality/Nonconformance/docs/",
    "Departments/Quality/Test/assets/acceptance/",
)
# 생성물은 원천이 이미 대상이고, 전수 대응표는 기준본 글자를 기록으로 담으므로 뺀다(REQ-034)
RESIDUAL_GENERATED = (GEN_PREFIX, MAP_REL)
REVISION_HISTORY_HEADING = re.compile(r"^## .*개정 이력\s*$")
MAPPING_DOC_REL = "Workflow/02_부서_구조_및_작업구역.md"
MAPPING_HEADING = re.compile(r"^### 2\.3(?!\d)")
SECTION_HEADING = re.compile(r"^#{1,3} ")


def residual_target(rel):
    if rel.startswith(RESIDUAL_EXCLUDED_TOP) or rel.startswith(RESIDUAL_GENERATED) or CARD_RE.match(rel):
        return False
    parts = rel.split("/")
    # 팀 폴더(Departments/<부>/<팀>/)의 results/·workspace/ 아래 전체는 이미 작성된 기록의 위치다
    if len(parts) >= 5 and parts[0] == "Departments" and parts[3] in ("results", "workspace"):
        return False
    return not rel.startswith(RESIDUAL_RECORD_PREFIXES)


def residual_lines(rel, text):
    """줄 단위로 뺄 범위(Markdown 개정 이력 H2부터 끝, 02의 2.3절)를 뺀 (줄 번호, 줄) 목록."""
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


def check_c1(source):
    """C1. [(위치, 원인)]과 대상 파일 수."""
    targets = [p for p in source.files() if residual_target(p)]
    print("[INFO] C1 옛 경로 잔존: 뺀 범위 - 폴더 전체: " + ", ".join(RESIDUAL_EXCLUDED_TOP)
          + ", 팀 폴더(Departments/<부>/<팀>/)의 results/·workspace/, " + ", ".join(RESIDUAL_RECORD_PREFIXES)
          + ", 생성물(.claude/guides/**, .claude/agents/part-*.md), 전수 대응표(" + MAP_REL + ")"
          + f" / 줄 단위: Markdown 파일의 「개정 이력」 H2 제목부터 끝, {MAPPING_DOC_REL}의 2.3절. 대상 파일 {len(targets)}개.")
    contents = source.read_many(targets)
    errors = []
    for rel in targets:
        data = contents.get(rel)
        if data is None or b"\0" in data:
            continue
        for no, line in residual_lines(rel, data.decode("utf-8", errors="replace")):
            for pattern in OLD_PATH_PATTERNS:
                m = pattern.search(line)
                if m:
                    errors.append((f"{rel}:{no}", f"옛 경로가 남음: {m.group(0)}"))
                    break
    return errors


# ---------------------------------------------------------------- C2·C3·C4

def actual_generated(source):
    return sorted(p for p in source.files() if p.startswith(GEN_PREFIX) or CARD_RE.match(p))


def check_c2(source, gen):
    errors = [("생성", msg) for code, msg in gen.errors if code == "C2"]
    expected = {bg.GEN_ROOT + rel: data for rel, data in gen.files.items()}
    actual = actual_generated(source)
    contents = source.read_many(actual)
    for path, data in sorted(expected.items()):
        have = contents.get(path)
        if have is None:
            errors.append((path, "만들어져야 하는 생성물이 없습니다"))
        elif have != data:
            errors.append((path, "생성물이 원천으로 다시 만든 내용과 다릅니다"))
    for path in actual:
        if path not in expected and path in contents:
            errors.append((path, "구성표가 만들지 않는 남는 생성물입니다"))
    return errors


def check_c3(source, gen):
    errors = [("안전장치 핵심", msg) for code, msg in gen.errors if code == "C3"]
    if gen.safety is None:
        return errors
    if bg.sha256(gen.safety["body"]) != gen.safety["sha"]:
        errors.append((bg.GEN_ROOT + bg.SAFETY_REL, "본문의 SHA-256이 머리 표시의 추출 SHA-256과 다릅니다"))
    cards = [p for p in actual_generated(source) if CARD_RE.match(p)]
    for path, data in sorted(source.read_many(cards).items()):
        if gen.safety["block"] not in data.decode("utf-8", errors="replace").replace("\r\n", "\n"):
            errors.append((path, "파트 카드의 안전장치 핵심 부분이 안전장치 핵심 본문과 다릅니다"))
    return errors


def check_c4(source, gen, docs):
    errors = [("배치", msg) for code, msg in gen.errors if code == "C4"]
    org = bg.org_table(docs)
    files = set(source.files())
    for code, _ in org:
        if f"{GEN_PREFIX}parts/{code}.md" not in files:
            errors.append((code, f"조직 표의 파트 {code}에 파트 지침 생성물({GEN_PREFIX}parts/{code}.md)이 없습니다"))
    gl = json.loads(bg.read_text(source, bg.LAYERS_REL) or "{}")
    cards = sorted(c for c, v in gl.get("parts", {}).items() if v.get("card"))
    subagents = bg.subagent_parts(docs)
    if subagents is None:
        errors.append(("조직 표", f"{bg.ORG_DOC_REL} 「조직 표」 「파트의 일을 맡는 세션」에서 서브에이전트 파트 목록을 찾지 못했습니다"))
    elif cards != sorted(subagents):
        errors.append(("구성표 card", f"card: true 파트 {cards}가 서브에이전트 파트 {sorted(subagents)}와 다릅니다"))
    pm_text = bg.read_text(source, bg.PROCESS_MAP_REL)
    used = set()
    if pm_text:
        for st in json.loads(pm_text).get("steps", []):
            used.update(st.get("parts", []))
    for c in cards:
        if c not in used:
            errors.append((c, f"서브에이전트 파트 {c}가 프로세스 맵 어느 단계의 parts에도 없습니다"))
    return errors


def budget_lines(gen):
    return [f"[INFO] 예산 초과 {layer} {name} {chars}/{limit}" for layer, name, chars, limit in gen.budgets
            if chars > limit]


# ---------------------------------------------------------------- C5 이관 검사와 단위

ITEM0 = re.compile(r"^(- |\* |\+ |\d+\. )")
HEAD = re.compile(r"^#{1,6} ")
SEP = re.compile(r"^\|\s*:?-{3,}")


def split_units(path, text):
    """기준본 문서를 단위로 나눈다(05 「형상통제 절차」 3항 「단위」). (줄 목록, [(시작 줄, 끝 줄)]) 줄 번호는 1부터."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    n = len(lines)
    units = []
    if not path.endswith(".md"):
        i = 0
        while i < n:
            if not lines[i].strip():
                i += 1
                continue
            j = i
            while j + 1 < n and lines[j + 1].strip():
                j += 1
            units.append((i + 1, j + 1))
            i = j + 1
        return lines, units
    i = 0
    if n and lines[0] == "---":
        j = 1
        while j < n and lines[j] != "---":
            j += 1
        cur = None
        for k in range(1, j):
            line = lines[k]
            if line and not line.startswith((" ", "\t", "- ")):
                if cur:
                    units.append(tuple(cur))
                cur = [k + 1, k + 1]
            elif cur is not None:
                cur[1] = k + 1
        if cur:
            units.append(tuple(cur))
        i = j + 1
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            j = i + 1
            while j < n and not lines[j].startswith("```"):
                j += 1
            units.append((i + 1, min(j, n - 1) + 1))
            i = j + 1
            continue
        if HEAD.match(line) or (line.strip() == "---" and not line.startswith(" ")):
            i += 1
            continue
        if line.startswith("|"):
            nxt = lines[i + 1] if i + 1 < n else ""
            if not (SEP.match(line) or SEP.match(nxt)):
                units.append((i + 1, i + 1))
            i += 1
            continue
        if ITEM0.match(line):
            j, last, fence = i + 1, i, False
            while j < n:
                l2 = lines[j]
                if fence:
                    last = j
                    if l2.strip().startswith("```"):
                        fence = False
                    j += 1
                    continue
                if not l2.strip():
                    j += 1
                    continue
                if l2.startswith((" ", "\t")):
                    if l2.strip().startswith("```"):
                        fence = True
                    last = j
                    j += 1
                    continue
                if ITEM0.match(l2) or HEAD.match(l2) or l2.startswith("|") or not lines[j - 1].strip():
                    break
                last = j
                j += 1
            units.append((i + 1, last + 1))
            i = last + 1
            continue
        if line.startswith(">"):
            j = i
            while j + 1 < n and lines[j + 1].startswith(">"):
                j += 1
            units.append((i + 1, j + 1))
            i = j + 1
            continue
        j = i
        while j + 1 < n:
            l2 = lines[j + 1]
            if not l2.strip() or HEAD.match(l2) or l2.startswith(("|", "```", ">")) or ITEM0.match(l2):
                break
            j += 1
        units.append((i + 1, j + 1))
        i = j + 1
    return lines, units


def heading_for(lines, start):
    """단위 앞의 가장 가까운 H2·H3 제목 줄에서 #들과 공백 한 칸을 뗀 글자(코드 울타리 안 제외)."""
    fence, last = False, ""
    for idx in range(0, start - 1):
        line = lines[idx]
        if line.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        m = re.match(r"^(#{2,3}) (.*)$", line)
        if m:
            last = m.group(2)
    return last


def git_show_many(root, base, paths):
    """기준본 커밋의 파일 내용을 {경로: 글자}로 돌려준다(git cat-file --batch 한 번)."""
    names = [f"{base}:{p}" for p in paths]
    res = subprocess.run(["git", "cat-file", "--batch"], cwd=root, capture_output=True,
                         input=("\n".join(names) + "\n").encode("utf-8"))
    if res.returncode != 0:
        raise bg.SourceError(f"기준본을 읽을 수 없습니다: {res.stderr.decode('utf-8', 'replace').strip()}")
    out, pos, found = res.stdout, 0, {}
    for p in paths:
        end = out.index(b"\n", pos)
        header = out[pos:end].decode("utf-8", "replace").split()
        pos = end + 1
        if len(header) != 3 or header[1] != "blob":
            continue
        size = int(header[2])
        found[p] = out[pos:pos + size].decode("utf-8", "replace").replace("\r\n", "\n")
        pos += size + 1
    return found


def baseline_targets(root, base):
    res = subprocess.run(["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", "-z", base, "--",
                          "AGENTS.md", "CLAUDE.md", "Workflow", ".claude/agents"], cwd=root, capture_output=True)
    if res.returncode != 0:
        raise bg.SourceError(f"기준본 트리를 읽을 수 없습니다({base}): {res.stderr.decode('utf-8', 'replace').strip()}")
    tree = [p for p in res.stdout.decode("utf-8", "replace").split("\0") if p]
    return sorted(p for p in tree if p in ("AGENTS.md", "CLAUDE.md") or p.startswith(("Workflow/templates/", ".claude/agents/"))
                  or re.fullmatch(r"Workflow/0[1-7]_[^/]+\.md", p))


def load_map(source):
    text = bg.read_text(source, MAP_REL)
    if text is None:
        raise bg.SourceError(f"전수 대응표가 없습니다: {MAP_REL}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise bg.SourceError(f"전수 대응표가 JSON으로 읽히지 않습니다: {MAP_REL} ({e.msg}, {e.lineno}행)")


def all_units(root, mm):
    texts = git_show_many(root, mm["baseline_commit"], mm.get("targets", []))
    out = []
    for path in mm.get("targets", []):
        if path not in texts:
            continue
        lines, units = split_units(path, texts[path])
        for s, _ in units:
            out.append((f"{path}:{s}", heading_for(lines, s), lines[s - 1][:40]))
    return out, texts


def layer_selectors(gl):
    layers = {"표준 공통": gl.get("standard", [])}
    for kind, key in (("부", "depts"), ("팀", "teams"), ("파트", "parts")):
        for name, ent in gl.get(key, {}).items():
            layers[f"{kind}:{name}"] = ent.get("select", [])
    return layers


def check_c5(root, source, docs, gen):
    """C5. [(담당, 위치, 원인)]."""
    mm = load_map(source)
    gl = json.loads(bg.read_text(source, bg.LAYERS_REL) or "{}")
    viol = []
    base = mm.get("baseline_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", str(base)):
        return [(DEFAULT_OWNER, "baseline_commit", f"기준본 커밋 해시 형식이 아닙니다: {base!r}")]
    expected = baseline_targets(root, base)
    if sorted(mm.get("targets", [])) != expected:
        diff = sorted(set(expected) ^ set(mm.get("targets", [])))
        viol.append((DEFAULT_OWNER, "targets", f"① targets가 기준본 트리의 대상 문서와 다릅니다: {diff}"))
    rows = mm.get("rows", [])
    by_base = {}
    for r in rows:
        by_base.setdefault(str(r.get("id", "")).split("#", 1)[0], []).append(r)
    units, texts = all_units(root, mm)
    unit_ids = set()
    for uid, heading, excerpt in units:
        unit_ids.add(uid)
        rs = by_base.get(uid)
        if not rs:
            viol.append((DEFAULT_OWNER, uid, "① 기준본 단위에 대응하는 행이 없습니다"))
            continue
        if len(rs) > 1 and not all("#" in str(r.get("id")) for r in rs):
            viol.append((rs[0].get("owner"), uid, "① 같은 단위에 나누지 않은 행이 둘 이상입니다"))
        for r in rs:
            if r.get("heading") != heading or r.get("excerpt") != excerpt:
                viol.append((r.get("owner"), r.get("id"), "① heading·excerpt가 기준본과 다릅니다"))
    for b, rs in by_base.items():
        if b not in unit_ids:
            for r in rs:
                viol.append((r.get("owner"), r.get("id"), "① 기준본에 없는 id입니다"))
    layers = layer_selectors(gl)
    cover_cache = {}

    def sel_cover(sel):
        key = json.dumps(sel, ensure_ascii=False, sort_keys=True)
        if key not in cover_cache:
            cover_cache[key] = bg.cover(docs, sel)[0]
        return cover_cache[key]

    safety_body = gen.safety["body"] if gen.safety else ""
    for r in rows:
        rid, owner = r.get("id"), r.get("owner")
        kind, action, loaded = r.get("kind"), r.get("action"), r.get("loaded_in")
        # ②
        if kind not in KINDS:
            viol.append((owner, rid, f"② kind 값이 허용 값이 아닙니다: {kind!r}"))
        elif action not in (ACTIONS_RULE if kind == "규정" else ACTIONS_NONRULE):
            viol.append((owner, rid, f"② {kind} 행의 action 값이 허용 값이 아닙니다: {action!r}"))
        if owner not in OWNERS or r.get("status") not in STATUSES:
            viol.append((owner, rid, f"② owner·status 값이 허용 값이 아닙니다: {owner!r}·{r.get('status')!r}"))
        if not isinstance(loaded, list):
            viol.append((owner, rid, "② loaded_in이 목록이 아닙니다"))
            continue
        if kind == "규정" and action != "삭제" and not loaded:
            viol.append((owner, rid, "② 「규정」 행(삭제 제외)인데 loaded_in(실리는 곳)이 비어 있습니다"))
        if kind == "비규정" and loaded:
            viol.append((owner, rid, "② 「비규정」 행인데 loaded_in이 비어 있지 않습니다"))
        if "원천 절만" in loaded and len(loaded) > 1:
            viol.append((owner, rid, "② 「원천 절만」을 다른 값과 함께 적었습니다"))
        # ⑤
        if action in ("통합", "삭제") and not str(r.get("note") or "").strip():
            viol.append((owner, rid, f"⑤ 「{action}」 행에 사유(note)가 없습니다"))
        # ③
        src = r.get("source")
        src_cover = None
        if action in ("이관", "개정", "통합"):
            if not isinstance(src, dict) or "doc" not in src:
                viol.append((owner, rid, "③ source(v05 원천)가 없습니다"))
                continue
            src_cover, err = bg.cover(docs, src)
            if src_cover is None:
                viol.append((owner, rid, f"③ 원천이 현행에 없습니다: {err}"))
                continue
        elif action == "안전장치 핵심으로 대체":
            name = src.get("safety") if isinstance(src, dict) else None
            if not name or name not in safety_body:
                viol.append((owner, rid, f"③ 안전장치 핵심에 그 항목이 없습니다: {name!r}"))
            if loaded != ["안전장치 핵심"]:
                viol.append((owner, rid, f"④ 「안전장치 핵심으로 대체」 행의 loaded_in은 「안전장치 핵심」이어야 합니다: {loaded}"))
            continue
        # ④
        if src_cover is None:
            continue
        for layer in loaded:
            if layer in ("원천 절만", "안전장치 핵심"):
                continue
            if layer not in layers:
                viol.append((owner, rid, f"④ loaded_in의 계층이 구성표에 없습니다: {layer}"))
                continue
            hit = any(s.get("doc") == src["doc"] and (sel_cover(s) or set()) >= src_cover for s in layers[layer])
            if not hit:
                viol.append((owner, rid, f"④ {layer} 생성물에 원천 {bg.sel_label(src)}이 실려 있지 않습니다"))
    return viol


# ---------------------------------------------------------------- 실행

def print_errors(code, errors, level="FAIL"):
    for loc, cause in errors:
        print(f"[{level}] {code} {loc} {cause}")
        if level == "FAIL":
            print(f"       조치: {ACTIONS[code]}")


def run_checks(root, source, owners=None, global_source=None, run_c1=True, commit_owner=None, quiet=False):
    """C1~C6과 --global-source 대조를 실행해 오류 수를 돌려준다.

    commit_owner가 문자열이면 커밋 전 검사 순서 5의 처리다(그 담당 행 위반은 [FAIL], 그 밖은 [WARN]).
    commit_owner가 False면 C5를 건너뛴다(커밋하는 REQ가 없음).
    """
    out = print if not quiet else (lambda *a, **k: None)
    counts = {}
    if run_c1:
        errs = check_c1(source)
        counts["C1"] = len(errs)
        print_errors("C1", errs)
        if not errs:
            out("[PASS] C1 옛 경로 잔존: 대상 파일에 옛 경로가 없습니다.")
    docs = bg.Docs(source)
    gen = bg.generate(source, None)
    for code, fn in (("C2", lambda: check_c2(source, gen)), ("C3", lambda: check_c3(source, gen)),
                     ("C4", lambda: check_c4(source, gen, docs))):
        errs = fn()
        counts[code] = len(errs)
        if not quiet:
            print_errors(code, errs)
            if not errs:
                out(f"[PASS] {code} {'생성물 대조' if code == 'C2' else '안전장치 핵심 무결성' if code == 'C3' else '파트 대조'}: 오류 없음.")
    if commit_owner is False:
        out("[INFO] C5 이관 검사: 커밋하는 REQ가 없어 건너뜁니다(HOTFIX·요청 커밋 등).")
        counts["C5"] = 0
    else:
        viol = check_c5(root, source, docs, gen)
        if commit_owner:
            mine = [(loc, cause) for o, loc, cause in viol if o == commit_owner]
            other = [(loc, f"{cause} (담당 {o})") for o, loc, cause in viol if o != commit_owner]
            if not quiet:
                print_errors("C5", other, level="WARN")
            viol_fail = mine
        else:
            viol_fail = [(loc, cause) for o, loc, cause in viol if not owners or o in owners]
        counts["C5"] = len(viol_fail)
        if not quiet:
            print_errors("C5", viol_fail)
            if not viol_fail:
                scope = (f"담당 {commit_owner}" if commit_owner else
                         (f"담당 {', '.join(owners)}" if owners else "모든 행"))
                out(f"[PASS] C5 이관 검사({scope}): 위반 없음.")
    if not quiet:
        for line in budget_lines(gen):
            print(line)
    if global_source:
        try:
            mark, _, body = bg.extract_safety(open(global_source, encoding="utf-8").read())
        except (OSError, UnicodeDecodeError, bg.SourceError) as e:
            out(f"[FAIL] 안전장치 핵심이 원천과 다름: 원천을 읽거나 추출할 수 없습니다({e})")
            out(f"       조치: {ACTIONS['G']}")
            counts["G"] = 1
        else:
            have = gen.safety or {}
            if mark != have.get("mark") or bg.sha256(body) != have.get("sha"):
                out(f"[FAIL] 안전장치 핵심이 원천과 다름: 원천 갱신 표기 {mark}, 추출 SHA-256 {bg.sha256(body)} / "
                    f"생성물 {have.get('mark')}, {have.get('sha')}")
                out(f"       조치: {ACTIONS['G']}")
                counts["G"] = 1
            else:
                out(f"[PASS] 안전장치 핵심이 원천({global_source})과 같습니다(갱신 표기 {mark}).")
                counts["G"] = 0
    return counts


def summary_for_baseline(root, source):
    """기준선 기록의 check(C2~C5 오류 수와 합계). 출력하지 않는다."""
    counts = run_checks(root, source, run_c1=False, quiet=True)
    return {**counts, "errors": sum(counts.values())}


def run_commit_check(root, staged, owner):
    """커밋 전 검사 순서 5. C1~C5 오류가 없으면 True(06 「형상통제 대조」 5항)."""
    cs.ROOT_DIR = root
    try:
        source = bg.StagedSource() if staged else bg.WorkTreeSource(root)
        if owner:
            print(f"[INFO] 형상통제 대조: C5의 담당은 커밋하는 REQ {owner}입니다(담당이 아닌 행의 위반은 [WARN]).")
        counts = run_checks(root, source, commit_owner=owner if owner else False)
    except bg.SourceError as e:
        print(f"[FAIL] 형상통제 대조를 실행할 수 없습니다: {e}")
        print("       조치: 원천 파일과 Git 상태를 확인하고, 해결되지 않으면 멈춰 보고하십시오.")
        return False
    total = sum(counts.values())
    if total:
        print(f"[FAIL] 형상통제 대조: 오류 {total}건({', '.join(f'{k} {v}' for k, v in counts.items() if v)}). 원천: {RULE}")
        return False
    print("[PASS] 형상통제 대조: C1~C5 오류 없음.")
    return True


def parse_args(argv):
    opts = {"overlay": [], "owner": [], "global": None, "units": False, "placement": None}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--overlay", "--owner", "--global-source", "--placement") and i + 1 < len(argv):
            v = argv[i + 1]
            if a == "--overlay":
                opts["overlay"].append(v)
            elif a == "--owner":
                opts["owner"].append(v)
            elif a == "--global-source":
                opts["global"] = v
            else:
                opts["placement"] = v
            i += 2
        elif a == "--units":
            opts["units"] = True
            i += 1
        else:
            raise ValueError(f"알 수 없는 인자: {a}")
    if opts["units"] and opts["placement"]:
        raise ValueError("--units와 --placement는 함께 줄 수 없습니다")
    return opts


def main(argv):
    try:
        opts = parse_args(argv)
    except ValueError as e:
        print(f"[FAIL] 사용법 오류: {e}")
        print("       사용법: python check_config.py [--overlay <폴더>]… [--owner <기록 이름>]… [--global-source <파일>] "
              "[--units | --placement <코드>]")
        return 2
    try:
        root = bg.repo_root()
        cs.ROOT_DIR = root
        source = bg.WorkTreeSource(root, opts["overlay"])
        if opts["units"]:
            mm = load_map(source)
            units, _ = all_units(root, mm)
            print(f"[INFO] 기준본 {mm['baseline_commit']} 대상 문서 {len(mm.get('targets', []))}개의 단위 {len(units)}개")
            for uid, heading, excerpt in units:
                print(f"{uid}\t{heading}\t{excerpt}")
            return 0
        if opts["placement"]:
            docs = bg.Docs(source)
            info = dict(bg.org_table(docs))
            code = opts["placement"]
            if code not in info:
                print(f"[FAIL] 조직 표에 없는 코드입니다: {code}")
                return 2
            v = info[code]
            chain = {"표준 공통", f"부:{v['부']}", f"팀:{v['팀']}", f"파트:{code}"}
            rows = [r for r in load_map(source).get("rows", []) if set(r.get("loaded_in") or []) & chain]
            print(f"[INFO] 파트 {code}의 사슬(표준 공통, 부:{v['부']}, 팀:{v['팀']}, 파트:{code})에 실리는 행 {len(rows)}개")
            for r in rows:
                src = r.get("source")
                label = bg.sel_label(src) if isinstance(src, dict) and "doc" in src else json.dumps(src, ensure_ascii=False)
                print(f"{r.get('id')}\t{', '.join(r.get('loaded_in'))}\t{r.get('action')}\t{label}")
            return 0
        print(f"[INFO] 형상통제 대조: 원천 {source.describe()}"
              + (f", C5 담당 {', '.join(opts['owner'])}" if opts["owner"] else ", C5 모든 행")
              + (f", 안전장치 핵심 원천 {opts['global']}(C1 생략)" if opts["global"] else ""))
        counts = run_checks(root, source, owners=opts["owner"], global_source=opts["global"],
                            run_c1=not opts["global"])
    except bg.SourceError as e:
        print(f"[FAIL] 원천을 읽을 수 없습니다: {e}")
        print("       조치: 경로와 파일을 확인하고, 해결되지 않으면 멈춰 보고하십시오.")
        return 2
    total = sum(counts.values())
    if total:
        print(f"[FAIL] 형상통제 대조: 오류 {total}건({', '.join(f'{k} {v}' for k, v in counts.items() if v)}). 원천: {RULE}")
        return 1
    print("[PASS] 형상통제 대조: 오류 0건.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
