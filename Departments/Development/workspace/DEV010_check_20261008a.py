#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REQ-010 구현 단계 일회성 조회 스크립트.

check_standard.py의 함수를 메모리 안의 가짜 HOTFIX 기록에 적용해,
HOTFIX 검사가 「수정 파일 수」를 세는지 「scope 항목 수」를 세는지 확인한다.
파일을 만들거나 고치지 않는다.
"""
import importlib.util
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    "check_standard", ROOT / "Departments/Development/assets/scripts/check_standard.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

rec = {"name": "HOTFIX-999_v01.md (가상)", "scope": {"Departments/Development/assets/src"},
       "approved": "2026-10-08T18:00:00+09:00"}
files = [f"Departments/Development/assets/src/m{i}.py" for i in range(5)]

print(f"HOTFIX_MAX_SCOPE = {cs.HOTFIX_MAX_SCOPE}")
print(f"scope 항목 수 = {len(rec['scope'])} (허용 1~{cs.HOTFIX_MAX_SCOPE}: "
      f"{1 <= len(rec['scope']) <= cs.HOTFIX_MAX_SCOPE})")
print(f"거버넌스 제외 경로 포함 = {any(cs.is_governance_path(s) for s in rec['scope'])}")
print(f"변경 파일 수 = {len(files)}, covers() = {cs.covers(rec, files)}")
