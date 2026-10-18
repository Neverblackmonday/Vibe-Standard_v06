---
task_id: "028"
gate: "EC"
result: "fail"
completed_at: "2026-10-13T16:15:27+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-028-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-028_v01.md`, `Departments/Design/results/RPT-028_v02.md` 8절 「EC 판단」 (입력 REQ `Departments/Secretariat/docs/requests/REQ-028_v04.md`)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-028_04.md`

## 2. 판정 기준별 결과
> 기준은 `Workflow/03_라이프사이클` 5절 표 「EC 판정」 행 ①~⑦이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | REQ 목적의 누락·왜곡 없음 | FAIL | 요구 항목 1(G1~G4, 3.4절 1·2번), 요구 항목 3·4(G12·G13, 3.4절 3~5번)와 D1~D13 반영 구조는 REQ 2절 「목적」과 맞다. 다만 요구 항목 2·3이 요구하는 「어느 커밋으로 끝났는지」의 기록에서, 3.4절 3번의 「그 안건의 커밋」 식별 규칙과 「마지막 커밋을 끝낸 커밋으로 본다」 판단 규칙을 커밋 이력에 그대로 적용하면 다른 안건의 커밋이 끝낸 커밋으로 골라진다(5절 D1). 근거: `git show --name-status --format=%H%n%s ee95f5a`의 제목 「chore: [REQ-020] REQ-014 일회성 파일 네 개 처리」와 삭제 경로 `Departments/Design/workspace/REQ-014_결과서차이_20261009b.py`·`REQ-014_복사_20261009a.py`, `git show --name-status --format=%H%n%s 3801c62`의 제목 「feat: [REQ-010-1] ... REQ-008 N2 반영」 |
| ② | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 9항목이 REQ-028_v04 머리말 `scope:` 9항목과 글자 그대로 같다(Read 대조). EC 2.1절 표의 1~9·11~13·15번은 부서 `results/`·`workspace/`·품질 기록 구역이고(`Workflow/02_부서_구조_및_작업구역` 4절 「REQ 승인 후」·「품질 기록」 행), 10번은 반영 원본 `check_standard.py`가, 14번은 `Departments/Secretariat/assets/inbox`가 scope에 있다 |
| ③ | 요청하지 않은 기능·추상화 없음 | PASS | G4 ③(종결 기록 이름 형식 `[FAIL]`)·④(`[WARN]`)·①(`[INFO]`)는 요구 항목 1의 효력 상실을 출력 없이 넘기지 않기 위한 것이며 사용자 전역 지침 「코드 작성 및 로깅」·「실행·검증 및 테스트」를 근거로 적었다. 새 근거 줄, RT 색인, 종결 취소 경로, 종결 기록 삭제 차단은 2.3절에서 명시적으로 뺐다. `Workflow/01` 「용어」 행은 REQ 4절 「scope 경로별 사유」의 `Workflow/01`(「종결」을 용어로 정의할 때) 범위다 |
| ④ | 완료 기준을 확인할 수 있음 | PASS | EC 5절 1~11번이 REQ 체크리스트 1~4의 하위 항목마다 확인 방법(단위 시험·인수 시험의 종료 코드, 적용본의 절, DEV 절, `git log --oneline 6c5d512..<HEAD 커밋>` 줄 수)을 정한다. 대조 기간의 현재 커밋 수 실측: `git log --oneline 6c5d512..HEAD \| wc -l` 결과 `32`(EC 1절 「변경 배경」의 32줄과 같다) |
| ⑤ | REQ 「결정」 열의 결정이 반영되었다 | PASS | REQ 3절 「결정」 열 D1~D13이 모두 「권고안」이다. EC 1절 「결정 반영 원칙」의 대응: D1→G9(05 1절), D2→G10(06 계층 3 「한계」와 2.1절 문안, 승인 기록 부분 유지), D3·D4→G11·G1(RT 색인 없음, 메시지 없이 판단), D5→G3·G6(그 안건의 커밋에 함께, HEAD만 읽어 자기 검사 통과), D6→G7, D7→G8, D8→G6(최종 승인·핫픽스 커밋은 비서실, 대표님 직접 커밋은 대표님, PM 커밋은 PM, 커밋 없는 종결은 결정을 받은 비서실. 요청 커밋 가운데 안건을 끝내는 것은 HOTFIX 커밋(`Workflow/05` 8.3절 「요청 커밋」 1)의 (나))이며 3.3절 4번이 그 순서에 종결 기록을 넣는다), D9→G12, D10~D12→G13·3.4절 5번, D13→문서 변경 없음 |
| ⑥ | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-028_v02` 8절에 판단(EC 있음), 해당 기준(3항·2항), 사유가 있다(`Workflow/03` 2.1절 5항의 항목). 변경 대상 `check_standard.py`와 `Workflow/01`·`02`·`03`·`05`·`06`·`07`은 `AGENTS.md` 「불변 원칙」 3항의 거버넌스 파일이며 동작·규칙(통과 근거 판단, 커밋 절차, 공식 진행 상태)을 바꾸므로 3항에 해당한다. 종결 기록 신설(4항 ③ 후보)이 섞여도 4항 끝 문장대로 EC를 붙인다 |
| ⑦ | EC가 뒤 단계 Claude Code 세션에 지정한 명령이 「명령 형태」 원리 안 | PASS | 지정 명령: `git log -1 --format=%H`, `git log --reverse --format=%H 6c5d512..<HEAD>`, `git log --oneline 6c5d512..<HEAD 커밋>`, `git log --diff-filter=A --format=%H -- <경로>`, `git show --name-status -M --format= <커밋>`, `git show <커밋>:<경로>`, `git status --porcelain -uall -- <경로>`, `git diff --no-index <원본> <적용본>`, `git diff --stat e956bab HEAD -- <원본>`, `python -m pytest Departments/Quality/assets/acceptance/REQ-028_v01`, `python Departments/Development/assets/scripts/check_standard.py`, `date -Iseconds`, 부서 `workspace/` 스크립트 실행. 모두 저장소 루트 기준 상대 경로이고 앞부분이 `.claude/settings.json` `allow`의 `Bash(git log*)`·`git show*`·`git status*`·`git diff*`·`python -m pytest*`·`python Departments/Development/assets/scripts/check_standard.py*`·`date*`·`python Departments/*/workspace/*`와 맞는다(`cat .claude/settings.json` 결과). `allow`에 없는 `git check-attr`·`git ls-tree`·`cp`는 스크립트 안 호출이나 Read·Write 도구로 정했다(2.1절, 3.4절 1·4번, 4절 위험 10). `check_standard.py` 안의 `git -c core.quotepath=false ls-tree`는 검사 코드의 하위 프로세스이며 세션 명령이 아니다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 권한 규칙 조회 | `cat .claude/settings.json` (Bash) | 2026-10-13T16:15:22+09:00 이전(아래 시각 조회 전 실행) | `allow`: `Bash(git status*)`, `Bash(git diff*)`, `Bash(git log*)`, `Bash(git show*)`, `Bash(git ls-files*)`, `Bash(wc *)`, `Bash(od *)`, `Bash(head *)`, `Bash(grep *)`, `Bash(date*)`, `Bash(tar --force-local -tf *)`, `Bash(python Departments/Development/assets/scripts/check_standard.py*)`, `Bash(python -m pytest*)`, `Bash(python Departments/*/workspace/*)`, `PowerShell(...)` 7개. `git check-attr`·`git ls-tree`·`git rev-parse`·`cp` 없음 |
| 대조 기간 커밋 목록 | `git log --oneline 6c5d512..HEAD` (Bash) | 2026-10-13T16:15:22+09:00 이전 | 32줄. 해당 줄: `ee95f5a chore: [REQ-020] REQ-014 일회성 파일 네 개 처리`, `3801c62 feat: [REQ-010-1] 역할 재편 후속 반영(AGENTS.md, secretariat 폐지, 검사기), 기존 결함 K1~K3·C2 정비, REQ-008 N2 반영`, `5ff92a1 feat: [REQ-014] ...`, `4d4ecb2 feat: [REQ-008] ...`, `300437f chore: [CEO] ... REQ-011 종결(하드포크에 흡수)`, `97262f3 REQ-021_v02: ...`, `67d2781 RES-022 커밋` |
| D1 근거 커밋 | `git show --name-status --format=%H%n%s ee95f5a` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `ee95f5a3d6f2607a99cc1b7620a22cf4a4be0e71` / `chore: [REQ-020] REQ-014 일회성 파일 네 개 처리` / `D Departments/Design/workspace/REQ-014_결과서차이_20261009b.py`, `D Departments/Design/workspace/REQ-014_복사_20261009a.py`, `A Departments/Development/results/DEV-020_v01.md` 등 9줄 |
| D1 근거 커밋 | `git show --name-status --format=%H%n%s 3801c62` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `3801c6266af2af854a0963a1d5259fe918043956` / `feat: [REQ-010-1] 역할 재편 후속 반영(AGENTS.md, secretariat 폐지, 검사기), 기존 결함 K1~K3·C2 정비, REQ-008 N2 반영` / `A Departments/Secretariat/docs/requests/REQ-010-1_v02.md` 등 |
| 최근 커밋 메시지 | `git log -3 --format=%h%n%B---` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `e956bab`의 근거 줄 `Approved-REQ`·`Approved-RES`·`Approval-Record`. `cafc8d9`·`2d8de76`은 제목 줄만 |
| 종결 기록 존재 | `git ls-files Departments/Secretariat/assets/inbox` (Bash) | 2026-10-13T16:15:22+09:00 이전 | 85줄. `종결기록_`으로 시작하는 파일 없음(ORDER, 승인 기록, 요구메모, `.gitkeep`) |
| 배포본 제외 규칙 | `grep -n -E "export-ignore" .gitattributes` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `15:Departments/Secretariat/assets/*/** export-ignore` 포함 18줄 |
| 검사 코드 위치 | `grep -n -E "WHITELIST_PREFIXES\|^def \|RECORD_NAME\|lab_only\|is_whitelisted\(\|index_paths\(\|check_secrets\(" Departments/Development/assets/scripts/check_standard.py` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `46:WHITELIST_PREFIXES = (`, `76:RECORD_NAME = re.compile(r"^(REQ\|HOTFIX)-(\d{3}(?:-\d+)?)_v(\d{2})\.md$")`, `154:def load_latest(folder, kind):`, `191:def load_records():`, `353:def index_paths():`, `401:def check_secrets(files, staged):`, `607: lab_only = ...`, `625: work_files = [f for f in files if not is_whitelisted(f)]` |
| 검사 코드 본문 | `sed -n 150,215p Departments/Development/assets/scripts/check_standard.py` (Bash) | 2026-10-13T16:15:22+09:00 이전 | `load_latest()`·`load_records()`가 승인 필드 형식과 HOTFIX 조건만 보고 종결 여부를 보지 않음(EC 1절 「변경 배경」과 같다) |
| 끝나지 않은 REQ의 scope | `grep -n -A12 "^scope:" Departments/Secretariat/docs/requests/REQ-029_v04.md Departments/Secretariat/docs/requests/REQ-030_v02.md` (Bash) | 2026-10-13T16:15:22+09:00 이전 | REQ-029_v04: `EC-029`, `Workflow/02`·`03`·`05`·`06`, `Workflow/templates/ORDER_TEMPLATE.md`, `check_standard.py`. REQ-030_v02: `EC-030`, `.claude/settings.json`, `Workflow/06` (EC 1절 「변경 배경」 여섯째 항목과 같다) |
| 커밋 수·기준 커밋 재확인 | `date -Iseconds; git log --oneline 6c5d512..HEAD \| wc -l; git log -1 --format=%H` (Bash) | 2026-10-13T16:15:22+09:00 | `2026-10-13T16:15:22+09:00` / `32` / `e956bab2bfe020510923ada212506ee975b87981` |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-13T16:15:27+09:00 | `2026-10-13T16:15:27+09:00` (머리말 `completed_at`과 같다) |
| 범위 대조 | 해당 없음 | — | EC 판정은 최종 판정 기준 2를 적용하지 않는다 |
| 커밋 전 검사 | 해당 없음 | — | EC 판정 기준에 커밋 전 검사 실행이 없다 |

- 실행하지 못한 명령: 없음(위 명령은 모두 권한 확인 요청 없이 실행되었다).
- 원본 문서의 문장 대조(EC 3.3절이 「현행」으로 인용한 문장)는 Read 도구로 `Workflow/03_라이프사이클.md` 6·7·9절, `Workflow/05_인수인계_및_실행명령.md` 1절·1.1절·8.3절·8.4절, `Workflow/06_통제장치_및_배포.md` 1·2.1·4·5절, `Workflow/02_부서_구조_및_작업구역.md` 2.1·4절을 열람해 확인했다. 인용 문장은 원본과 같고, 05 1.1절 6번의 「①~⑩」은 세 곳이다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」을 따른다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | `EC-028_v01.md` 3.4절 3번 둘째·셋째 항목(「그 안건의 커밋」, 「판단」) | 「그 안건의 커밋」을 「제목 줄이나 근거 줄에 기록 이름이 낱말로 들어 있는 커밋」으로 정하고 「그 안건의 마지막 커밋을 끝낸 커밋으로 본다」고 판단하게 해, 다른 안건의 커밋이 끝낸 커밋으로 골라진다. 실측: `ee95f5a`(제목 「chore: [REQ-020] REQ-014 일회성 파일 네 개 처리」, `REQ-014_` 파일 삭제)는 `REQ-014`의 커밋으로 잡혀 `REQ-014`의 끝낸 커밋이 `5ff92a1`이 아니라 `REQ-020`의 커밋 `ee95f5a`가 되고, `3801c62`(제목 「[REQ-010-1] ... REQ-008 N2 반영」)는 `REQ-008`의 커밋으로 잡혀 `REQ-008`의 끝낸 커밋이 `4d4ecb2`가 아니라 `REQ-010-1`의 커밋 `3801c62`가 된다. 이는 G1 (가) 「REQ는 최종 판정서 승인 뒤의 커밋」(그 안건 자신의 커밋)과 어긋나며, 종결 기록의 「끝낸 커밋」과 끝난 시각이 틀린다(요구 항목 2·3, 체크리스트 3 ①②). 최종 판정의 커밋 이력 대조(체크리스트 3 ②, 4절 위험 8)도 같은 규칙을 기준으로 하면 이 오류를 잡지 못한다. 고칠 방향(예): 제목 줄의 안건 표기(`[REQ-xxx]`·`[HOTFIX-xxx]`)와 근거 줄 `Approved-REQ`·`Confirmed-HOTFIX`로 그 안건의 커밋을 정하고, 표기가 다른 안건인 커밋은 제목 본문에 기록 이름이 있거나 그 안건 파일을 바꿔도 그 안건의 커밋에서 뺀다. 파일 목록 기준은 안건 표기가 없는 커밋에만 쓴다 | Rework | 설계 |
| D2 | `EC-028_v01.md` 3.5절 3번 | 이 REQ 자신의 종결 기록 경로를 `종결기록_<커밋 날짜>_REQ-028.md`로 적어, G2(「`<YYYYMMDD>`는 종결 기록을 작성한 날짜(KST)다」, 「커밋 날짜는 같은 커밋에 넣는 기록을 쓸 때 정해지지 않는다」)와 3.3절 6번 ④(07 2절 「작성 날짜」)와 모순된다. 이 문장은 `RPT-028_v03` 반영 명령 표 아래에 옮겨져 최종 승인 커밋을 하는 비서실이 읽으므로, 자정을 넘겨 커밋하면 표준과 다른 날짜로 이름을 지을 수 있다. 고칠 방향: `<커밋 날짜>`를 `<작성 날짜>`(또는 `<YYYYMMDD>`, 07 2절 「종결 기록」 항 참조)로 바꾼다 | Rework | 설계 |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
