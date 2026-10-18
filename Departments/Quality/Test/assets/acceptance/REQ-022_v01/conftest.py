# -*- coding: utf-8 -*-
"""REQ-022 인수 시험의 명령행 옵션.

두 옵션은 결함 사본(원본 Workflow/, 실험 단계 결과서 등)으로 시험이 실제로 실패하는지(Red) 확인할 때만 쓴다(ACC-022 4절).
현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다. 환경 변수 대신 옵션을 쓰는 까닭은
환경 변수 대입 명령이 권한 확인 대상이기 때문이다(ACC-019 3절의 선례).
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="Workflow 문서가 바로 들어 있는 폴더. 없으면 "
             "Departments/Design/workspace/REQ-022_적용본_vNN(가장 높은 버전)/Workflow.적용본")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-022_vNN.md 가운데 "
             "구현 단계 결과서(v03 이상)의 가장 높은 버전")
