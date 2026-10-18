---
task_id: "032"
gate: "EC"
result: "fail"
completed_at: "2026-10-18T01:12:36+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # PM 지시문의 「effort: medium」 표기
---

# RES-032-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-032_v03.md`, `Departments/Design/results/RPT-032_v03.md`(8절 「EC 판단」), `Departments/Development/results/DEV-032_v04.md`(6절 「실험 결과」). 근거 REQ `Departments/Secretariat/docs/requests/REQ-032_v06.md`(승인 `2026-10-18T00:40:08+09:00`, 「결정」 열 D1~D6·D8·D10~D21 모두 권고안)
- **판정 차수**: 1차 (`REQ-032_v06` 재승인 뒤 원스톱의 첫 EC 판정. `RES-032-EC_v01`·`v02`는 `REQ-032_v04`의 원스톱 판정서이며 이 셈에 들지 않는다)
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-032_06.md`

## 2. 판정 기준별 결과
| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| ① | REQ 목적의 누락·왜곡 없음 | PASS | 요구 항목 18의 하위 항목(부 → 팀 구조, 공통 하위 폴더, 파트 폴더 없음, 파트 단위 쓰기 경로와 지키는지 보는 방법, 대응 위치, 경로를 가리키는 곳의 수정과 잔존 검사·차단)은 EC 3.3·3.4·3.6절 2번·3.14절, 요구 항목 20 ①~⑥은 3.6절 3~6번·3.7절·G12에 계획이 있다. 「아래를 지킨다」의 세 항목은 3.1절 표(원천은 Workflow 절), 3.6절 머리(새 명령 안에 커밋·삭제 없음)·G18(반영 명령의 확인 화면), 3.7절 P5~P9 행에 반영되었다. 작성 파트 대조를 두지 않는 처리(ORDER 3절 45항)는 G6과 2.3절에 있다 |
| ② | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 11개 항목 가운데 `.claude/settings.json`, `.claude/agents/development.md`, `.claude/agents/engineering.md`는 REQ 항목 `.claude` 안이고, 나머지 8개는 REQ 항목과 글자가 같다(두 머리말 열람) |
| ③ | 요청하지 않은 기능·추상화 없음 | PASS | 새 명령 네 개와 훅은 하위 요구 ①~④가 요구한 것이다. G14의 시험 저장소 예외는 D15 권고안의 「임시 Git 저장소가 필요한 인수 시험의 실행 방법을 다시 정하지 않아도 되고」를 지키는 데 필요하다. 3.6절 5번의 「최종 승인 커밋 제목 줄 유형 `feat`」 규정은 준비 명령이 메시지를 만들기 위해 필요한 값이며 기능 추가로 보지 않았다 |
| ④ | 완료 기준을 확인할 수 있음 | FAIL | 5절 15행의 「「v04」 Grep 0건(`check_standard.py`·`.githooks/`·`setup.cmd` 적용본)」은 G12 ③의 변경 위치와 맞지 않아 그대로 확인할 수 없다(결함 D3) |
| ⑤ | REQ 「결정」 열의 결정이 반영되었다 | FAIL | D1~D6·D8·D10~D21의 권고안은 1절 「결정 반영 원칙」의 G 번호 대응대로 반영되었다(G1 영문 팀 이름, G2 최종 승인 커밋에서 이동, D3의 대기 팀 폴더 미생성과 `.gitkeep` 처리, 3.5절 표의 옛 범위·새 범위 대응, G5 같은 커밋 반영, G4 연락·셸 작업 폴더, G7 차단 시점과 대상 범위, G15 적용 시점, G8~G12, G13·G14). 다만 D20 권고안(요청 커밋에서 따로 실행하던 커밋 전 검사를 없애고 훅 출력으로 판단)을 반영하는 3.8절 6번 ④가 `Workflow/05` 8.3절 「요청 커밋」 예외 (마)·(바)의 「5)의 검사」 문장을 고칠 위치로 정하지 않아, 적용본에 없어진 검사를 가리키는 문장이 남는다(결함 D1) |
| ⑥ | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-032_v03` 8절: 판단 「EC 있음」, 3항(거버넌스 파일과 보안·권한 설정의 변경)과 2항. REQ `scope:`의 `AGENTS.md`, `Workflow`, `.claude`, `.githooks`, `.gitattributes`, `setup.cmd`, `Departments/Development/assets/scripts/`는 `AGENTS.md` 「불변 원칙」 3항의 거버넌스 파일이며, 계획이 그 동작·규칙·설정을 바꾸므로 3항에 맞고 4항 ①~③에 들지 않는다. 8절 「사유」 ③의 작성 파트 대조와 「실험 결과 인용」 칸의 `DEV-032_v01`은 `RPT-032_v02` 8절을 그대로 옮긴 표기이며(2.1절 5항), 같은 결과서 1절이 `REQ-032_v06`과의 대조로 판단이 바뀌지 않음을 밝혔다. EC 1절은 실험 결과를 `DEV-032_v04` 6절에서 인용하며 요지가 그 절과 맞다 |
| ⑦ | EC가 뒤 단계의 Claude Code 세션에 실행을 지정한 명령이 「명령 형태」의 원리 안에 있다 | PASS | 3.9절(구현 단계)의 명령은 `git log -1 --format=%H`, `git diff --stat 655a45d -- …`, `git ls-files .claude/agents`, `python -m pytest … -p no:cacheprovider`, `python Departments/Development/assets/scripts/check_standard.py`로 모두 `settings.json` `allow` 규칙(5·6·8·15·16행)과 앞부분이 맞는 단독 명령이며, 검색은 Grep 도구로 정했다. 3.10절(명세 단계)의 `git diff --no-index`, `git diff --stat`, `git log`도 같다. 새 규정이 PM·비서실 세션에 지정하는 `check_env.py`·`check_overlap.py`·`prepare_final_commit.py` 실행은 3.5절 10행이 `Bash(...)`·`PowerShell(...)` 규칙을 새로 등록한다. 3.9절 4번의 반영 명령은 형상통제팀(C02) 명령이므로 `Workflow/06` 2.1절 「문서가 지정하는 명령」의 대상이 아니다 |

