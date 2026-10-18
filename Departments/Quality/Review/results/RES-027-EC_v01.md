---
task_id: "027"
gate: "EC" # REQ | EC | SPEC | FINAL (REQ 판정, EC 판정, 명세 판정, 최종 판정)
result: "fail" # pass | fail | rejected
completed_at: "2026-10-12T01:20:05+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-027: 판정서 (EC 판정)

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-027_v01.md` (판정 입력: `Departments/Secretariat/docs/requests/REQ-027_v03.md`, 승인 기록 `Departments/Secretariat/assets/inbox/승인기록_20261012_REQ-027_v03.md`, 설계 결과서 `Departments/Design/results/RPT-027_v01.md` 8절 「EC 판단」)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-027_01.md` (원인 분류 `C3`·`C1`. `C3` 누적 2건으로 표준 개정 제안 있음, `proposals: [C3]`)

## 2. 판정 기준별 결과
기준은 `Workflow/03_라이프사이클` 5절 표 「EC 판정」 행 ①~⑦이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | 요구 항목 6과 REQ 2절 「목적」(조직 정리, 설계 서브에이전트 이름, 시각 디자인 문서의 이름·위치·작성 부서, 구현 전 판정과 입력 흐름)은 EC 3.2절 G1~G10과 3.3·3.4절이 덮는다. 다만 시각 디자인 판정을 새 판정 종류로 두면서 판정 종류를 열거한 `Workflow/02` 2절 표 품질 행을 반영 대상에서 빠뜨렸다(결함 D1). 또 EC 5절 완료 기준 8이 REQ 체크리스트 ⑧의 「판정 `pass`를 받은 시각 디자인 문서」 조건을 빼고 적었다(결함 D2) |
| 2 | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 22개 항목을 REQ 머리말 `scope:`와 대조했다. `Departments/Marketing/assets/icons`·`fonts`·`images`는 REQ의 `Departments/Marketing` 안이고, 그 밖의 항목은 REQ와 글자까지 같다 |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 새 단계(시각 디자인, 시각 디자인 판정)와 판정서 `-DESIGN`은 D8 권고안이 EC에 맡긴 「판정의 형태, `workflow:` 표기, 판정 기준」의 결정이다(REQ 3절 D8). 서식을 두지 않고(D7) 선택 부서 체계·파트 규정을 더하지 않는다(EC 2.3절) |
| 4 | 완료 기준을 확인할 수 있음 | FAIL | EC 5절 완료 기준 1~14는 적용본 위치, Grep, `git status`, 결과서 절로 확인할 수 있다. 다만 기준 8이 REQ 체크리스트 ⑧과 달라 그대로 확인하면 체크리스트 ⑧의 충족을 보장하지 못한다(결함 D2) |
| 5 | REQ 「결정」 열의 결정이 반영되었다 | PASS | 승인 기록 「D번호별 결정」(D1 권고안, D2 수정안, D3~D7 권고안, D8 수정안, D9~D10 권고안)과 EC 1절 「결정 반영 원칙」이 같다. D2 수정안은 2.3절(파트를 두는 규정도, 두지 않는다고 단정하는 규정도 더하지 않음), D8 수정안은 G8과 3.3절 4번 ⑫ 5.5절 5항(개발은 그 안건에서 판정 `pass`를 받은 문서를, 설계는 그 전에 판정을 받아 커밋된 HEAD의 문서만 입력으로 씀)에 반영되었다. D5(G4), D6(2.3절), D7(G5), D9(G9)도 권고안대로다 |
| 6 | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-027_v01` 8절은 3항(거버넌스 파일 `AGENTS.md`·`Workflow/`·`.claude/`의 규칙 변경)과 2항(커밋된 표준의 규칙 변경)을 들었고, 4항 ①~③에 해당하지 않는다는 사유를 적었다. REQ `scope:`의 정규 대상 대부분이 `AGENTS.md` 「불변 원칙」 3항의 거버넌스 파일이므로 판단이 맞다 |
| 7 | EC가 뒤 단계 세션에 지정한 명령이 「명령 형태」의 원리 안 | PASS | EC 2.1절·3.4절·3.5절이 지정한 명령(`git log -1 --format=%H`, `git diff --stat cafc8d9 -- …`, `git diff --no-index …`, `git status --porcelain -uall -- …`, `git ls-files .claude/agents`, `grep -n -E …`, `grep -rn -E …`, `python Departments/Development/assets/scripts/check_standard.py`, `python -m pytest …`, `python Departments/*/workspace/*` 형태의 복사 스크립트)은 모두 저장소 루트의 단독 명령이며 앞부분이 `.claude/settings.json` `allow`의 `Bash(git log*)`·`Bash(git diff*)`·`Bash(git status*)`·`Bash(git ls-files*)`·`Bash(grep *)`·`Bash(python Departments/Development/assets/scripts/check_standard.py*)`·`Bash(python -m pytest*)`·`Bash(python Departments/*/workspace/*)`와 맞는다. `cd`·`git -C`·`git -c`·묶음·변수·반복문·`cp`·`rm`·`mv`를 쓰지 않는다. 삭제는 비서실의 반영 단계로 넘겼다(2.2절) |

**EC가 인용한 사실의 확인**
- 기준 커밋: `git log -1 --format=%H%n%cI` 결과가 EC 1절과 같다(4절 검증 기록).
- 원본 미변경: `git status --porcelain -uall -- Workflow .claude AGENTS.md Departments/Marketing Departments/Visual Departments/Design` 결과는 EC와 설계 결과서 두 줄뿐이다(4절).
- 추적 파일: `git ls-files Departments/Marketing Departments/Visual .claude/agents` 결과가 EC 1절의 `.gitkeep` 11개와 정의 파일 여섯 개와 같다(4절).
- 비주얼·`design` 언급 위치: Grep 도구(패턴 `비주얼|[Vv]isual|\bdesign\b`, 범위 거버넌스 파일)의 결과가 EC 1절의 줄 번호(`AGENTS.md` 30·32행, `Workflow/01` 39행, `Workflow/02` 50·55행, `Workflow/03` 55·127·191·286·289행, `Workflow/07` 16행, `.claude/agents/design.md` 2행, `visual.md`)와 같다. `check_standard.py`, `operations.md`, `setup.cmd`, `.gitattributes`, `.githooks/`에는 패턴 `Visual|Marketing|agents|SPEC|gate|비주얼|마케팅|명세 판정|design`이 없다.
- 3.3절이 바꿀 원문으로 인용한 문구(`Workflow/01` 「조직」 행, `Workflow/02` 「기능」 항목, `Workflow/03` 2절·4절 2항·5절 표·최종 판정 기준 7·10·5.1~5.4절·7·8·12·13절, `Workflow/05` 1.1절 6번 ①, `Workflow/06` 1절 표 계층 4, `Workflow/07` 1절 표·추적 관계·2절 판정 구분·「PRD·TAD」 항·3절 첫 항목·3절 표 RES 행·4절 「대상」, 서식 네 개, `.claude/agents/` 세 개)와 이전 리비전 태그 위치가 현행 파일에 있다(Grep·Read 확인).

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 기준 커밋 조회 | `git log -1 --format=%H%n%cI` (Bash) | 2026-10-12T01:18:09+09:00 이전(같은 세션, 아래 시각 조회 전에 실행) | `cafc8d9f02a98228764f302c7eb724b7e0b5f995` / `2026-10-11T23:58:41+09:00` |
| 범위 대조(관련 경로) | `git status --porcelain -uall -- Workflow .claude AGENTS.md Departments/Marketing Departments/Visual Departments/Design` (Bash) | 2026-10-12T01:18:09+09:00 이전(같은 세션) | `?? Departments/Design/docs/tad/EC-027_v01.md` / `?? Departments/Design/results/RPT-027_v01.md` |
| 추적 파일 조회 | `git ls-files Departments/Marketing Departments/Visual .claude/agents` (Bash) | 2026-10-12T01:18:09+09:00 이전(같은 세션) | `.claude/agents/design.md`, `.claude/agents/development.md`, `.claude/agents/marketing.md`, `.claude/agents/operations.md`, `.claude/agents/quality.md`, `.claude/agents/visual.md`, `Departments/Marketing/assets/banners/.gitkeep`, `Departments/Marketing/assets/media/.gitkeep`, `Departments/Marketing/docs/.gitkeep`, `Departments/Marketing/results/.gitkeep`, `Departments/Marketing/workspace/.gitkeep`, `Departments/Visual/assets/fonts/.gitkeep`, `Departments/Visual/assets/icons/.gitkeep`, `Departments/Visual/assets/images/.gitkeep`, `Departments/Visual/docs/.gitkeep`, `Departments/Visual/results/.gitkeep`, `Departments/Visual/workspace/.gitkeep` |
| 권한 규칙 열람 | `cat .claude/settings.json` (Bash) | 2026-10-12T01:18:09+09:00 이전(같은 세션) | `allow`에 `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git show*)`, `Bash(git ls-files*)`, `Bash(wc *)`, `Bash(od *)`, `Bash(head *)`, `Bash(grep *)`, `Bash(date*)`, `Bash(tar --force-local -tf *)`, `Bash(python Departments/Development/assets/scripts/check_standard.py*)`, `Bash(python -m pytest*)`, `Bash(python Departments/*/workspace/*)`와 `PowerShell(...)` 규칙 7개. 확인 요청 없이 실행되었다 |
| 판정 종류 열거 위치 조회 | Grep 도구, 패턴 `명세 판정`, 범위 `AGENTS.md`, `Workflow/01`·`02`·`04`·`05`·`06`·`07`, `Workflow/templates/*.md` | 2026-10-12T01:18:09+09:00 이전(같은 세션) | `Workflow\02_부서_구조_및_작업구역.md:52:\| 품질 \| \`quality\` \| 판정(REQ 판정, EC 판정, 명세 판정, 최종 판정), 시험실(…` 외. 52행은 EC 1절 「판정 종류를 열거한 곳」과 3.3절 3번에 없다 |
| 커밋 전 검사 | 실행하지 않음 | — | EC 판정 기준은 커밋 전 검사 결과를 요구하지 않는다. 판정 대상은 EC 문서이며 정규 경로 변경이 없다 |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-12T01:20:05+09:00 | `2026-10-12T01:20:05+09:00` (머리말 `completed_at`과 같다). 부적합 기록 작성 전에 조회한 `2026-10-12T01:18:13+09:00`은 쓰지 않고, 부적합 기록을 작성하고 1절을 고친 뒤 다시 조회했다 |

- 위 표의 「2026-10-12T01:18:09+09:00 이전」 행은 시각 조회 명령을 따로 실행하지 않았다. 같은 세션에서 첫 시각 조회(`date -Iseconds`, 결과 `2026-10-12T01:18:09+09:00`) 전에 실행한 명령이다.
- 실행하지 못한 명령: 없음.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」을 따른다. 이 REQ는 `REQ-024` 커밋 뒤에 첫 버전을 작성했으므로 적용 대상이다(REQ 1절 「분류 규정의 적용」).

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | EC 1절 「변경 배경」 넷째 항목, 2.2절 3번, 3.3절 3번 | 시각 디자인 판정을 새 판정 종류로 두면서(G6), 판정 종류를 열거한 `Workflow/02_부서_구조_및_작업구역` 2절 표 품질 행 책임 칸의 「판정(REQ 판정, EC 판정, 명세 판정, 최종 판정)」을 반영 대상에서 빠뜨렸다. EC 1절은 「판정 종류를 열거한 곳」을 나열하면서 이 칸을 빼먹었고, 3.3절 3번은 02 2절 표의 설계·마케팅·비주얼 행만 고친다. 그대로 명세를 하면 적용본에서 품질의 책임 목록(02가 원천)에 시각 디자인 판정이 없고, 03 5.5절 4항과 5절 표는 품질이 그 판정을 하도록 정해 두 문서가 어긋난다. 명세 판정을 새로 둔 `REQ-021_v02`도 같은 칸에 명세 판정을 더했다(02 개정 이력 `REQ-021_v02` 행). 고칠 곳: 3.3절 3번에 품질 행 책임 칸을 「판정(REQ 판정, EC 판정, 명세 판정, 시각 디자인 판정, 최종 판정)」으로 바꾸는 항목을 더하고, 2.2절 3번 「변경 내용」, 3.3절 3번 ⑦ 개정 이력 문안, 1절 「판정 종류를 열거한 곳」에도 같은 내용을 넣는다. `Workflow/02`는 REQ·EC `scope:` 안이고 D8이 판정 형태를 EC에 맡겼으므로 승인된 기준 안에서 고칠 수 있다 | Rework | 설계 |
| D2 | EC 3.3절 4번 ⑥ 「구현」 행 문안, 5절 완료 기준 8 | REQ 체크리스트 ⑧은 「현행 `Workflow/03` 5절 표 「구현」 행의 입력에 판정 `pass`를 받은 시각 디자인 문서가 있으며」를 확인한다. EC 3.3절 4번 ⑥은 「구현」 행 입력에 「, 시각 디자인 문서(화면을 구현할 때. 5.5절 5항)」만 더해 판정 조건을 적지 않고, EC 5절 완료 기준 8도 「「구현」 행 입력에 시각 디자인 문서가 있으며」로 판정 조건을 뺐다. EC의 완료 기준을 채워도 최종 판정이 체크리스트 ⑧을 그 문구대로 대조하면 근거가 모자라 다시 반려될 수 있다. 「인수 시험」 행에 더하는 문안(「판정 `pass`인 시각 디자인 판정서와 시각 디자인 문서」)과도 표현이 다르다. 고칠 곳: 「구현」 행 문안을 판정을 받은 시각 디자인 문서라는 조건이 드러나게 바꾸고(예: 「, 판정을 받은 시각 디자인 문서(화면을 구현할 때. 그 안건의 시각 디자인 판정 `pass` 또는 HEAD의 문서. 5.5절 5항)」), 5절 완료 기준 8을 REQ 체크리스트 ⑧과 같은 조건으로 고친다. 5.5절 5항의 입력 조건(G8)은 바꾸지 않아도 된다 | Rework | 설계 |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
