---
task_id: "024"
gate: "REQ"
result: "fail"
completed_at: "2026-10-11T01:17:59+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-024: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-024_v01.md` (출처 ORDER `Departments/Secretariat/assets/inbox/ORD-006_v11.md`)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-024_01.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절의 원문 J·K·L, 요구 항목 11, 「REQ에서 정할 사항」의 재작업 항목, 3절 10항이 ORDER 1절 95~120행, 2절 355·378행, 3절 402행과 같다. 「REQ에서 정할 사항」의 다섯 가지(태그를 붙일 기록, 판단 주체, Repair 승인 경로, REQ 없는 문구 변경 경로, 전역 지침 승인과의 관계)가 D1~D5로 모두 올라 있고, 태그 형식은 ORDER대로 EC에 넘겼다. D2 권고안이 대표님 원문의 「기능·품질 영향」 기준을 「승인된 기준 안에서 고칠 수 있는지」로 바꾸지만, 원문 그대로의 기준을 대안 (가)로 함께 올리고 바꾼 이유를 적어 대표님이 정하게 했으므로 왜곡으로 보지 않는다 |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | REQ가 맡는 요구 항목은 11 하나이고 체크리스트도 11 한 행이다. 하위 ①~⑨가 D1~D6과 요구 항목 11의 「별도 RP 문서 없음」을 나눠 확인한다 |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | FAIL | D3 권고안(Repair 결함이 있는 판정서가 나오면 파이프라인을 멈춤)을 반영하면 `Workflow/05_인수인계_및_실행명령` 4절 「진행 상태 보고」 2항(판정이 `fail`일 때 「[부서명]이 수정한 뒤 다시 판정합니다」를 출력)이 Repair `fail`과 어긋나는데, `Workflow/05`가 scope에 없고 4절 표 아래 「scope에 넣지 않는」 목록에도 판단이 없다. 결함 D1. scope의 나머지 경로(`Workflow/01`·`03`, `RES_TEMPLATE.md`, `quality.md`, EC 경로)는 4절 표 아래 사유와 맞고 요구 밖 경로가 없다 |
| ④ | 분류가 정의 기준과 맞고, ORDER 제안과 다르면 사유가 있으며, `workflow:`가 2절과 맞다 | PASS | 2절 「분류 근거」가 Critical(승인 통제의 경계를 정하는 변경, 거버넌스 파일)을 `Workflow/03` 2절 표 Critical 행과 대조해 적었고 ORDER `classification_proposal`(Critical)과 같다. `workflow:`는 EC 판단 → EC 작성 → EC 판정 → 명세 → 명세 판정 → 인수 시험 → 구현 → 최종 판정으로 2절 표 Critical 행과 같다 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | FAIL | 체크리스트 11 ①·④·⑦의 원본 경로 `git status` 확인은 적용본으로만 고치는 거버넌스 파일에 대해 늘 비어 있는 결과를 내므로 요구(D1·D4·「별도 RP 문서 없음」)를 확인하지 못한다. 결함 D2 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 체크리스트 11 ⑧ 뒷부분이 두 뜻으로 읽힌다. 결함 D3 |
| ⑦ | Critical·Major REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 2절 「목적」은 달성할 결과만 적고 문구·서식은 EC(없으면 명세 단계 산출물)로 넘겼다. D1~D6은 ORDER 「REQ에서 정할 사항」이 정하라고 한 정책·범위와 적용 시점이며, D5의 「재작업 규정에 … 적는다」도 담을 내용(정책)만 정하고 문구안은 아니다. 태그 형식은 정하지 않았다. 4절 「작업」 열은 할 일과 산출물 이름만 적었다 |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 5절 머리 안내와 3절 표 아래 둘째 글머리가 D1~D7 권고안을 전제로 쓴 사실과, 권고안이 아닌 결정을 고르면 「결정」 열이 우선한다는 사실을 적었다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| REQ 2절 「현행 표준의 RP」 사실 | Grep `재작업\|Rework\|Repair\|수리`, 범위 `Workflow/**`, `AGENTS.md`, `.claude/**`, `Departments/Development/assets/scripts/**` | 2026-10-11T01:16:21+09:00 이전 | `Workflow\01_표준_개요.md:71:\| 파생 안건 \| 원 안건에서 미결로 남거나 새로 생긴 작업. 번호는 \`REQ-xxx-n\` \| 재작업 절차서(RP), 재의뢰 \|` 한 줄(REQ 기재와 같다) |
| REQ 2절 「판정 결과 건수」 | Grep `^result: "(fail\|rejected)"`, 범위 `Departments/Quality/results` | 같은 때 | `Found 50 files`. 이름별로 EC 판정 17개, 최종 판정 2개(`RES-012_v01.md`, `RES-014_v02.md`), REQ 판정 31개, 명세 판정 없음(REQ 기재와 같다) |
| 서식·검사 스크립트의 결함 목록 참조 | Grep `반려 부서\|결함 목록`, 범위 `Workflow/**`, `.claude/**`, `AGENTS.md`; Grep `결함 목록\|반려 부서\|RES_TEMPLATE`, 범위 `Departments/Development/assets/scripts` | 같은 때 | 전자: `quality.md:25`, `Workflow/04_모델_운용.md:67`, `Workflow/03_라이프사이클.md` 26·76·138·139·140·207·287행, `RES_TEMPLATE.md` 42·43·71행. 후자: 결과 없음 |
| 진행 문구 규정 | Read `Workflow/05_인수인계_및_실행명령.md` 82~88행 | 같은 때 | 82행 `## 4. 진행 상태 보고`, 87행 `2. 판정이 \`fail\`일 때: \`[단계명] 판정에서 결함 N건이 지적되어 [부서명]이 수정한 뒤 다시 판정합니다.\`` |
| 서브에이전트 정의 수 | Glob `.claude/agents/*` | 같은 때 | `marketing.md`, `visual.md`, `design.md`, `quality.md`, `development.md`, `operations.md`(6개. 체크리스트 11 ⑨의 「6개」와 같다) |
| 시각 조회 | `date -Iseconds` (Bash) | 2026-10-11T01:16:21+09:00 | `2026-10-11T01:16:21+09:00` |
| 품질·거버넌스 경로 상태 | `git status --porcelain -uall -- Departments/Quality Workflow AGENTS.md .claude` (PowerShell) | 2026-10-11T01:16:49+09:00 | 출력 없음 |
| 완료 시각 | `Get-Date -Format o` (PowerShell) | 2026-10-11T01:17:59+09:00 | `2026-10-11T01:17:59.9944746+09:00` |

