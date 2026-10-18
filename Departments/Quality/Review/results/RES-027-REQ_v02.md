---
task_id: "027"
gate: "REQ"
result: "fail"
completed_at: "2026-10-12T00:11:47+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-027-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-027_v02.md`(출처 ORDER `Departments/Secretariat/assets/inbox/ORD-006_v12.md`). 판정 범위는 `git diff --no-index Departments/Secretariat/docs/requests/REQ-027_v01.md Departments/Secretariat/docs/requests/REQ-027_v02.md`의 변경분이다
- **판정 차수**: 재판정 1차(직전 판정서 `Departments/Quality/results/RES-027-REQ_v01.md`)
- **부적합 기록**: 해당 없음

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다. 변경분이 닿지 않는 기준은 직전 판정 결과를 유지한다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | 변경분이 1절 요청 원문 인용과 요구 항목을 바꾸지 않았다(diff에서 1절의 변경은 「이전 버전과의 관계」 항목 추가뿐). 직전 판정 결과 유지 |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 5절은 여전히 번호 6 한 행이다. ⑦에 D7 확인이 늘었을 뿐 대응 관계는 같다 |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | FAIL | 직전 결함 D1은 해소됐다. 직전 판정서가 든 경로(`Workflow/05` 1.1절 6번 ①(36행), `RES_TEMPLATE.md` 3·14행, `REQ_TEMPLATE.md` 12행, `.claude/agents/quality.md` 3행)와 `Workflow/06` 1절 표 계층 4(13행)·5절 4항(103행), `ACC_TEMPLATE.md` 19행이 scope에 들어갔고, 4절 표 아래 사유의 위치가 실제 파일 내용과 맞다(4절 검증 기록). `Workflow/04`를 뺀 사유(33행 「EC 판정·명세 판정·인수 시험 등」으로 묶어 빠짐없이 열거하지 않음)도 실제와 맞다. 다만 D8의 다른 절반(개발의 구현 입력)을 덮지 못한다. 결함 D1 |
| ④ | 분류가 2절 정의 기준과 맞고, ORDER 제안과 다르면 사유가 있으며, `workflow:`가 2절과 맞다 | PASS | 머리말 `classification:`·`workflow:`에 변경 없음. 직전 판정 결과 유지 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | PASS | 체크리스트 ⑦의 새 확인 두 가지가 `git status --porcelain -uall -- Workflow/templates`(`??` 줄 유무), `git status --porcelain -uall -- Departments/Marketing`(`DESIGN.md` 유무)로 실행해 확인할 수 있다. `Workflow/templates`의 확인을 「결과 없음」에서 「`??` 줄이 없음」으로 바꾼 것은 1절 변경 목록에 따로 적히지 않았으나, 서식 세 개가 scope에 들어간 뒤에도 「이 REQ로 생긴 파일이 없다」를 그대로 확인하는 형태이므로 뜻이 바뀌지 않는다 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | PASS | 직전 결함 D2 해소. D7 권고안에 「이 REQ는 표준에 이름·위치·작성 부서 규정만 두고 `DESIGN.md` 파일은 만들지 않는다. 파일은 시각 디자인 문서를 처음 만드는 안건이 만든다」가 들어갔고, 4절 `Departments/Marketing` 사유에서 D7이 빠져(「D3의 폴더 정리」) 같은 뜻이며, 체크리스트 ⑦이 파일 없음을 확인한다. 새로 들어간 4절 표 아래 문장(「EC가 정한 형태에 따라 고칠 곳이 없는 파일은 고치지 않는다」)도 한 가지로 읽힌다 |
| ⑦ | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 변경분의 4절 「명세」·「구현」 행은 대상 파일과 「반영 계획이 정한 파일」만 적고 반영 문구는 EC에 넘겼다 |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 새 scope 문단이 D8의 판정 형태 선택(EC 결정)과 관계없이 덮도록 쓰였다. 체크리스트 머리 안내의 권고안 전제 문장은 그대로다 |

