---
task_id: "036"
gate: "EC"
result: "fail"
completed_at: "2026-10-26T22:48:27+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기(Workflow/04_모델_운용 「모델 메타데이터 기록」)
---

# RES-036-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-036_v01.md`, `Departments/Design/results/RPT-036_v01.md` 8절 「EC 판단」. 기준 REQ `Departments/Secretariat/docs/requests/REQ-036_v02.md`(승인 `2026-10-26T21:54:40+09:00`, 「결정」 열 D1~D6 권고안)
- **판정 차수**: 1차 (최초 판정)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-036_02.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 5절 표 「EC 판정」 행 ①~⑦이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | REQ 목적의 누락·왜곡 없음 | PASS | REQ 2절 「목적」 ①~④가 EC 1절 「변경 목표」와 3.1절 표 1~4행에 하나씩 대응한다. ① PowerShell 커밋·푸시(와 D1의 삭제·이동): F1 「`ask`」, F5 ② 줄바꿈: F2 ③ 결정 범위 대조 칸: F3·F6·F7 ④ 판정 서브에이전트의 모델: F1 「훅」, F4, F5. 체크리스트 1~4가 5절 완료 기준 1~8에 대응한다. D5 범위가 좁아진 문제는 ⑤에서 다룬다 |
| ② | EC scope가 REQ scope 안 | PASS | EC `scope:` 8개(`Departments/Design/docs/tad/EC-036`, `.claude/settings.json`, `.gitattributes`, `Workflow/03_라이프사이클.md`, `Workflow/04_모델_운용.md`, `Workflow/06_통제장치_및_배포.md`, `Workflow/templates/EC_TEMPLATE.md`, `Workflow/templates/DEV_TEMPLATE.md`)가 모두 REQ `scope:`에 있다. REQ의 `.claude/agents`를 뺀 사유는 2.3절 첫 항목에 있고, 2.1절 1~12번은 부서 `results/`·`workspace/`와 품질 기록 경로다 |
| ③ | 요청하지 않은 기능·추상화 없음 | PASS | 훅은 품질 기동만 검사하고(H1) 별도 스크립트 파일을 만들지 않는다(H6, 2.3절). F3이 「EC 판정」 행 밖에 네 곳(EC 판단·명세 통과 조건, 명세 판정 ⑤, 최종 판정 기준 1)을 더 고치는 것은, 요구 항목 3이 정한 결과서 서식의 칸이 EC 없는 안건에서 쓰이고 대조되게 하기 위한 것이다(3.4절 F3 끝 항목). v05의 같은 서식도 이 칸의 쓰는 곳과 대조를 명세 판정 ⑤·최종 판정 기준 1로 정했다(`git show master:Workflow/templates/DEV_TEMPLATE.md` 10절 안내문) |
| ④ | 완료 기준을 확인할 수 있음 | PASS | 5절 완료 기준 1~12는 명령(`python -m pytest …`, `check_standard.py` 종료 코드, `git diff HEAD -- .claude/agents`, `git diff --no-index`, Glob)이나 열람 대상(적용본의 절, 개발 결과서의 실측 결과)이 정해져 있다 |
| ⑤ | REQ 「결정」 열의 결정이 반영되었다 | FAIL | D1·D2·D3·D4·D6은 3.3절 행과 반영 위치(F1 「`ask`」·2.3절·F2·F2 「D4 참고 명령」·F4)가 결정 문안과 맞는다. D5는 결함 D1·D2(5절) |
| ⑥ | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | RPT-036_v01 8절: 대상이 모두 `AGENTS.md` 「불변 원칙」 3항의 거버넌스 파일이고 `.claude/settings.json`의 `ask`(접근 권한 규칙)를 바꾸므로 2.1절 3항에 맞고, 커밋된 표준을 바꾸므로 2항에도 맞는다. 4항 ①~③에 들지 않는다는 사유도 맞다. 대상 원본이 추적 파일이고 HEAD와 같다는 사실은 아래 4절 `git status --porcelain -uall` 결과(대상 경로 변경 없음)로 확인했다 |
| ⑦ | EC가 뒤 단계의 Claude Code 세션에 실행을 지정한 명령이 「명령 형태」의 원리 안에 있다 | PASS | 지정 명령: `python -m pytest Departments/Quality/assets/acceptance/REQ-036_v01`(`Bash(python -m pytest*)`), `python Departments/Development/assets/scripts/check_standard.py`(같은 이름 규칙), `git diff HEAD -- .claude/agents`·`git diff --no-index <원본> <적용본>`(`Bash(git diff*)`), `git ls-files --eol`(`Bash(git ls-files*)`). 별칭 조회, 임시 저장소 실측, 임시 복제의 Claude Code 기동은 부서 `workspace/` 일회성 스크립트(`Bash(python Departments/*/workspace/*)`)로 하게 정했다(F1, 「구현 실측」). 적용본 복사는 Read·Write 도구로 하고 `cp`를 쓰지 않게 했다(2.1절). D4 참고 명령은 대표님이 실행하는 명령이며 실측은 스크립트 안에서 한다 |

