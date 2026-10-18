---
task_id: "014"
gate: "EC" # REQ | EC | FINAL (REQ 판정, EC 판정, 최종 판정)
result: "fail" # pass | fail | rejected
completed_at: "2026-10-09T09:43:44+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델. 다르면 무효(Workflow/04_모델_운용 「모델」)
  effort: "medium (실행 명령 기준)" # PM 지시문의 effort 표기에서 전달받은 값(Workflow/04_모델_운용 「모델 메타데이터 기록」)
---

# RES-014-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-014_v01.md` (v01, `status: draft`). 대조 기준 `Departments/Secretariat/docs/requests/REQ-014_v01.md`(승인 `2026-10-09T09:25:18+09:00`, 근거 `Departments/Secretariat/assets/inbox/승인기록_20261009_REQ-014_v01.md`)
- **판정 차수**: 1차

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「단계별 통과 조건과 판정 기준」 표의 「EC 판정」 행이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | 요구 항목 1~13과 D1~D14가 EC 3.2절 F1~F20, 3.3절 1~13번에 모두 대응한다. D8은 REQ 「결정」 열의 수정 결정(승인 기록 D8 원문)대로 F12·5절 7번에 반영되었고, D11은 2.3절에서 「문서 변경 없음」으로 처리되어 REQ 권고안과 같다. 다만 요구 항목 10의 설계(F13, 3.3절 9번 ④)가 기존 07 3.1절 6항과 두 가지로 읽히고(결함 D2), 요구 항목 11의 기록 방법(F14, 3.3절 10번 ①)이 범위 제외로 둔 `Workflow/04_모델_운용` 3절과 모순된다(결함 D1) |
| 2 | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 13개 항목은 모두 REQ `scope:` 안에 있다. `Workflow/templates/*` 6개는 REQ의 `Workflow/templates` 폴더 항목 안이고, `Workflow/04_모델_운용.md`는 EC에서 빠졌다(부분집합). 2.1절 1~14번은 부서 직속 `results/`·`workspace/` 경로다 |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 새 서식 4개는 3절 13항(V3 승인)이 정했다. 새 폴더는 `assets/planning/` 하나이며 D1 권고안 범위다. 기획 승인·설계 동결·출시 승인 게이트를 넣지 않았다(2.3절). 검사·권한 파일은 대조만 한다(3.4절) |
| 4 | 완료 기준을 확인할 수 있음 | PASS | 5절 1~16번은 적용본 열람, Grep, `git diff --no-index`, `check_standard.py` 종료 코드로 확인한다. 다만 D1을 고치면 5절 4번(「04 적용본이 없다」)과 11번의 확인 대상이 바뀔 수 있다 |

