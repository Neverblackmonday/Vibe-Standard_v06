---
task_id: "007"
classification: "Major" # Critical | Major | Minor (Workflow/03_라이프사이클 「분류별 단계」)
created: "YYYY-MM-DD"
approved: "" # 대표님 직접 기재 또는 Workflow/07_문서_서식_및_번호 「승인 기록」 절차. 형식 "YYYY-MM-DDTHH:MM:SS+09:00". 비어 있으면 작업·커밋 불가
author:
  agent: "PM"
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium (실행 명령 기준)" # 실행 명령 지시문의 effort 값과 출처. 얻을 수 없으면 "확인 불가"(Workflow/04_모델_운용 「모델 메타데이터 기록」)
workflow:
  # "<부서>: <단계명>"을 단계 순서대로 적는다(Workflow/03_라이프사이클 「원스톱 파이프라인」). 단계는 분류마다 Workflow/03_라이프사이클 「분류별 단계」 표를 따르며, EC 작성·EC 판정·명세 판정과 Minor의 명세는 EC 판단 결과와 관계없이 적는다(실행 여부는 EC 판단으로 정한다. Workflow/03_라이프사이클 「EC 적용 기준」). 실험 단계가 있으면 "<부서>: 실험"을 "Design: EC 판단" 앞에 적는다(Workflow/03_라이프사이클 「실험 단계」). Critical·Major는 "Quality: 명세 판정"과 구현 사이에 "Quality: 인수 시험"을 늘 둔다(Workflow/03_라이프사이클 「시험실」)
  - "Design: EC 판단"
  - "Design: EC 작성"
  - "Quality: EC 판정"
  - "Design: 명세"
  - "Quality: 명세 판정"
  - "Quality: 인수 시험"
  - "Development: 구현"
  - "Quality: 최종 판정"
scope:
  # 수정을 허용할 경로. 폴더는 끝에 / 없이 적는다. 모든 분류에서 EC 경로를 포함한다(EC 판단 결과와 관계없다). 실험 단계가 있으면 실험 폴더 Lab/<REQ 번호>_<주제>를 포함한다
  - Departments/Design/docs/tad/EC-007
  - Departments/Design/docs/prd/01_개요.md
  - Departments/Development/assets/src/main.py
  - Departments/Development/assets/tests/test_main.py
---

# REQ-007: 안건 제목

> 파일명은 `REQ-<번호>_v<버전>.md`, 파생 안건은 `REQ-<번호>-<파생 번호>_v<버전>.md`다(`Workflow/07_문서_서식_및_번호` 「번호와 버전」). 이 안내문은 작성할 때 지운다.

## 1. 요청 원문
> ORDER(`Departments/Secretariat/assets/inbox/ORD-<번호>_v<버전>.md`)를 출처로 밝히고, 지시 원문과 이 REQ가 맡는 요구 항목을 ORDER의 번호 그대로 원형 인용한다. 5절 체크리스트는 이 요구 항목 번호와 1:1로 대응한다.

## 2. 배경 및 목적
- **배경**: 이 작업이 필요한 사실
- **목적**: 달성할 결과

## 3. 결정 사항 및 선택지
> 정할 일의 작성 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 1항을 따른다.
> 번호는 `D1`부터 붙이며 승인 문구의 D번호(`Workflow/07_문서_서식_및_번호` 「승인 기록」 2항)와 같다.

| 번호 | 정할 일 | 권고안 | 대안 | 결정 |
| :---: | :--- | :--- | :--- | :--- |
| D1 | 예: effort | `medium` | `high` | 대표님 직접 기재 또는 `Workflow/07_문서_서식_및_번호` 「승인 기록」 |

## 4. 실행 계획
> 실험 단계가 있으면 표 첫 행에 실험 단계(부서, 실험 목적, 대상 `Lab/` 경로)를 적는다. EC 작성·EC 판정·명세 판정 행은 EC 판단에 따라 실행하거나 건너뛰는 단계이며, 대상 경로는 실행할 때의 경로다(`Workflow/03_라이프사이클` 「EC 적용 기준」).

| 단계 | 부서 | 작업 | 대상 경로 |
| :--- | :--- | :--- | :--- |
| EC 판단 | 설계 | EC 필요 여부 판단과 기록 | `Departments/Design/results/RPT-007_v01.md` |
| EC 작성 | 설계 | EC 작성 | `Departments/Design/docs/tad/EC-007_v01.md` |
| EC 판정 | 품질 | EC 판정 | `Departments/Quality/results/RES-007-EC_v01.md` |
| 명세 | 설계 | PRD·TAD 작성 | `Departments/Design/docs/prd/01_개요.md` |
| 명세 판정 | 품질 | 명세 판정 | `Departments/Quality/results/RES-007-SPEC_v01.md` |
| 인수 시험 | 품질 | 인수 시험 작성과 구현 전 실행 | `Departments/Quality/assets/acceptance/REQ-007_v01/`, `Departments/Quality/results/ACC-007_v01.md` |
| 구현 | 개발 | 구현과 단위 테스트 | `Departments/Development/assets/src/main.py` |
| 최종 판정 | 품질 | 체크리스트 번호별 근거 대조 | `Departments/Quality/results/RES-007_v01.md` |

## 5. 검증 및 완료 기준 (체크리스트)
> 작성 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」을 따른다. 항목마다 확인 방법을 한 줄로 적는다. 확인 방법이 명령·시험의 실행 결과인 항목은 Critical·Major에서 인수 시험의 대상이 된다(`Workflow/03_라이프사이클` 「시험실」).

| 번호 | 요청 원문 항목 | 확인 방법 |
| :---: | :--- | :--- |
| 1 | 예: 요청 원문 1번 | 예: `python -m pytest Departments/Development/assets/tests` 통과 |
| 2 | 예: 요청 원문 2번 | 예: `Departments/Design/docs/prd/01_개요.md` 「기능 요구사항」 절 기재 |

## 6. 실행 명령
> 명령 형식은 `Workflow/05_인수인계_및_실행명령` 「실행 명령」, effort는 `Workflow/04_모델_운용` 「effort」를 따른다.

```bash
claude --model claude-opus-5-5 --effort medium --permission-mode acceptEdits "Departments/Secretariat/docs/requests/REQ-007_v01.md 원스톱 파이프라인을 실행하라. Workflow/03_라이프사이클.md 「원스톱 파이프라인」 절을 따른다. effort: medium"
```
