---
task_id: "021"
gate: "REQ"
result: "fail"
completed_at: "2026-10-10T10:37:26+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-021-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-021_v01.md`(입력 ORDER `Departments/Secretariat/assets/inbox/ORD-006_v11.md`)
- **판정 차수**: 1차(최초 판정)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-021_01.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 3절 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절의 원문 D·E·I·J, 요구 항목 2, 「REQ에서 정할 사항」 세 항목, 3절 1·6·7항을 ORDER 1절(32~101행), 2절 2항(343행), 「REQ에서 정할 사항」(363·372·373행), 3절(390·395·396행)과 대조했고 원형과 같다(원문 J의 「기존의  설계나」 두 칸 공백 포함). 요구 항목 2의 요소(모든 분류의 설계 단계, 콘텐츠의 설계 선행, 핫픽스 예외, EC 정의, 설계의 EC 판단, 분류와 EC 분리)는 D1·D2·D3·D4와 체크리스트 2의 ①~⑤가 덮는다. 「REQ에서 정할 사항」 세 항목은 D1~D7이 덮는다 |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 이 REQ가 맡는 요구 항목은 2 하나이고, 5절 체크리스트도 번호 2 한 행이다 |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | FAIL | 결함 D1(5절). D6 권고안이 더하는 판정(EC가 없는 Critical·Major 안건의 명세 판정)의 판정서를 커밋 대상으로 열거하는 `Workflow/05_인수인계_및_실행명령` 1.1절 6번 ①이 scope 밖이다. 요구 밖 경로는 없다(scope 경로별 사유가 4절 표 아래에 있고, 각 경로에서 EC·분류 기술을 Grep으로 확인함) |
| ④ | 분류와 `workflow:`가 2절과 맞다 | PASS | `classification: "Critical"`. scope에 거버넌스 파일(`Workflow/`, `.claude/agents/`)이 있어 `Workflow/03` 2절 Critical 적용 대상과 맞다. `workflow:`는 EC 작성 → EC 판정 → 명세 → 인수 시험 → 구현 → 최종 판정으로 2절 Critical 단계와 같다(실험 단계 없음). REQ 3절 표 아래에 이 REQ 자체는 현행 규정으로 진행한다고 적었다 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | PASS | 체크리스트 2의 ①~⑨는 적용본·결과서의 열람과, 개발 결과서에 적을 검색 명령 결과(②)로 확인한다 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | PASS | 결함 수준의 중의성은 없다. 체크리스트 2 ⑥의 「⑦의 판정」 표기는 문체 지적 S2로 적었다 |
| ⑦ | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 2절 「목적」은 달성할 결과만 적고 문구·위치·서식 변경 내용은 EC에 넘긴다. 3절 D1~D8은 정책·범위·완료 기준·effort의 선택이며, 기록 위치·형식(D5), REQ 기재 방식(D2), 판정 기준 문구와 판정서 구분(D6)은 EC에 넘긴다. 4절 「작업」 열은 할 일과 산출물 이름만 적었다. D6의 「「EC 또는 이 명세가 구현 방법을 정한다」로 맞춘다」는 정할 내용의 요지로 읽었고, 문구안으로 오독되지 않게 문체 지적 S1로 적었다 |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 체크리스트와 실행 계획은 D1~D8 권고안을 전제로 쓰고, 그 전제를 3절 표 아래 둘째 항목과 5절 머리 안내에 적었다 |

