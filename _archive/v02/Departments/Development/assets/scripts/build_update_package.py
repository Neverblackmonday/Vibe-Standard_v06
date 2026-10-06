#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""표준 업데이트용 원클릭 마우스 복붙 패키지(Update_Package) 자동 빌더 스크립트.

표준 저장소의 최신 거버넌스 및 매뉴얼 파일만 추출하여,
고객 제품 코드를 전혀 건드리지 않는 1:1 거울(Mirror) 구조로 번들링합니다.
"""

import os
import shutil
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
UPDATE_PKG_DIR = ROOT_DIR / "Update_Package"

# 금지된 고객 제품 구역 패턴 (패키지에 절대 포함되면 안 됨)
FORBIDDEN_PATTERNS = [
    "assets/src",
    "assets/tests",
    "CEO/References",
    "Design/docs/prd",
    "Design/docs/tad",
    "results",
    "workspace",
    "_archive",
]

def clean_dir(target_dir: Path):
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

def copy_file(src: Path, dst: Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def verify_encoding_and_bom(file_path: Path):
    raw = file_path.read_bytes()
    # setup.cmd BOM 0개 검증
    if file_path.name.lower() == "setup.cmd":
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError(f"[ERROR] {file_path.name}에 UTF-8 BOM이 존재합니다.")
    # UTF-8 디코딩 검증
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ValueError(f"[ERROR] {file_path}는 유효한 UTF-8이 아닙니다: {e}")

def build_package():
    print("=" * 60)
    print("[BUILD] 바이브 코딩 표준 v02 업데이트 패키지(Update_Package) 생성 시작")
    print(f"  - 소스 루트: {ROOT_DIR}")
    print(f"  - 타깃 디렉터리: {UPDATE_PKG_DIR}")
    print("=" * 60)

    clean_dir(UPDATE_PKG_DIR)
    copied_files = []

    # 1. 루트 거버넌스 파일 복사
    root_files = ["AGENTS.md", "CLAUDE.md", "setup.cmd", ".gitattributes"]
    for rf in root_files:
        src = ROOT_DIR / rf
        if src.exists():
            dst = UPDATE_PKG_DIR / rf
            copy_file(src, dst)
            copied_files.append(dst)

    # 2. .claude/ 거버넌스 및 에이전트 복사
    claude_settings = ROOT_DIR / ".claude/settings.json"
    if claude_settings.exists():
        dst = UPDATE_PKG_DIR / ".claude/settings.json"
        copy_file(claude_settings, dst)
        copied_files.append(dst)

    agents_dir = ROOT_DIR / ".claude/agents"
    if agents_dir.exists():
        for af in agents_dir.glob("*.md"):
            dst = UPDATE_PKG_DIR / ".claude/agents" / af.name
            copy_file(af, dst)
            copied_files.append(dst)

    # 3. Workflow/ 7대 매뉴얼 복사
    workflow_dir = ROOT_DIR / "Workflow"
    if workflow_dir.exists():
        for wf in sorted(workflow_dir.glob("*.md")):
            dst = UPDATE_PKG_DIR / "Workflow" / wf.name
            copy_file(wf, dst)
            copied_files.append(dst)

    # 4. 검사 스크립트 복사
    chk_script = ROOT_DIR / "Departments/Development/assets/scripts/check_standard.py"
    if chk_script.exists():
        dst = UPDATE_PKG_DIR / "Departments/Development/assets/scripts/check_standard.py"
        copy_file(chk_script, dst)
        copied_files.append(dst)

    # 5. 부서별 템플릿 집약 복사 -> Departments/Standard_Templates/
    template_mappings = [
        (ROOT_DIR / "Departments/Secretariat/docs/requests/REQ_TEMPLATE.md", "REQ_TEMPLATE.md"),
        (ROOT_DIR / "Departments/Secretariat/results/HOTFIX_TEMPLATE.md", "HOTFIX_TEMPLATE.md"),
        (ROOT_DIR / "Departments/Design/docs/prd/PRD_TEMPLATE.md", "PRD_TEMPLATE.md"),
        (ROOT_DIR / "Departments/Design/docs/tad/TAD_TEMPLATE.md", "TAD_TEMPLATE.md"),
        (ROOT_DIR / "Departments/Design/docs/tad/EC_TEMPLATE.md", "EC_TEMPLATE.md"),
        (ROOT_DIR / "Departments/Quality/results/RES_TEMPLATE.md", "RES_TEMPLATE.md"),
    ]
    # RP_TEMPLATE 대체 확인
    rp_tmpl = ROOT_DIR / "Departments/Secretariat/docs/requests/RP-002.md"
    if rp_tmpl.exists():
        template_mappings.append((rp_tmpl, "RP_TEMPLATE.md"))

    for src, tmpl_name in template_mappings:
        if src.exists():
            dst = UPDATE_PKG_DIR / "Departments/Standard_Templates" / tmpl_name
            copy_file(src, dst)
            copied_files.append(dst)

    # 6. 무결성 및 인코딩 검증
    print("\n[VERIFY] 무결성 및 인코딩 검사 수행 중...")
    for f in copied_files:
        rel = f.relative_to(UPDATE_PKG_DIR).as_posix()
        # 금지된 고객 구역 포함 여부 실측
        for forbidden in FORBIDDEN_PATTERNS:
            if forbidden in rel:
                raise RuntimeError(f"[FATAL] 고객 금지 구역이 패키지에 포함되었습니다: {rel}")
        verify_encoding_and_bom(f)
        print(f"  [OK] {rel} (UTF-8 유효)")

    print("\n" + "=" * 60)
    print(f"[SUCCESS] Update_Package 빌드 완료: 총 {len(copied_files)}개 파일 번들링 성공")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = build_package()
        sys.exit(0 if success else 1)
    except Exception as err:
        print(f"\n[BUILD FAILED] {err}", file=sys.stderr)
        sys.exit(1)
