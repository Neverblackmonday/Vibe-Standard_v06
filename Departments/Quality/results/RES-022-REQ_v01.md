---
task_id: "022"
gate: "REQ"
result: "fail"
completed_at: "2026-10-10T12:52:59+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-022-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-022_v01.md`(입력 ORDER `Departments/Secretariat/assets/inbox/ORD-006_v11.md`)
- **판정 차수**: 1차(최초 판정)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-022_01.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 3절 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절의 원문 J·K·M·N(선택형 질문·답 포함)·O·P(선택형 질문·답 포함)·Q·R·S·T, 요구 항목 10, 「REQ에서 정할 사항」 9개 항목, 3절 5·11~17항을 ORDER 1절(91~236행), 2절(352, 375, 379~386행), 3절(395, 401~407행)과 줄마다 대조했다. 차이가 없다(이중 공백 「기존의  설계」, 「오더 006  확정」 포함, Grep 대조 결과 두 파일에 같은 줄이 각 5건). 요구 항목 10의 요구(분류 정의, 품질 평가 단계, 모델 등급·기본값, 단계별 모델, 기본값 밖 사용의 명시·승인, 핫픽스, 분류 제안·확정, 현행 규정 삭제와 묶인 규정, 격상)는 체크리스트 10 ①~⑫에 모두 대응한다. 입력 ORDER의 작업 트리 변경은 머리말 `related_req:`에 1줄 추가뿐이다(`git diff --stat`) |
| ② | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 요구 항목은 10 하나이고 체크리스트도 10 한 행이다(1절 「5절 체크리스트의 번호는 요구 항목 번호와 같다」) |
| ③ | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | FAIL | 결함 D1. 요구 밖 경로는 없다(4절 표 아래 scope 경로별 사유가 경로마다 있고, Grep 결과 `Workflow/01`·`02`·`05`·`06`·`07`, 서식 5개, `.claude/agents/` 6개에 분류·모델·`auditor.model` 관련 문장이 있다). 다만 `AGENTS.md`를 scope에서 뺀 사유가 사실과 맞지 않아, 결정 표 권고안(D9~D11)이 요구하는 실행을 scope가 덮는지 확인할 수 없다 |
| ④ | 분류와 `workflow:`가 2절과 맞다 | PASS | `classification: "Critical"`. 대상이 거버넌스 파일(`Workflow/`, `.claude/agents/`)이므로 현행 2절 표 Critical 「적용 대상」에 맞고 ORDER `classification_proposal: "Critical"`과 같다. `workflow:`는 `Development: 실험` → `Design: EC 판단` → `Design: EC 작성` → `Quality: EC 판정` → `Design: 명세` → `Quality: 명세 판정` → `Quality: 인수 시험` → `Development: 구현` → `Quality: 최종 판정`으로 2절 Critical 행, 11.2절 2항(실험 단계 항목 형식과 위치), 12절 2항(인수 시험 위치)과 맞다. `scope:`에 실험 폴더 `Lab/REQ-022_모델지정`과 EC 경로가 있다 |
| ⑤ | 완료 기준을 실행이나 열람으로 확인할 수 있다 | FAIL | 결함 D2. 체크리스트 10 ⑥의 「특정 모델 하나로 고정하는 문장이 없다」는 같은 체크리스트 ③·④가 요구하는 문장과의 경계가 정해지지 않아 열람으로 한 가지 결과를 낼 수 없다. 나머지 ①~⑤, ⑦~⑫는 적용본·결과서 열람과 기재된 검색 결과로 확인할 수 있다 |
| ⑥ | 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 결함 D2(체크리스트 10 ⑥), 결함 D1(D10 근거가 서비스가 다른 모델을 전제하는데, 그 모델로 원스톱 파이프라인·최종 판정을 실행하는 방식이 정해지지 않음). 문체 지적 S1 |
| ⑦ | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 2절 「목적」은 모델 지정 방법을 실험과 EC로 넘긴다. 4절 「작업」 열은 실측 대상과 산출물 이름만 적는다. 3절 D5·D6·D8의 권고안은 단일 원천, 확인 책임, 기재 범위 같은 정책이며 「명령·정의 파일에서 모델을 지정하는 방법」, 「기재 위치와 문구」는 EC로 넘긴다. D5의 「모델 ID를 적는 위치」는 ORDER 「REQ에서 정할 사항」 넷째 항목이 REQ에서 정하라고 넘긴 정책이다 |
| ⑧ | 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 4절 실행 계획과 5절 체크리스트가 D1~D13 권고안을 전제로 한다는 사실이 3절 표 아래 둘째 항목과 5절 머리 안내에 있고, 체크리스트 항목마다 해당 결정 번호(D1~D11)를 괄호로 적었다 |

