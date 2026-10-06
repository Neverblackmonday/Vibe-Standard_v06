# Vibe Standard v01 → v02 이관 검토

- 작성: 2026-10-05 19:14 (KST)
- 대상: `D:\Vibe Standard`(표준 v4.1.0, `Development/src/vibe_standard/Standard/VERSION` 기준). 비교 대상은 `D:\Vibe Coding\Vibe Standard_v02`이며, 같은 날 조회했을 때 폴더 9개만 있고 파일은 없었습니다.
- 열람 범위: 루트 설정·지침 파일, `.claude/`(훅·에이전트·스킬·설정), `Development/scripts/`, `Development/tests/`, `Standard/`(README·LIFECYCLE·CHANGELOG·VERSION), `Design/docs/tad/` 2건, 대기 목록, 8차 점검 PDF 5건, REQ-20261005-005. 2026-10-05 19시(KST)에 PC에서 받은 사본을 기준으로 했습니다.
- 열람하지 않은 것: `.env`(비밀값이 들어 있을 수 있음), 과거 REQ·RES 본문, `Operations/logs/`, 각 `workspace/` 기록, `References/` 지침 사본, `Sample/` 하위 폴더 일부. `Sample/` 하위는 폴더 조회의 깊이 제한(5단계)에 걸려 집계하지 못했습니다. 루트의 `AGENTS.md`·`setup.cmd`와 `Sample`의 같은 파일은 크기(7,492바이트, 4,258바이트)가 같아서 루트 파일로 판단했지만, 내용을 비교하지는 않았습니다.

---

## 1. 결론

v01이 복잡해진 원인은 크게 세 가지입니다.

1. **표준이 자기 자신을 개발했습니다.** 표준을 고치는 일에도 REQ → 단계 실행 → 품질 판정 절차를 적용했습니다. 이 때문에 제품 폴더, 내보내기(`export.py`), 이름 변환(`_dot_claude`), 자기 점검 2,504줄을 따로 유지해야 했습니다.
2. **기본 기능 대신 자체 구현을 쌓았습니다.** 훅·스크립트 5개가 2,103줄입니다. 승인 기록, 스냅샷, 해시, 실행 차수, 실패 결과서 이동, Bash 명령 해석까지 직접 구현했고, 그 결과 오탐이 반복되었습니다.
3. **사고가 한 번 날 때마다 규칙이 늘었습니다.** v01의 8차 점검 문서는 규칙 29개 가운데 근거가 확인되는 것이 5개뿐이라고 정리했습니다. REQ-20261005-002 한 건에서는 규칙이 다섯 번 작업을 막았지만, 실제 피해를 막은 경우는 없었습니다.

v01은 8차 점검에서 이미 다음 결론을 냈습니다. 「표준의 핵심은 REQ·RES 문서 체계와 승인 없는 수정 차단 두 가지」라는 것입니다. 따라서 v02에는 **문서 서식과 원칙은 대부분 가져오고, 자동화 코드는 거의 가져오지 않는 방식**을 권고합니다.

### 규모 비교 (v01 실측, 줄 수)

| 구분 | v01 파일 | 줄 수 | v02 권고 |
|---|---|---|---|
| 훅 | `approve_hook.py`, `guard_hook.py` | 368 + 249 | 단순화하거나 삭제(결정 1) |
| 스크립트 | `vibe_common.py`, `stage_check.py`, `check_standard.py` | 624 + 422 + 440 | `check_standard.py`만 축소(약 80줄 목표, 추정) |
| 자기 점검 | `run_selftest.py` | 2,504 | 가져오지 않음 |
| 스킬 7개 | `t-req`·`t-res`·`t-run`·`t-qa`·`t-docs`·`t-work`·`t-ops` | 316 | 2~3개로 통합 |
| 절차 문서 | `AGENTS.md`, LIFECYCLE, README | 63 + 246 + 81 | `AGENTS.md` 하나로 통합 |
| 이력·명세 | `CHANGELOG.md`, `02_실행구조.md` | 479 + 696 | 가져오지 않음(참고용으로만 보관) |

줄 수는 2026-10-05 19시에 받은 사본에 `wc -l`을 실행해 확인했습니다.

---

## 2. 그대로 가져올 것

크기가 작고, 실제 사고에서 근거가 나왔거나 전역 지침이 요구하는 항목입니다.

