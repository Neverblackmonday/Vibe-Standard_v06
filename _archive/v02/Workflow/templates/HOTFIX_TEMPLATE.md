---
hotfix_id: "001"
created: "2026-10-06"
author:
  agent: "Secretariat"
  model: "확인 불가" # 실제 실행 모델 (Workflow/04_모델_운용_기준 「모델 메타데이터 기록」)
  thinking: "medium" # 실제 적용 effort
confirmed: "" # 대표님만 기재 (예: "2026-10-06"). 미확인 시 커밋 차단
scope:
  - Departments/Development/assets/src/main.py
---

# HOTFIX-001: 핫픽스 제목

> 대상 조건과 절차는 `Workflow/03_라이프사이클_및_워크플로우` 「핫픽스 트랙」을 따른다. 대상 조건: 기존 기능의 결함 또는 오탈자, 수정 파일 3개 이하, 거버넌스 파일·`CEO/`·`.claude/` 제외, 새 기능·새 파일 없음. 하나라도 어긋나면 정규 REQ로 전환한다.
> `scope:`에는 수정 파일을 3개 이하로 적고, 항목 줄에 주석(`#`)을 붙이지 않는다.

## 1. 지시 원문, 승인된 대상 파일 목록, 현상과 위험도
- **지시 원문**:
  > 대표님의 지시 원문을 원형 그대로 인용합니다.
- **사전 승인 내역**: 승인 일시와 방식(대표님이 지시하며 대상 파일을 확정했는지, 비서실이 제시한 목록을 승인했는지)
- **승인된 대상 파일 목록**:

| 번호 | 경로 | 원인 | 변경 요지 |
| :---: | :--- | :--- | :--- |
| 1 | `Departments/Development/assets/src/main.py` | 결함 원인 | 수정 요지 |

- **현상**: 실제로 관찰한 결함 증상과 재현 방법
- **위험도**: 영향 범위와 수정하지 않을 때의 위험

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
| 표준 검사 | `python Departments/Development/assets/scripts/check_standard.py` | YYYY-MM-DDThh:mm:ss+09:00 | 실행 결과 원문 |
| 관련 테스트 | `python -m pytest Departments/Development/assets/tests` | YYYY-MM-DDThh:mm:ss+09:00 | 실행 결과 원문 |

## 4. 대표님 사후 확인
- **확인 결과**: 대표님이 수정 내역과 검증 결과를 확인한 뒤 머리말 `confirmed:`에 날짜를 기재합니다. 대표님 확인이 독립 판정을 대신합니다.
- **커밋 메시지**: `fix: [HOTFIX-001] 요약`
