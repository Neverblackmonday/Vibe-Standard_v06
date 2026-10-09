# -*- coding: utf-8 -*-
"""REQ-019 인수 시험의 명령행 옵션.

--acc-target은 결함 사본이나 기대 형태의 사본으로 시험의 판정을 확인할 때만 쓴다(ACC-019 4절).
현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다. 환경 변수 대신 옵션을 쓰는 까닭은
환경 변수 대입 명령이 권한 확인 대상이기 때문이다(Workflow/06 적용본 2.1절 「명령 형태」 ②).
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-target", default=None,
        help="대상 settings.json 경로, 또는 '{'로 시작하는 JSON 문자열. 없으면 개발 적용본의 최신 버전")