| 번호 | 항목 | v01 위치 | 가져올 이유 |
|---|---|---|---|
| A1 | `CLAUDE.md`를 `@AGENTS.md` 한 줄로 두는 구조 | 루트 `CLAUDE.md` | 전역 지침 1절이 이 방식을 요구합니다 |
| A2 | 배치 파일 CRLF 강제 | `.gitattributes` | W-1 사고(2026-10-02, `setup.cmd`가 LF로 저장되어 Windows 실행 오류)에서 나온 규칙입니다 |
| A3 | 핵심 엔지니어링 원칙: 선구현 금지, KISS·YAGNI, 추측 금지 | `AGENTS.md` 2절 3·4번 | 표준의 목적 자체이고 분량이 짧습니다 |
| A4 | 커밋 메시지 형식 `{type}: [REQ-{task_id}] 요약` | `AGENTS.md` 4절 | REQ와 커밋을 연결하는 유일한 수단입니다 |
| A5 | 권한 설정의 `ask`: `git commit`, `git push`, `rm`, `mv`, `cp`, `touch` | `.claude/settings.json` | Claude Code 기본 기능만으로 전역 지침의 불변 예외(커밋·푸시, 삭제·덮어쓰기 승인)를 구현합니다 |
| A6 | 반려 사유 다섯 가지와 「질문하지 않고 추측 없이 반려」 원칙 | `t-res` 2절 | 서브에이전트가 임의로 판단하지 못하게 막는 짧고 분명한 규칙입니다 |
| A7 | REQ 판정 관점 여덟 가지 | `t-req` 3절 | 판정 세션에 바로 넘길 수 있는 점검표입니다 |
| A8 | 품질 단계의 「범위 초과 대조」(요구에 없는 기능·옵션·설정을 추가하면 fail) | `t-qa` 5번 | scope 파일 안에서 생기는 과구현을 잡는 유일한 장치입니다(8차 RCCA 점검) |
| A9 | 표준 개정 원칙: 새 규칙은 사고 이력, 되돌리기 가능성, 기본 기능 대체 여부 세 가지를 따져서만 만들고, REQ 하나에는 목적 하나만 담음 | 8차 점검 「표준 규칙 정리」, `t-req` 2절 8·9번 | v02가 다시 복잡해지는 것을 막는 장치입니다. 두 문장으로 줄여 `AGENTS.md`에 둡니다 |

---

## 3. 단순화해서 가져올 것

| 번호 | 항목 | v01 형태 | v02 권고 형태 |
|---|---|---|---|
| B1 | REQ 서식 | 9개 절, 근거 절에 하위 항목 4개, 결과 줄 형식 규칙 | 요청 원문 / 배경·목적 / 결정 표 / scope(머리말) / 검증 및 완료 기준 / REQ 판정. 6개 절로 줄입니다. 6절 「작업 범위」 본문은 scope와 중복이므로 삭제합니다(8차 점검 24번) |
| B2 | RES 서식 | 5개 절, 로그 줄 9종 인용 규칙 | 머리말 `result: pass·fail·rejected` / 변경 파일 / 검증 결과(명령·시각·결과 원문) / 반려 사유(반려일 때만). 로그 인용 규칙은 삭제합니다 |
| B3 | 단계 서브에이전트 | 에이전트 4개와 스킬 4개(`t-docs`·`t-work`·`t-ops`·`t-qa`, 각 18~40줄) | 부서별 에이전트 파일 하나에 절차를 직접 적습니다. 머리말 형식(`skills`, `disallowedTools: Agent, WebFetch, WebSearch, mcp__*`, `permissionMode`)은 그대로 씁니다 |
| B4 | 실행 순서 | `t-run` 48줄(실행 차수, 단계 검사, `--close`, RCCA, `git add` 경로 규칙) | 설계 → 개발 → 품질 순서와 「실패하면 멈추고 보고」만 적습니다(약 10줄 목표, 추정) |
| B5 | 라이프사이클 | LIFECYCLE 246줄 + `AGENTS.md` 1절 | `AGENTS.md`에 한 줄로 적습니다: 접수 → REQ·판정 → 승인 → 실행 → 품질 판정 → 커밋 |
| B6 | 표준 검사 `check_standard.py` | 8개 검사, 440줄 | v01이 「유지할 것」으로 결론 낸 3개만 남깁니다: 1번(REQ·RES 이름·중복), 4번(배치 파일 CRLF·BOM), 5번(`.claude/*.json` 형식). 나머지 2·3·6·7·8번은 오탐이 기록되었거나 다른 장치와 중복됩니다(8차 점검 5·6·11~13번) |
| B7 | `setup.cmd` | 131줄, 5단계, `.env` 복사, pytest 확인 | `git init`, `core.quotepath false`, `core.hooksPath`, 첫 커밋만 남깁니다. **현재 결함:** 104행 첫 커밋 메시지는 `v4.0.0`으로 고정되어 있지만 `VERSION` 파일은 `v4.1.0`입니다. v02에서는 버전을 `VERSION` 한 곳에서 읽게 합니다 |
| B8 | 승인과 수정 차단 | 승인 훅 368줄 + 수정 차단 훅 249줄 + 공통 모듈 624줄. 승인 입력 5분 유효, `~/.vibe` 기록, 작업 트리 검사, 진행 파일, 스냅샷, REQ 해시, Bash 명령 해석 | 결정 1의 권고안: 「승인 REQ-번호」 입력을 승인 기록으로 남기고, Edit·Write 대상이 승인된 scope 안에 있는지만 확인합니다(두 훅 합계 약 100줄 목표, 추정). Bash 명령은 해석하지 않습니다. v01 오탐 대부분이 Bash 해석에서 나왔기 때문입니다(8차 점검 1·7번) |
| B9 | 폴더 구성 | 도메인 5개마다 `docs/`·`results/`·`workspace/`. 빈 폴더 `releases/`, `live/`, `logs/`, `inbox/`, `research/`, `prd/` | 부서마다 `results/`만 둡니다. 명세는 `Design/docs/`에만 둡니다. 그 밖의 폴더는 실제로 쓰게 될 때 만듭니다(8차 점검 14~18번) |
| B10 | `.gitignore` | 581바이트 | `.claude/settings.local.json`, `.env`, 캐시 항목만 남기고 쓰지 않는 `.claude/work/`는 삭제합니다(8차 점검 25번) |
| B11 | `PROJECT.md` 템플릿 | 2,516바이트 | 목표·환경·시작 방법만 둡니다. 「현행 버전」 줄은 `VERSION`과 중복이므로 삭제합니다(8차 점검 23번) |