**그 밖의 확인**
- 2절 「배경」의 사실 대조: `Workflow/04` 1절(모델 표, 14~16행), 2절(effort), 4절(35행), `Workflow/03` 4절 4항(102행)·5.2절 5항(162행)·7절 6항(181행)·8절(197행)·13절 `C8`(301행), `Workflow/05` 65행 명령 형식, `REQ_TEMPLATE.md` 73행, `RES_TEMPLATE.md` 8행 주석, `AUDIT_TEMPLATE.md` 27행, `PM_DIRECTIVE_TEMPLATE.md` 12행, `Workflow/06` 7절 1·5행(178·182행), `.claude/agents/` 6개의 `model: inherit`, `.claude/` 아래 `settings.json`에 「model」 문자열 없음, `check_standard.py`가 있는 `Departments/Development/assets/scripts/`에 `model`·`auditor`·`Opus`·`classification` 문자열 없음을 Grep으로 확인했다. 배경 기재와 같다.
- 최신 커밋은 `97262f3`이며 REQ 2절 「배경」의 기재와 같다.
- 머리말 `approved:`는 비어 있다(승인 전 상태와 맞음).
- 참고(결함 아님): D12 권고안대로 실험 단계에서 중급 모델 시험 세션을 띄우려면 개발 서브에이전트가 그 세션을 기동해야 한다. 서브에이전트 정의는 `disallowedTools: Agent`이며(`Workflow/06` 3절), 셸로 다른 세션을 띄우는 명령은 `allow` 목록에 있는지 확인하지 않았다. 실험 중 `Workflow/03` 7절 5항으로 멈출 수 있다.

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 실행하지 못한 명령(대신함) | Bash `cd "/d/Vibe Coding/Vibe Standard_v04" && python -I - <<'EOF' …`(REQ 1절 인용 줄과 ORDER 줄의 일치 대조), PowerShell `$code = @' … '@; python -I -c $code`, Bash `python -I -c "…"` | 2026-10-10T12:51:33+09:00 이전 | 실행되지 않음. 메시지 원문: 첫째 「This Bash command contains multiple operations. The following part requires approval: python -I -」, 둘째 「This PowerShell command contains multiple operations. The following part requires approval: $code = @' …」, 셋째 「This command requires approval」. 대신 Read 도구로 두 파일의 해당 줄을 열어 줄마다 대조하고, 공백까지 달라지기 쉬운 줄과 긴 줄의 끝 부분을 Grep으로 두 파일에서 같은 건수가 나오는지 확인했다(아래 행). 이 대조는 판정 기준 ①의 근거이며 시각·변경 목록·종료 코드·해시 같은 명령 결과값을 요구하는 확인이 아니다(`Workflow/03` 5.2절 1·3항) |
| 인용 대조 | Grep `최종 판정 반려 누적 때의 격상 규정도 새 분류 기준에 맞춘다\(3절 5항, 1절 경위의 원문 L 뒤 항목\)\.$\|모델 등급 필드를 두지 않음: 원문 Q 둘째 메시지 뒤 비서실 권고와 셋째 메시지\)\.$\|비서실 권고는 같은 최고급 모델, 같은 effort로 판정하는 것\)$\|기존의  설계나\|오더 006  확정` (count, `ORD-006_v11.md`·`REQ-022_v01.md`) | 2026-10-10T12:51:33+09:00 이전 | `REQ-022_v01.md:5`, `ORD-006_v11.md:5` |
| 최신 커밋 | Bash `git log -1 --format=%h` | 2026-10-10T12:51:33+09:00 이전 | `97262f3` |
| 입력 ORDER 변경 확인 | Bash `git diff --stat -- Departments/Secretariat/assets/inbox/ORD-006_v11.md` | 2026-10-10T12:51:33+09:00 이전 | `1 file changed, 1 insertion(+)`(LF→CRLF 경고 1줄 포함) |
| 사본·참조 조회 | Grep `opus\|Opus\|Fable\|판정 모델\|claude-opus\|classification\|격상\|차상위 분류` (저장소 루트, `Departments/`·`_archive/`·`Audits/`·`CEO/`·`Lab/`·`Storage/` 제외), Grep `모델\|분류\|auditor\|effort` (`Workflow/`), Grep `model\|모델\|분류\|격상` (`.claude/`), Grep `model\|auditor\|Opus\|classification` (`Departments/Development/assets/scripts/`, 대소문자 무시) | 2026-10-10T12:51:33+09:00 이전 | 2절 「그 밖의 확인」 첫 항목의 위치들. `AGENTS.md`의 해당 문자열은 개정 이력 68행 「판정 모델 규정 강화」뿐. `scripts/`는 「No matches found」 |
| ORDER의 모델 출처 조회 | Grep `Astra\|astra\|Sol급\|Luna\|서비스가 서로` (`ORD-006_v11.md`) | 2026-10-10T12:51:33+09:00 이전 | 320행 「GPT-6 계열은 Astra(2026-09-03 공개, 최상위 모델), Sol(…), Luna(…) 세 모델이다」 외 |
| 시각 조회 | Bash `date "+%Y-%m-%dT%H:%M:%S%z"` | 2026-10-10T12:51:33+09:00 | `2026-10-10T12:51:33+0900` |
| 판정 완료 시각 | Bash `date "+%Y-%m-%dT%H:%M:%S%z"` | 2026-10-10T12:52:59+09:00 | `2026-10-10T12:52:59+0900` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | 4절 표 아래 넷째 항목(scope 제외 사유), 3절 D9·D10·D11 | scope 제외 사유가 사실과 맞지 않고, Claude Code 밖 모델의 처리가 빠졌다. ① 넷째 항목은 `AGENTS.md`를 빼는 근거로 「「불변 원칙」 4항은 판정 모델을 `Workflow/04_모델_운용`에 맡기고 모델 이름을 적지 않으며」라고 적었다. 그러나 4항은 「판정은 Claude Code의 독립된 품질 서브에이전트가 … 수행한다. 그 밖의 세션이 작성한 판정서는 무효다」로 판정 세션의 실행 환경을 정한다. ② ORDER 3절 12항의 등급에는 Claude가 아닌 모델(최고급 Astra, 고급 Sol급·Gemini Pro급, 중급 GPT Luna급·Gemini Flash급)이 있다. ORDER 1절 경위 320행은 Astra·Sol·Luna를 OpenAI GPT-6 계열로 적었고, D10 근거도 「최고급 모델(Fable급, Astra)은 실행할 수 있는 서비스가 서로 달라」라고 적는다. ③ 그런데 D9·D11 권고안은 승인된 최고급 모델로 그 안건을 실행하고 같은 최고급 모델로 최종 판정하게 한다. 대표님이 Astra를 승인하면 최종 판정서가 Claude Code 품질 서브에이전트가 아닌 세션에서 나오고, 4항에 따라 무효가 된다. 원스톱 파이프라인(PM과 서브에이전트, `Workflow/05` 3절 `claude --model` 명령)도 그 모델로 실행할 수 없다. REQ는 이런 모델을 파이프라인에서 쓸 수 있는지 정하지 않았고, 쓸 수 있으면 필요한 `AGENTS.md` 개정을 scope에 넣지 않았으며, 쓸 수 없으면 그 한계를 결정 사항이나 체크리스트에 적지 않았다. 체크리스트 10 ④·⑧의 「단계마다 정해진 모델로 실행」도 그 모델에서는 확인할 수 없다. 고칠 방향(구현 방법은 정하지 않음): Claude Code에서 실행할 수 없는 등급 모델을 원스톱 파이프라인·판정에 쓸지를 결정 표의 정할 일로 올려 대표님이 정하게 하거나 ORDER 확정 사항의 범위 안에서 한계를 적고, 그 결정에 맞게 `AGENTS.md` scope 포함 여부와 제외 사유를 고친다 | PM |
| D2 | 5절 체크리스트 10 ⑥ | 「적용본 전체(설계·개발 적용본 폴더의 모든 파일)에 판정 모델이나 파이프라인 모델을 특정 모델 하나로 고정하는 문장이 없다」가 같은 체크리스트가 요구하는 문장과 겹친다. ③은 「기본값(고급 Opus 최신 버전·`medium`…)」, ④는 「REQ 작성 파이프라인(PM의 REQ 작성과 REQ 판정)은 분류와 관계없이 고급」을 요구하므로 적용본에는 「REQ 판정은 고급 기본값(Opus 최신 버전)으로 실행한다」는 뜻의 문장이 들어간다. ⑧(D5)은 등급별 기본 모델의 모델 ID를 한 문서에 적게 한다. scope 안의 서식(`REQ_TEMPLATE.md`, `RES_TEMPLATE.md`)에는 머리말 예시값 `model: "Claude Opus 5.5"`가 있다. 이 문장과 예시값이 「특정 모델 하나로 고정하는 문장」인지 정해지지 않아, 같은 적용본을 두고 최종 판정이 `pass`와 `fail` 가운데 어느 쪽으로도 판정할 수 있다. 금지 대상을 특정해야 한다(예: 현행 「`auditor.model`은 `Claude Opus 5.5`여야 한다」나 「파이프라인 안의 모든 서브에이전트 `Claude Opus 5.5`」처럼 분류·단계·승인과 관계없이 모델 하나를 정하는 문장으로 한정하고, 등급별 기본값·단계별 모델 규정, 모델 ID 원천 문서, 머리말 예시값은 대상이 아니라고 적는다) | PM |

## 6. 문체 지적
> 지적의 구분과 처리는 `Workflow/03_라이프사이클` 「판정 지적의 구분과 문체 지적 처리」를 따른다. 이 판정은 `fail`이므로 결함을 고치는 같은 새 버전에 함께 반영한다(5.1절 6항).

| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | 3절 표 아래 셋째 항목 | 이 REQ 자체는 현행 규정(파이프라인 안 모든 세션 `Claude Opus 5.5`)으로 진행한다. | 이 REQ 자체는 현행 규정(파이프라인 안 모든 세션 `Claude Opus 5.5`)으로 진행한다. 실험 폴더 안의 시험 세션은 D12의 결정을 따른다. | PM |

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
