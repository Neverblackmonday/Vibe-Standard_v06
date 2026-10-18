---
created: "2026-10-13"
author:
  agent: "Secretariat"
  model: "claude-opus-5-5" # 작성 세션의 설정 모델. 실제 서빙 모델은 확인 불가
  session: "코워크·20261013T0935"
---

# Claude Code 지침 로드와 effort 설정 확인

## 1. 조사 질문

- 대표님 질문(2026-10-13, 코워크 비서실 대화): 「제일 중요한 전역지침은 어쩔꺼? 내 아이디어는 전역지침은 다른 프로젝트에도 써먹어야 하니, 현재대로 냅두고, 우리 지침에, 전역지침은 읽지마시오.라고 하면 안읽게 될라나?」
- 함께 확인한 것: 파트별 effort 설정이 가능한지

## 2. 방법

- Claude Code 공식 문서를 서브에이전트가 조회했습니다(2026-10-13). 아래 「요지」는 그 조회 결과의 문서 문장 요지이며, 문서는 바뀔 수 있습니다.
- Claude Code 버전은 대표님 PC의 Claude Code 세션 기록(2026-10-06 ~ 10-13 사본)의 `version` 값으로 확인했습니다.

## 3. 확인 결과

| 질문 | 결과 | 출처와 요지 |
| :--- | :--- | :--- |
| 전역 지침(`~/.claude/CLAUDE.md`)은 자동으로 실리는가 | 예. 세션 시작 때 프로젝트 `CLAUDE.md`와 함께 실림 | https://code.claude.com/docs/en/memory.md 「Claude reads them at the start of every session」, https://code.claude.com/docs/en/claude-directory.md 「Loaded alongside the project CLAUDE.md at session start」 |
| 프로젝트 지침에 「읽지 마라」라고 적으면 막을 수 있는가 | 아니오. 문서에 그런 방법이 없음. CLAUDE.md는 강제 설정이 아니라 맥락이며 사용자 파일이 먼저 실림 | memory.md 「context, not enforced configuration」 |
| 서브에이전트가 지침 파일을 싣지 않게 할 수 있는가 | 예. 정의 파일 머리말 `omitClaudeMd: true`이면 사용자·프로젝트·local CLAUDE.md를 싣지 않음(관리 정책 파일은 실림). Claude Code 2.1.271 이상 | https://code.claude.com/docs/en/sub-agents.md 「Every other built-in and custom subagent loads both, unless its definition sets the omitClaudeMd field」 |
| 프로젝트 단위로 사용자 파일만 뺄 수 있는가 | 확인 불가. 후보는 프로젝트 설정 `claudeMdExcludes`(경로 글롭 제외)이나 사용자 파일 제외 예시가 문서에 없음 | memory.md 「Exclude specific CLAUDE.md files」 절 |
| 모든 CLAUDE.md를 끄는 설정 | 환경 변수 `CLAUDE_CODE_DISABLE_CLAUDE_MDS`는 사용자·프로젝트·자동 메모리를 모두 끔(범위가 넓음) | https://code.claude.com/docs/en/env-vars.md |
| 서브에이전트별 effort | 정의 파일 머리말 `effort`(low~max)가 세션 effort보다 앞섬. 호출 인자로도 effort를 줄 수 있음(2.1.292 이상, 머리말보다 앞섬). 환경 변수 `CLAUDE_CODE_EFFORT_LEVEL`은 둘 다보다 앞섬 | sub-agents.md |
| 대표님 PC의 Claude Code 버전 | 기록에 나온 가장 최근 버전 2.1.295. 위 두 기능의 요건(2.1.271, 2.1.292) 이상 | 세션 기록 사본의 `version` 값(2.1.286, 2.1.287, 2.1.289, 2.1.293, 2.1.295) |

## 4. 현행 규정과의 관계

- `Workflow/04` 2절은 「서브에이전트 정의 파일에 `effort`를 적지 않는다」와 「한 파이프라인 실행의 모든 세션은 실행 명령의 `--effort` 값으로 실행」을 정합니다. 파트별 effort를 쓰려면 이 절을 개정해야 합니다.
- `omitClaudeMd`를 쓰면 프로젝트 `CLAUDE.md`(`@AGENTS.md` 가져오기)도 실리지 않으므로, 서브에이전트에 필요한 표준 공통 규정은 정의 파일 안에 넣어야 합니다.

## 5. 확인하지 못한 항목

- `claudeMdExcludes`로 사용자 수준 `~/.claude/CLAUDE.md`를 뺄 수 있는지, Windows 경로 표기
- 대표님 PC에서 `omitClaudeMd`와 서브에이전트별 effort가 실제로 동작하는지(실측 필요)
