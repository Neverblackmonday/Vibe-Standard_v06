---
task_id: "015"
gate: "EC" # REQ | EC | FINAL (REQ 판정, EC 판정, 최종 판정)
result: "fail" # pass | fail | rejected
completed_at: "2026-10-09T12:10:00+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델. 다르면 무효(Workflow/04_모델_운용 「모델」)
  effort: "medium (실행 명령 기준)" # PM 지시문의 effort 표기에서 전달받은 값(Workflow/04_모델_운용 「모델 메타데이터 기록」)
---

# RES-015-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-015_v01.md` (근거 REQ `Departments/Secretariat/docs/requests/REQ-015_v02.md`)
- **판정 차수**: 1차

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 「단계별 통과 조건과 판정 기준」 표의 EC 판정 행 ①~⑤다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | 요구 항목 1~5가 EC 3.2절 F1~F19, 3.3절 1~12번에 대응한다. 다만 요구 항목 1·3·4·5의 핵심 절차인 「최종 승인 커밋」이 EC 안에서 서로 어긋나 그대로 명세하면 실행할 수 없다(5절 D1). 요구 항목 4의 목적(일회성 파일을 최종 판정서 승인 뒤 커밋에서 함께 정리)이 추적 중인 일회성 파일이 있는 안건에서 이루어지지 않는다 |
| 2 | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 14개 경로는 REQ `scope:` 안이다. 서식 7개는 REQ의 `Workflow/templates` 폴더 아래이며 `Get-ChildItem Workflow/templates` 결과로 7개 파일이 모두 있다. 2.1절 1~15번은 부서 직속 `results/`·`workspace/` 경로다 |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | F6~F8은 ORDER 원인 B(`ORD-004_v01` 36행 「금지 명령, 실패 정의, 한글 인코딩, 멈춘 뒤 되돌리지 않음」)에서 나왔다. F14의 HOTFIX 번호 문장과 F13의 AUDIT `session`은 D7 ②·③(비서실 산출물·HOTFIX의 세션 기록, 번호 충돌 방지)의 범위 안이다. 호출 문구 서식 파일과 잠금 파일을 두지 않는다(F4, F10) |
| 4 | 완료 기준을 확인할 수 있음 | PASS | EC 5절 1~9번이 적용본 절·Grep·Glob·`check_standard.py` 종료 코드로 확인 방법을 정한다. 3.4절 1번 ①~⑥이 구현 단계 대조 항목을 정한다 |
| 5 | REQ 「결정」 열의 결정 반영 | PASS | REQ 3절 D1~D9 「결정」 열은 모두 「권고안」이다. D1→F3·3.3절 3번, D2→F4·F5, D3→F1, D4→F19·3.3절 3번 ②~⑧, D5→F15~F18, D6→3.3절 12번 1항, D7→F9·F10·F12~F14, D8→F11, D9→머리말 effort `medium` |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(EC 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 기준 커밋 확인 | `git log -1 --format="%h %cI"` | 2026-10-09T12:08:04+09:00 | `5ff92a1 2026-10-09T10:55:22+09:00` |
| 원본 변경 여부 | `git diff --stat 5ff92a1 -- AGENTS.md Workflow` | 2026-10-09T12:08:04+09:00 | (출력 없음) |
| 서식 파일 존재 | `Get-ChildItem Workflow/templates -Name` | 2026-10-09T12:08:04+09:00 | `AUDIT_TEMPLATE.md` `BACKLOG_TEMPLATE.md` `BRIEFING_TEMPLATE.html` `DEV_TEMPLATE.md` `EC_TEMPLATE.md` `HOTFIX_TEMPLATE.md` `ORDER_TEMPLATE.md` `PLAN_TEMPLATE.md` `PM_DIRECTIVE_TEMPLATE.md` `PRD_TEMPLATE.md` `REQ_TEMPLATE.md` `RES_TEMPLATE.md` `TAD_TEMPLATE.md` |
| 기존 015 판정서 | `Get-ChildItem Departments/Quality/results -Name \| Select-String 015` | 2026-10-09T12:08:04+09:00 | `RES-015-REQ_v01.md` `RES-015-REQ_v02.md` |
| 원본 절 위치 대조 | Read `Workflow/05_인수인계_및_실행명령.md` 1·1.1·2·6절, `Workflow/07_문서_서식_및_번호.md` 2절·3.1절, `Workflow/02_부서_구조_및_작업구역.md` 2.1·4절, `Workflow/03_라이프사이클.md` 5·9절 | 2026-10-09T12:05+09:00 | EC 2.2절·3.3절이 가리키는 문구(05 1.1절 1·2·5번과 6번 ⑤, 1절 ⑦ 괄호, 6절 2·3항, 02 2.1절 ③ 괄호와 4절 「최종 승인 뒤 반영」 행, 07 2절 ORDER·HOTFIX·실행 기록 항과 「비서실 산출물의 버전」 항, 3.1절 4항 1)가 원본에 있다 |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | EC 3.2절 F10·F17, 3.3절 3번 ④ 「최종 승인 커밋」 순서 4)·5) | 모순. F17은 1.1절 5번 정리에서 추적 중인 일회성 파일을 `git rm -- <경로>`로 지우게 한다. `git rm`은 작업 트리와 함께 인덱스에서도 파일을 지우므로 그 삭제가 스테이징된다. 그런데 「최종 승인 커밋」 순서는 4) 정리 뒤 5)에서 F10의 「스테이징을 시작하기 전 `git diff --cached --name-only` 결과가 비어 있는지 확인, 비어 있지 않으면 다른 세션이 Git 작업 중인 것으로 보고 멈춘다」를 실행한다. 추적 중인 일회성 파일이 「삭제 대상」에 있는 안건은 5)에서 반드시 멈추고, 3.2절 F7·F10에 따라 되돌리지도 못한다. 3.4절 1번 ①의 대조는 `check_standard.py --staged`만 보므로 이 충돌을 잡지 못한다. 수정 방향 예: F10의 시작 전 확인을 「최종 승인 커밋」 4) 정리(또는 3) 반영) 앞으로 옮기거나, 5)의 확인 대상을 「인덱스의 변경이 4)에서 `git rm`으로 지운 경로뿐인지」로 바꾼다. 어느 쪽이든 F10 본문과 3.3절 3번 ④가 같은 순서를 말하게 한다 | 설계 |

## 6. 문체 지적
> 지적의 구분과 처리는 `Workflow/03_라이프사이클` 「판정 지적의 구분과 문체 지적 처리」를 따른다.

| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | EC 3.3절 3번 ② 「세션 종료 조건」 | 「최종 승인 커밋」 3번의 「PM 기동」 | 「최종 승인 커밋」 순서 2)(1.1절 3번)의 「PM 기동」 | 설계 |
| S2 | EC 3.3절 3번 ④ 「최종 승인 커밋」 순서 1) | 1) 「승인 기록」(1.1절 2번) | 1) 「승인 기록」(1.1절 2번. 「승인 기록」 절차의 6)에서 이어 온 경우는 건너뛴다) | 설계 |

## 7. 판정 범위 밖 확인 사항
- F8의 「셸 명령은 Git Bash로 실행한다」가 Antigravity 실행 환경에서 가능한지는 이 저장소의 문서로 확인할 수 없다(확인 불가). 결함으로 분류하지 않았다.
