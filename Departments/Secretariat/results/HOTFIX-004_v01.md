---
hotfix_id: "004"
created: "2026-10-10"
author:
  agent: "Secretariat"
  model: "Gemini 3.8 Flash"
  effort: "medium"
  session: "Antigravity·20261010T2026"
confirmed: "2026-10-10T23:10:32+09:00" # 대리 기재: Antigravity·20261010T2026, 근거 Departments/Secretariat/assets/inbox/승인기록_20261010_HOTFIX-004_v01.md
scope:
  # 사전 승인된 대상 파일. 대상 조건은 Workflow/03_라이프사이클 「핫픽스 트랙」
  - .claude/agents/development.md
  - .claude/agents/operations.md
---

# HOTFIX-004: 개발·운영 서브에이전트 무인 실행 권한 참조 추가

## 1. 지시 원문과 사전 승인
- **지시 원문**:
  > 대표 장기 외출 중 ORD-006 남은 REQ의 개발·운영 단계가 「중단 조건」 5항으로 멈추지 않게 핫픽스로 처리한다. 원인: 개발·운영 서브에이전트 정의에 Workflow/06 「무인 실행 권한」 참조가 없음(NCR-023_04 재발 방지책 셋째 행, NCR-023_03 제안 ①). HOTFIX-003은 design.md만 고쳤다. 변경 요지: .claude/agents/development.md와 .claude/agents/operations.md의 「업무와 참조 절」 마지막 줄 아래에 각각 「- 명령 실행(명령 도구와 형태): `Workflow/06_통제장치_및_배포` 「무인 실행 권한」.」 한 줄 추가. REQ-023 최종 승인 커밋이 끝난 뒤의 파일을 수정한다. 이 건에 한해 Workflow/03 「핫픽스 트랙」 대상 조건의 거버넌스 파일 제외와 AGENTS.md 「불변 원칙」 3항의 예외를 대표가 승인하며, 이 예외 승인과 사유를 HOTFIX에 적는다 / 사전 승인된 대상 파일 목록: .claude/agents/development.md, .claude/agents/operations.md / 사전 승인 문구: 핫픽스 사전 승인, 대상 .claude/agents/development.md·.claude/agents/operations.md 2개, 거버넌스 파일 예외 승인
- **사전 승인**: 2026-10-10T22:41:14+09:00 (사전 승인 문구: 「핫픽스 사전 승인, 대상 .claude/agents/development.md·.claude/agents/operations.md 2개, 거버넌스 파일 예외 승인」)
- **예외 승인 및 사유**:
  - `Workflow/03_라이프사이클` 「핫픽스 트랙」 대상 조건의 거버넌스 파일 제외 및 `AGENTS.md` 「불변 원칙」 3항에 대한 예외를 대표가 명시적으로 승인함.
  - 사유: 대표 장기 외출 중 개발·운영 서브에이전트 정의에 `Workflow/06_통제장치_및_배포` 「무인 실행 권한」 참조가 없어 허용 목록 밖 명령을 실행하여 「중단 조건」 5항으로 파이프라인이 멈추는 사태를 미연에 방지하고(NCR-023_04 재발 방지책 셋째 행, NCR-023_03 제안 ① 반영), ORD-006 남은 REQ의 무인 진행을 보장하기 위함.
- **승인된 대상 파일**:

| 번호 | 경로 | 원인 | 변경 요지 |
| :---: | :--- | :--- | :--- |
| 1 | `.claude/agents/development.md` | 개발 서브에이전트 정의에 `Workflow/06` 「무인 실행 권한」 참조가 없음 | 「업무와 참조 절」 마지막 줄 아래에 「- 명령 실행(명령 도구와 형태): `Workflow/06_통제장치_및_배포` 「무인 실행 권한」.」 1행 추가 |
| 2 | `.claude/agents/operations.md` | 운영 서브에이전트 정의에 `Workflow/06` 「무인 실행 권한」 참조가 없음 | 「업무와 참조 절」 마지막 줄 아래에 「- 명령 실행(명령 도구와 형태): `Workflow/06_통제장치_및_배포` 「무인 실행 권한」.」 1행 추가 |

