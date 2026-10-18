---
task_id: "022"
gate: "EC"
result: "fail"
completed_at: "2026-10-10T14:42:25+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-022-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-022_v01.md`(`status: draft`). 대조 입력: `Departments/Secretariat/docs/requests/REQ-022_v02.md`, `Departments/Design/results/RPT-022_v01.md` 8절 「EC 판단」, `Departments/Development/results/DEV-022_v02.md` 6절 「실험 결과」, `Departments/Secretariat/assets/inbox/승인기록_20261010_REQ-022_v02.md`(D5·D13 수정안 원문)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-022_02.md`

## 2. 판정 기준별 결과
| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | REQ 목적의 누락·왜곡 없음 | FAIL | EC 1절 「변경 목표」와 3.1·3.2절이 REQ 2절 「목적」의 항목(분류 재정의, 모델 등급·기본값·단계별 모델, Fable 금지·판정 모델 고정 삭제, 묶인 규정 정비, 분류 제안·확정, 격상)을 모두 다룬다. 다만 REQ 체크리스트 10 ④와 ORDER 3절 15항의 「REQ 작성 파이프라인(PM의 REQ 작성과 REQ 판정)은 분류와 관계없이 고급」이 원스톱 파이프라인 진행 중이나 중단 뒤 PM이 작성하는 REQ 새 버전에서 지켜지게 설계되지 않았다(결함 D2) |
| ② | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 13개 경로(`Departments/Design/docs/tad/EC-022`, `Workflow/01`~`07`, 서식 5개)가 모두 REQ-022_v02 `scope:`에 있다. REQ scope의 `Lab/REQ-022_모델지정`, `.claude/agents/` 6개는 EC가 고치지 않는 경로이며 EC 2.1절 표 아래·2.3절에 사유가 있다 |
| ③ | 요청하지 않은 기능·추상화 없음 | PASS | 신설 항목(04 1.1~1.3절, 03 최종 판정 기준 10, 03 3절 1항 「분류 근거」, 07 4절 「모델 ID 갱신의 예외」, 01 「용어」 두 행)은 REQ 체크리스트 10 ①~⑬과 D5·D6·D8·D13에 대응한다(EC 3.1절 원천 표, 5절 완료 기준 1~13). F6 ①(PM 시작 때 자기 모델 확인)과 F6 ③(별칭 대신)은 D5 「단계별 모델로 세션을 기동하는 PM 책임」의 이행 수단이다 |
| ④ | 완료 기준을 확인할 수 있음 | PASS | EC 5절 완료 기준 1~17이 적용본 위치·결과서 절·명령(`check_standard.py`, `python -m pytest …`)으로 확인 방법을 정한다 |
| ⑤ | REQ 「결정」 열의 결정이 반영되었다 | FAIL | 승인 기록 「D번호별 결정」과 REQ 3절 「결정」 열 대조. D1→F1, D2→F2, D3→F11, D4→F2·2.3절, D6→F8, D7→F7, D8→F10, D9·D10→F7 ③, D11→F5, D12→DEV-022_v02 6절 「D12 범위」, D14→문서 변경 없음으로 반영되었다. D13 수정안(Claude Code 실행 가능 모델만 사용, 등급표 유지, 현행 실행 도구가 Claude Code라는 사유와 함께 `Workflow/` 한 곳에만 기재, 다른 문서는 참조, 다른 실행 도구 도입은 뒤의 ORDER·REQ)은 F4·F7 ③·2.3절로 반영되었다. D5 수정안 가운데 모델 ID 단일 원천(F3), 실행 명령·서식·정의의 원천 준수(F13·F14), PM 기동 책임(F6), 모델 ID만 바뀌는 갱신의 비서실 보고·대표님 직접 수정·`AGENTS.md` 3항 비해당·07 4절 예외·개정 이력 `CEO` 행과 「이전 ID → 새 ID」·리비전 태그 불변·판정 전제 제외 커밋 `[CEO]`·`--no-verify`(F9, 3.3절 7번 ③), 등급 배정·모델 계열 변경의 ORDER·REQ(F9 ③)는 반영되었다. 다만 D5 수정안이 EC에 넘긴 「갱신의 적용 시점(진행 중인 안건의 처리, D6 모델 대조의 기준)」이 REQ 작성 파이프라인에서 정해지지 않았고, F9 ①의 적용 시점 문안이 `inherit` 서브에이전트의 실제 동작과 맞지 않는다(결함 D3) |
| ⑥ | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-022_v01` 8절: 판단 「EC 있음」, 해당 기준 3항·2항. REQ scope의 정규 대상이 거버넌스 파일(`AGENTS.md` 「불변 원칙」 3항 목록의 `Workflow/`, `.claude/`)이고, 변경이 그 규칙(분류 정의, 격상, 판정 모델, effort 승인, 모델 ID 원천)을 바꾸므로 `Workflow/03_라이프사이클` 2.1절 3항에 해당한다. 4항 ①이 섞여도 4항 끝 문장대로 EC를 붙인다. 판단과 사유가 2.1절 2~4항과 맞다 |

**실험 결과 인용 확인**(`Workflow/03_라이프사이클` 11.2절 5·6항): EC 1절 「실험 결과 인용」이 `DEV-022_v02` 6절(최종본)을 경로와 함께 인용하고, 3.2절 F3·F6·F8·F14와 4절 위험 1~4의 근거로 쓴다. 인용한 요지(① 호출 인자 `model: "sonnet"` → `claude-sonnet-5-5`, ② 호출 인자 없음 → `claude-opus-5-5`, ③ 세션 기록 파일의 한계, 별칭·강제 설정·effort의 문서 근거)는 `DEV-022_v02` 6절 원문과 맞다. `DEV-022_v02` 5절의 「확인 불가」 항목(Opus 밖 오케스트레이터의 상속, 호출 인자의 모델 ID 직접 지정, effort 상속)을 EC가 실측한 것으로 적은 곳은 없다(F6 근거, 4절 위험 1·2·3, 3.3절 6번 ②). 인용 번호 표기는 결함 D1을 본다.

**결과서 번호 확인**: REQ 4절은 구현 단계 결과서를 `DEV-022_v02`로 적었으나 실험 단계가 v02를 써서 EC가 `DEV-022_v03`으로 적었다(EC 1절). 부서 `results/`는 scope 대조 대상이 아니고(`Workflow/03_라이프사이클` 최종 판정 기준 2), 같은 부서 결과서의 다음 버전 번호를 쓰는 처리이므로 결함으로 보지 않는다.

## 3. 체크리스트 대조 (최종 판정만)
- 해당 없음 (EC 판정)

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 기준 커밋 확인(실행하지 못함) | Bash `cd "/d/Vibe Coding/Vibe Standard_v04" && ... git log --oneline -1 ...` | 2026-10-10T14:41+09:00 무렵 | 메시지 원문: `This command changes directory before running a version-control command, which can pick up untrusted hooks or repository configuration from the target directory. Approve only if you trust it.` |
| 기준 커밋 확인(실행하지 못함) | Bash `...; git -C "/d/Vibe Coding/Vibe Standard_v04" log --oneline -1; ...` | 2026-10-10T14:41+09:00 무렵 | 메시지 원문: `This Bash command contains multiple operations. The following part requires approval: git -C "/d/Vibe Coding/Vibe Standard_v04" log --oneline -1` |
| 대신한 명령(기준 커밋, 거버넌스 원본 무변경) | PowerShell `git log --oneline -1; git diff --stat HEAD -- .claude Workflow AGENTS.md` | 2026-10-10T14:41+09:00 무렵(직전 Bash `date -Iseconds` 실측 `2026-10-10T14:41:16+09:00`) | `97262f3 REQ-021_v02: 설계 필수와 EC 적용 기준 반영` (diff 출력 없음). EC 1절 「변경 배경」의 기준 커밋·원본 무변경 기재와 같다 |
| 「등급」 사용처 확인 | Grep `등급` (glob `{Workflow/**,AGENTS.md,.claude/agents/**}`) | 2026-10-10T14:41+09:00 무렵 | `Workflow\03_라이프사이클.md:3:> 이 문서가 정하는 것: 등급별 흐름, ...` 1건. EC 1절 「변경 배경」 첫째 하위 항목과 같다 |
| 실험 기록 F번호 확인 | Bash `grep -n "F2\b\|F3\b\|F4\b\|F7\b\|F9\b" Lab/REQ-022_모델지정/실험기록_v01.md` | 2026-10-10T14:41+09:00 무렵 | `44:\| F2 \| sub-agents 「Choose a model」 \| ...`, `45:\| F3 \| ...`, `46:\| F4 \| sub-agents 「Run every subagent on one model」 \| ...CLAUDE_CODE_SUBAGENT_MODEL_FORCE...`, `49:\| F7 \| model-config \| 「Aliases point to the recommended version ...」`, `51:\| F9 \| model-config effort \| ...` (결함 D1의 근거) |
| 판정 시각 | PowerShell `Get-Date -Format o` | 2026-10-10T14:42:25+09:00 | `2026-10-10T14:42:25.7786245+09:00` |

- 커밋 전 검사와 인수 시험 재실행은 EC 판정 기준의 대상이 아니므로 실행하지 않았다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | `EC-022_v01` 3.2절 F6·F14 「근거」 칸, 4절 위험 2 「대응」 칸 | **지칭 불명확**. EC는 자기 결정 번호로 F1~F17을 쓰면서, 같은 칸에서 실험 기록(`Lab/REQ-022_모델지정/실험기록_v01.md` 3절)의 문서 근거 번호 F2·F4·F7·F9를 구분 없이 「(F2)」 꼴로 인용한다. F6 근거의 「버전 고정에는 모델 ID를 쓴다(F7)」·「정의 파일의 `effort`는 세션 effort보다 앞서므로(F9)」는 실험 기록 번호인데, 바로 옆 「사후 대조(F8)」는 EC 번호다. F14 근거 「호출 인자가 무시되나(F4)」와 위험 2 「공식 문서(F2)는」도 실험 기록 번호다. EC의 F4(실행 도구의 모델 제한), F7(기본값 밖 사용), F9(모델 ID 갱신), F2(분류별 단계)와 뜻이 달라, 명세·구현이 「대응표의 해당 행에 결정 번호를 적는다」(3.2절 머리)를 따를 때 근거를 잘못 짚는다. 실험 기록 번호에는 출처를 붙여(예: 「실험 기록 v01 F9」) EC 결정 번호와 구분해야 한다 | 설계 |
| D2 | `EC-022_v01` 3.2절 F5(「격상·강화로 PM이 작성하는 REQ 새 버전과 그 REQ 판정은 REQ 작성 파이프라인 행을 따른다」), F6 ①(PM은 「시작할 때」 자기 실행 모델을 확인) | **누락**. REQ 체크리스트 10 ④와 ORDER 3절 15항은 PM의 REQ 작성과 REQ 판정을 분류와 관계없이 고급으로 정한다. EC는 ① 격상·강화 밖의 REQ 새 버전(`Workflow/03_라이프사이클` 6절 「진행 중인 안건의 요구가 바뀜」, 11.2절 7항 실험 단계 추가, 5.1절 5항 3의 원스톱 파이프라인 첫 단계 전 문체 반영본)이 어느 행을 따르는지 정하지 않았다. ② 격상·강화의 REQ 새 버전도, Minor 안건의 PM은 원스톱 실행 명령의 `--model`(중급)로 기동된 세션이며 PM 자기 모델은 기동 뒤 바꿀 수단이 없다(F6 ①은 시작 때만 확인). 같은 문서 8절 「초기화」는 대표님 답 뒤 「같은 세션에서 계속하는 경우」를 인정하므로, 그 경우 중급 PM이 REQ 새 버전을 작성하게 된다. REQ 새 버전마다 따를 행과, PM 세션 모델이 그 행과 다를 때 PM이 할 일(예: 멈추고 REQ 작성 명령으로 다시 기동하게 보고)을 04 1.2절 문안으로 정해야 한다 | 설계 |
| D3 | `EC-022_v01` 3.2절 F9 ①②, 3.3절 4번 ② 1.1절 「갱신」 항목 | **누락·모순**. D5 수정안은 「갱신의 적용 시점(진행 중인 안건의 처리, D6 모델 대조의 기준)」을 EC에 넘겼다. ① F9 ②의 이전 ID 허용은 「그 안건 REQ `approved:`의 날짜」를 기준으로 하므로, `approved:`가 비어 있는 REQ 작성 파이프라인에서는 기준이 없다. REQ 작성 명령으로 기동된 PM이 실행 중에 모델 ID가 갱신되면, 그 PM이 `inherit`로 띄운 REQ 판정 세션은 이전 ID로 실행되고 1.2절 대조(현행 값만 맞음)에서 무효가 되어, 다시 판정해도 같은 결과로 `Workflow/03_라이프사이클` 7절 6항 중단에 이른다. ② F9 ①은 「갱신은 원천 문서를 고친 뒤 기동하는 세션부터 적용」이라고 정하지만, F9 근거와 실험 ②대로 갱신 뒤 기동한 `inherit` 서브에이전트는 실행 중인 PM의 이전 모델로 실행된다. 문안이 실제 동작과 맞지 않아 그 서브에이전트가 규정 위반으로 읽힌다. 적용 시점의 기준을 「그 파이프라인 실행(PM 세션)의 기동」으로 정하는 등, 두 파이프라인 모두에서 대조 기준이 정해지게 고쳐야 한다 | 설계 |

## 6. 문체 지적
- 없음

## 7. 삭제 대상 (최종 판정만)
- 해당 없음 (EC 판정)

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
- 해당 없음 (EC 판정)
