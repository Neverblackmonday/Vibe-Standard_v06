---
task_id: "029"
gate: "EC"
result: "fail"
completed_at: "2026-10-14T17:12:41+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-029-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-029_v01.md`, `Departments/Design/results/RPT-029_v01.md` 8절 「EC 판단」. 기준 REQ `Departments/Secretariat/docs/requests/REQ-029_v05.md`(승인 `2026-10-14T16:01:45+09:00`, 「결정」 열 D1~D13 권고안)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-029_03.md`

## 2. 판정 기준별 결과
| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | REQ 2절 「목적」의 항목(겹치지 않으면 REQ 작성 허용, 겹치면 끝난 뒤 작성, 진행 중의 범위, 판단 주체·시점·단위, 맞지 않게 된 REQ의 처리, 원스톱 착수 시점, ORDER 5절과의 관계)은 EC 3.1·3.2·3.3절에 모두 대응한다. 다만 「진행 중」의 범위가 D1보다 좁게 구현되었다(5절 D1) |
| 2 | EC scope가 REQ scope 안 | PASS | EC `scope:` 다섯 항목(`Departments/Design/docs/tad/EC-029`, `Workflow/02`·`03`·`05`, `Workflow/templates/ORDER_TEMPLATE.md`)이 모두 REQ `scope:`에 같은 글자로 있다. 뺀 `Workflow/06`·`check_standard.py`의 사유는 EC 2.3절(D6 권고안) |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 7절 11·12항과 13절 1항의 대상 제외(G10)는 D2·D5·D7의 멈춤을 7절 첫 문장(「아래 경우에만 멈추고」)의 목록에 넣고 13절 1항 ③의 번호 열거와 맞추는 것이다. 3.1절 6항(판정 `fail` 뒤 새 버전의 scope 추가 대조)은 D2 「REQ 파일을 저장하기 전에 판단」의 적용이다. 잠금 표시 장치는 정하지 않았다(2.3절, REQ 1절 「참고」) |
| 4 | 완료 기준을 확인할 수 있음 | PASS | EC 5절 1~14번이 적용본의 절·항, `RPT-029_v02` 「원본과의 차이」·사본 대조, `DEV-029_v01`, 명령(`check_standard.py`, `python -m pytest`)으로 확인하게 정했다 |
| 5 | REQ 「결정」 열의 결정이 반영되었다 | FAIL | D2~D6, D8~D13은 3.2절 G3~G12와 3.3절에 반영되었다. D1은 진행 중을 「번호별 최신 REQ의 `approved:`」로 판단해 승인 뒤 REQ 새 버전을 쓰는 안건을 빼고, 같은 판단을 쓰는 D7(4.1절 2·6항)과 D10(3.1절 1항)도 영향을 받는다(5절 D1). D7의 실행 중 판단 패턴이 파생 안건을 구분하지 못한다(5절 D2) |
| 6 | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-029_v01` 8절: 판단 「EC 있음」, 3항(거버넌스 파일 `Workflow/`의 규칙 변경)·2항(커밋된 표준·서식 변경). REQ `scope:`의 대상이 `AGENTS.md` 「불변 원칙」 3항 목록 안이고, 변경이 착수·중단 규칙을 바꾸므로 4항 ①~③에 들지 않는다. 판단 항목(판단, 해당 기준, 사유)이 `Workflow/03` 2.1절 5항과 맞다 |
| 7 | EC가 뒤 단계의 Claude Code 세션에 실행을 지정한 명령이 「명령 형태」의 원리 안에 있다 | PASS | 지정 명령: `git ls-files -- Departments/Secretariat/assets/inbox/`, `git status --porcelain -uall -- <경로>`, `git log --since=... --format="%H %cI %s" HEAD -- <경로 목록>`, `git show <커밋> -- <문서>`, `git log -1 --format=%H`, `git diff --stat cf820c7 HEAD -- <원본>`, `git diff --no-index <원본> <적용본>`, `python Departments/Development/assets/scripts/check_standard.py`, `python -m pytest Departments/Quality/assets/acceptance/REQ-029_v01`. 모두 `git`·`python` 바로 뒤 하위 명령으로 시작하는 단독 명령이며 `.claude/settings.json` `allow`의 `Bash(git ls-files*)`·`Bash(git status*)`·`Bash(git log*)`·`Bash(git show*)`·`Bash(git diff*)`·`Bash(python Departments/Development/assets/scripts/check_standard.py*)`·`Bash(python -m pytest*)`와 앞부분이 맞는다. 경로는 저장소 루트 기준 상대 경로다. 검색은 Grep·Glob 도구, 복사는 Read·Write 도구로 정했다(2.1절, 위험 8) |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-14T17:12:41+09:00 | `2026-10-14T17:12:41+09:00` |
| EC 원본 대상의 마지막 커밋(EC 1절 사실 확인) | `git log --format="%h %cI %s" -3 -- Workflow/02_부서_구조_및_작업구역.md Workflow/03_라이프사이클.md Workflow/05_인수인계_및_실행명령.md Workflow/templates/ORDER_TEMPLATE.md` (Bash) | 2026-10-14T17:12:10+09:00 앞 | `a7d7c56 2026-10-13T22:28:06+09:00 feat: [REQ-028] 끝난 REQ·HOTFIX를 커밋 전 검사의 통과 근거에서 빼기와 종결 기록` 외 2줄(`e956bab` REQ-027, `cafc8d9` REQ-026) |
| HEAD와 최근 커밋 | `git log -5 --format="%h %cI %s"` (Bash) | 2026-10-14T17:12:10+09:00 앞 | 첫 줄 `cf820c7 2026-10-14T13:09:36+09:00 docs: [CEO] ORD-010_v08·ORD-012_v05와 비서실 연락 추가` |
| 범위 대조(거버넌스·EC 경로) | `git status --porcelain -uall -- Workflow Departments/Development/assets/scripts Departments/Design/docs/tad` (Bash) | 2026-10-14T17:12:10+09:00 앞 | `?? Departments/Design/docs/tad/EC-029_v01.md` |
| 커밋된 종결 기록(EC 1절, 3.1절 4항 수단의 확인) | `git ls-files -- Departments/Secretariat/assets/inbox/` (Bash) | 2026-10-14T17:12:10+09:00 앞 | `종결기록_20261013_REQ-007.md`~`종결기록_20261013_REQ-028.md`, `종결기록_20261013_HOTFIX-003.md`~`HOTFIX-006.md`가 있고, `REQ-029`·`REQ-030`의 종결 기록은 없다 |
| D1 결함의 사례 확인 | `grep -n "^created:\|^approved:\|^scope:" -A0 Departments/Secretariat/docs/requests/REQ-030_v02.md Departments/Secretariat/docs/requests/REQ-030_v01.md Departments/Secretariat/docs/requests/REQ-029_v04.md` (Bash) | 2026-10-14T17:12:10+09:00 앞 | `REQ-029_v04.md:6:approved: "2026-10-13T09:38:56+09:00" ...`, `REQ-030_v01.md:6:approved: "" ...`, `REQ-030_v02.md:4:created: "2026-10-12"`. `REQ-029_v05.md`는 Read 도구로 `created: "2026-10-14"`, `approved: "2026-10-14T16:01:45+09:00"` 확인 |
| 권한 규칙 확인 | `cat "D:/Vibe Coding/Vibe Standard_v04/.claude/settings.json"` (Bash) | 2026-10-14T17:12:10+09:00 앞 | `allow` 21개 규칙(2절 7번 근거의 규칙 포함) |
| 커밋 전 검사 | 실행하지 않음 | — | EC 판정 기준에 들지 않으며 판정 대상이 커밋 전 산출물(EC·RPT)이다 |

- 판정 시작 때 REQ·EC·RPT 열람을 `cd "D:/Vibe Coding/Vibe Standard_v04" && cat ...`(Bash) 한 번으로 실행했다. 「명령 형태」의 원리(①)를 벗어난 형태이나 권한 확인 요청 없이 실행되었고, 결과는 파일 열람과 같아 판정 근거로는 Read 도구로 다시 읽은 내용을 썼다. 위 `.claude/settings.json` 조회도 절대 경로를 쓴 형태다. 판정에 필요한 명령 가운데 실행하지 못한 명령은 없다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」을 따른다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | `EC-029_v01` 3.2절 G2, 3.3절 2번 ① 3.1절 2항·4항 「승인 필드」, 같은 ② 4.1절 2항(「3.1절 4항의 방법」)·6항, 3.1절 1항 | 「진행 중인 안건」을 「번호별 최신 REQ의 `approved:`가 기재된 때부터」로 정해, 한 번 승인된 뒤 최신 버전이 `approved: ""`인 안건(5.3절 4항 Repair, 4.1절 5항 착수 전 대조, 6절 「진행 중인 안건의 요구가 바뀜」, 「결정」 변경으로 REQ 새 버전을 쓰고 재승인을 기다리는 안건)을 진행 중·실행 중에서 뺀다. REQ D1 권고안은 「REQ가 승인된 때부터 그 안건이 끝날 때까지 전체」이며 「중단 조건으로 멈춰 대표님 결정을 기다리는 동안」을 넣고, `Workflow/07` 1.1절 1항도 「멈춘 뒤 대표님 결정으로 계속하는 안건(REQ 새 버전 포함)은 끝난 것이 아니다」로 정한다. 실패 경로: ① 안건 A가 실행 중 Repair로 멈추고 REQ 새 버전(`approved: ""`)을 저장하면, 그 사이 다른 PM이 A의 `scope:`와 겹치는 REQ를 저장할 수 있고(D1·D2 위반), 4.1절 1항으로 다른 원스톱 B를 착수할 수 있다. A가 재승인 뒤 다시 실행되면 4.1절 6항(단계 산출물이 있음)으로 1항을 건너뛰어 A·B가 함께 진행된다(D7 위반). ② 그 기간에 A 자신의 REQ 새 버전 명령이 오면 대상 REQ의 최신 버전이 미승인이어서 3.1절 1항의 제외(D10)에 들지 않는다. 실제 사례: `REQ-029`는 `_v04`가 2026-10-13T09:38:56+09:00에 승인된 뒤 `_v05`(`created: "2026-10-14"`)가 2026-10-14T16:01:45+09:00에 승인되기 전까지 최신 버전의 `approved:`가 비어 있었다. 고칠 곳: 진행 중의 시작을 「그 번호의 REQ 가운데 승인 필드가 기재된 버전이 하나라도 있는 때」로 하고, 대조할 `scope:`(최신 버전과 승인된 버전)와 4.1절 2항·3.1절 1항의 판단을 같은 정의에 맞춘다. REQ `scope:`와 「결정」 열 안에서 EC만 고쳐 맞출 수 있다 | Rework | 설계 |
| D2 | `EC-029_v01` 3.2절 G6, 3.3절 2번 ② 4.1절 2항 | 실행 중 판단의 이름 패턴 「`RES-<번호>-`로 시작」은 원 안건의 `RES-<번호>-EC_`·`-SPEC_`·`-DESIGN_`뿐 아니라 파생 안건의 판정서(`Workflow/07` 「번호와 버전」 예 `RES-007-1-EC_v02.md`, `RES-007-1-REQ_v01.md`)에도 맞는다. 같은 문장의 「파생 안건 번호는 `_`·`-`까지 비교해 원 안건과 구분한다」와 어긋나 오판한다. 실패 경로: 파생 안건 `REQ-029-1`의 `RES-029-1-EC_v01.md`가 있으면, 승인되었고 착수하지 않은 `REQ-029`를 실행 중으로 보아 4.1절 6항으로 1·5항을 건너뛰고 `REQ-029-1`과 함께 착수한다(D7 위반). 「REQ 판정서 밖의 RES」 제외도 파생 안건의 `RES-<번호>-<파생 번호>-REQ_`를 빼지 못한다. 고칠 곳: 판정 구분 접미사까지 넣은 패턴(예: `RES-<번호>_`, `RES-<번호>-EC_`, `RES-<번호>-SPEC_`, `RES-<번호>-DESIGN_`)으로 바꾼다 | Rework | 설계 |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
