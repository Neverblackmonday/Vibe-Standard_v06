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
  # "<부서>: <단계명>"을 단계 순서대로 적는다(Workflow/03_라이프사이클 「원스톱 파이프라인」). Minor는 EC 작성·EC 판정이 없다
  - "Design: EC 작성"
  - "Quality: EC 판정"
  - "Design: 명세"
  - "Development: 구현"
  - "Quality: 최종 판정"
scope:
  # 수정을 허용할 경로. 폴더는 끝에 / 없이 적는다. Critical·Major는 EC 경로를 포함한다
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

| 정할 일 | 권고안 | 대안 | 결정 |
| :--- | :--- | :--- | :--- |
| 예: effort | `medium` | `high` | 대표님 직접 기재 또는 `Workflow/07_문서_서식_및_번호` 「승인 기록」 |

## 4. 실행 계획
| 단계 | 부서 | 작업 | 대상 경로 |
| :--- | :--- | :--- | :--- |
| EC 작성 | 설계 | EC 작성 | `Departments/Design/docs/tad/EC-007_v01.md` |
| EC 판정 | 품질 | EC 판정 | `Departments/Quality/results/RES-007-EC_v01.md` |
| 명세 | 설계 | PRD·TAD 작성 | `Departments/Design/docs/prd/01_개요.md` |
| 구현 | 개발 | 구현과 단위 테스트 | `Departments/Development/assets/src/main.py` |
| 최종 판정 | 품질 | 체크리스트 번호별 근거 대조 | `Departments/Quality/results/RES-007_v01.md` |

## 5. 검증 및 완료 기준 (체크리스트)
> 작성 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」을 따른다. 항목마다 확인 방법을 한 줄로 적는다.

| 번호 | 요청 원문 항목 | 확인 방법 |
| :---: | :--- | :--- |
| 1 | 예: 요청 원문 1번 | 예: `python -m pytest Departments/Development/assets/tests` 통과 |
| 2 | 예: 요청 원문 2번 | 예: `Departments/Design/docs/prd/01_개요.md` 「기능 요구사항」 절 기재 |

## 6. 실행 명령
> 명령 형식은 `Workflow/05_인수인계_및_실행명령` 「실행 명령」, effort는 `Workflow/04_모델_운용` 「effort」를 따른다.

```bash
claude --model claude-opus-5-5 --effort medium --permission-mode acceptEdits "Departments/Secretariat/docs/requests/REQ-007_v01.md 원스톱 파이프라인을 실행하라. Workflow/03_라이프사이클.md 「원스톱 파이프라인」 절을 따른다. effort: medium"
```
