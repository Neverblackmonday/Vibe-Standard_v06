---
task_id: "007"
created: "YYYY-MM-DD"
author:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium (실행 명령 기준)" # 실행 명령 지시문의 effort 값과 출처. 얻을 수 없으면 "확인 불가"(Workflow/04_모델_운용 「모델 메타데이터 기록」)
test_dir: "Departments/Quality/assets/acceptance/REQ-007_v01" # 이 ACC가 기록하는 인수 시험 폴더. 시험을 바꾸지 않은 수정 버전은 직전 ACC와 같은 폴더. 「대상 없음」이면 ""
has_tests: "yes" # yes | no
---

# ACC-007: 인수 시험 절차서

> 파일명은 `ACC-<번호>_v<버전>.md`이고 위치는 `Departments/Quality/results/`다(`Workflow/07_문서_서식_및_번호` 「문서 체계」). 작성 기준은 `Workflow/03_라이프사이클` 「시험실」을 따른다. 이 안내문은 작성할 때 지운다.

## 1. 입력 문서
- REQ: `Departments/Secretariat/docs/requests/REQ-007_v01.md`
- EC: `Departments/Design/docs/tad/EC-007_v01.md` (EC가 없으면 「해당 없음」. EC의 유무는 `Workflow/03_라이프사이클` 「EC 적용 기준」 첫 문단)
- 명세 판정서: `Departments/Quality/results/RES-007-SPEC_vNN.md` (명세 판정이 없으면 「해당 없음」)
- 시각 디자인 판정서: `Departments/Quality/results/RES-007-DESIGN_vNN.md` (시각 디자인 판정이 없으면 「해당 없음」)
- 명세 결과서: `Departments/Design/results/RPT-007_v01.md`
- 수정 버전이면 직전 ACC와 개발의 결함 보고(DEV 7절) 경로. 최초 작성이면 「해당 없음」

## 2. 체크리스트 항목 분류
| 체크리스트 번호 | 요청 원문 항목 | 확인 구분(실행·열람·혼합) | 시험 함수 | 근거(확인 방법 문구) |
| :---: | :--- | :---: | :--- | :--- |
| 1 | 요청 원문 1번 | 실행 | `test_c1_<요지>` | 확인 방법 문구 |
| 2 | 요청 원문 2번 | 열람 | — | 확인 방법 문구 |

## 3. 시험 파일
> 해시는 `git diff --no-index --full-index /dev/null <파일>` 출력의 `index` 줄에서 `..` 뒤의 값이다. 최종 판정이 같은 명령으로 대조한다.

| 경로 | 해시 |
| :--- | :--- |
| `Departments/Quality/assets/acceptance/REQ-007_v01/test_req007.py` | 40자리 해시 |

## 4. 구현 전 실행
> 수정 버전이면 제목을 「수정 시점의 실행」으로 바꿔 적는다.

| 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- |
| `python -m pytest Departments/Quality/assets/acceptance/REQ-007_v01` | YYYY-MM-DDTHH:MM:SS+09:00 | 결과 원문 |

**구현 전에 통과한 시험과 사유**
- 없으면 「없음」. 있으면 시험 함수마다 구현 전에 통과한 사유를 적는다.

## 5. 대상 없음 사유 (`has_tests: "no"`일 때만)
- 실행으로 확인하는 체크리스트 항목이 없다고 본 사유

## 6. 수정 판단 (수정 버전만)
| 결함 보고 번호(DEV 7절) | 결함 여부 | 사유 | 바꾼 시험 |
| :---: | :---: | :--- | :--- |
| 1 | 결함 / 결함 아님 | 사유 | 바꾼 시험 함수. 바꾸지 않았으면 「없음」(이때 `test_dir`은 직전 폴더를 그대로 둔다) |

## 7. 실행하지 못한 명령
> 판정 세션 밖 서브에이전트가 이 문서를 작성하는 단계에서 실행하지 못한 명령과, 권한 확인 요청이 승인되어 실행한 명령을 적는다. 기준과 오케스트레이터의 확인은 `Workflow/03_라이프사이클` 「판정 세션 밖의 명령 실행」을 따른다. 대신하지 못했으면 마지막 칸을 「대신하지 못함」으로 시작하고, 승인되어 실행했으면 「확인 요청 승인 뒤 실행」을 적는다. 없으면 표 대신 「없음」을 적는다.

| 번호 | 명령 원문 | 도구 | 메시지 원문 | 대신한 수단과 그 결과 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `git rev-parse HEAD` | Bash | 메시지 원문 | `git log -1 --format=%H`(Bash) 결과 40자리 해시 |
