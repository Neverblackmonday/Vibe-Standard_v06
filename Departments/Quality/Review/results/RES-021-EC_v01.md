---
task_id: "021"
gate: "EC"
result: "fail"
completed_at: "2026-10-10T11:10:22+09:00" # 판정 세션에서 PowerShell `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"`로 조회한 시각
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-021-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-021_v01.md`(대조 기준 `Departments/Secretariat/docs/requests/REQ-021_v02.md`)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-021_02.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「단계별 통과 조건과 판정 기준」 표의 「EC 판정」 행 ①~⑤다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | REQ 2절 목적(모든 분류의 설계 단계, 분류와 EC의 분리, EC를 붙이는 기준, 판단의 기록과 확인, EC가 없는 Critical·Major의 구현 방법과 판정, 실험 단계 위치, 핫픽스 예외)은 EC 1절 「변경 목표」, 3.1절, 3.2절 F1~F13, 3.3·3.4절로 모두 다룬다. 다만 03 적용본 2.1절 5항의 「이 절」이 2.1절과 설계 결과서 「EC 판단」 절 가운데 어느 쪽인지 정해지지 않고(결함 D1), 「EC가 있으면/없으면」 조건이 판단 기록과 EC 파일 존재 가운데 무엇을 기준으로 하는지 정해지지 않아 2.1절 8항이 만드는 상태(「EC 없음」 판단과 `draft` EC가 함께 있음)에서 입력 문서가 두 뜻으로 읽힌다(결함 D2) |
| 2 | EC scope가 REQ scope 안 | PASS | EC `scope:` 16개 항목이 REQ `scope:` 16개 항목과 같다(머리말 대조). 2.1절 신규 파일은 부서 직속 `results/`·`workspace/`와 품질 인수 시험 경로로 scope 대상이 아니다(`Workflow/02_부서_구조_및_작업구역` 「작업 구역」) |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 새로 더하는 것(EC 판단 단계, 2.1절, 명세 판정과 `RES-xxx-SPEC`, RPT 「EC 판단」·「구현 계획」 절, F3의 해석 문장 세 개)은 모두 REQ D1~D7과 REQ 2절 목적이 EC에 넘긴 사항(규정의 문구·위치, 기록 위치·형식, 판정서 구분)에 연결된다. `check_standard.py`·`settings.json`·`AGENTS.md`를 고치지 않는다(2.3절) |
| 4 | 완료 기준을 확인할 수 있음 | FAIL | 5절 완료 기준 1~12는 적용본 절, 결과서 절, 명령으로 확인할 수 있게 적혀 있다. 그러나 REQ 체크리스트 2 ②는 「「EC」와 분류 이름을 함께 검색한 명령과 결과 원문」을 요구하는데, EC 3.4절 2번 ①의 명령은 분류 이름만 검색한다(결함 D3) |
| 5 | REQ 「결정」 열의 결정이 반영되었다 | PASS | REQ 3절 「결정」 열은 D1~D8 모두 「권고안」이다. D1: 2절 표·표 아래 항목, 2.1절 5·6항(F1·F5). D2: 2.1절 5·6항, 3절 1항 「EC 판단과 REQ」, `REQ_TEMPLATE.md`·07 3절 REQ 행(F5·F6). D3: 2.1절 1·2·4항(F3). D4: 2.1절 3항(F3). D5: 2.1절 5·7항, 5절 표 「EC 판정」 ⑥·「명세 판정」 ⑦, 최종 판정 기준 9, `DEV_TEMPLATE.md` 8절(F4·F7·F8). D6: 3절 1항, 5절 표 「명세 판정」 행, 07·05·06·서식(F9~F11). D7: 11.2절 2·3·5·6항, 12절 1항(F12). REQ-016 D1은 2.3절에서 제외. D8: `medium`(문서 변경 없음) |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(EC 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 최신 커밋과 원본 변경 여부(EC 1절 「변경 배경」 대조) | PowerShell `git log -1 --format=%h; git diff --stat HEAD -- .claude Workflow AGENTS.md; Get-Date -Format o` | 2026-10-10T11:09:35+09:00 | `ee95f5a` / (diff 출력 없음) / `2026-10-10T11:09:35.5606492+09:00` |
| 대신한 명령 | 실행하지 못한 명령: Bash `cd "/d/Vibe Coding/Vibe Standard_v04"; git log -1 --format=%h; git diff --stat HEAD -- .claude Workflow AGENTS.md; date …`, Bash `git -C "/d/Vibe Coding/Vibe Standard_v04" log -1 --format=%h`, Bash `git -C … diff --stat HEAD -- .claude Workflow AGENTS.md` | 2026-10-10T11:09 무렵(+09:00) | 메시지 원문: 첫 명령 `This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.`, 둘째·셋째 명령 `This command requires approval`. 위 행의 PowerShell 명령으로 대신했다(`Workflow/03_라이프사이클` 「판정 세션의 명령 실행」 3항) |
| 원본 대상 위치 대조 | Read `Workflow/03_라이프사이클.md` 전체, `Workflow/07_문서_서식_및_번호.md` 전체, `Workflow/templates/RES_TEMPLATE.md`·`DEV_TEMPLATE.md`·`REQ_TEMPLATE.md` | 2026-10-10T11:0x(+09:00) | EC 3.3절이 바꿀 대상으로 인용한 문구(03 3절 1항 「구현 방법은 EC에서 정한다.」·「결정과 체크리스트」 끝 문장, 5절 표 각 행 입력, 기준 7, 5.1절 4항, 5.2절 1항, 7절 7항, 8절, 11.2절 2·3·5·6항, 12절 1·2·4항, 13절 1·3항, 07 1절 RES 행·추적 관계, 2절 판정 구분, 3절 REQ·RES 행, 서식 주석)가 원본과 같다 |
| 04·05·06 대상 위치 대조 | Grep `RES\(REQ 판정\|REQ·EC·최종 판정\|최종 판정에서 적용본\|EC 경로, 대상 파일 경로` in `Workflow` | 같은 시각대 | 05 36행 「RES(REQ 판정, EC 판정, 최종 판정)」, 04 26행 「REQ 경로, EC 경로, 대상 파일 경로,」, 06 13행 「REQ·EC·최종 판정」, 06 95행 「품질 서브에이전트가 최종 판정에서 적용본을 판정한다.」. EC 3.3절 4~6번의 대상과 같다 |
| 범위 제외 판단 대조 | Grep `EC\|Minor\|분류` in `AGENTS.md`; Grep `Minor\|Critical\|Major` in `Workflow`(03 제외); Grep `EC\|Minor\|명세` in `.claude/agents`; Grep `RECORD_NAME\|results\|gate\|EC` in `check_standard.py` | 같은 시각대 | `AGENTS.md` 결과 없음. `Workflow`(03 제외)의 분류 이름은 `ORDER_TEMPLATE.md` 5행, `REQ_TEMPLATE.md` 3·11·19·58행, 07 69·70행, `DEV_TEMPLATE.md` 14행이며 EC와 묶인 줄(`REQ_TEMPLATE.md` 11·19행, 07 70행, `DEV_TEMPLATE.md` 14행)은 모두 EC 3.3절 7·8·10번이 바꾼다. `.claude/agents`의 EC·Minor 기술은 `design.md` 3·13행, `development.md` 3·13행, `quality.md` 3·14행이며 3.4절 1번이 다룬다. `check_standard.py`는 `RECORD_NAME`이 `REQ\|HOTFIX`만 맞추고(76행), 부서 직속 `results/`·`workspace/`를 scope 대조에서 뺀다(112~113행). EC 1절·2.3절 서술과 같다 |
| 부적합 누적 대조 | Grep `^(recorded_at\|causes\|proposals\|  - )` in `Departments/Quality/docs/nonconformance` | 같은 시각대 | `NCR-018_01`(C4), `NCR-018_02`(C3), `NCR-018_03`(C1), `NCR-019_01`(C9, C5), `NCR-019_02`(C5, 제안 C5), `NCR-019_03`(C1, C5, C3, 제안 C1·C3), `NCR-019_04`(C9), `NCR-021_01`(C2) |
| 판정 완료 시각 | PowerShell `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"` | 2026-10-10T11:10:22+09:00 | `2026-10-10T11:10:22+09:00` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | `EC-021_v01.md` 3.3절 3번 ⑤ 2.1절 5항 | 2.1절 첫 문장은 「… 그 기록·확인은 이 절이 원천이다」로 「이 절」을 2.1절의 뜻으로 쓴다. 그런데 같은 절 5항은 「실험 결과는 EC가 있으면 EC가, 없으면 이 절이 인용한다」, 「설계 결과서의 다음 버전을 쓰면 이 절을 그대로 옮긴다」에서 「이 절」을 설계 결과서 「EC 판단」 절의 뜻으로 쓴다. 문안대로 적용본을 만들면 「EC 없음」일 때 실험 결과를 인용하는 곳이 03 2.1절로 읽힐 수 있고, 11.2절 2·5항과 F12(설계 결과서 「EC 판단」 절이 인용)와 어긋난다. 고칠 방향: 5항의 두 「이 절」을 「설계 결과서 「EC 판단」 절」로 바꾼다 | 설계 |
| D2 | `EC-021_v01.md` 3.3절 3번 ⑤ 2.1절 8항, ⑨ 5절 표 「명세」·「구현」·「최종 판정」 행, 4번 ①, 3.4절 1번 ②, 3.3절 10·12번 | 적용본 여러 곳이 입력과 경로를 「EC가 있으면/없으면」, 「EC(있으면)」, 「EC 경로(EC가 있을 때)」로 정한다. 2.1절 8항은 「EC 있음」 판단이 EC 판정에서 「EC 없음」으로 바뀌면 「EC는 `draft`로 두고」 진행하게 하므로, EC 파일은 있으나 판단은 「EC 없음」인 상태가 생긴다. 이 상태에서 「구현」 행 입력 「EC(없으면 REQ와 설계 결과서)」, 「최종 판정」 행 입력 「EC(있으면)」, 04 지시문의 「EC 경로(EC가 있을 때)」, `DEV_TEMPLATE.md`·`ACC_TEMPLATE.md` 1절 「EC가 없으면 「해당 없음」」이 EC 파일의 존재를 기준으로 하는지 최신 「EC 판단」 절의 판단을 기준으로 하는지 두 뜻으로 읽혀, 개발이 `fail` 판정을 받은 `draft` EC를 구현 입력으로 쓰거나 최종 판정이 그 EC를 대조 기준에 넣을 수 있다. 고칠 방향: 2.1절에 「이 표준에서 「EC가 있다」·「EC가 없다」는 최신 설계 결과서 「EC 판단」 절의 판단을 말하며, 8항으로 남은 `draft` EC는 뒤 단계의 입력이 아니다」는 뜻의 문장을 두고, 위 위치가 그 문장을 따르게 한다 | 설계 |
| D3 | `EC-021_v01.md` 3.4절 2번 ①, 5절 완료 기준 2 | REQ 체크리스트 2 ②는 「「EC」와 분류 이름을 함께 검색한 명령과 결과 원문이 개발 결과서에 있다」를 확인 방법으로 정했다. EC는 `grep -rn -E "Critical\|Major\|Minor" <설계 적용본> <개발 적용본>`(분류 이름만 검색)을 정하고, 「EC」가 든 줄은 결과를 읽어 사람이 고르게 한다. 이 명령은 「EC」를 검색하지 않으므로 최종 판정이 REQ 원문(최종 판정 기준 1)과 대조할 때 체크리스트 2 ②의 확인 방법을 충족하지 못한 것으로 판단할 수 있다. 고칠 방향: 「EC」와 분류 이름을 함께 검색하는 명령(예: 분류 이름 검색 결과를 「EC」로 다시 거르는 명령)과 그 결과 원문을 개발 결과서에 적게 하고, 넓은 검색을 함께 남기려면 두 명령의 관계를 적는다 | 설계 |

## 6. 문체 지적
| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | `EC-021_v01.md` 3.3절 1번 ② | `「명세 판정 \| EC가 없는 Critical·Major 안건의 명세 단계 산출물의 품질 판정. 판정서 `RES-xxx-SPEC` \| —」` | `「명세 판정 \| 명세 단계 산출물의 품질 판정. 판정서 `RES-xxx-SPEC`. 실행 조건과 기준은 `Workflow/03_라이프사이클` 「단계별 통과 조건과 판정 기준」 \| —」` (3.1절 원천 표의 「01 「용어」 명세 판정 행은 이름과 참조만 둔다」와 맞춘다) | 설계 |
| S2 | `EC-021_v01.md` 3.3절 10번 ① | `(「EC 판단」 절. EC가 없으면 「구현 계획」 절 포함)` | `(「EC 판단」 절. EC가 없는 Critical·Major이면 「구현 계획」 절 포함)` (「구현 계획」 절은 9절 제목대로 EC가 없는 Critical·Major에만 있다) | 설계 |
| S3 | `EC-021_v01.md` 3.3절 7번 ② | `RPT 「EC 판단」 절 → EC → RES-EC(EC가 있을 때) → PRD·TAD(`related_req`)·RPT → RES-SPEC(명세 판정이 있을 때)` | `RPT 「EC 판단」 절 → (EC가 있을 때) EC → RES-EC → PRD·TAD(`related_req`)·RPT → (명세 판정이 있을 때) RES-SPEC` (괄호 조건이 EC와 RES-EC 둘 다에 걸린다는 것을 드러낸다) | 설계 |
| S4 | `EC-021_v01.md` 3.3절 1번 ① 첫째 행 | `「설계 단계 \| 설계가 맡는 원스톱 파이프라인 단계(EC 판단, EC 작성, 명세)를 묶어 부르는 말. 원천은 `Workflow/03_라이프사이클` 「분류별 단계」 \| —」` | `「설계 단계 \| 설계가 맡는 원스톱 파이프라인 단계를 묶어 부르는 말. 해당 단계는 `Workflow/03_라이프사이클` 「분류별 단계」가 원천이다 \| —」` (03 2절 표 아래 항목과 같은 단계 목록을 두 곳에 적지 않는다) | 설계 |

## 7. 삭제 대상 (최종 판정만)
해당 없음(EC 판정).

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음(EC 판정).
