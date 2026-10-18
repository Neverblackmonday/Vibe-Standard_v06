---
task_id: "032"
gate: "EC"
result: "fail"
completed_at: "2026-10-16T23:02:33+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5" # 실제 판정 모델(세션 시스템 정보의 모델 ID claude-opus-5-5)
  effort: "medium (실행 명령 기준)" # 오케스트레이터 지시문의 「effort: medium」 표기
---

# RES-032-EC: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-032_v01.md`(`status: draft`). 대조 기준: `Departments/Secretariat/docs/requests/REQ-032_v04.md`(승인 `2026-10-16T16:48:15+09:00`, 「결정」 열 D1~D21 권고안), `Departments/Design/results/RPT-032_v01.md` 8절 「EC 판단」
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-032_03.md`

## 2. 판정 기준별 결과
기준은 `Workflow/03_라이프사이클` 5절 표 「EC 판정」 행 ①~⑦이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | 요구 항목 18(구조·이동·작업 구역·대응·경로 바꾸기·잔존 검사)과 20 ①~⑥은 EC 3.1~3.7절에 대응이 있다. 그러나 D1(이 REQ 자신의 커밋에서 이동 뒤 현행 절차 단계의 경로가 정해지지 않아 보호 범위가 끊김), D3(반영 이동 명령이 확인 화면 없이 실행될 수 있어 요구 항목 20 「커밋·삭제·덮어쓰기는 지금처럼 확인 화면에서 대표님 승인」과 어긋남), D5(대응표에 운영부·마케팅부 행이 없어 요구 항목 18 「이미 작성된 기록의 경로는 대응으로 읽는다」를 채우지 못함)가 있다 |
| 2 | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 11개 항목은 REQ `scope:`의 같은 항목이거나 그 안의 경로다(`.claude/settings.json`, `.claude/agents/development.md`, `.claude/agents/engineering.md`는 REQ `.claude` 안). `.gitignore`는 넣지 않았다(EC 2.3절, REQ 1절 「참고」와 같음) |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 새 명령 네 개(`check_commit_msg.py`, `check_env.py`, `prepare_final_commit.py`, `check_overlap.py`)와 대장은 요구 항목 20 ①~④·⑥에 대응한다. 공통 함수는 `check_standard.py`를 `import`해 다시 구현하지 않는다(3.6절 머리). 핫픽스팀(V03) 기동 전 점검, 대기 팀 폴더, 파트별 정의는 만들지 않는다(2.3절) |
| 4 | 완료 기준을 확인할 수 있음 | PASS | 5절 1~23행이 체크리스트 18 ①~⑫, 20 ①~⑩과 G17을 확인 수단(적용본 위치, 인수 시험, `DEV-032_v02` 「대조」, `git diff`, Grep)과 함께 대응시킨다 |
| 5 | REQ 「결정」 열의 결정이 반영되었다 | FAIL | 1절 「결정 반영 원칙」이 D1~D21을 G1~G17에 대응시키고 대부분 권고안대로 반영했다. 그러나 D4(`[CEO]` 커밋 본문 처리가 D16보다 넓게 막음)와 D1(D13 「지금 절차」와 D5의 반영에 필요한 결정이 빠짐)이 있다 |
| 6 | 「EC 판단」 절의 「EC 있음」 판단이 2.1절 2~4항과 맞다 | PASS | `RPT-032_v01` 8절은 `AGENTS.md`, `Workflow`, `.claude`, `.githooks`, `.gitattributes`, `setup.cmd`, 검사 스크립트 폴더(거버넌스 파일)와 `settings.json`(보안·권한 설정)의 규칙·설정을 바꾸므로 3항(늘 붙이는 경우)과 2항에 해당하고, 4항 ①~③이 아니며 새 파일 신설이 섞여도 4항 끝 문장대로 EC를 붙인다고 적었다. 판단이 맞다 |
| 7 | EC가 뒤 단계의 Claude Code 세션에 실행을 지정한 명령이 「명령 형태」의 원리 안에 있다 | FAIL | 3.9절 1~7번·3.10절의 명령(`git log -1 --format=%H`, `git diff --stat 655a45d -- …`, `git diff --no-index …`, `python -m pytest …`, `python Departments/Development/assets/scripts/check_standard.py`)은 `settings.json` `allow` 규칙과 앞부분이 맞고 묶음·`cd`·전역 옵션이 없다. 그러나 D2(3.13절 ⑤ 「이동 목록」을 얻는 명령이 원리 안의 형태로 지정되지 않음)가 있다. 반영 명령(3.9절 4번)은 `Workflow/06` 2.1절 「문서가 지정하는 명령」대로 이 기준의 대상이 아니며 D3은 기준 1로 판정했다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(EC 판정)

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 기준 커밋 조회 | `git log -1 --format=%H%n%cI` (Bash) | 2026-10-16T23:01:23+09:00 직전 | `655a45da3201d30fc198831fb37bdd9b38409fe8` / `2026-10-16T11:54:42+09:00` |
| 거버넌스 원본의 작업 트리 변경 | `git diff --stat HEAD -- AGENTS.md CLAUDE.md Workflow .claude .githooks .gitattributes .gitignore setup.cmd Departments/Development/assets/scripts` (Bash) | 2026-10-16T23:01:23+09:00 직전 | (출력 없음) |
| 시각 조회 | `date -Iseconds` (Bash) | 2026-10-16T23:01:23+09:00 | `2026-10-16T23:01:23+09:00` |
| 추적 `.gitkeep` 대조(EC 3.3절 3번 37개, 삭제 17개, 이동 20개) | `git ls-files Departments \| grep "\.gitkeep$"` 와 `grep -c` (Bash. 앞에 저장소 루트로의 `cd`를 붙여 실행했으며 권한 거부 없이 실행됨. 이 행과 아래 두 행이 같다) | 2026-10-16T23:01+09:00 무렵 | 37개. 목록이 EC 3.3절 3번 「삭제」 행 17개와 그 밖 20개로 나뉨을 확인 |
| 현행 `allow` 규칙 | Bash `cat -n .claude/settings.json` | 2026-10-16T23:01+09:00 무렵 | 17행 `"Bash(python Departments/*/workspace/*)"`, 15행 `"Bash(python Departments/Development/assets/scripts/check_standard.py*)"`, 16행 `"Bash(python -m pytest*)"` |
| 기존 부적합 기록 대조 | Bash `grep`·`awk`로 `Departments/Quality/docs/nonconformance/NCR-*.md` 머리말 추출 | 2026-10-16T23:01+09:00 무렵 | 52건. 결과는 `NCR-032_03.md` 4절 |
| 완료 시각 조회 | `date -Iseconds` (Bash) | 2026-10-16T23:02:33+09:00 | `2026-10-16T23:02:33+09:00`(머리말 `completed_at`과 같다) |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 구분은 `Workflow/03_라이프사이클` 「재작업 구분」을 따른다(`REQ-032_v01`은 `REQ-024` 커밋 뒤에 작성되어 적용 대상). 다섯 건 모두 승인된 REQ의 `scope:`·「결정」 열을 바꾸지 않고 EC 문안으로 고칠 수 있으므로 `Rework`다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | EC 2.3절 「이 REQ 자신의 실행」, 3.9절 4번 ⑤~⑦ | EC는 이 REQ 자신의 최종 승인 커밋을 현행 규정(커밋 `655a45d`)으로 한다고 정하면서(D13), 반영 ② 이동 뒤에 실행되는 현행 `Workflow/05` 1.1절 6·7번의 처리를 정하지 않았다. ① 7번은 `python Departments/Development/assets/scripts/check_standard.py --staged`를 실행하게 하나, 이동 뒤에는 그 경로에 파일이 없다(3.3절 2번 표 `Departments/Development/assets/` 행). 3.9절 4번은 ⑥ 스테이징에서 ⑦ 커밋으로 넘어가며 7번을 언급하지 않는다. ② 6번 ⑪은 종결 기록을 `Departments/Secretariat/assets/inbox/`에 쓰게 하나, 새 `check_standard.py`는 종결 기록을 `Departments/Secretariat/Secretary/assets/inbox/`에서만 읽고(3.5절 14행) 옛 위치는 옛 경로 잔존 검사의 뺄 범위(3.6절 2번 ②)에도 들지 않는다. 옛 위치에 쓰면 뒤 커밋의 검사가 `REQ-032`를 끝난 안건으로 보지 못해 `scope:`(`Departments`, `AGENTS.md`, `Workflow`, `.claude` 등)가 통과 근거로 계속 남거나, 종결 기록 본문의 옛 경로(「대상 기록」 줄 등)로 이 커밋이 막힐 수 있다. D5(옮기는 동안 보호를 빈틈없이 이어 감)의 반영에 필요한 결정이 빠졌다. 이동 뒤의 현행 절차 단계에서 옛 경로를 2.3절 대응으로 읽는다는 처리처럼, 단계마다 쓰는 경로·명령을 정해야 한다 | Rework | 설계부 |
| D2 | EC 2.1절 표 아래 셋째 항목, 3.9절 3·5번, 3.13절 ⑤ | 3.13절 ⑤는 `DEV-032_v02` 「이동 목록」에 실제 저장소에 대한 이동 명령 미리보기 출력(옛 경로 → 새 경로 전체, 뺀 파일과 사유, 건수)을 적게 하나, 그 출력을 얻는 명령이 지정되지 않았다. 2.1절은 12·13번 파일을 `python -m pytest` 형태로 실행한다고 정하지만 12번(이동 명령)은 시험 파일이 아니어서 그 형태로는 미리보기가 출력되지 않고, 3.9절 5번은 단위 시험이 `tmp_path` 아래 시험 저장소에서만 돈다고 정한다. 직접 실행 형태(`python Departments/Development/workspace/REQ-032_move_<YYYYMMDD>a.py`)는 EC가 `EC-031_v02` 6절 6·7행의 확인 요청 사례를 들어 피한 형태다. 구현 세션이 어느 명령으로 이 산출물을 만들지 정해지지 않아, 그 명령이 `Workflow/06` 2.1절 「명령 형태」의 원리 안에 있는지 확인할 수 없다 | Rework | 설계부 |
| D3 | EC 3.9절 4번 ②, 4절 13행 | 반영 ② 이동 명령 `python Departments/Development/workspace/REQ-032_move_<YYYYMMDD>a.py --apply`는 반영 때 형상통제팀(C02) 세션에 적용되는 현행 `allow` 규칙 `Bash(python Departments/*/workspace/*)`(`.claude/settings.json` 17행. 개발 적용본의 `settings.json`은 ④에서야 복사된다)과 글자 그대로 맞는다. 그래서 `Departments/` 아래 파일 전체를 옛 경로에서 없애고 새 경로에 만드는 명령이 확인 화면 없이 실행될 수 있다. 현행 `Workflow/06` 2.2절 표는 반영 명령이 `allow`에 없어 확인 화면이 뜬다는 것을 반영 통제의 전제로 적고, REQ 요구 항목 20은 「커밋·삭제·덮어쓰기는 지금처럼 확인 화면에서 대표님 승인을 거친다」고 정하며, EC 자신도 G14로 그 규칙으로 실행하는 스크립트 안에서 이동을 하지 않는다는 규정을 더한다. EC는 이 관계를 다루지 않았다(4절 13행은 구현 단계의 명령만 다룬다). 이동 명령이 확인 화면을 거치게 하는 실행 형태나 처리를 정해야 한다 | Rework | 설계부 |
| D4 | EC 3.6절 3번 「커밋 종류별」 | `[CEO]` 커밋 본문에서 `^[A-Z][A-Za-z]*(-[A-Za-z]+)*: ` 형태의 줄을 모두 근거 줄로 보고 키를 `Request-Record`·`Follows`로만 허용하므로, 근거 줄이 없는 대표님 직접 커밋도 본문에 `Refs: …`, `Note: …` 같은 줄이 있으면 실패한다. D16 결정은 「`[CEO]` 커밋은 제목 줄 형식만 확인하고 근거 줄이 없어도 통과」시키고 근거 줄이 있을 때만 키와 경로 형식을 확인하게 하며, 근거 줄의 키는 `Workflow/07_문서_서식_및_번호` 2절 「커밋 메시지」 표와 「같은 안건의 여러 커밋」이 정한다(`Approved-REQ`, `Approved-RES`, `Approval-Record`, `Style-Check-RES`, `Confirmed-HOTFIX`, `Request-Record`, `Follows`). 07의 키가 아닌 줄까지 근거 줄로 보아 실패시키는 것은 결정보다 넓게 막는다 | Rework | 설계부 |
| D5 | EC 3.3절 2번 표와 표 아래 첫 항목, 3.2절 G16, 3.3절 1번 결과서 위치 항목, 3.8절 3번 ③·8번 ① | 대응표(02 2.3절에 둘 표)에 운영부·마케팅부 행이 없고, 표 아래 문장은 운영부·마케팅부 하위 폴더를 「대응하는 새 폴더가 없는 폴더」로 적는다. 그런데 3.3절 1번과 3.8절은 규정의 `Departments/Marketing/docs/DESIGN.md`(`Workflow/07` 15행), `Departments/Operations/results/RPT-xxx_vNN.md`(`Workflow/05` 114행), `Operations/assets/live/`(`Workflow/02` 57행)를 `Marketing/VisualDesign/docs/DESIGN.md`, `Operations/Security/results/`, `Operations/Release/assets/live/`로 바꾼다. G16은 경로를 3.3절 2번 표로 바꾼다고 정하므로 이 바꾸기는 표에 근거가 없고, 그 옛 경로를 적은 기록(예: `REQ-027` 기록)은 2.3절 표로 읽을 수 없다. 운영부 `results/`처럼 옛 폴더 하나가 대기 팀 둘로 나뉘는 경우의 읽는 규칙도 없다. 요구 항목 18 「이미 작성된 기록의 경로는 고치지 않고 대응으로 읽는다」와 대응을 한 곳에 둔다는 원천 관계(3.1절 표)에 어긋난다 | Rework | 설계부 |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
