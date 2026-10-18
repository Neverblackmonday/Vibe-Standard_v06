---
ec_id: "007"
task_id: "007"
created: "YYYY-MM-DD"
author:
  agent: "Design"
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium (실행 명령 기준)" # 실행 명령 지시문의 effort 값과 출처. 얻을 수 없으면 "확인 불가"(Workflow/04_모델_운용 「모델 메타데이터 기록」)
status: "draft" # draft | approved (Workflow/07_문서_서식_및_번호 「머리말」 EC 상태 전이)
gate: "" # approved로 바꿀 때 최신 EC 판정서 경로 (예: Departments/Quality/results/RES-007-EC_v01)
scope:
  # 대상 REQ scope의 부분집합. 폴더는 끝에 / 없이, 기록 문서는 버전 없이 적는다
  - Departments/Design/docs/tad/EC-007
  - Departments/Design/docs/prd/01_개요.md
  - Departments/Development/assets/src/main.py
  - Departments/Development/assets/tests/test_main.py
---

# EC-007: 변경 계획 제목

## 1. 개요
- **관련 안건**: `Departments/Secretariat/docs/requests/REQ-007_v01`
- **EC 판단**: 설계 결과서 「EC 판단」 절 경로와 해당 기준(`Workflow/03_라이프사이클` 「EC 적용 기준」의 항 번호)
- **변경 배경**: REQ 「배경 및 목적」 가운데 이번 변경과 직접 관련된 사실
- **변경 목표**: REQ 목적을 이번 EC가 달성할 결과로 바꾸어 적는다

## 2. 작업 범위
### 2.1 신규 생성 파일
| 번호 | 경로 | 내용 | 담당 단계 |
| :---: | :--- | :--- | :---: |
| 1 | `Departments/Design/docs/prd/01_개요.md` | 제품 개요 PRD | 명세 |

### 2.2 기존 수정 파일
| 번호 | 경로 | 변경 내용 | 담당 단계 |
| :---: | :--- | :--- | :---: |
| 1 | `Departments/Development/assets/src/main.py` | 변경 내용 요약 | 구현 |

### 2.3 범위 제외 항목
- REQ에 언급되었으나 이번 EC에서 다루지 않는 항목과 사유. 없으면 「없음」

## 3. 세부 설계
### 3.1 구조 변경
변경 전후의 폴더 구조, 모듈 관계, 데이터 흐름을 적는다.

### 3.2 단계별 작업
| 단계 | 부서 | 작업 | 산출물 |
| :--- | :--- | :--- | :--- |
| 명세 | 설계 | PRD·TAD 작성 | `Departments/Design/docs/prd/01_개요.md` |
| 인수 시험 | 품질 | 인수 시험 작성과 구현 전 실행 | `Departments/Quality/assets/acceptance/REQ-007_v01/`, `Departments/Quality/results/ACC-007_v01.md` |
| 구현 | 개발 | 구현과 테스트 | `Departments/Development/assets/src/main.py` |

## 4. 위험 분석 및 대응
| 번호 | 위험 | 영향 | 대응 |
| :---: | :--- | :--- | :--- |
| 1 | 위험 내용 | 영향 범위 | 대응 방안 |

## 5. 완료 기준
| 번호 | 기준 | 확인 방법 |
| :---: | :--- | :--- |
| 1 | 단위 테스트 통과 | `python -m pytest Departments/Development/assets/tests` |
| 2 | 인수 시험 통과 | `python -m pytest Departments/Quality/assets/acceptance/REQ-007_v01` |
| 3 | 커밋 전 검사 통과 | `python Departments/Development/assets/scripts/check_standard.py` 종료 코드 0 |
| 4 | REQ 체크리스트 번호별 근거 확보 | 최종 판정서 「체크리스트 대조」 절 |

## 6. 실행하지 못한 명령
> 판정 세션 밖 서브에이전트가 이 문서를 작성하는 단계에서 실행하지 못한 명령과, 권한 확인 요청이 승인되어 실행한 명령을 적는다. 기준과 오케스트레이터의 확인은 `Workflow/03_라이프사이클` 「판정 세션 밖의 명령 실행」을 따른다. 대신하지 못했으면 마지막 칸을 「대신하지 못함」으로 시작하고, 승인되어 실행했으면 「확인 요청 승인 뒤 실행」을 적는다. 없으면 표 대신 「없음」을 적는다.

| 번호 | 명령 원문 | 도구 | 메시지 원문 | 대신한 수단과 그 결과 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `git rev-parse HEAD` | Bash | 메시지 원문 | `git log -1 --format=%H`(Bash) 결과 40자리 해시 |
