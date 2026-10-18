---
hotfix_id: "003"
created: "YYYY-MM-DD"
author:
  agent: "Development" # 핫픽스팀(V03) 세션
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium (실행 명령 기준)" # 핫픽스 실행 명령 지시문의 effort 값과 출처(Workflow/04_모델_운용 「모델 메타데이터 기록」)
origin: "" # 결함을 들여온 안건의 기록 이름과 버전(예: "REQ-024_v03", "HOTFIX-005_v01"). 알 수 없으면 "확인 불가". 근거는 1절 「원인 안건 근거」(Workflow/07_문서_서식_및_번호 「머리말」)
confirmed: "" # 대표님 직접 기재 또는 Workflow/07_문서_서식_및_번호 「승인 기록」 절차. 형식 "YYYY-MM-DDTHH:MM:SS+09:00". 비어 있으면 커밋 불가
scope:
  # 사전 승인된 대상 파일. 대상 조건은 Workflow/03_라이프사이클 「핫픽스 트랙」
  - Departments/Development/Implementation/assets/src/main.py
---

# HOTFIX-003: 핫픽스 제목

> 대상 조건과 절차는 `Workflow/03_라이프사이클` 「핫픽스 트랙」을 따른다. 파일명은 `HOTFIX-<번호>_v<버전>.md`다. 이 안내문은 작성할 때 지운다.

## 1. 지시 원문과 사전 승인
- **지시 원문**:
  > 대표님 지시를 원형 그대로 인용한다.
- **사전 승인**: 비서실 세션이 제시한 대상 목록을 대표님이 승인한 일시와 승인을 받은 세션 식별자(핫픽스 실행 명령 지시문의 「사전 승인」)(`Workflow/03_라이프사이클` 「핫픽스 트랙」)
- **승인된 대상 파일**:

| 번호 | 경로 | 원인 | 변경 요지 |
| :---: | :--- | :--- | :--- |
| 1 | `Departments/Development/Implementation/assets/src/main.py` | 결함 원인 | 수정 요지 |

- **현상**: 관찰한 결함 증상과 재현 방법
- **위험도**: 영향 범위와 고치지 않을 때의 위험
- **원인 안건 근거**: 머리말 `origin`을 정한 근거(예: 결함이 든 줄을 바꾼 커밋의 `git log` 결과와 그 커밋의 근거 줄). 「확인 불가」이면 찾아본 방법

## 2. 수정 내역
> `deny` 경로 대상 파일은 고치지 않고 변경 후 원문을 수정안으로 적는다(`Workflow/03_라이프사이클` 「핫픽스 트랙」 2항). 이 안내문은 작성할 때 지운다.

### 2.1 `Departments/Development/Implementation/assets/src/main.py`
- **변경 전**:
```text
변경 전 원문
```
- **변경 후**:
```text
변경 후 원문
```

## 3. 검증 결과
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 커밋 전 검사 | `python Departments/Development/Implementation/assets/scripts/check_standard.py` | YYYY-MM-DDTHH:MM:SS+09:00 | 결과 원문 |
| 관련 테스트 | `python -m pytest Departments/Development/Implementation/assets/tests` | YYYY-MM-DDTHH:MM:SS+09:00 | 결과 원문 |

## 4. 체크리스트
| 번호 | 확인 항목 | 결과 | 근거 |
| :---: | :--- | :---: | :--- |
| 1 | `Workflow/03_라이프사이클` 「핫픽스 트랙」의 대상 조건을 모두 충족 | | |
| 2 | 수정 파일이 승인된 대상 파일 목록과 같음 | | |
| 3 | 커밋 전 검사와 관련 테스트 통과 | | |

## 5. 대표님 사후 확인
- 대표님이 2~4절을 확인한 뒤 `confirmed:`를 적거나 `Workflow/07_문서_서식_및_번호` 「승인 기록」대로 기재하게 한다. 대표님 확인이 독립 판정을 대신한다.
- 커밋 메시지: 제목 줄 `fix: [HOTFIX-003] 요약`, 근거 줄 `Confirmed-HOTFIX: Departments/Development/Hotfix/results/HOTFIX-003_v01.md`. 형상통제팀(C02)이 「요청 커밋」으로 커밋하면 `Request-Record: <요청 기록 경로>`를 더한다(`Workflow/07_문서_서식_및_번호` 「번호와 버전」의 「커밋 메시지」)
