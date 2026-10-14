# -*- coding: utf-8 -*-
"""REQ-029 인수 시험의 명령행 옵션.

옵션은 결함 사본(다른 안건의 적용본·기록 등)으로 시험이 실제로 실패하는지(Red)
확인할 때만 쓴다(ACC-029 4절). 현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 명령 앞의 환경 변수 대입이 권한 확인 대상이기 때문이다.
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더. 주면 설계 쪽 현행 적용본을 이 폴더 하나로 바꾼다. "
             "없으면 Departments/Design/workspace/REQ-029_적용본_vNN의 가장 높은 버전")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 주면 개발 쪽을 이 폴더 하나로 바꾼다. 없으면 "
             "Departments/Development/workspace/REQ-029_적용본_vNN의 가장 높은 버전(없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-029_vNN.md의 가장 높은 버전")
    parser.addoption(
        "--acc-run-log", default=None,
        help="체크리스트 ⑭에서 읽는 PM 실행 기록. 없으면 Departments/Secretariat/workspace/실행기록_REQ-029.md")
    parser.addoption(
        "--acc-no-order-baseline", action="store_true", default=False,
        help="체크리스트 ⑩에서 인수 시험 작성 때 이미 있던 ORDER 변경(기준값)을 인정하지 않는다")