- 처음 시도한 Bash `git -C "D:/Vibe Coding/Vibe Standard_v04" status --porcelain -uall -- Departments/Quality Workflow AGENTS.md .claude`는 실행되지 않았다. 메시지 원문: 「This command requires approval」. 같은 값을 PowerShell의 `git status --porcelain -uall -- Departments/Quality Workflow AGENTS.md .claude`로 대신 얻었다(`Workflow/03_라이프사이클` 「판정 세션의 명령 실행」 3항).
- 부적합 기록 누적 대조를 위해 처음 시도한 Bash 반복 명령(`ls … && for f in …`)은 「A variable in this command can't be checked before it runs」로 실행되지 않았다. 같은 값을 `ls`와 Grep(`^recorded_at|^  - C|^proposals|^causes`, 범위 `Departments/Quality/docs/nonconformance`)으로 대신 얻었다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | REQ 머리말 `scope:`, 4절 표 아래 「scope 경로별 사유」·「scope에 넣지 않는다」 글머리 | D3 권고안은 Repair 결함이 있는 판정서가 나오면 파이프라인을 멈추게 하지만, `Workflow/05_인수인계_및_실행명령` 4절 「진행 상태 보고」 2항은 판정이 `fail`이면 조건 없이 「[부서명]이 수정한 뒤 다시 판정합니다」를 출력하게 정한다. Repair `fail`에서 이 문구를 그대로 쓰면 실제 흐름(중단·대표님 보고)과 다른 진행 문구가 나가고, 고치려면 scope 밖인 `Workflow/05`를 바꿔야 해 원스톱 파이프라인이 「중단 조건」 1항으로 멈출 수 있다. REQ는 `Workflow/05`를 scope에도, 넣지 않는 사유 목록에도 적지 않았다(기준 ③). 고칠 방향: `Workflow/05`를 scope에 넣고 사유(4절 「진행 상태 보고」의 `fail` 문구)를 적거나, 넣지 않는다면 Repair `fail` 때 그 문구를 어떻게 처리하는지 판단과 근거를 4절 표 아래에 적는다 | PM(비서실 폴더 REQ 작성) |
| D2 | REQ 5절 체크리스트 11 ①의 「`git status --porcelain -uall -- Workflow/templates/NCR_TEMPLATE.md Workflow/templates/DEV_TEMPLATE.md` 결과가 비어 있다」, ④의 「`git status --porcelain -uall -- AGENTS.md` 결과가 비어 있고」, ⑦의 「`git status --porcelain -uall -- Workflow/07_문서_서식_및_번호.md` 결과가 비어 있다」 | 세 확인 대상은 모두 거버넌스 파일 원본이다. 거버넌스 파일은 적용본으로만 고치므로(REQ 4절 안내, `Workflow/06_통제장치_및_배포` 「거버넌스 파일 개정 절차」) 원본의 `git status`는 판정 시점에 늘 비어 있고, 설계·개발 적용본 폴더에 `NCR_TEMPLATE.md`·`DEV_TEMPLATE.md`·`AGENTS.md`·`Workflow/07`의 적용본(태그 자리 추가, REQ 없는 문구 변경 경로, 새 문서 종류)이 생겨도 이 확인은 통과한다. 최종 판정 기준 2 「범위 대조」도 부서 `workspace/`를 허용하므로 걸러내지 못한다. 그래서 D1(결과서·부적합 기록에 태그를 붙이지 않음), D4(REQ 없는 문구 변경 경로 없음), 「별도 RP 문서 없음」을 확인하지 못한다. 같은 체크리스트 머리 안내가 정의한 「현행 거버넌스 파일」(적용본이 있으면 적용본)을 ⑦ 앞부분에서는 쓰고 이 세 곳에서는 쓰지 않아 기준도 엇갈린다(기준 ⑤). `REQ-023` REQ 판정 결함 D1(`RES-023-REQ_v01.md`, `NCR-023_01.md`)과 같은 원인이다. 고칠 방향: 세 곳을 「현행 거버넌스 파일 가운데 `NCR_TEMPLATE.md`·`DEV_TEMPLATE.md`(또는 `AGENTS.md`, `Workflow/07`)가 원본과 같다(적용본 폴더에 그 파일의 적용본이 없다)」처럼 적용본을 포함하도록 적고, 원본의 `git status`는 원본을 직접 고치지 않았다는 보조 근거로 둔다 | PM(비서실 폴더 REQ 작성) |
| D3 | REQ 5절 체크리스트 11 ⑧ 「현행 거버넌스 파일에서 Rework·Repair를 「용어」 표의 쓰지 않는 말로 쓴 곳이 없다」 | 이 문장은 (가) Rework·Repair라는 말이 「용어」 표의 「쓰지 않는 말」 열에 올라 있거나 그런 뜻으로 쓰인 곳이 없다는 뜻으로도, (나) 새로 정의할 Rework·Repair 행의 「쓰지 않는 말」(예: 「재작업 절차서(RP)」)을 Rework·Repair 대신 쓴 곳이 없다는 뜻으로도 읽힌다. 현행 「파생 안건」 행의 「쓰지 않는 말」에 「재작업 절차서(RP)」가 있어 두 뜻이 판정 결과를 다르게 만들 수 있다. 또 「용어」 표 자체와 개정 이력 표를 대조에서 빼는지(최종 판정 기준 6)도 적지 않았다(기준 ⑥). 고칠 방향: 확인하려는 상태를 하나로 적는다(예: 「적용본 「용어」 표의 Rework·Repair 행이 정한 쓰지 않는 말을, 「용어」 표와 개정 이력 표를 뺀 현행 거버넌스 파일에서 쓴 곳이 없다」와 「파생 안건」 행의 「재작업 절차서(RP)」 처리를 따로 적는다) | PM(비서실 폴더 REQ 작성) |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