---

## 4. 가져오지 않을 것

| 번호 | 항목 | v01 위치 | 제외 이유 |
|---|---|---|---|
| C1 | 자기 점검(기능 시험 59건, 변이 124건) | `Selftest/run_selftest.py`(2,504줄) | 자체 구현 기능을 시험하는 코드입니다. 자체 구현을 줄이면 시험할 대상이 없어집니다. 전체 실행에 약 10분이 걸립니다(8차 점검 「자체구현기능」 문서) |
| C2 | 제품·내보내기 구조 | `export.py`, `_dot_claude`·`_dot_agents`·`CLAUDE.md.tmpl` 이름 변환, `01_제품구조.md` | 표준이 자기 자신을 개발했기 때문에 생긴 구조입니다. v02 폴더 자체를 복사용 원본으로 두면 필요 없습니다(결정 2) |
| C3 | 단계 검사 | `stage_check.py`(422줄): 실행 차수 폴더, 실패 결과서 `_실패{n}차` 이동, 단계 로그 | 단계 결과는 품질 서브에이전트와 `git status`·`git diff`로 확인합니다. pre-quality 단계에서 같은 시험을 302초·271초 동안 다시 실행한 중복도 있었습니다(8차 점검 4번) |
| C4 | Bash 명령 해석·`.vibe` 문자열 차단 | `guard_hook.py` | 기록된 오탐: heredoc 커밋, `git add`, `cmp`, `awk >`, `2>/dev/null`. 대기 목록 2번에 「미처리」로 남아 있습니다 |
| C5 | 상태·중지·재실행·복구·알림 | v3.x에서 이미 삭제한 기능의 흔적 | 데스크톱 앱 작업 창과 완료 알림이 같은 일을 합니다 |
| C6 | RCCA 5칸 서식과 대기 목록 효과 검토 절차 | `t-run` 「RCCA 기록」, LIFECYCLE ⓪단계 | 절차가 무겁습니다. v02에서는 실패 보고에 「원인과 재발 방지」 두 줄을 적는 것으로 대신합니다 |
| C7 | Antigravity 훅 | `.agents/hooks.json` | 상대 경로라서 작업 폴더가 다르면 동작하지 않고, v4부터는 Antigravity가 단계 작업에 참여하지 않습니다(8차 점검 「확인 필요」 항목). 규칙은 Antigravity도 읽는 `AGENTS.md`가 맡습니다(결정 3) |
| C8 | 운영 파라미터 단계 | `Operations/live/`, `t-ops`, `operations` 에이전트 | 이 저장소에서 한 번도 쓰이지 않았습니다(8차 RCCA 점검 4번). 필요한 프로젝트에서 추가합니다 |
| C9 | 세션 시작 때 미결 안건 보고 의무 | `AGENTS.md` 4절 2번 | 거절 뒤 재의뢰하지 않은 REQ가 영구히 미결로 남습니다(8차 점검 9번) |
| C10 | 이력 문서 | `CHANGELOG.md`(479줄), `02_실행구조.md`(696줄), `_archive/`, REQ·RES·로그·브리핑 | 그대로 옮기지 않고 v01 폴더를 참고 기록으로 남겨 둡니다 |
| C11 | `References/` 전역 지침 사본(v22~v28 7건) | `References/` | 전역 지침은 세션에 주입됩니다. 사본이 쌓이면 어느 것이 현행본인지 확인하는 부담이 생깁니다 |
| C12 | `.env.example`과 `.env` 복사 단계 | 루트, `setup.cmd` 4단계 | 값을 쓰는 곳이 없는 일반 뼈대입니다(8차 점검 「확인 필요」 항목) |
| C13 | 「자체 판정 금지」 문구 6곳 이상 중복 | 에이전트 3개, 스킬 3개, `AGENTS.md`, LIFECYCLE | 중복 문구를 없애고 `AGENTS.md` 한 줄만 남깁니다(8차 점검 19번) |
| C14 | `settings.json`의 `crossSessionInbound`, `deny`의 `SendMessage`·`ListAgents`·`Bash(claude *)`·`~/.vibe` | `.claude/settings.json` | 다른 세션이 「승인」을 입력하는 것을 막기 위한 설정입니다. B8의 승인 기록 방식을 채택하면 `crossSessionInbound: refuse`만 남기고, 훅을 두지 않으면 모두 삭제합니다 |

