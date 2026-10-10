# -*- coding: utf-8 -*-
"""REQ-023 인수 시험의 명령행 옵션.

네 옵션은 결함 사본(원본 Workflow/, 다른 안건의 적용본, 다른 안건의 개발 결과서 등)으로 시험이 실제로
실패하는지(Red) 확인할 때만 쓴다(ACC-023 4절). 현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 환경 변수 대입 명령이 권한 확인 대상이기 때문이다(ACC-019 3절의 선례).
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더(Workflow.적용본/을 담은 폴더). Workflow.적용본/·.claude.적용본/이 없으면 "
             "그 폴더 자체를 Workflow/의 적용본으로 본다. 없으면 "
             "Departments/Design/workspace/REQ-023_적용본_vNN(가장 높은 버전)")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더(.claude.적용본/을 담은 폴더). 없으면 "
             "Departments/Development/workspace/REQ-023_적용본_vNN(가장 높은 버전. 없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-023_vNN.md의 가장 높은 버전")
    parser.addoption(
        "--acc-original-dir", default=None,
        help="원본 Workflow 폴더. 없으면 저장소의 Workflow/")