**2절 「배경」 사실 확인**(2026-10-10 조회)
- `Workflow/03` 2절 표 33~35행, 3절 1항 46행, 2항 ⑦(61행), 5절 표 「명세」 행 입력(81행), 11.2절 3항(213행): REQ 기재와 같다.
- `Workflow/templates/REQ_TEMPLATE.md` 11·19행, `Workflow/07` 12행(EC 「엔지니어링 변경 계획서」)·70행(REQ `scope` 「Critical·Major는 `Departments/Design/docs/tad/EC-xxx` 포함」), `.claude/agents/development.md` 13행: REQ 기재와 같다.
- `Workflow/01_표준_개요` 「용어」 표: EC 관련 행은 62행 「EC 판정」뿐이다.
- `check_standard.py`: 「RES」·「gate」·「-EC」 검색 결과는 76·160행의 `RECORD_NAME`(REQ·HOTFIX 파일명) 뿐이며 분류·EC를 검사하는 로직은 없다.
- 최신 커밋 `ee95f5a`(아래 검증 기록).

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 시각 조회 | Bash `date "+%Y-%m-%dT%H:%M:%S%z"` | 2026-10-10T10:37:08+09:00 | `2026-10-10T10:37:08+0900` |
| 최신 커밋 | Bash `git log -1 --format=%h` | 2026-10-10T10:37:08+09:00 이후 | `ee95f5a` |
| 실행하지 못한 명령(대신함) | Bash `cd "/d/Vibe Coding/Vibe Standard_v04" && git log -1 --format=%h && ...`, Bash `git -C "D:/Vibe Coding/Vibe Standard_v04" log -1 --format=%h` | 2026-10-10T10:37:08+09:00 이후 | 실행되지 않음. 메시지 원문: 「This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.」, 「This command requires approval」. 대신 위 행의 `git log -1 --format=%h`(작업 디렉터리에서 실행)로 같은 값을 얻었다(`Workflow/03` 5.2절 3항) |
| scope 대조 | Grep `EC` (`Workflow/0[1256]*.md`, `Workflow/04*.md`, `Workflow/templates/ACC_TEMPLATE.md`, `.claude/agents/*.md`) | 2026-10-10T10:37:08+09:00 이전 | `Workflow/05_인수인계_및_실행명령.md:36` 「… REQ, EC, DEV, RPT, RES(REQ 판정, EC 판정, 최종 판정), ACC, NCR. …」 외 `Workflow/05`는 41·56·236행(REQ·EC `scope:`, PM 지시문, 개정 이력) |
| scope 대조 | Grep `Minor\|Critical·Major\|Critical\|Major` (기록 문서 폴더 제외) | 2026-10-10T10:37:08+09:00 이전 | `Workflow/07`, `Workflow/03`, `.claude/agents/development.md`, `DEV_TEMPLATE.md`, `REQ_TEMPLATE.md`, `ORDER_TEMPLATE.md`. `ORDER_TEMPLATE.md`는 5행 `classification_proposal` 주석뿐이며 EC와 묶인 기술이 없다 |
| 판정 완료 시각 | Bash `date "+%Y-%m-%dT%H:%M:%S%z"` | 2026-10-10T10:37:26+09:00 | `2026-10-10T10:37:26+0900` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | REQ 머리말 `scope:`, 4절 표 아래 셋째 항목 | D6 권고안은 EC가 없는 Critical·Major 안건에 품질의 명세 판정을 새로 두고, 체크리스트 2 ⑦은 `Workflow/07`의 판정서 구분과 `RES_TEMPLATE.md`의 `gate:`가 이 판정과 맞을 것을 요구한다. 그런데 최종 판정서 승인 뒤 커밋에 넣을 판정서를 「RES(REQ 판정, EC 판정, 최종 판정)」로 열거하는 `Workflow/05_인수인계_및_실행명령` 1.1절 6번 ①(36행)이 scope에 없다. 4절은 `Workflow/05`를 「EC를 분류와 묶어 적은 곳이 없다」는 이유로 뺐으나, D6의 판정 추가가 이 열거에 미치는 영향은 따지지 않았다. 이대로 진행하면 ① 명세 판정의 판정서가 커밋 대상 열거에서 빠져 안건 커밋에 들어가지 않을 수 있고(추적성), ② 구현 단계 대조에서 이 어긋남이 드러나면 「중단 조건」 1항으로 파이프라인이 멈춘다. 기준 ③(scope가 요구를 모두 덮음) 미충족. 처리 방향: `Workflow/05_인수인계_및_실행명령.md`를 scope에 넣고 사유를 적거나, 넣지 않는다면 D6의 판정서가 1.1절 6번 ①의 열거를 바꾸지 않아도 되는 근거를 REQ에 적는다 | PM |

## 6. 문체 지적
| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | REQ 3절 D6 권고안 끝 문장 | REQ 작성 기준(Critical·Major REQ는 구현 방법을 정하지 않음)과 REQ 판정 기준 ⑦은 「EC 또는 이 명세가 구현 방법을 정한다」로 맞춘다. | REQ 작성 기준(Critical·Major REQ는 구현 방법을 정하지 않음)과 REQ 판정 기준 ⑦은 EC 또는 이 명세가 구현 방법을 정한다는 내용으로 맞춘다(문구는 EC에서 정한다). | PM |
| S2 | REQ 5절 체크리스트 2 ⑥ | EC를 붙이지 않은 판단을 대조하는 판정(Critical·Major는 ⑦의 판정, Minor는 최종 판정) | EC를 붙이지 않은 판단을 대조하는 판정(Critical·Major는 이 항목 ⑦의 명세 판정(D6), Minor는 최종 판정) | PM |

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