## 3. 체크리스트 대조 (최종 판정만)
- 해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-26T22:48:27+09:00 | `2026-10-26T22:48:27+09:00` (머리말 `completed_at`과 같다) |
| 범위 대조 | `git status --porcelain -uall` (Bash) | 2026-10-26T22:47:54+09:00 이전 같은 세션 | 37행, 모두 `??`(미추적). 이 안건 관련: `Departments/Design/docs/tad/EC-036_v01.md`, `Departments/Design/results/RPT-036_v01.md`, `Departments/Quality/docs/nonconformance/NCR-036_01.md`, `Departments/Quality/results/RES-036-REQ_v01.md`, `RES-036-REQ_v02.md`, `Departments/Secretariat/docs/requests/REQ-036_v01.md`, `REQ-036_v02.md`, `Departments/Secretariat/workspace/실행기록_REQ-036.md`. 그 밖은 `REQ-035` 관련 9건과 `Departments/Secretariat/` 아래 비서실 기록. `.claude`, `.gitattributes`, `Workflow` 아래 변경은 없다 |
| 기준 커밋 | `git log -1 --format=%H%n%cI` (Bash) | 같은 세션 | `57e55ec73b351a8678ddd1d9e5a2d2160c620e02` / `2026-10-26T22:12:39+09:00` (EC 1절 「변경 배경」의 기준 커밋과 같다) |
| v05 대조(③ 근거) | `git show master:Workflow/templates/DEV_TEMPLATE.md \| grep -n -A8 "^## 10"` (Bash) | 같은 세션 | 81행 `## 10. 결정 반영 대조 (EC가 없는 안건의 설계부 결과서만)`, 82행 안내문에 「대조 기준은 … (Critical·Major는 표 「명세 판정」 행 ⑤, Minor는 최종 판정 기준 1)이다」 |
| v05 대조(③ 근거) | `git show master:Workflow/03_라이프사이클.md \| grep -n "대조 칸\|범위 대조\|3.3절"` (Bash) | 같은 세션 | 165행 「EC 판정」 행 ⑤에 「EC 「결정 반영 대조」 표(서식 `EC_TEMPLATE.md` 3.3절)에 결정마다 행이 있고, 판단 수단이 덮는 범위가 결정 문안의 범위(기간·대상)와 같거나, 다르면 그 차이와 사유가 결정과 어긋나지 않는다」 |
| 커밋 전 검사 | 해당 없음 | — | EC 판정 기준에 없다. 판정 대상 파일을 고치지 않았다 |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」을 따른다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | `EC-036_v01.md` 3.3절 D5 행 「차이와 사유」, 3.4절 F1 H3, 4절 위험 3 (연동: F4 ⑥, F5 「훅」 ⑤) | REQ D5 권고안의 대상은 「판정 서브에이전트가 판정 모델과 다른 모델로 기동되지 않게 한다」인데, EC는 최종 판정 기동에서 호출 인자를 고급 이상 계열의 다른 모델로 적는 경우를 훅이 막지 않게 정했다. 이 경우에는 최고급이 승인된 안건에서 고급 모델로 판정하는 경우, 곧 REQ 2절 「분류 근거」가 든 「판정 모델보다 낮은 모델의 판정」이 들어 있다. EC는 그 사유로 최고급 승인이 REQ 「결정」 열의 문장으로만 있어 기계가 읽을 수 없고 REQ 서식과 `Workflow/07`(`scope:` 밖)을 고쳐야 한다고 적었다. 그러나 이 사유는 확인되지 않았다. 판정 모델은 `Workflow/04_모델_운용` 1.2절 표 넷째 행대로 그 안건의 모델에서 정해지고, 원스톱 PM 세션은 그 안건의 모델로 기동되며 시작할 때 이를 확인한다(같은 절 「PM의 책임」 ①, `Workflow/05_인수인계_및_실행명령` 3절). 또 최고급은 REQ에 모델 ID를 늘 적고(`Workflow/04` 1.3절 3항) 실행 명령의 `--model`에도 들어간다. EC는 `scope:` 안의 장치(`.claude/settings.json`의 훅)가 이런 근거로 필요한 모델을 정할 수 있는지 검토하지 않았다. 검토 결과 정말 `scope:` 밖 파일이 필요하다면 REQ 3절 「D5와 `scope:`」의 처리(그 단계에서 「중단 조건」 1항으로 멈추고 보고)를 따라야 한다. 차이를 EC 안에서 남긴 채 EC 판정에 넘기는 것은 이 처리와 다르다. 고칠 방향: 최종 판정 기동이 1.2절 표의 판정 모델과 다른 모델로 기동되면 막도록 H3과 3.3절, F4, F5, 위험 3을 고친다. 그럴 수 없음을 근거와 함께 확인하면 REQ 「D5와 `scope:`」대로 멈추는 처리로 바꾼다 | Rework | 설계 |
| D2 | `EC-036_v01.md` 3.3절 D5 행 「이 EC가 정한 내용이 덮는 범위」·「차이와 사유」 | 3.3절 D5 행은 훅이 막지 못하는 경우로 D1의 경우 하나만 적었다. 그러나 EC가 정한 규칙에는 실행 전에 막지 못하는 경우가 두 가지 더 있다. 그래서 「덮는 범위」 ②(「최종 판정 기동: 호출 인자 `model`이 없는 기동(상속)과 고급 아래 모델 기동을 막는다」)가 실제보다 넓게 적혔다. (a) H3은 모델 이름에 `opus`·`fable`이 들어 있으면 통과시키므로, 1.1절 표의 값도 아니고 1.1절 「갱신」 ③이 허용하는 이전 ID도 아닌 같은 계열의 다른 버전 모델 ID(예: 이전 세대 Opus의 모델 ID)도 통과한다. PM이 한 번만 잘못 적어도 판정 모델과 다른 모델로 기동된다. (b) PM이 최종 판정의 단계명을 F4 「3절 1항」과 다르게 적고 호출 인자도 빠뜨리면 H2가 최종 판정 기동으로 보지 않아 H4로 통과하고, PM 모델(Minor이면 중급)을 이어받는다. 4절 위험 2는 이 경우를 적었지만 3.3절에는 없다. 고칠 방향: 두 경우를 설계로 막거나, 막지 않으면 3.3절 「차이와 사유」에 적고 그 사유가 D5와 어긋나지 않음을 밝힌다. D1을 고치면서 H3의 판단 방식이 바뀌면 (a)는 함께 없어질 수 있다 | Rework | 설계 |

- 두 결함 모두 승인된 REQ의 `scope:`(`.claude/settings.json`, `Workflow/04`·`06`)와 「결정」 열 안에서 EC를 고쳐 맞출 수 있으므로 Rework로 정했다(`Workflow/03_라이프사이클` 5.3절 2항). D1을 고치려면 `scope:` 밖 파일이 필요하다고 설계가 확인하면, 그 처리는 REQ 3절 「D5와 `scope:`」와 「중단 조건」 1항을 따른다.

## 6. 문체 지적
| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | `EC-036_v01.md` 3.4절 F1 「훅」 H1 | 그 밖의 호출은 통과시킨다(D6. 다른 부서 서브에이전트의 기동은 바뀌지 않는다). | 그 밖의 호출은 통과시킨다(D6. 검사가 정상으로 실행되면 다른 부서 서브에이전트의 기동은 바뀌지 않는다. 검사가 실행되지 않거나 오류로 끝나면 H6대로 모든 기동을 막는다). | 설계 |

## 7. 삭제 대상 (최종 판정만)
- 해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
- 해당 없음