**사실 대조**(EC 1절 「변경 배경」)
- 최신 커밋 `300437f`(2026-10-09T08:45:29+09:00), 작업 트리에 `AGENTS.md`·`Workflow/` 변경 없음: 아래 검증 기록과 같다.
- `check_standard.py` 35~39행 `WHITELIST_PREFIXES`에 `Departments/Secretariat/assets/`, 68~70행 부서 직속 `results/`·`workspace/` 제외, 115행 `load_latest()`의 `{kind}-*.md` glob: 파일 열람 결과와 같다.
- `.gitattributes` 9행 `Departments/**/REQ-[0-9][0-9][0-9]*.md`는 파일명이 `REQ-`로 시작할 때만 맞으므로 `실행기록_REQ-xxx.md`와 겹치지 않는다. 13행(`workspace/**`)과 15행(`Departments/Secretariat/assets/*/**`)이 실행 기록과 `assets/planning/` 내용을 배포본에서 뺀다. EC 3.4절 1번 ④의 대조 대상과 맞다.
- `.claude/settings.json` `deny`에 `Departments/Secretariat` 경로가 없고 `ask`에 `Bash(git push*)`가 있다: 열람 결과와 같다.
- `.claude/agents/`에서 Grep `승인 기재|재판정|결정|푸시|브리핑|실행 기록` 결과 0건: 같다.
- 승인 기재 주체로 PM을 적은 현행 문장(`Workflow/01` 40행 PM 행, `Workflow/02` 46행 PM ④·69행 「승인 기재」 행, `Workflow/07` 95행 3.1절 3항)은 모두 EC 3.3절 6번 ①~③이 다룬다. Grep `승인 기재|승인 기록|대리 기재|결정」 열`(`AGENTS.md`, `Workflow/`, `.claude/agents/`)로 확인했다.

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(EC 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 범위 대조 | `git status --porcelain -uall` | 2026-10-09T09:42:04+09:00~09:43:44+09:00 사이(앞뒤 `date -Iseconds` 결과) | `?? Departments/Design/docs/tad/EC-014_v01.md` / `?? Departments/Quality/results/RES-014-REQ_v01.md` / `?? Departments/Secretariat/assets/inbox/ORD-003_v03.md` / `?? Departments/Secretariat/assets/inbox/ORD-003_v04.md` / `?? Departments/Secretariat/assets/inbox/승인기록_20261009_REQ-014_v01.md` / `?? Departments/Secretariat/docs/requests/REQ-014_v01.md` |
| 기준 커밋 | `git log -1 --format="%H %cI"` | 2026-10-09T09:42:04+09:00~09:43:44+09:00 사이(앞뒤 `date -Iseconds` 결과) | `300437f55168e364f8719fd7b496979550d9f683 2026-10-09T08:45:29+09:00` |
| 서브에이전트 정의 Grep | Grep `승인 기재\|재판정\|결정\|푸시\|브리핑\|실행 기록` (`.claude/agents`) | 2026-10-09T09:42:04+09:00~09:43:44+09:00 사이(앞뒤 `date -Iseconds` 결과) | `Found 0 total occurrences across 0 files.` |
| 커밋 전 검사 | 실행하지 않음 | — | EC 판정은 문서 판정이며 산출물 변경이 없어 실행 대상이 아니다 |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | EC 3.2절 F14 「기록」, 3.3절 10번 ① 「기록」, 2.3절 `Workflow/04_모델_운용.md` 항 | **모순.** F14는 「오케스트레이터가 그 재판정 지시문에 초기화 사실을 적고」로 정한다. 그러나 현행 `Workflow/04_모델_운용` 3절 1항은 서브에이전트 지시문에 「REQ 경로, EC 경로, 대상 파일 경로, 단계명, effort 표기만」 넣게 하고, 3항은 재판정 지시문에 「직전 판정서의 결함 표와 문체 지적 표, 반려 부서 결과서의 수정 목록, 변경분만」 넣게 한다. EC 2.3절은 04를 고치지 않는다고 정했으므로, 명세가 EC대로 03 8절을 쓰면 03과 04가 서로 다른 지시문 구성을 정하게 된다. 품질 서브에이전트가 「판정 차수」에 초기화를 적으려면 지시문으로 그 사실을 받아야 하므로, 04를 그대로 두면 F14의 기록 방법은 실행할 수 없다. 고치는 방법은 설계가 정한다. 예: (가) 04 3절 3항에 「대표님 답 뒤 다시 세는 재판정이면 그 사실」을 더하고 EC `scope:`·2.1절·2.3절·5절 4번에 04를 반영한다(REQ `scope:`에 `Workflow/04_모델_운용.md`가 있고, REQ 체크리스트 4번 ④는 3절 1항과 무관한 04 변경을 허용한다) (나) 04를 고치지 않는 다른 전달 방법을 정하고 그 방법이 04 3절 1·3항과 맞는 근거를 적는다 | 설계 |
| D2 | EC 3.2절 F13 「07 적용본 3.1절에 8항」 문안, 3.3절 9번 ④ | **중의성.** 8항 문안은 「대표님이 의결 요청(REQ 승인 요청 포함)에 답해 권고안이 아닌 선택지나 수정안을 고르면, 그 결정을 「결정」 열에 기록하고 REQ 새 버전을 작성하지 않는다」이고, 6항(「승인 필드를 기재한 뒤 결정을 바꾸려면 REQ 새 버전을 작성한다」)은 그대로 둔다. 「(REQ 승인 요청 포함)」은 승인 요청 밖의 의결 요청도 8항 대상이라고 읽히게 한다. 승인 필드 기재 뒤 원스톱 파이프라인이 중단 조건으로 멈춰 대표님이 결정 표의 선택을 바꾸는 경우, 8항으로 읽으면 「결정」 열만 고치고 새 버전을 만들지 않으며, 6항으로 읽으면 REQ 새 버전을 만든다. F13 근거 칸과 REQ D12 권고안은 「15항은 승인 때의 결정 기록이고 6항은 승인 뒤의 변경」이라고 구분하지만, 이 구분이 8항 문안에 없다. 8항 문안에 적용 시점(승인 필드와 같은 기재 작업에서 확정하는 결정. 승인 필드 기재 뒤의 변경은 6항)을 명시하거나, 승인 요청 밖의 의결 요청이 무엇을 가리키는지 정해야 한다 | 설계 |

## 6. 문체 지적
없음.
