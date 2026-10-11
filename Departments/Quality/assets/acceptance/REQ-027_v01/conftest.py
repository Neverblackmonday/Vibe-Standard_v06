# -*- coding: utf-8 -*-
"""REQ-027 인수 시험의 명령행 옵션.

옵션은 결함 사본(다른 안건의 적용본 등)으로 시험이 실제로 실패하는지(Red)
확인할 때만 쓴다(ACC-027 4절). 현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 명령 앞의 환경 변수 대입이 권한 확인 대상이기 때문이다.
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더. 주면 설계 쪽 현행 적용본을 이 폴더 하나로 바꾼다. "
             "없으면 Departments/Design/workspace/REQ-027_적용본_vNN의 가장 높은 버전")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 주면 개발 쪽을 이 폴더 하나로 바꾼다. 없으면 "
             "Departments/Development/workspace/REQ-027_적용본_vNN의 가장 높은 버전(없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-027_vNN.md의 가장 높은 버전")
    parser.addoption(
        "--acc-own-req", default="027",
        help="체크리스트 6 ⑥⑨에서 「이 REQ 번호」로 보는 번호. 기본값 027")
