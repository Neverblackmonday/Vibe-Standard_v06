---
task_id: "001"
classification: "Major" # 안건 분류: Critical, Major, Minor
created: "2026-10-06"
approved: "" # 대표님 직접 승인 시 날짜 및 시각 기재 (예: "2026-10-06T14:30:00+09:00"). 미승인 시 작업/커밋 차단
author:
  agent: "Secretariat"
  model: "3.8 Flash" # 실제 비서실 작성 모델
  thinking: "medium"
workflow:
  # 엔지니어링 라이프사이클에 따라 수행할 부서를 순서대로 기재
  - Design       # 1단계: EC 변경계획서 작성
  - Quality      # 2단계: EC 사전 승인 검토 (1차 게이트)
  - Design       # 3단계: PRD/TAD 명세 구체화 (대표님 검토)
  - Development  # 4단계: 소스코드 및 시험 구현
  - Quality      # 5단계: 최종 삼중 검수 및 RES 발행
scope:
  - Departments/Design/docs/prd/01_개요.md
  - Departments/Development/assets/src/main.py
  - Departments/Development/assets/tests/test_main.py
---

# REQ-001: 안건 제목

## 1. 요청 원문
> 대표님의 최초 지시 원문 또는 핵심 대화 내용을 기록합니다.

## 2. 배경 및 목적
- **배경**: 이 작업을 수행하게 된 배경
- **목적**: 달성하고자 하는 구체적 목표

## 3. 결정 사항 및 선택지
| 정할 일 | 권고안 | 대안 | 결정 |
| :--- | :--- | :--- | :--- |
| 예: 메인 모델 | Claude Opus 5.5 | Claude Sonnet 5.5 | 권고안 |

## 4. 워크플로우 및 부서별 실행 계획
머리말 `workflow:`에 명시된 순서대로 부서 에이전트가 호출되어 실행됩니다.

| 단계 | 담당 부서 (에이전트) | 권고 모델 | 세부 작업 내용 | 작업 대상 경로 |
| :---: | :--- | :---: | :--- | :--- |
| **1단계** | **설계 (Design)** | `Claude Opus 5.5` | REQ 분석 및 엔지니어링 변경 계획서(`EC-xxx.md`) 초안 작성 | `Departments/Design/docs/tad/` |
| **2단계** | **품질 (Quality)** | `Claude Opus 5.5` | EC 적합성 검토 및 사전 승인 판정 (1차 게이트) | `Departments/Quality/results/` |
| **3단계** | **설계 (Design)** | `Claude Opus 5.5` | 승인된 EC 기반 제품 명세(`PRD`) 및 아키텍처(`TAD`) 작성 (대표님 검토) | `Departments/Design/docs/prd/`, `tad/` |
| **4단계** | **개발 (Development)** | `Claude Opus 5.5` | 승인된 EC 및 PRD/TAD 기반 기능 구현 및 단위 테스트 작성 | `Departments/Development/assets/src/`, `tests/` |
| **5단계** | **품질 (Quality)** | `Claude Opus 5.5` | REQ 요구사항 원점 대조, EC 범위 대조, 삼중 최종 검수 및 RES 발행 | `Departments/Quality/results/RES-001.md` |

## 5. 검증 및 완료 기준 (체크리스트)
> 비서실은 1절 「요청 원문」의 요구 항목을 빠짐없이 나누어 번호를 붙이고, 항목마다 확인 기준을 한 줄로 적습니다. 번호는 요청 원문 항목과 1:1로 대응합니다. 품질팀은 최종 판정서(`RES-001.md`)에 번호별 근거를 기재하고, 비서실은 최종 보고 전에 모든 번호에 근거가 있는지 대조합니다.

| 번호 | 요청 원문 항목 | 확인 기준 |
| :---: | :--- | :--- |
| 1 | 예: 요청 원문의 첫째 요구 | 예: `Departments/Development/assets/tests/test_main.py` 실행 결과 전원 통과 |
| 2 | 예: 요청 원문의 둘째 요구 | 예: `Departments/Design/docs/prd/01_개요.md` 해당 절 기재 |

## 6. 작업자 인수인계 및 Claude Code CLI 실행 명령
> 대표님이 승인(`approved: "YYYY-MM-DDTHH:MM:SS+09:00"`)을 기재하면, 비서실은 코드를 직접 수정하지 않고 아래 원스톱 실행 명령 하나를 대표님께 안내합니다. 대표님이 저장소 루트에서 한 번 실행하면 메인 세션이 `workflow:` 순서대로 부서 서브에이전트를 기동합니다. 명령 규격은 `Workflow/05_비서실_클로드cli_인수인계_정책` 「원스톱 실행 명령」을 따르며, `--effort`는 기본 `medium`으로 채우며 `high`는 대표님 승인 시에만 적용합니다.

```bash
claude --model claude-opus-5-5 --effort high --permission-mode acceptEdits "Departments/Secretariat/docs/requests/REQ-001.md 원스톱 파이프라인을 실행하라. Workflow/03의 「원스톱 파이프라인」 절을 따른다."
```
