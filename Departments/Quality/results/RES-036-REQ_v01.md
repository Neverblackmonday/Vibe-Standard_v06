---
task_id: "036"
gate: "REQ" # REQ | EC | SPEC | DESIGN | FINAL (REQ 판정, EC 판정, 명세 판정, 시각 디자인 판정, 최종 판정)
result: "fail" # pass | fail | rejected
completed_at: "2026-10-26T21:24:06+09:00" # 판정을 마칠 때 조회한 시각을 결과 그대로 적는다. 조회·기재 방법과 조회하지 못했을 때의 처리는 Workflow/03_라이프사이클 「판정 세션의 명령 실행」
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델. 그 단계에 정해진 모델과 다르면 무효(Workflow/04_모델_운용 「단계별 모델」)
  effort: "medium (실행 명령 기준)" # 실행 명령 지시문의 effort 값과 출처. 얻을 수 없으면 "확인 불가"(Workflow/04_모델_운용 「모델 메타데이터 기록」)
---

# RES-036-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-036_v01.md`(출처 ORDER `Departments/Secretariat/assets/inbox/ORD-013_v02.md`)
- **판정 차수**: 1차(최초 판정, REQ 전체 대조)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-036_01.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다. 최초 판정이므로 REQ 전체를 ORDER와 상위 규정에 대조했다. 이 REQ가 흡수하는 `REQ-035_v03.md`(REQ 판정 `pass`)와의 차이는 `git diff --no-index`로 따로 확인했다(아래 표 아래 「흡수 기록과의 차이」).

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | 1절이 인용한 ORDER 문장(2절 머리 문단, 「가」 머리와 요구 항목 1~4, 「REQ에서 정할 사항」 요구 항목 1·2·4, 3절 8·14·16항과 16항의 하위 항목 4개, 5절 1·2항)을 한 줄씩 `grep -c -x -F '<인용 줄>' ORD-013_v02.md`로 대조해 모두 1건씩 일치했다(18줄). 원문 U·V·X·AA·AC 인용은 ORDER 1절 116·120·128·142·150행과 같다. 「REQ에서 정할 사항」의 항목은 D1·D2(요구 항목 1), D3·D4(요구 항목 2), D5·D6과 3절 표 아래 「D5와 `scope:`」(요구 항목 4)가 모두 맡는다. 3절 16항이 정한 「D1~D6과 그 권고안을 이어 씀」은 `REQ-035_v03.md`와의 diff에서 D1·D2·D3·D6 행이 같고, D4는 문체 지적 반영 한 문장, D5는 끝 문장 추가뿐임을 확인했다 |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 5절 1~4번이 요구 항목 1~4와 같은 번호로 대응한다(`Workflow/07_문서_서식_및_번호` 1절 「추적 식별자」). 요구 항목 1의 「`Workflow/06` 2절 「`ask`」 항과 2.1절을 맞춤」은 1③, 요구 항목 2의 「예외 유지」는 2②, 요구 항목 3의 세 대상(EC 서식, 결과서 서식, EC 판정 기준)은 3①②, 요구 항목 4는 4①~③이 덮는다 |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | PASS | 요구 항목 1: `.claude/settings.json`, `Workflow/06_통제장치_및_배포.md`. 요구 항목 2: `.gitattributes`. 요구 항목 3: `Workflow/templates/EC_TEMPLATE.md`, `Workflow/templates/DEV_TEMPLATE.md`(결과서 서식. `Workflow/07` 1절 표 DEV·RPT 행), `Workflow/03_라이프사이클.md`(162행 「EC 판정」 행). 요구 항목 4: `Workflow/04_모델_운용.md`(45행 「서브에이전트 정의」, 39~46행 「PM의 책임」·「판정서 모델 대조」), `.claude/agents`(정의 파일 5개 모두 `model: inherit`, `grep -n "^model:" .claude/agents/*.md`). EC 경로 `Departments/Design/docs/tad/EC-036`은 `Workflow/07` 3절 표 REQ 행대로다. `check_standard.py`에는 `settings.json` 내용·정의 파일 모델·줄바꿈을 검사하는 곳이 없어(`grep` 결과 66행 `GOVERNANCE_PATHS`의 `.gitattributes`뿐) 검사 스크립트를 고칠 필요가 생기지 않는다. 실행 전 장치가 `scope:` 밖 파일을 요구하는 경우의 처리는 ORDER 「REQ에서 정할 사항」 요구 항목 4대로 3절 표 아래 「D5와 `scope:`」에 있다. 요구 밖 경로는 없다(4절 「scope 경로별 사유」) |
| ④ | 분류가 2절 정의 기준과 맞고, `workflow:`가 2절과 맞다 | PASS | Critical. 거버넌스 파일과 권한 설정을 바꾸며(`Workflow/03_라이프사이클` 43행 「예」 열 「거버넌스 파일, 보안·권한」), ORDER `classification_proposal`과 같다. `workflow:`는 Critical 단계(EC 판단 → [EC 작성 → EC 판정] → 명세 → [명세 판정] → 인수 시험 → 구현 → 최종 판정)와 같고 선택 단계(실험, 시각 디자인)는 넣지 않았다 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | PASS | 1①②·2①②는 인수 시험 실행, 1③·2③·3①②·4①②는 열람, 4③은 `git diff --no-index` 실행으로 확인한다. 참고(결함·문체 아님): 모든 정의 파일이 `disallowedTools: Agent`이므로(`Workflow/06_통제장치_및_배포` 3절) 4①의 실측은 개발 서브에이전트가 `Agent` 도구로 품질 서브에이전트를 직접 기동하는 방식으로는 할 수 없다. 실측 방법은 EC(또는 명세 단계 산출물)에서 정해야 한다 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 결함 D1. 1절 참고 「`REQ-035`와의 관계」의 변경 목록이 실제 변경과 다르다(5절). 그 밖에 D4의 「`setup.cmd`와 `_archive/` 아래 `setup.cmd` 4개」는 994−989=5와 `git ls-files --eol` 결과(작업 트리 CRLF인 `.cmd` 5개: `setup.cmd`, `_archive/` 아래 4개)로 하나로 읽힌다. 5절 2번 ①의 「텍스트 파일」 범위는 2번 ②와 함께 읽으면 예외가 빠짐을 알 수 있어 문체 지적(S1)으로 분류했다 |
| ⑦ | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 2절 「목적」 ①~④는 결과만 적는다. 3절 D1~D6의 정할 일·권고안·대안은 확인 범위, 기존 경로 유지 여부, 줄바꿈 종류, 실행 주체·시점, 사전 차단과 사후 무효의 선택, 개정 범위만 정한다. 「D5와 `scope:`」는 장치의 위치와 형태를 EC(없으면 명세 단계 산출물)에 넘긴다. 4절 「작업」 열은 할 일과 산출물 이름만 적는다(구현 ③은 `Workflow/06` 5절 3항이 정한 대조 절차) |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 5절 머리에 「D1~D6에 따라 달라지는 항목은 권고안을 전제로 쓴다」와 「결정」 열 우선이 있다. 1①(D1), 2③(D4), 4①(D5), 4③(D6)이 이 전제에 든다. 4절 표의 단계는 결정과 관계없고, 표 아래 사유 문장은 결정마다 조건을 적었다 |