- **현상**: 개발·운영 서브에이전트가 무인 실행 권한 허용 목록과 명령 형태를 알지 못해 허용 목록 밖 명령 실행 시 「중단 조건」 5항으로 멈출 위험이 존재함.
- **위험도**: 대표 장기 외출 중 ORD-006 파이프라인의 개발·운영 단계가 자동 진행되지 못하고 중단됨.

## 2. 수정 내역
### 2.1 `.claude/agents/development.md`
- **변경 전**:
```markdown
- 거버넌스 적용본과 규칙·검사 대조: `Workflow/06_통제장치_및_배포` 「거버넌스 파일 개정 절차」.
- 인수 시험: 인수 시험 단계가 있으면 현행 인수 시험을 실행해 통과시키고 결과를 결과서 3절에 적는다(`Workflow/03_라이프사이클` 「시험실」).

## 금지 사항
```
- **변경 후**:
```markdown
- 거버넌스 적용본과 규칙·검사 대조: `Workflow/06_통제장치_및_배포` 「거버넌스 파일 개정 절차」.
- 인수 시험: 인수 시험 단계가 있으면 현행 인수 시험을 실행해 통과시키고 결과를 결과서 3절에 적는다(`Workflow/03_라이프사이클` 「시험실」).
- 명령 실행(명령 도구와 형태): `Workflow/06_통제장치_및_배포` 「무인 실행 권한」.

## 금지 사항
```

### 2.2 `.claude/agents/operations.md`
- **변경 전**:
```markdown
## 업무와 참조 절
- 보안 점검: `Workflow/06_통제장치_및_배포` 「보안 점검」. 결과는 운영 결과서(RPT, 서식 `Workflow/templates/DEV_TEMPLATE.md`)에 적는다.

## 금지 사항
```
- **변경 후**:
```markdown
## 업무와 참조 절
- 보안 점검: `Workflow/06_통제장치_및_배포` 「보안 점검」. 결과는 운영 결과서(RPT, 서식 `Workflow/templates/DEV_TEMPLATE.md`)에 적는다.
- 명령 실행(명령 도구와 형태): `Workflow/06_통제장치_및_배포` 「무인 실행 권한」.

## 금지 사항
```

## 3. 검증 결과
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 커밋 전 검사 | `python Departments/Development/assets/scripts/check_standard.py` | 2026-10-10T22:42:48+09:00 | [SUCCESS] 바이브 표준 v04 커밋 전 검사 통과. |
| 관련 테스트 | `python -m pytest Departments/Development/assets/tests` | 2026-10-10T22:42:52+09:00 | collected 0 items / no tests ran in 0.01s (종료 코드 1: 테스트 없음) |

## 4. 체크리스트
| 번호 | 확인 항목 | 결과 | 근거 |
| :---: | :--- | :---: | :--- |
| 1 | `Workflow/03_라이프사이클` 「핫픽스 트랙」의 대상 조건을 모두 충족 | 충족 (대표 예외 승인) | 기존 기능 결함 보완, 수정 파일 2개(3개 이하), 새 기능/새 파일 없음. 거버넌스 파일 제외 요건은 대표 명시적 예외 승인 적용 |
| 2 | 수정 파일이 승인된 대상 파일 목록과 같음 | 충족 | 승인된 대상 목록인 `.claude/agents/development.md`, `.claude/agents/operations.md` 2개 파일만 수정 |
| 3 | 커밋 전 검사와 관련 테스트 통과 | 조건부 충족 | 커밋 전 검사 통과(`[SUCCESS]`). 관련 테스트는 정의된 테스트 파일이 없어 0건 수집으로 종료 코드 1 반환 |

## 5. 대표님 사후 확인
- 대표님이 2~4절을 확인한 뒤 `confirmed:`를 적거나 `Workflow/07_문서_서식_및_번호` 「승인 기록」대로 기재하게 한다. 대표님 확인이 독립 판정을 대신한다.
- 커밋 메시지: `fix: [HOTFIX-004] 개발·운영 서브에이전트 무인 실행 권한 참조 추가`
