---
task_id: "007"
created: "YYYY-MM-DD"
author:
  agent: "Development"
  model: "Claude Opus 5.5" # 실제 실행 모델
  effort: "medium (실행 명령 기준)" # 실행 명령 지시문의 effort 값과 출처. 얻을 수 없으면 "확인 불가"(Workflow/04_모델_운용 「모델 메타데이터 기록」)
---

# DEV-007: 개발부 결과서

## 1. 입력 문서
- REQ: `Departments/Secretariat/docs/requests/REQ-007_v01.md`
- EC: `Departments/Design/docs/tad/EC-007_v01.md` (EC가 없으면 「해당 없음」. EC의 유무는 `Workflow/03_라이프사이클` 「EC 적용 기준」 첫 문단)
- 명세: 참조한 PRD·TAD 경로
- 설계부 결과서: `Departments/Design/results/RPT-007_vNN.md`(「EC 판단」 절. EC가 없는 Critical·Major이면 「구현 계획」 절 포함). 설계부 결과서 자신이면 「해당 없음」
- 시각 디자인 문서: 입력으로 쓴 시각 디자인 문서 경로와 근거(그 안건의 시각 디자인 판정서 경로, 또는 HEAD 커밋 해시. `Workflow/03_라이프사이클` 「시각 디자인 단계」). 쓰지 않았으면 「해당 없음」

## 2. 변경 파일
| 번호 | 경로 | 변경 내용 | 근거(EC 절 또는 REQ 체크리스트 번호) |
| :---: | :--- | :--- | :--- |
| 1 | `Departments/Development/assets/src/main.py` | 변경 요지 | EC 2.2절 1번 |

## 3. 검증 결과
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 단위 테스트 | `python -m pytest Departments/Development/assets/tests` | YYYY-MM-DDTHH:MM:SS+09:00 | 실행 결과 원문 |
| 인수 시험(인수 시험 단계가 있으면) | `python -m pytest Departments/Quality/assets/acceptance/REQ-007_v01` | YYYY-MM-DDTHH:MM:SS+09:00 | 실행 결과 원문 |
| 커밋 전 검사 | `python Departments/Development/assets/scripts/check_standard.py` | YYYY-MM-DDTHH:MM:SS+09:00 | 실행 결과 원문 |

## 4. 적용본 (거버넌스 파일을 바꾼 경우만)
| 적용본 경로 | 원본 경로 | 반영 명령 |
| :--- | :--- | :--- |
| `Departments/Development/workspace/REQ-007_적용본_v01/...` | 원본 경로 | 복사 명령 |

## 5. 확인하지 못한 항목
- 없으면 「없음」. 있으면 항목과 사유를 「확인 불가」로 적는다.

**실행하지 못한 명령**

> 판정 세션 밖 서브에이전트가 이 문서를 작성하는 단계에서 실행하지 못한 명령과, 권한 확인 요청이 승인되어 실행한 명령을 적는다. 기준과 오케스트레이터의 확인은 `Workflow/03_라이프사이클` 「판정 세션 밖의 명령 실행」을 따른다. 대신하지 못했으면 마지막 칸을 「대신하지 못함」으로 시작하고, 승인되어 실행했으면 「확인 요청 승인 뒤 실행」을 적는다. 없으면 표 대신 「없음」을 적는다.

| 번호 | 명령 원문 | 도구 | 메시지 원문 | 대신한 수단과 그 결과 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | `git rev-parse HEAD` | Bash | 메시지 원문 | `git log -1 --format=%H`(Bash) 결과 40자리 해시 |

## 6. 실험 결과 (실험 단계를 맡은 경우만)
> 뒤 단계에서 이 결과서의 다음 버전을 쓰면 이 절을 그대로 옮긴다(`Workflow/03_라이프사이클` 「실험 단계」).

- **실험 목적**:
- **`Lab/` 경로**: `Lab/REQ-007_<주제>`
- **요지**:
- **정규 경로로 복사·이동하지 않았다는 확인**:

## 7. 인수 시험 결함 보고 (있는 경우만)
> 인수 시험을 고치지 않고 이 절에 적어 PM에 보고한다(`Workflow/03_라이프사이클` 「시험실」).

| 번호 | 시험(파일·함수) | 결함으로 본 사유 | 체크리스트 번호 |
| :---: | :--- | :--- | :---: |
| 1 | `Departments/Quality/assets/acceptance/REQ-007_v01/test_req007.py::test_c1_<요지>` | 사유 | 1 |

## 8. EC 판단 (설계부 결과서만)
> 기준과 기록 규칙은 `Workflow/03_라이프사이클` 「EC 적용 기준」을 따른다. 같은 안건에서 이 결과서의 다음 버전을 쓰면 이 절을 그대로 옮긴다. 판단을 바꾸면 바꾼 판단과 근거 판정서 경로를 적는다.

| 항목 | 기재 |
| :--- | :--- |
| 판단 | EC 있음 / EC 없음 |
| 해당 기준 | 「EC 적용 기준」 2·3·4항 가운데 해당하는 항(4항은 ①~③ 번호까지) |
| 사유 | 바꾸거나 만드는 산출물의 경로와, 그 동작·규칙·규격이 바뀌는지 |
| 명세 산출물 | Minor이고 EC 없음이면 「필요」 또는 「필요 없음」과 사유. 그 밖은 「해당 없음」 |
| 실험 결과 인용 | 실험 단계가 있고 EC 없음이면 실험 결과서 경로와 6절 요지. 그 밖은 「해당 없음」 |
| 판단 변경 | 판단을 바꾸었으면 이전 판단과 근거 판정서 경로. 아니면 「해당 없음」 |

## 9. 구현 계획 (EC가 없는 Critical·Major의 설계부 결과서만)
> 구현 방법은 이 절과 명세 산출물이 정한다(`Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 1항). 명세 판정이 이 절을 판정한다.

| 번호 | 구현 단계 작업 | 대상 경로 | 완료 기준 | 확인 방법 |
| :---: | :--- | :--- | :--- | :--- |
| 1 | 작업 내용 | `Departments/Development/assets/src/main.py` | 기준 | `python -m pytest Departments/Development/assets/tests` |