- **흡수 기록과의 차이**: `git diff --no-index REQ-035_v03.md REQ-036_v01.md`의 변경은 머리말(`task_id`, `source_order`, `scope:` EC 경로), 제목, 1절(ORDER v02 인용 갱신, 참고 항목 교체), 2절 배경(조회 시각, 요구 항목 1의 종결 기록 경로 표기, 요구 항목 4의 새 문장), 3절(D4 한 문장, D5 끝 문장, 「D5와 `scope:`」 항목), 4절(대상 경로 번호, 표 아래 마지막 문장 추가), 6절(대상 파일)이다. 1절 참고의 목록과의 대조 결과는 결함 D1에 적었다.
- **사실 대조**: 2절 배경의 값을 다시 조회해 확인했다. `ask` 여섯 규칙과 `allow`의 `PowerShell(...)` 일곱 규칙(`.claude/settings.json`), `.claude/` 아래 `agents`·`settings.json`뿐(`ls -a .claude`), `git ls-files --eol`의 `i/lf w/crlf` 994개·`i/lf w/lf` 168개·`i/none` 46개·`i/crlf` 0개(모두 1208개), `종결기록_20261015_REQ-030.md` 존재, `master`의 `NCR-029_03.md` 경로와 개정 제안(EC 서식 3절, `Workflow/03` 5절 표 「EC 판정」 행), `master`에 `REQ-036` 파일·커밋 없음, `Departments/Secretariat/docs/requests/`의 가장 큰 번호 `035`. 인용한 상위 규정(`Workflow/04` 1.2절 「PM의 책임」 ③과 Minor 예, `Workflow/06` 2.1절 「명령 도구」, 5절 3항, 7절 1·5행, `Workflow/05` 1.1절 8번의 커밋 명령 예, 3절 표 아래 첫 항목, `Workflow/03` 7절 1·4항)은 원문과 맞는다. 6절 실행 명령은 `Workflow/05` 3절 원스톱 실행 명령 형식과 `Workflow/04` 1.1절 고급 기본 모델 ID `claude-opus-5-5`와 맞는다.

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(REQ 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 대상 문서 열람 | `cd "/d/Vibe Coding/Vibe Standard_v06" && cat Departments/Secretariat/docs/requests/REQ-036_v01.md && echo ===== && cat Departments/Secretariat/assets/inbox/ORD-013_v02.md`(Bash) | 2026-10-26T21:23:41+09:00 이전(명령별 시각은 조회하지 않음) | 출력이 길어 파일로 저장되었다. 이 명령은 앞에 폴더 이동(`cd`)을 붙여 `Workflow/06_통제장치_및_배포` 2.1절 「명령 형태」와 다른 형태로 실행했다. 권한 확인 요청 없이 실행되었고 결과는 판정에 영향이 없다(이후 두 파일은 Read 도구로 다시 읽었다). 이후 명령은 저장소 루트 기준 상대 경로로 실행했다 |
| 흡수 기록과의 차이 | `pwd; ls .claude/agents Workflow/templates; git diff --no-index Departments/Secretariat/docs/requests/REQ-035_v03.md Departments/Secretariat/docs/requests/REQ-036_v01.md` | 같음 | 정의 파일 5개(`development.md`, `engineering.md`, `marketing.md`, `operations.md`, `quality.md`). diff 덩어리 `@@ -1,8 +1,8 @@`, `@@ -18,7 +18,7 @@`, `@@ -29,10 +29,10 @@`, `@@ -46,6 +46,14 @@`, `@@ -63,32 +71,41 @@`, `@@ -102,30 +119,36 @@`, `@@ -141,5 +164,5 @@`. 2절 배경 요구 항목 4에 「`.claude/` 아래에는 `settings.json`과 `agents/`만 있다(같은 조회).」 추가, 요구 항목 1의 「(종결 기록 위 경로)」가 「(`Departments/Secretariat/assets/inbox/종결기록_20261015_REQ-030.md`)」로 바뀜, 4절 표 아래 끝에 「검사 스크립트와 Git 훅을 넣지 않는 까닭은 3절 표 아래 「D5와 `scope:`」 항목에 적었다.」 추가 |
| 정의 파일 모델·매뉴얼 절 | `grep -n "^#" Workflow/04_모델_운용.md Workflow/06_통제장치_및_배포.md Workflow/05_인수인계_및_실행명령.md Workflow/07_문서_서식_및_번호.md Workflow/02_부서_구조_및_작업구역.md Workflow/templates/EC_TEMPLATE.md Workflow/templates/DEV_TEMPLATE.md; grep -n "^model:" .claude/agents/*.md` | 같음 | 정의 파일 5개 모두 4행 `model: inherit`. `EC_TEMPLATE.md` 3절 하위는 「3.1 구조 변경」·「3.2 단계별 작업」뿐 |
| 줄바꿈 분류 | `git ls-files --eol \| grep -c "i/lf.*w/crlf"` 외 같은 형태 3건, `git ls-files --eol \| grep -E "\.(cmd\|bat)$\|\.githooks/"`, `git ls-files --eol \| wc -l`, `cat .gitattributes` | 같음 | `994`, `168`, `46`, `0`. 작업 트리 CRLF인 `.cmd` 5개(`setup.cmd`, `_archive/v02/…/REQ-002_적용본_v01/setup.cmd`, `_archive/v02/Update_Package/setup.cmd`, `_archive/v02/setup.cmd`, `_archive/v03/setup.cmd`), `.bat` 없음, `.githooks/pre-commit` 등 3개는 `w/lf`. 전체 `1208`. `.gitattributes` 줄바꿈 규칙은 `*.bat text eol=crlf`, `*.cmd text eol=crlf`, `.githooks/* text eol=lf` 세 줄 |
| `master` 대조 | `git ls-tree -r --name-only master \| grep -E "REQ-036\|NCR-029_03"; git log --oneline master \| grep -c "REQ-036"; git log -1 --format=%H; git show master:Departments/Quality/Nonconformance/docs/NCR-029_03.md \| head -40` | 같음 | `Departments/Quality/Nonconformance/docs/NCR-029_03.md`만 나옴(REQ-036 파일 없음), `0`, HEAD `d6fff5a324e6757f1c156b0aea22df56640eb8dd`. `NCR-029_03` 원인 분류 `C1` |
| 검사 스크립트·REQ 폴더 | `grep -n -E "settings\.json\|\.claude/agents\|model: inherit\|gitattributes\|PowerShell\|\"ask\"" Departments/Development/assets/scripts/check_standard.py; git show master:Departments/Quality/Nonconformance/docs/NCR-029_03.md \| grep -n -E "EC 판정\|개정 제안\|^## 5"; ls Departments/Secretariat/docs/requests/` | 같음 | `66:    ".gitattributes",`뿐. NCR 51행 개정 대상 「`Workflow/templates/EC_TEMPLATE.md` 3절 「세부 설계」, `Workflow/03_라이프사이클` 5절 표 「EC 판정」 행」. REQ 폴더의 가장 큰 번호 `REQ-035`(이번 대상 `REQ-036_v01.md` 제외) |
| `.claude/`·작업 트리·종결 기록 | `ls -a .claude; git ls-files .claude; git status --porcelain -uall; ls Departments/Secretariat/assets/inbox \| grep -E "종결기록_20261015_REQ-030"` | 같음 | `.claude` 아래 `agents`, `settings.json`. 추적 파일 6개. 미추적 28건(판정서·부적합 기록 작성 전). `종결기록_20261015_REQ-030.md` 있음 |
| 인용 대조 | `grep -c -x -F '<REQ 1절 인용 줄에서 「> 」를 뗀 문장>' Departments/Secretariat/assets/inbox/ORD-013_v02.md`(Bash, 3회에 18줄) | 같음 | 18줄 모두 `1` |
| 부적합 누적 대조 | `ls Departments/Quality/docs/nonconformance/; grep -l -E "^  - C4" Departments/Quality/docs/nonconformance/*.md; grep -n -E "^recorded_at\|^proposals\|^  - C" Departments/Quality/docs/nonconformance/*.md` | 같음 | 기존 기록 43건. `C4`가 든 기록은 `NCR-018_01.md`, `NCR-028_03.md`. `C4`를 제안한 가장 최근 기록 `NCR-028_03.md`(2026-10-13T13:33:17+09:00) |
| 부적합 기록 시각 | `date -Iseconds` | 2026-10-26T21:23:41+09:00 | `2026-10-26T21:23:41+09:00`(`NCR-036_01.md` `recorded_at`) |
| 범위 대조 | `git status --porcelain -uall` | 2026-10-26T21:24:06+09:00 직전 | 미추적 29건. 위 28건에 `Departments/Quality/docs/nonconformance/NCR-036_01.md`가 더해졌다. 추적 파일 변경 없음 |
| 완료 시각 조회 | `date -Iseconds` | 2026-10-26T21:24:06+09:00 | `2026-10-26T21:24:06+09:00` |

- 실행하지 못한 명령: 없음. 권한 확인 요청이 있었던 명령: 없음.
- 열람·Grep으로 대조한 문서: `REQ-036_v01.md` 전체, `ORD-013_v02.md` 전체, `RES-035-REQ_v03.md`, `NCR-035_01.md`, `AGENTS.md`, `.claude/settings.json`, `Workflow/03_라이프사이클.md` 2절·2.1절·3절·4절·5절 표·5.1절·5.2절·7절·13절, `Workflow/04_모델_운용.md` 1~4절, `Workflow/05_인수인계_및_실행명령.md` 1.1절·3절, `Workflow/06_통제장치_및_배포.md` 1~5절·7절, `Workflow/07_문서_서식_및_번호.md` 1~3절, `Workflow/templates/RES_TEMPLATE.md`, `Workflow/templates/NCR_TEMPLATE.md`.
- 판정 모델 대조: REQ 판정은 고급 기본 모델, effort `medium`(`Workflow/04_모델_운용` 1.2절 「REQ 작성 파이프라인」 행)이며, 이 판정 세션의 실행 모델 `Claude Opus 5.5`(세션 시스템 정보 `claude-opus-5-5`)와 지시문의 `effort: medium`과 같다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」 1항대로 REQ 판정의 결함이므로 「해당 없음」이다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | `REQ-036_v01.md` 1절 참고 「`REQ-035`와의 관계」(96~100행) | 사실 오류와 누락. 「3절 D1~D6과 그 권고안·대안은 `REQ-035_v03.md` 3절을 이어 썼다. 바꾼 곳은 아래뿐이다」와 넷째 항목 「2절 배경의 조회 시각을 이 REQ 작성 때의 조회로 바꿨다. 조회 값은 `REQ-035_v03.md`와 같다」가 실제 변경과 다르다. `git diff --no-index REQ-035_v03.md REQ-036_v01.md`에는 목록에 없는 변경이 있다. ① 2절 배경 요구 항목 4에 새 조회 값 「`.claude/` 아래에는 `settings.json`과 `agents/`만 있다(같은 조회)」를 더했다(「조회 값은 같다」와 어긋남) ② 2절 배경 요구 항목 1의 「(종결 기록 위 경로)」를 종결 기록 경로로 바꿨다 ③ 4절 표 아래 마지막에 「검사 스크립트와 Git 훅을 넣지 않는 까닭은 …」 문장을 더했다. 이 목록은 이미 `pass`를 받은 `REQ-035_v03.md`와 무엇이 달라졌는지 대표님이 REQ를 검토할 때 기대는 기재이므로, 빠진 변경(특히 ①의 새 사실 기재)을 검토 대상에서 놓치게 할 수 있다. 목록에 빠진 변경을 더하거나, 완전성을 단정하는 문구(「아래뿐이다」, 「조회 값은 … 같다」)를 실제 변경에 맞게 고친다 | 해당 없음 | 비서실(PM) |

## 6. 문체 지적
> 지적의 구분과 처리는 `Workflow/03_라이프사이클` 「판정 지적의 구분과 문체 지적 처리」를 따른다.

| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | `REQ-036_v01.md` 5절 2번 확인 방법 ①(159행) | 텍스트 파일의 작업 트리 내용 해시가 두 설정에서 같고 줄바꿈이 LF임을 확인해 통과한다 | 기존 예외(`*.bat`·`*.cmd`) 밖의 텍스트 파일의 작업 트리 내용 해시가 두 설정에서 같고 줄바꿈이 LF임을 확인해 통과한다 | 비서실(PM) |

## 7. 삭제 대상 (최종 판정만)
해당 없음(REQ 판정).

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음(REQ 판정).
