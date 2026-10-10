---
task_id: "022"
gate: "EC"
result: "fail"
completed_at: "2026-10-10T14:55:54+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-022-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-022_v02.md`(`status: draft`). 판정 범위는 `EC-022_v01` 대비 변경분이다. 대조 입력: `Departments/Secretariat/docs/requests/REQ-022_v02.md`, `Departments/Secretariat/assets/inbox/승인기록_20261010_REQ-022_v02.md`, 직전 판정서 5절 결함 D1~D3, 현행 `Workflow/03`·`05`·`07`, `Workflow/templates/PM_DIRECTIVE_TEMPLATE.md`, `Workflow/templates/ORDER_TEMPLATE.md`
- **판정 차수**: 재판정 1차(직전 판정서 `Departments/Quality/results/RES-022-EC_v01.md`)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-022_03.md`

## 2. 판정 기준별 결과
변경분(1절 「결정 반영 원칙」·「번호 표기」·「이전 버전과의 관계」, 2.2절 표 3·5·12행, 3.1절 두 표, 3.2절 머리와 F5·F6·F8·F9·F11·F13·F14·F18, 3.3절 3·4·5·12번, 4절 위험 2·5·7·11, 5절 완료 기준 4·7·8)만 판정했다. 변경분 밖의 판정 결과는 직전 판정서를 따른다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| D1 확인 | 직전 결함 D1(실험 기록 번호와 EC 결정 번호의 구분) | 해소 | 1절 「번호 표기」 신설. F6 근거의 「(실험 기록 v01 F7)」·「(실험 기록 v01 F9)」·「사후 대조(이 EC의 F8)」, F14 근거의 「(실험 기록 v01 F4)」·「이 EC의 F8 대조」, 위험 2의 「공식 문서(실험 기록 v01 F2)」·「(이 EC의 F8 ①)」·「(이 EC의 F8 ⑤)」로 바뀌었다. Grep `\(F\d+\)|문서 근거|실험 기록 v01 F`(EC-022_v02) 결과의 나머지 「(Fn)」(106·108·165·175·299·305행 등)은 모두 이 EC의 결정 번호를 가리키는 문맥이다. 50행의 「(F2)」는 `DEV-022_v02` 원문의 꼴을 설명하는 문장이다 |
| D2 확인 | 직전 결함 D2(REQ 새 버전의 작성 모델과 PM 모델이 다를 때의 처리) | 해소(새 결함 D4는 별도) | F18 ①이 REQ 새 버전의 사유를 열거하고(03 3절 3항, 6절, 11.2절 7항, 5.1절 5항, 8절, 07 3.1절 6항. 현행 문서에서 각 위치를 확인함) 작성 전 모델·effort 확인과 다를 때의 9항 멈춤을 정한다. 같은 세션 계속(03 8절 「초기화」)도 작성 전 확인으로 덮인다. 9항은 13절 1항의 대상 목록 ③(1·3·5·6·7·8)에 들지 않고, 제외 문장 「7절 4·9항과」로 바뀌어 모순이 없다. 05 3절의 현행 문구 「두 명령 모두 형식은 같다.」, `PM_DIRECTIVE_TEMPLATE.md`의 「명령 종류」·「대상 파일」 줄, 03 4절 1항의 「첫 단계 전에 5.1절 5항을 실행하고」 문장이 3.3절의 위치 지정과 맞다. ORDER 서식 3절 제목 「대화 중 확정된 사항」도 F18 ②와 맞다 |
| D3 확인 | 직전 결함 D3(모델 ID 갱신의 적용 시점과 대조 기준) | 해소 | F9 ①이 적용 시점을 PM 세션의 기동으로 정하고, 실행 중인 PM이 띄우는 서브에이전트는 기동 때의 값으로 실행한다고 적어 실험 ②(`inherit`는 오케스트레이터 모델을 따름)와 맞다. F9 ②가 대조 기준을 REQ 첫 버전 `created:`(07 3절 표의 REQ 필수 필드, 날짜 형식)로 바꿔 `approved:`가 비어 있는 REQ 작성 파이프라인에서도 기준이 정해진다. F6 ③, F8 ①, 3.3절 4번 ②, 위험 5, 완료 기준 7·8이 같은 내용으로 바뀌었다. 참고: 첫 REQ 작성 PM 세션이 자정을 넘겨 v01을 만들고 그 사이 갱신이 있으면 근거 칸의 「`created:`는 모든 PM 실행보다 앞서거나 같은 날」이 맞지 않는 경계가 있으나, 그 결과는 중단 6항 보고로 드러나 사람이 처리하므로 결함으로 보지 않는다 |
| ① | REQ 목적의 누락·왜곡 없음 | PASS | 변경분이 REQ 체크리스트 10 ④와 ORDER 3절 15항(REQ 작성 파이프라인은 분류와 관계없이 고급)을 모든 REQ 새 버전 경로에 적용한다(F5, F18, 3.1절 둘째 표 둘째 행) |
| ② | EC scope가 REQ scope 안 | PASS | 머리말 `scope:` 변경 없음(diff의 첫 변경 덩어리가 32행부터 시작). F18이 고치는 위치(03 3절 1항·4절 1항·7절 9항·13절 1항, 04 1.2절, 05 3절, `PM_DIRECTIVE_TEMPLATE.md`)는 모두 기존 EC scope 안이다 |
| ③ | 요청하지 않은 기능·추상화 없음 | PASS | 신설한 「REQ 새 버전 명령」과 7절 9항은 직전 결함 D2의 이행 수단이며, 위험 11에 비용과 Critical·Major 기본값 안건에서 절차가 늘지 않는다는 점을 적었다 |
| ④ | 완료 기준을 확인할 수 있음 | PASS | 완료 기준 4·7·8이 F18 ②~⑤, F9 ①②의 적용본 위치로 확인 방법을 정한다 |
| ⑤ | REQ 「결정」 열의 결정이 반영되었다 | PASS | D5 수정안이 EC에 넘긴 「갱신 적용 시점」이 F9 ①②로 두 파이프라인 모두에서 정해졌다. 「결정 반영 원칙」에 ORDER 3절 15항의 이행 번호(F5·F18)가 더해졌다 |
| ⑥ | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | 변경분 밖. 직전 판정서 ⑥과 같다 |
| 기타 | EC 안의 정합성(`Workflow/03_라이프사이클` 5.1절 1항 결함 정의의 모순) | FAIL | F18 ①의 04 1.2절 「REQ 새 버전」 문안과 F18 ②의 05 3절 표 아래 문안이 근거 파일을 서로 다르게 적는다(결함 D4) |

**이전 버전과의 관계 대조**: EC 1절 「이전 버전과의 관계」가 적은 고친 곳을 `git diff --no-index` 결과와 대조했다. 결함 D1·D2·D3 항목에 적은 위치가 모두 diff에 있고, diff의 변경 가운데 그 목록에 없는 곳은 없다.

## 3. 체크리스트 대조 (최종 판정만)
- 해당 없음 (EC 판정)

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 변경분 조회(실행하지 못함) | Bash `cd "/d/Vibe Coding/Vibe Standard_v04" && date "+%Y-%m-%d %H:%M:%S %z" && git diff --no-index Departments/Design/docs/tad/EC-022_v01.md Departments/Design/docs/tad/EC-022_v02.md; echo "exit=$?"` | 2026-10-10T14:55+09:00 이전(아래 판정 시각 조회 전) | 메시지 원문: `This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.` |
| 변경분 조회(실행하지 못함) | PowerShell `Get-Date -Format o; git diff --no-index ...; "exit=$LASTEXITCODE"` | 같음 | 메시지 원문: `Command contains expandable strings with embedded expressions` |
| 변경분 조회(실행하지 못함) | PowerShell `Get-Date -Format o; git diff --no-index ...; $LASTEXITCODE` | 같음 | 메시지 원문: `This PowerShell command contains multiple operations. The following part requires approval: Get-Date -Format o; git diff --no-index Departments/Design/docs/tad/EC-022_v01.md Departments/Design/docs/tad/EC-022_v02.md; $LASTEXITCODE` |
| 대신한 명령(변경분 조회) | PowerShell `git diff --no-index Departments/Design/docs/tad/EC-022_v01.md Departments/Design/docs/tad/EC-022_v02.md` | 같음 | 출력 74.4KB(도구가 파일로 저장해 전부 열람). 첫 줄: `diff --git a/Departments/Design/docs/tad/EC-022_v01.md b/Departments/Design/docs/tad/EC-022_v02.md`, `index 600a915..e86b10f 100644`. 변경 덩어리 머리: `@@ -32,7 +32,7 @@`, `@@ -47,6 +47,12 @@`, `@@ -80,16 +86,16 @@`, `@@ -111,7 +117,8 @@`, `@@ -124,12 +131,12 @@`, `@@ -137,19 +144,20 @@`, `@@ -163,7 +171,7 @@`, `@@ -179,28 +187,32 @@`, `@@ -225,9 +237,10 @@`, `@@ -282,15 +295,16 @@`, `@@ -298,11 +312,11 @@` |
| 변경 규모 | PowerShell `git diff --no-index --stat Departments/Design/docs/tad/EC-022_v01.md Departments/Design/docs/tad/EC-022_v02.md` | 2026-10-10T14:55+09:00 무렵 | ` .../docs/tad/{EC-022_v01.md => EC-022_v02.md}      \| 70 +++++++++++++---------`, ` 1 file changed, 42 insertions(+), 28 deletions(-)` |
| 시각 조회(diff 직후) | PowerShell `Get-Date -Format o` | 2026-10-10T14:55:45+09:00 | `2026-10-10T14:55:45.8410420+09:00` |
| D1 잔여 확인 | Grep `\(F\d+\)\|문서 근거\|실험 기록 v01 F` (`EC-022_v02.md`, `-o`) | 2026-10-10T14:55+09:00 무렵 | 「(Fn)」 출현 행 50·52·106·108·120·150·153·165·175·269·299·301~306. 출처 없는 실험 기록 번호 인용 없음(2절 D1 확인) |
| 부적합 누적 조회 | Grep `^(recorded_at\|  - C\d\|proposals:\|causes:)` (`Departments/Quality/docs/nonconformance`) | 2026-10-10T14:55+09:00 무렵 | `C3`을 `proposals:`에 적은 최근 기록 `NCR-019_03`(2026-10-10T05:30:43+09:00) 뒤 `C3` 기록 없음 |
| 판정 시각 | PowerShell `Get-Date -Format o` | 2026-10-10T14:55:54+09:00 | `2026-10-10T14:55:54.9722812+09:00` |

- 커밋 전 검사와 인수 시험 재실행은 EC 판정 기준의 대상이 아니므로 실행하지 않았다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D4 | `EC-022_v02` 3.2절 F18 ①(04 1.2절 「REQ 새 버전」 문안의 「근거 파일로 쓸 기록(문체 반영이면 그 승인 기록, 그 밖이면 결정을 적은 ORDER 새 버전)」)과 F18 ②(05 3절 표 아래 항목) | **모순·단일 원천 위반**. F18 ②는 「문체 반영」의 근거 파일을 「그 REQ 승인의 승인 기록(대표님 본인이 승인 필드를 기재했으면 그 REQ 파일)」로 정하는데, F18 ①은 같은 내용을 04 1.2절에 다시 적으면서 괄호 안 예외를 뺐다. 대표님 본인이 `# 문체 반영` 주석으로 승인한 REQ(07 3.1절 2·4항: 이때 승인 기록을 만들지 않는다)에서 Minor PM이 9항으로 멈추면, 04를 따르는 PM은 있지 않은 「승인 기록」을 근거 파일로 보고한다. 또 EC 3.1절 원천 표는 실행 명령의 종류·형식·지시문(「REQ 새 버전 명령」 포함)의 원천을 05 3절로 정하고 다른 문서는 참조만 둔다고 하므로, 04가 근거 파일의 종류를 다시 적는 것은 EC 자신의 원천 표와도 맞지 않는다. 04 1.2절 문안의 근거 파일 부분을 05 「실행 명령」 참조로 바꾸는 등 한 곳에만 두어야 한다 | 설계 |

## 6. 문체 지적
- 없음

## 7. 삭제 대상 (최종 판정만)
- 해당 없음 (EC 판정)

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
- 해당 없음 (EC 판정)
