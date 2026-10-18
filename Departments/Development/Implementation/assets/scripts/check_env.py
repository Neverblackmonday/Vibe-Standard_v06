#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_env.py - 설치·PM 기동 전 점검

규칙의 원천은 Workflow/06_통제장치_및_배포 「설치·PM 기동 전 점검」이고, 쓰는 시점은 setup.cmd(설치 때)와
Workflow/05_인수인계_및_실행명령 「비서실 실행 절차」의 「PM 기동」 2-1)(PM 기동 전)이다. 이 스크립트는 그 구현이다.

읽는 것(어떤 파일·설정도 고치지 않는다. 신뢰 상태도 읽기만 한다):
  ① git config --get core.hooksPath가 .githooks인지
  ② .githooks/pre-commit과 .githooks/commit-msg가 있는지
  ③ 사용자 홈의 .claude.json에서 저장소 루트의 hasTrustDialogAccepted가 true인지(Claude Code 폴더 신뢰 상태)
  ④ .claude/settings.json이 JSON으로 읽히고 permissions.allow가 비어 있지 않은지(allow 적용 조건)
사용법: python check_env.py --setup   # 설치 때. ①② 문제는 실패(종료 코드 1), ③④ 문제는 경고와 안내(종료 코드 0)
        python check_env.py           # PM 기동 전. 하나라도 문제가 있으면 실패(종료 코드 1)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# 거버넌스 구역(스크립트 폴더)에 바이트코드 캐시를 만들지 않는다
sys.dont_write_bytecode = True
import check_standard as cs  # noqa: E402  (출력 인코딩 고정, 저장소 루트)

ROOT_DIR = cs.ROOT_DIR
SOURCE = "Workflow/06_통제장치_및_배포 「설치·PM 기동 전 점검」"
HOOKS_PATH = ".githooks"
HOOK_FILES = (".githooks/pre-commit", ".githooks/commit-msg")
TRUST_GUIDE = ("저장소 루트에서 Claude Code(`claude`)를 한 번 실행해 폴더 신뢰 확인 화면에서 신뢰를 고른 뒤 종료하고, "
               "이 점검을 다시 실행하십시오.")


def git_out(args):
    res = subprocess.run(["git", *args], cwd=ROOT_DIR, capture_output=True)
    return res.returncode, res.stdout.decode("utf-8", "replace").strip()


def check_hooks_path():
    """① 훅 경로. 문제가 없으면 None, 있으면 사유를 돌려준다."""
    code, value = git_out(["config", "--get", "core.hooksPath"])
    if code != 0 or value != HOOKS_PATH:
        return f"core.hooksPath가 {HOOKS_PATH}가 아닙니다(현재: {value or '설정 없음'}). setup.cmd를 실행하십시오."
    return None


def check_hook_files():
    """② 훅 파일. 문제가 없으면 None, 있으면 사유를 돌려준다."""
    missing = [rel for rel in HOOK_FILES if not (ROOT_DIR / rel).is_file()]
    if missing:
        return f"훅 파일이 없습니다: {', '.join(missing)}. 저장소의 .githooks/를 확인하십시오."
    return None


def norm_path(text):
    norm = text.replace("\\", "/").rstrip("/")
    # Windows는 경로의 대소문자를 가리지 않으므로 대소문자를 무시해 비교한다
    return norm.lower() if os.name == "nt" else norm


def check_trust():
    """③ 신뢰 상태. 문제가 없으면 None, 「신뢰 처리 전이거나 확인 불가」이면 사유를 돌려준다."""
    code, top = git_out(["rev-parse", "--show-toplevel"])
    if code != 0 or not top:
        return "저장소 루트를 조회할 수 없어 신뢰 상태를 확인하지 못했습니다."
    state = Path.home() / ".claude.json"
    if not state.is_file():
        return f"사용자 상태 파일({state.name})이 사용자 홈에 없습니다."
    try:
        with open(state, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        # 파일 내용은 출력하지 않는다(사용자 상태 파일이다)
        return f"사용자 상태 파일을 읽을 수 없습니다({type(e).__name__})."
    projects = data.get("projects") if isinstance(data, dict) else None
    if not isinstance(projects, dict):
        return "사용자 상태 파일에 projects 항목이 없습니다."
    target = norm_path(top)
    entry = next((v for k, v in projects.items() if norm_path(k) == target), None)
    if not isinstance(entry, dict):
        return "사용자 상태 파일에 이 저장소 루트의 항목이 없습니다."
    if "hasTrustDialogAccepted" not in entry:
        return "이 저장소 루트의 항목에 hasTrustDialogAccepted 키가 없습니다."
    if entry["hasTrustDialogAccepted"] is not True:
        return "이 저장소 루트의 hasTrustDialogAccepted가 true가 아닙니다."
    return None


def check_allow():
    """④ allow 적용 조건. 문제가 없으면 None, 있으면 사유를 돌려준다."""
    settings = ROOT_DIR / ".claude" / "settings.json"
    try:
        with open(settings, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as e:
        return f".claude/settings.json을 JSON으로 읽을 수 없습니다({type(e).__name__})."
    allow = data.get("permissions", {}).get("allow") if isinstance(data, dict) else None
    if not isinstance(allow, list) or not allow:
        return ".claude/settings.json의 permissions.allow가 비어 있습니다."
    return None


def main(argv):
    setup = "--setup" in argv
    mode = "설치 점검(--setup)" if setup else "PM 기동 전 점검"
    print(f"[INFO] {mode}을 시작합니다(읽기만 하고 고치지 않습니다. {SOURCE}).")
    hard = [p for p in (check_hooks_path(), check_hook_files()) if p]
    trust = check_trust()
    allow = check_allow()

    for p in hard:
        print(f"[FAIL] {p}")
    if not hard:
        print(f"[PASS] 훅 경로({HOOKS_PATH})와 훅 파일({', '.join(HOOK_FILES)})이 있습니다.")

    # ③④는 설치 때는 경고로, PM 기동 전에는 실패로 다룬다(REQ-032 D17)
    soft_tag = "[WARN]" if setup else "[FAIL]"
    soft = [p for p in (trust, allow) if p]
    if trust:
        print(f"{soft_tag} 신뢰 처리 전이거나 확인 불가: {trust}")
    if allow:
        print(f"{soft_tag} {allow}")
    if not soft:
        print("[PASS] 적용 조건 충족: 폴더 신뢰 상태가 true이고 permissions.allow가 있습니다"
              "(allow가 실제로 적용되는지는 세션 밖에서 읽을 수 없습니다).")
    if trust:
        print(f"       안내: {TRUST_GUIDE}")

    if hard or (soft and not setup):
        if not setup:
            print("       조치: PM을 기동하지 않고 이 출력과 안내를 대표님께 보고하십시오"
                  "(Workflow/05_인수인계_및_실행명령 「비서실 실행 절차」의 「PM 기동」 2-1)).")
        return 1
    if soft:
        print("[PASS] 설치 점검: 훅 설정은 마쳤습니다. 위 경고는 설치 뒤 Claude Code에서 처리하십시오.")
    else:
        print(f"[PASS] {mode} 통과.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
