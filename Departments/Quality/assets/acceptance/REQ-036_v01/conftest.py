# -*- coding: utf-8 -*-
"""REQ-036 인수 시험의 명령행 옵션.

--acc-dev-dir는 결함 사본이나 기대 형태의 사본으로 시험의 판정을 확인할 때만 쓴다(ACC-036 4절).
현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다. 환경 변수 대신 옵션을 쓰는 까닭은
명령 앞의 환경 변수 대입이 권한 확인 대상이기 때문이다(Workflow/06 2.1절 「명령 형태」 ③).
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 주면 개발 쪽 현행 적용본을 이 폴더 하나로 바꾼다. 없으면 "
             "Departments/Development/workspace/REQ-036_적용본_vNN의 가장 높은 버전")
