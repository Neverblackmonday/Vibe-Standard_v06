# -*- coding: utf-8 -*-
"""REQ-032 인수 시험의 명령행 옵션.

옵션은 결함 사본(다른 안건의 적용본 등)으로 시험이 실제로 실패하는지(Red) 확인할 때만 쓴다(ACC-032 4절).
현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 명령 앞의 환경 변수 대입이 권한 확인 대상이기 때문이다.
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더. 없으면 설계부 workspace의 REQ-032_적용본_vNN 가운데 가장 높은 버전")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 없으면 개발부 workspace의 REQ-032_적용본_vNN 가운데 가장 높은 버전(없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발부 결과서. 없으면 DEV-032_vNN(NN은 02 이상) 가운데 가장 높은 버전")
    parser.addoption(
        "--acc-rpt-result", default=None,
        help="설계부 결과서. 없으면 RPT-032_vNN 가운데 가장 높은 버전")
