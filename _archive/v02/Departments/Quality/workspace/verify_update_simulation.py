#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""품질 게이트 독립 검증 스크립트: Update_Package 무결성 및 복붙 시뮬레이션."""

import os
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
PKG_DIR = ROOT_DIR / "Update_Package"
SIM_DIR = ROOT_DIR / "Departments/Quality/workspace/temp_simulation_project"

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

def verify_package():
    print("[1] Update_Package 파일 목록 및 금지 구역 실측")
    files = list(PKG_DIR.rglob("*"))
    actual_files = [f for f in files if f.is_file()]
    print(f"  - 총 파일 수: {len(actual_files)}개")

    forbidden_found = []
    for f in actual_files:
        rel = f.relative_to(PKG_DIR).as_posix()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in rel:
                forbidden_found.append(rel)
    print(f"  - 금지 구역 위반 파일 수: {len(forbidden_found)}건")
    if forbidden_found:
        print(f"    위반 목록: {forbidden_found}")

    # setup.cmd BOM 검증
    setup_file = PKG_DIR / "setup.cmd"
    raw_setup = setup_file.read_bytes()
    has_bom = raw_setup.startswith(b"\xef\xbb\xbf")
    print(f"  - setup.cmd BOM 존재 여부: {has_bom}")
    has_crlf = b"\r\n" in raw_setup
    print(f"  - setup.cmd CRLF 존재 여부: {has_crlf}")

    # 전체 파일 UTF-8 검증
    utf8_errors = []
    for f in actual_files:
        try:
            f.read_bytes().decode("utf-8")
        except Exception as e:
            utf8_errors.append((f.name, str(e)))
    print(f"  - UTF-8 디코딩 실패 건수: {len(utf8_errors)}건")

    return len(actual_files) == 27 and len(forbidden_found) == 0 and not has_bom and has_crlf and len(utf8_errors) == 0

def run_simulation():
    print("\n[2] 가상 프로젝트 대상 마우스 복붙(Ctrl+C / Ctrl+V) 무손실 시뮬레이션")
    if SIM_DIR.exists():
        shutil.rmtree(SIM_DIR)
    SIM_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 고객의 기존 프로젝트 상태 모의 생성
    client_files = {
        "assets/src/customer_app.py": "# 고객 비즈니스 로직 - 손상되면 안 됨\nprint('Customer Core Logic')",
        "assets/tests/test_customer.py": "def test_app(): assert True",
        "Design/docs/prd/PRD_Customer_Product.md": "# 고객 제품 기획서",
        "Design/docs/tad/TAD_Customer_Arch.md": "# 고객 제품 설계서",
        "CEO/References/Confidential_Strategy.txt": "대표님 전용 대외비 전략 문서",
        "Departments/Quality/results/RES-001.md": "# 고객 프로젝트 1호 판정서",
        "Departments/Design/workspace/memo.txt": "고객 설계팀 작업 메모",
        # 구버전 거버넌스 파일들 (덮어써져야 할 대상)
        "AGENTS.md": "# 구버전 헌장 (v01)",
        "CLAUDE.md": "@AGENTS.md",
        "setup.cmd": "@echo off\r\nrem 구버전 setup",
        "Workflow/01_vibe_standard_overview.md": "# 구버전 01",
    }

    for rel_path, content in client_files.items():
        fp = SIM_DIR / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")

    print("  - 가상 프로젝트 고객 자산 7종 및 구버전 파일 4종 생성 완료")

    # 2. 마우스 복붙 덮어쓰기 시뮬레이션 (Update_Package 내부 전 항목을 복사)
    for src_file in PKG_DIR.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(PKG_DIR)
            dst_file = SIM_DIR / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)

    print("  - Update_Package 전체 항목 덮어쓰기 복붙 완료")

    # 3. 고객 자산 보존 검증
    loss_count = 0
    for rel_path, expected_content in client_files.items():
        fp = SIM_DIR / rel_path
        if not fp.exists():
            print(f"  [CRITICAL LOSS] 파일이 삭제됨: {rel_path}")
            loss_count += 1
            continue
        actual_content = fp.read_text(encoding="utf-8")
        if rel_path in ["assets/src/customer_app.py", "assets/tests/test_customer.py", 
                        "Design/docs/prd/PRD_Customer_Product.md", "Design/docs/tad/TAD_Customer_Arch.md",
                        "CEO/References/Confidential_Strategy.txt", "Departments/Quality/results/RES-001.md",
                        "Departments/Design/workspace/memo.txt"]:
            if actual_content != expected_content:
                print(f"  [CORRUPTION] 고객 자산 내용이 훼손됨: {rel_path}")
                loss_count += 1
            else:
                print(f"  [PRESERVED] 100% 무손실 보존 확인: {rel_path}")

    # 4. 거버넌스 파일 최신화 검증
    agents_updated = (SIM_DIR / "AGENTS.md").read_text(encoding="utf-8") != client_files["AGENTS.md"]
    templates_present = (SIM_DIR / "Departments/Standard_Templates/REQ_TEMPLATE.md").exists()
    agents_present = (SIM_DIR / ".claude/agents/secretariat.md").exists()
    check_present = (SIM_DIR / "Departments/Development/assets/scripts/check_standard.py").exists()

    print(f"  - AGENTS.md 최신 갱신 여부: {agents_updated}")
    print(f"  - Standard_Templates 전달 여부: {templates_present}")
    print(f"  - 서브에이전트 7종 전달 여부: {agents_present}")
    print(f"  - check_standard.py 전달 여부: {check_present}")

    # 가상 프로젝트 정리
    shutil.rmtree(SIM_DIR)
    print("  - 가상 시뮬레이션 프로젝트 정리 완료")

    return loss_count == 0 and agents_updated and templates_present and agents_present and check_present

if __name__ == "__main__":
    p_ok = verify_package()
    s_ok = run_simulation()
    if p_ok and s_ok:
        print("\n>>> [FINAL AUDIT RESULT]: ALL TESTS PASSED (100% SUCCESS) <<<")
    else:
        print("\n>>> [FINAL AUDIT RESULT]: FAILED <<<")