---

## 5. v02 폴더와의 대응

v02는 `CEO/`와 `Departments/{Design, Development, Marketing, Operations, Quality, Secretariat, Visual}`로 구성되어 있습니다. v01과 비교하면 `Marketing`, `Visual`, `CEO`가 새로 생겼습니다.

- `Departments/Secretariat` ← v01 `Secretariat`(REQ 보관). `requests/` 하나만 둡니다.
- `Departments/Design`·`Development`·`Quality` ← v01의 같은 도메인. `results/`만 둡니다.
- `Departments/Operations` ← v01 `Operations`. C8에 따라 운영 단계는 가져오지 않으므로 이 폴더의 용도를 새로 정해야 합니다.
- `CEO/` ← v01 `References/`(대표님이 직접 넣고 고치는 자료)에 해당하는지 확인이 필요합니다(결정 4).
- `Marketing`·`Visual`: v01에 해당하는 도메인이 없습니다. 에이전트와 절차를 새로 정의해야 합니다.

---

## 6. 결정 사항

| 번호 | 정할 일 | 권고안 | 대안 | 근거 |
|---|---|---|---|---|
| 1 | 승인과 수정 차단 | 최소 훅: 승인 기록 + Edit·Write의 scope 판정(약 100줄 목표) | 훅 없이 권한 설정(`ask`)과 Git만 사용 | v01은 「승인 없는 수정 차단」을 핵심으로 판정했습니다(대표님 진술: 에이전트의 임의 수정). 오탐 원인인 Bash 해석만 뺍니다 |
| 2 | 표준을 관리하는 방식 | v02 폴더를 복사용 원본으로 직접 고치고, 고친 내용은 Git 커밋으로 남김 | v01처럼 제품 폴더 + 내보내기 + 자기 점검 | 자기 개발 구조가 복잡성의 가장 큰 원인입니다(C1·C2) |
| 3 | Antigravity 훅 | 가져오지 않음(규칙은 `AGENTS.md`가 맡음) | 경로를 고쳐서 유지 | 상대 경로 결함이 있고 v4부터 사용 실적이 없습니다 |
| 4 | `CEO/` 폴더 용도 | v01 `References/`(대표님 전용 자료) 역할 | 다른 용도(대표님 지정) | 확인 불가. v02 폴더가 비어 있어 용도를 판단할 근거가 없습니다 |
| 5 | 명세 파일명 버전 | 결정 2를 채택하면 Git이 이력을 관리하므로 파일명에 버전을 붙이지 않음 | 전역 지침 7항대로 `_v01` 파일명 사용 | v01 「표준 규칙 정리」 결정 2와 전역 지침 7항이 충돌합니다. 버전 없는 파일명을 쓰려면 지침 수정안을 따로 승인받아야 합니다 |

---

## 7. 근거 파일 (v01, 모두 `D:\Vibe Standard` 기준)

- `AGENTS.md`, `setup.cmd`, `.claude/settings.json`, `.claude/hooks/*.py`, `.claude/skills/*/SKILL.md`, `.claude/agents/*.md`
- `Development/scripts/*.py`, `Development/src/vibe_standard/Standard/README.md`, `Development/src/vibe_standard/Standard/VERSION`
- `Design/docs/tad/01_제품구조.md`
- `Secretariat/inbox/표준개선_대기목록.md`
- `Secretariat/briefings/20261005_8차점검_표준항목정리.pdf`(26건 점검, 이 문서에서 「8차 점검 N번」으로 인용)
- `Secretariat/briefings/20261005_8차점검_자체구현기능_기본기능대체.pdf`
- `Secretariat/briefings/20261005_8차점검_표준규칙정리.pdf`
- `Secretariat/briefings/20261005_8차점검_표준화추가개선점.pdf`
- `Secretariat/briefings/20261005_8차점검_개발함정_RCCA.pdf`