## 3. 체크리스트 대조 (최종 판정만)
- 해당 없음 (EC 판정)

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 권한 규칙 열람 | `cat -n .claude/settings.json` (Bash) | 2026-10-18T01:00+09:00 무렵 | `allow` 15행 `Bash(python Departments/Development/assets/scripts/check_standard.py*)`, 17행 `Bash(python Departments/*/workspace/*)`, 23행 `PowerShell(python Departments/Development/assets/scripts/check_standard.py *)`, `deny` 39·40행 `Edit(Departments/Development/assets/scripts/**)`·`Write(…)`. EC 3.5절 7~9행의 행 번호와 같다 |
| 이동 대응표의 추적 파일 수 | `git ls-files Departments/Secretariat/assets/inbox/연락 \| grep -vc "\.gitkeep$"` 외 같은 형태 9개 (Bash) | 2026-10-18T01:03+09:00 무렵 | `36`, `5`, `239`, `4`, `51`, `208`, `15`, `166`, `.gitkeep` `37`, `Departments/Development/assets/` 아래 비`.gitkeep` 2개. EC 3.3절 2번 표의 해당 행 수와 같다 |
| `.gitkeep` 목록 | `git ls-files Departments \| grep "\.gitkeep$"` (Bash) | 같은 무렵 | 37개. 3.3절 3번 「삭제」 행 17개는 모두 있고, 나머지 20개는 2번 표의 행에 맞는다 |
| 대응표에 맞지 않는 미추적 파일 | `git ls-files --others --exclude-standard Departments \| grep -v "<대응표 옛 경로 11개>"` (Bash) | 2026-10-18T01:04+09:00 무렵 | 출력 없음(미추적 140개가 모두 대응표의 옛 경로 아래) |
| 맞는 줄이 없다고 적은 파일의 옛 경로 패턴 | `grep -nE "(Secretariat\|Design\|Development\|Quality\|Operations\|Marketing)/(assets\|docs\|results\|workspace)" .gitignore CLAUDE.md setup.cmd .claude/agents/marketing.md .claude/agents/operations.md .claude/agents/quality.md Workflow/04_모델_운용.md Workflow/templates/BRIEFING_TEMPLATE.html Workflow/templates/PM_DIRECTIVE_TEMPLATE.md Workflow/templates/AUDIT_TEMPLATE.md Workflow/templates/BACKLOG_TEMPLATE.md` (Bash) | 2026-10-18T01:05+09:00 무렵 | 출력 없음, 종료 코드 1. EC 3.14절 머리의 「맞는 줄이 없었다」와 같다 |
| 01·02의 옛 경로 줄 | `grep -nE "<3.6절 2번 ③의 두 패턴>" Workflow/01_표준_개요.md Workflow/02_부서_구조_및_작업구역.md` (Bash) | 같은 무렵 | 02의 57, 66, 152~161, 163행과 개정 이력 177·179·181행. 01은 없음. EC 3.14절 1번의 02 행 번호와 같다 |
| 「v04」 표기 | `grep -n "v04" Departments/Development/assets/scripts/check_standard.py setup.cmd .githooks/pre-commit` (Bash) | 2026-10-18T01:07+09:00 무렵 | `check_standard.py:4`(첫 설명 줄), `check_standard.py:100`(`# 이 검사는 사고 이력 없이 대표님 결정으로 넣은 예방 검사이며(근거 ORD-005_v04 원문 N),`), `check_standard.py:806`(성공 문구), `setup.cmd:3`, `setup.cmd:26`, `.githooks/pre-commit:2` |
| 앞 원스톱 적용본의 100행 처리 | `grep -n "사고 이력 없이" "Departments/Development/workspace/REQ-032_적용본_v01/Departments/Development/Implementation/assets/scripts.적용본/check_standard.py"` (Bash) | 2026-10-18T01:08+09:00 무렵 | `194:# 이 검사는 사고 이력 없이 대표님 결정으로 넣은 예방 검사이며(근거: Workflow/06 「비밀정보 검출」 ⑦ 도입 근거),` |
| `ROOT_DIR` 깊이 | `grep -n "ROOT_DIR\s*=" Departments/Development/assets/scripts/check_standard.py` (Bash) | 2026-10-18T01:06+09:00 무렵 | `44:ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent` |
| `REQ-032` 이전 커밋 | `git log --format="%h %s" HEAD \| grep -E "\[(REQ-03[2-5]\|REQ-1[0-9][0-9])"` (Bash) | 2026-10-18T01:06+09:00 무렵 | 출력 없음(3.9절 4번 ⑦의 메시지에 `Follows`가 필요 없다) |
| NCR 누적 조회 | `grep`·`sed`로 `Departments/Quality/docs/nonconformance/*.md`의 `recorded_at`·`causes:`·`proposals:` 조회 (Bash) | 2026-10-18T01:10+09:00 무렵 | `NCR-032_06` 4절에 적음 |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-18T01:12:36+09:00 | `2026-10-18T01:12:36+09:00` |

