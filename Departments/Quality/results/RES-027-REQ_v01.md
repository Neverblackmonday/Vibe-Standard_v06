---
task_id: "027"
gate: "REQ"
result: "fail"
completed_at: "2026-10-12T00:07:23+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-027-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-027_v01.md`(출처 ORDER `Departments/Secretariat/assets/inbox/ORD-006_v12.md`)
- **판정 차수**: 1차
- **부적합 기록**: 해당 없음

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절의 원문 B·C·D·U, 요구 항목 6, 「REQ에서 정할 사항」 네 항목이 ORDER 1절(46~68행, 243~251행), 2절 6항(370행), 「REQ에서 정할 사항」(383~386행)과 글자 그대로 같다. 요구 항목 6의 물음(선택 부서 체계, 파트, 비주얼 통합과 담당, 정의 파일·`name:`·서브에이전트 열, 부서 폴더·이름과 기존 기록 경로, 시각 디자인 문서의 이름·위치·작성 부서, 판정 단계와 입력 방식)이 D1~D8에 하나씩 대응한다. 2절 「배경」의 사실을 다시 조회해 확인했다(4절 검증 기록) |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 이 REQ가 맡는 요구 항목은 6 하나이고 5절 체크리스트도 번호 6 한 행이다. 하위 확인 ①~⑨는 D1~D9, ⑩은 개정 규칙 대조다 |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | FAIL | 결함 D1. 요구 밖 경로는 없다(4절 아래 「scope 경로별 사유」의 경로마다 D 번호가 있음) |
| ④ | 분류가 2절 정의 기준과 맞고, ORDER 제안과 다르면 사유가 있으며, `workflow:`가 2절과 맞다 | PASS | `classification: "Critical"`. 거버넌스 파일과 서브에이전트 정의를 바꾸며, 설계 서브에이전트 이름이 어긋나면 모든 안건의 EC 판단 단계를 기동하지 못한다는 근거(2절 「분류 근거」)가 `Workflow/03` 2절 표 Critical 행과 맞다. ORDER `classification_proposal: "Critical"`과 같다. `workflow:`가 Critical 단계(EC 판단 → EC 작성 → EC 판정 → 명세 → 명세 판정 → 인수 시험 → 구현 → 최종 판정)와 같다 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | PASS | 체크리스트 ①~⑩이 Grep, `git status --porcelain -uall -- <경로>`, 열람 위치(현행 거버넌스 파일, 개발 결과서)를 지정한다. 「현행 거버넌스 파일」, 「적용본이 없다」, 「규정이 있다」의 뜻이 5절 머리 안내에 있다 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 결함 D2 |
| ⑦ | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 3절 권고안·대안은 정책·범위·이름 선택(두는지, 합치는지, 이름, 위치, 적용 시점, effort)이며, 반영 문구·위치, 정의 파일·폴더의 처리, 판정을 따로 된 단계로 둘지와 `workflow:` 표기·판정 기준은 EC(없으면 명세 단계 산출물)로 넘겼다(2절 「목적」 끝 문장, D3·D8). 4절 「작업」 열은 할 일과 산출물 이름만 적었다 |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 체크리스트 머리 안내와 3절 표 아래 둘째 항목에 「D1~D10의 권고안을 전제로 작성」과 「결정」 열 우선이 적혀 있다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 마케팅·비주얼 추적 파일 | `git ls-files Departments/Marketing Departments/Visual` | 2026-10-12T00:07 전후(같은 Bash 호출의 `date` 이전) | `.gitkeep` 11개(Marketing: `assets/banners`, `assets/media`, `docs`, `results`, `workspace`. Visual: `assets/fonts`, `assets/icons`, `assets/images`, `docs`, `results`, `workspace`) |
| `Departments/Design` 경로를 담은 추적 파일 수 | `git grep -l "Departments/Design" cafc8d9 \| grep -v ":_archive/" \| wc -l`, `git grep -l "Departments/Design" cafc8d9 -- _archive \| wc -l` | 같은 시점 | `399`, `77`. 첫 시도 `git grep ... -- . ':!_archive'`는 `fatal: Unimplemented pathspec magic '_' in ':!_archive'`로 실패해 위 명령으로 다시 실행했다 |
| 기준 커밋 | `git log -1 --format=%H` | 같은 시점 | `cafc8d9f02a98228764f302c7eb724b7e0b5f995` |
| 레퍼런스 폴더·정의 파일 목록 | `ls "CEO/references/design.md references/"; ls .claude/agents` | 같은 시점 | `krds.md samsung-one-ui.md shadcn.txt toss.md yeogi.md` / `design.md development.md marketing.md operations.md quality.md visual.md` |
| 마케팅·비주얼 언급 위치 | Grep `비주얼\|[Vv]isual\|마케팅\|[Mm]arketing`(거버넌스 파일 전체) | 같은 시점 | `.claude/agents/visual.md` 3, `AGENTS.md` 2, `.claude/agents/marketing.md` 3, `Workflow/02` 2, `Workflow/01` 1, `Workflow/03` 5, `Workflow/07` 1. `Workflow/03`은 55·127·191·286·289행 |
| 설계 서브에이전트 이름 언급 | Grep `` `design` ``·`name: design`·`agents/design`·`\bdesign\b`(거버넌스 파일 전체) | 같은 시점 | `.claude/agents/design.md:2 name: design`, `Workflow/02:50` 설계 행 서브에이전트 열 두 곳뿐 |
| 판정 종류를 열거한 위치 | Grep `gate\|명세 판정\|EC 판정`(`Workflow/04`·`05`·`06`, `RES_TEMPLATE.md`, `REQ_TEMPLATE.md`, `.claude/agents/quality.md`) | 같은 시점 | `RES_TEMPLATE.md:3 gate: "FINAL" # REQ \| EC \| SPEC \| FINAL`, `RES_TEMPLATE.md:14` 판정서 파일명 열거, `.claude/agents/quality.md:3` description의 판정 열거, `Workflow/05:36` 커밋 대상 RES(REQ 판정, EC 판정, 명세 판정, 최종 판정) 열거, `REQ_TEMPLATE.md:12` `workflow:` 단계 순서 안내 등 |
| 기존 판정서 확인 | `ls Departments/Quality/results/ \| grep "RES-027"` | 2026-10-12T00:07:20+09:00 직전 | 출력 없음 |
| 완료 시각 조회 | `date -Iseconds` | 2026-10-12T00:07:23+09:00 | `2026-10-12T00:07:23+09:00` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> REQ 판정의 결함이므로 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」 1항에 따라 「해당 없음」이다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | REQ 머리말 `scope:`, 4절 표 아래 둘째 항목(`Workflow/04`·`05`·`06`과 서식을 scope에서 뺀 사유), 3절 D8 | scope가 D8을 모두 덮지 못한다. D8 권고안은 시각 디자인 문서의 판정을 「따로 된 단계로 둘지 기존 판정에 넣을지」를 EC에 넘겼는데, 따로 된 판정 단계를 고르면 판정 종류를 열거한 `Workflow/templates/RES_TEMPLATE.md`(3행 `gate:` 값, 14행 파일명), `.claude/agents/quality.md`(3행 description, 「업무와 참조 절」), `Workflow/05_인수인계_및_실행명령` 1.1절 6번 ①(커밋 대상 RES 열거. 빠지면 새 판정서가 안건 커밋에서 빠진다), `Workflow/templates/REQ_TEMPLATE.md`(12행 `workflow:` 단계 순서 안내)를 고쳐야 하며 이 경로는 모두 scope 밖이다. 기존 판정에 넣는 안도 현행 판정 가운데 「마케팅 산출물 뒤, 구현 전」에 늘 실행되는 판정이 없어(EC 판정·명세 판정은 설계 산출물 직후이고 명세 판정은 「EC 없음」 Critical·Major에서만 실행, Minor는 둘 다 없을 수 있음. `Workflow/03` 2.1절 6항) 같은 문제가 생길 수 있다. 4절 표 아래 둘째 항목의 제외 사유는 이름 Grep(D3·D5)과 D7만 따졌고 D8의 영향을 따지지 않았다. EC가 따로 된 단계를 고르면 구현 중 `Workflow/03` 「중단 조건」 1항으로 멈춘다. 고치는 방법은 둘 가운데 하나다. (가) 위 경로를 scope에 넣고 사유를 적는다 (나) 판정을 따로 된 단계로 둘지를 대표님이 정할 일로 D8에서 나눠 정하고, 권고안에 맞는 scope를 둔다 | 해당 없음 | 비서실(PM) |
| D2 | 3절 D7 권고안 「프로젝트마다 하나 둔다(D3 권고안이면 `Departments/Marketing/docs/DESIGN.md`)」, 4절 구현 행, 5절 체크리스트 ⑦ | 이 REQ가 `Departments/Marketing/docs/DESIGN.md` 파일 자체를 만드는지가 두 가지로 읽힌다. 「프로젝트마다 하나 둔다」와 scope의 `Departments/Marketing`은 이 저장소에도 그 파일을 두라는 뜻으로 읽힐 수 있고, 「첫 대상 제품·콘텐츠가 정해지지 않았다」와 4절 구현 행(폴더 「정리」만 적음)은 표준에 위치 규정만 두고 파일은 만들지 않는다는 뜻으로 읽힌다. 체크리스트 ⑦은 `Workflow/07`의 규정만 확인하고 파일의 유무를 확인하지 않아, 설계·개발이 빈 `DESIGN.md`를 만들면 최종 판정 기준 4(요청하지 않은 기능)로 볼지 판단 근거가 없다. 만드는지를 D7 권고안에 밝히고(예: 「이 REQ는 위치 규정만 두고 파일은 만들지 않는다」) 체크리스트 ⑦에 그에 맞는 확인을 더해야 한다 | 해당 없음 | 비서실(PM) |

## 6. 문체 지적
| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | 5절 체크리스트 ③ 첫 문장 | 현행 `AGENTS.md` 1절 조직 표, `Workflow/01` 「용어」 「조직」 행, `Workflow/02` 2절 표에 비주얼이 따로 된 조직으로 없고, 비주얼(시각 디자인)이 마케팅의 기능으로 적혀 있다. | 현행 `AGENTS.md` 1절 조직 표, `Workflow/01` 「용어」 「조직」 행, `Workflow/02` 2절 표 가운데 어디에도 비주얼이 따로 된 조직으로 없고, 세 곳 모두에 비주얼(시각 디자인)이 마케팅의 기능으로 적혀 있다. | 비서실(PM) |

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