**문체 지적 반영 대조**: 직전 S1은 5절 체크리스트 ③ 첫 문장이 수정 문안과 글자 그대로 같다(diff 확인). 결함 재판정 대상에서 뺐다(`Workflow/03_라이프사이클` 「판정 지적의 구분과 문체 지적 처리」 6항).

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 변경분 | `git diff --no-index Departments/Secretariat/docs/requests/REQ-027_v01.md Departments/Secretariat/docs/requests/REQ-027_v02.md` | 2026-10-12T00:11 전후(완료 시각 조회 이전) | 머리말 `scope:` 6줄 추가, 1절 「이전 버전과의 관계」 추가, 3절 D7 행, 4절 「명세」·「구현」 행과 표 아래 사유 문단(둘째 항목을 두 항목으로 교체), 5절 ③·⑦, 6절 REQ 경로. LF→CRLF 경고 2줄 |
| 판정 종류 열거 위치 | Grep `SPEC\|gate\|명세 판정\|EC 판정`(`Departments/Development/assets/scripts`, `.githooks`, `.claude`, `Workflow/templates`, `Workflow/04`·`05`·`06`) | 같은 시점 | `quality.md:3·14`, `RES_TEMPLATE.md:3·14·60`, `REQ_TEMPLATE.md:12·15·17·51·57·59`, `EC_TEMPLATE.md:10`, `DEV_TEMPLATE.md:74`, `ACC_TEMPLATE.md:19`, `06:61·103`, `05:36`, `04:33`. 스크립트·훅에는 없음 |
| 스크립트·훅의 판정 이름 검사 | `git grep -n -E "SPEC\|RES-\|gate" cafc8d9 -- Departments/Development/assets/scripts .githooks .claude` | 같은 시점 | 출력 없음 |
| 위치 확인 | Read `Workflow/05` 28~37행, Grep `Workflow/06` 제목·계층 4 | 같은 시점 | `05` 36행이 1.1절 6번 ①의 RES 열거, `06` 13행이 계층 4 「REQ·EC·명세·최종 판정」, 103행이 5절 4항 |
| 선례(명세 판정 신설)의 변경 파일 | `git log --oneline --grep=REQ-021`, `git show --stat --format=%s 97262f3` | 같은 시점 | `Workflow/01`~`07`, `templates/ACC`·`DEV`·`EC`·`REQ`·`RES_TEMPLATE.md`, `.claude/agents/design.md`·`development.md`·`quality.md` 변경 |
| 개발 입력 열거 위치 | Read `Workflow/templates/DEV_TEMPLATE.md` 1~22행, Grep `입력\|명세 산출물\|판정서`(`Workflow/templates`), Grep `PRD`(서식, `Workflow/04`, `development.md`·`operations.md`) | 같은 시점 | `DEV_TEMPLATE.md` 12~16행 「1. 입력 문서」: REQ, EC, 「명세: 참조한 PRD·TAD 경로」, 설계 결과서. 시각 디자인 문서 자리 없음. `EC_TEMPLATE.md` 48행·`REQ_TEMPLATE.md` 58행은 단계 예시 |
| 기준 커밋 | `git log -1 --format=%H` | 2026-10-12T00:11:38+09:00 | `cafc8d9f02a98228764f302c7eb724b7e0b5f995` |
| 기존 판정서 확인 | `ls Departments/Quality/results/ \| grep "RES-027"` | 2026-10-12T00:11:38+09:00 | `RES-027-REQ_v01.md` |
| 완료 시각 조회 | `date -Iseconds` | 2026-10-12T00:11:47+09:00 | `2026-10-12T00:11:47+09:00` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> REQ 판정의 결함이므로 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」 1항에 따라 「해당 없음」이다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | REQ 머리말 `scope:`, 4절 표 아래 둘째·셋째 항목(새 scope 문단과 「그 밖의 서식(`Workflow/templates/`)도 같은 이유로 넣지 않으며」), 3절 D8 | scope가 D8 권고안의 「판정 `pass`를 받은 문서는 … 개발이 구현할 때 입력으로 쓴다」를 덮지 못한다. 이 입력 관계는 판정 형태(EC 결정)와 관계없이 권고안 자체가 정한 것인데, 개발의 입력 문서를 빠짐없이 열거한 `Workflow/templates/DEV_TEMPLATE.md` 1절 「입력 문서」(12~16행: REQ, EC, 「명세: 참조한 PRD·TAD 경로」, 설계 결과서)에는 시각 디자인 문서와 그 판정서를 적을 자리가 없고, 이 파일은 scope 밖이다. v02가 새로 쓴 제외 사유는 「판정 종류나 판정 입력을 열거한 파일」만 따졌고 구현 입력을 열거한 파일을 따지지 않았다. 입력이 바뀐 선례인 `REQ-021`(커밋 `97262f3`)도 `DEV_TEMPLATE.md`를 고쳤다. 이대로면 EC가 개발 결과서 서식에 시각 디자인 문서 입력을 넣기로 할 때 `Workflow/03` 「중단 조건」 1항으로 멈추거나, `Workflow/03` 5절 표 「구현」 행(체크리스트 ⑧)과 개발 결과서 서식의 입력 목록이 어긋난 채 남는다. 고치는 방법은 둘 가운데 하나다. (가) `Workflow/templates/DEV_TEMPLATE.md`를 scope에 넣고 4절 사유(D8의 구현 입력)와 4절 「명세」 행의 적용본 대상을 맞춘다 (나) 서식을 고치지 않는 이유(예: 입력의 원천은 `Workflow/03` 5절 표이고 서식의 「명세」 줄이 시각 디자인 문서를 덮는다는 판단)를 4절 제외 사유에 밝힌다 | 해당 없음 | 비서실(PM) |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