- 위 명령은 모두 확인 요청 없이 실행되었다. 실행하지 못한 명령은 없다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | `EC-032_v03` 3.8절 6번 ④(와 3.8절 머리 「아래 위치와 3.14절 목록 밖의 문장은 바꾸지 않는다」) | ④는 `Workflow/05` 8.3절 「요청 커밋」 순서 5)를 「5) 커밋 전 검사는 따로 실행하지 않는다(1.1절 7번과 같다)」로 바꾸고 예외 (나)만 고치게 한다. 같은 항목의 예외 (마) 「섞인 커밋은 … 5)의 검사가 실패하지만, 그런 REQ가 있으면 검사를 통과하므로 검사에 맡기지 않는다」와 (바) 「`CEO/` 변경과 그 밖의 변경을 섞으면 5)의 검사가 실패한다」는 고칠 위치가 아니며, 3.8절 머리가 정한 위치 밖 문장을 바꾸지 못하게 하므로 명세가 고칠 수도 없다. 반영 뒤 05에는 없어진 「5)의 검사」를 근거로 삼는 문장이 남아 모순이 된다(D20). (마)·(바)의 이 문장을 「커밋 때 훅(pre-commit의 `check_standard.py --staged`)」으로 바꾸는 위치와 문안을 ④에 더하고, (바)의 「5)~7)」·「4)~7)」을 그대로 둘지도 정한다 | Rework | 설계부 |
| D2 | `EC-032_v03` 3.9절 3번(이동 명령 「기본은 이 스크립트에서 세 단계 위」, 미리보기 시험 「스크립트에서 세 단계 위」)과 3.5절 13행(「`ROOT_DIR`는 스크립트 위치에서 다섯 단계 위」 → 「여섯 단계 위」) | 두 곳이 「단계 위」를 서로 다른 기준점으로 센다. 3.5절 13행은 현행 코드(`Path(__file__).resolve().parent` 다섯 번, 44행)와 맞으므로 파일에서 세는 기준이다. 같은 기준으로 세면 `Departments/Development/workspace/` 바로 아래의 이동 명령은 `.parent` 네 번이 저장소 루트이고, 「세 단계 위」는 `Departments/`다. 이 기본값은 형상통제팀(C02)이 `--root` 없이 실행하는 반영 명령(3.9절 4번 ②)에서 쓰이므로, 글자대로 구현하면 반영 때 이동 명령이 저장소 루트를 잘못 잡는다. 기준점을 정해 한 가지로 적는다(예: `Path(__file__).resolve().parents[3]`) | Rework | 설계부 |
| D3 | `EC-032_v03` 5절 15행(「「v04」 Grep 0건(`check_standard.py`·`.githooks/`·`setup.cmd` 적용본)」)과 3.2절 G12 ③ | G12 ③이 「v04」를 바꿀 곳으로 정한 것은 `check_standard.py` 첫 설명 줄·성공 문구, 훅 주석, `setup.cmd` 안내·첫 커밋 메시지, 07 예외 문구다. 현행 `check_standard.py` 100행에는 기록 이름 `ORD-005_v04`가 있고 G12 ③과 3.14절은 이 줄을 바꿀 곳으로 정하지 않았으므로, 계획대로 구현하면 「v04」 Grep이 0건이 되지 않는다. 0건을 만들려면 EC가 정하지 않은 문안으로 기록 참조를 고쳐야 하며, 앞 원스톱의 개발 적용본(`REQ-032_적용본_v01`, 194행)이 실제로 이 줄을 고쳐 썼다. Grep 패턴(예: 표준 버전 표기 `표준 v04`)과 100행의 처리(그대로 둠, 또는 바꿀 문안)를 정한다 | Rework | 설계부 |

