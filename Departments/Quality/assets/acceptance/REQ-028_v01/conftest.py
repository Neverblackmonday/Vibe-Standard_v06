# -*- coding: utf-8 -*-
"""REQ-028 인수 시험의 명령행 옵션.

옵션은 결함 사본(다른 안건의 적용본, 원본 검사기 등)으로 시험이 실제로 실패하는지(Red)
확인할 때만 쓴다(ACC-028 4절). 현행 인수 시험 실행(구현 단계, 최종 판정)에서는 주지 않는다.
환경 변수 대신 옵션을 쓰는 까닭은 명령 앞의 환경 변수 대입이 권한 확인 대상이기 때문이다.
"""


def pytest_addoption(parser):
    parser.addoption(
        "--acc-script", default=None,
        help="시험할 check_standard.py. 없으면 개발 적용본(Departments/Development/workspace/"
             "REQ-028_적용본_vNN의 가장 높은 버전)의 scripts.적용본/check_standard.py, 그것이 없으면 원본")
    parser.addoption(
        "--acc-design-dir", default=None,
        help="설계 적용본 폴더. 없으면 Departments/Design/workspace/REQ-028_적용본_vNN의 가장 높은 버전")
    parser.addoption(
        "--acc-dev-dir", default=None,
        help="개발 적용본 폴더. 없으면 Departments/Development/workspace/REQ-028_적용본_vNN의 가장 높은 버전"
             "(없으면 개발 적용본 없음)")
    parser.addoption(
        "--acc-dev-result", default=None,
        help="개발 결과서 파일. 없으면 Departments/Development/results/DEV-028_vNN.md의 가장 높은 버전")
    parser.addoption(
        "--acc-close-dir", default=None,
        help="종결 기록을 읽을 폴더. 없으면 Departments/Secretariat/assets/inbox")
    parser.addoption(
        "--acc-head", default="HEAD",
        help="체크리스트 4 ⑤에서 기간 안 커밋이 조상으로 남아 있어야 하는 커밋. 기본값 HEAD")
