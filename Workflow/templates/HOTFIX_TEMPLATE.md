---
hotfix_id: "003"
created: "YYYY-MM-DD"
author:
  agent: "Secretariat"
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium" # 실제 적용 effort
  session: "<서비스>·<세션 이름>" # 작성 세션의 세션 식별자(Workflow/05_인수인계_및_실행명령 「비서실 동시 운용」)
confirmed: "" # 대표님 직접 기재 또는 Workflow/07_문서_서식_및_번호 「승인 기록」 절차. 형식 "YYYY-MM-DDTHH:MM:SS+09:00". 비어 있으면 커밋 불가
scope:
  # 사전 승인된 대상 파일. 대상 조건은 Workflow/03_라이프사이클 「핫픽스 트랙」
  - Departments/Development/assets/src/main.py
---

# HOTFIX-003: 핫픽스 제목

> 대상 조건과 절차는 `Workflow/03_라이프사이클` 「핫픽스 트랙」을 따른다. 파일명은 `HOTFIX-<번호>_v<버전>.md`다. 이 안내문은 작성할 때 지운다.

## 1. 지시 원문과 사전 승인
- **지시 원문**:
  > 대표님 지시를 원형 그대로 인용한다.
- **사전 승인**: 비서실이 제시한 대상 목록을 대표님이 승인한 일시(`Workflow/03_라이프사이클` 「핫픽스 트랙」)
- **승인된 대상 파일**:

| 번호 | 경로 | 원인 | 변경 요지 |
| :---: | :--- | :--- | :--- |
| 1 | `Departments/Development/assets/src/main.py` | 결함 원인 | 수정 요지 |

- **현상**: 관찰한 결함 증상과 재현 방법
- **위험도**: 영향 범위와 고치지 않을 때의 위험

## 2. 수정 내역
### 2.1 `Departments/Development/assets/src/main.py`
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
| 커밋 전 검사 | `python Departments/Development/assets/scripts/check_standard.py` | YYYY-MM-DDTHH:MM:SS+09:00 | 결과 원문 |
| 관련 테스트 | `python -m pytest Departments/Development/assets/tests` | YYYY-MM-DDTHH:MM:SS+09:00 | 결과 원문 |

## 4. 체크리스트
| 번호 | 확인 항목 | 결과 | 근거 |
| :---: | :--- | :---: | :--- |
| 1 | `Workflow/03_라이프사이클` 「핫픽스 트랙」의 대상 조건을 모두 충족 | | |
| 2 | 수정 파일이 승인된 대상 파일 목록과 같음 | | |
| 3 | 커밋 전 검사와 관련 테스트 통과 | | |

## 5. 대표님 사후 확인
- 대표님이 2~4절을 확인한 뒤 `confirmed:`를 적거나 `Workflow/07_문서_서식_및_번호` 「승인 기록」대로 기재하게 한다. 대표님 확인이 독립 판정을 대신한다.
- 커밋 메시지: `fix: [HOTFIX-003] 요약`