## 6. 문체 지적
| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | `EC-032_v03` 3.4절 표 「REQ 작성」 행 「수정 주체(파트)」 칸 | `P01` | `P01(REQ 승인 전. 승인된 REQ의 새 버전도 그 버전의 승인 전에 쓴다)` | 설계부 |
| S2 | `EC-032_v03` 3.2절 G18 ② | 「반영 명령은 `allow` 규칙과 앞부분이 맞지 않는 형태로 적으므로 확인 화면이 뜬다. Python 스크립트로 하는 반영 명령은 `python -I <스크립트 경로>`처럼 `allow` 규칙과 맞지 않는 형태로 적는다」로 바꾼다 | 같은 행의 「C02는 반영에 두 도구를 쓰지 않고 결과서의 반영 명령(셸의 `cp`)만 실행한다」를 「C02는 반영에 두 도구를 쓰지 않고 결과서의 반영 명령(셸의 `cp`와, 결과서가 정한 Python 스크립트)만 실행한다」로 바꾸고, 「반영 명령은 `allow` 규칙과 앞부분이 맞지 않는 형태로 적으므로 확인 화면이 뜬다. Python 스크립트로 하는 반영 명령은 `python -I <스크립트 경로>`처럼 `allow` 규칙과 맞지 않는 형태로 적는다」로 바꾼다 | 설계부 |

## 7. 삭제 대상 (최종 판정만)
- 해당 없음 (EC 판정)

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
- 해당 없음 (EC 판정)
