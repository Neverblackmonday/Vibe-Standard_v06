# -*- coding: utf-8 -*-
"""REQ-024 인수 시험의 명령행 옵션.

옵션은 결함 사본(다른 안건의 적용본, 원본 Workflow/, 다른 결과서 등)으로 시험이 실제로 실패하는지(Red)
확인할 때만 쓴다(ACC-024 4절). 현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 환경 변수 대입 명령이 권한 확인 대상이기 때문이다(ACC-019 3절의 선례).
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더. 주면 현행 거버넌스 파일의 설계 쪽 적용본과 「적용본이 없다」 확인 대상을 이 폴더 하나로 "
             "바꾼다. 없으면 Departments/Design/workspace/REQ-024_적용본_vNN(현행은 가장 높은 버전, "
             "「적용본이 없다」는 모든 버전)")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 주면 개발 쪽을 이 폴더 하나로 바꾼다. 없으면 "
             "Departments/Development/workspace/REQ-024_적용본_vNN(없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-024_vNN.md의 가장 높은 버전")
    parser.addoption(
        "--acc-original-dir", default=None,
        help="원본 Workflow 폴더. 없으면 저장소의 Workflow/")
    parser.addoption(
        "--acc-own-req", default="024",
        help="체크리스트 11 ⑥에서 「이 REQ 번호」로 보는 번호. 기본값 024")
