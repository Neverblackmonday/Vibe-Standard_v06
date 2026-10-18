---
task_id: "032"
gate: "REQ"
result: "fail"
completed_at: "2026-10-15T02:38:02+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-032-REQ: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-032_v01.md` (v01)
- **판정 차수**: 1차
- **부적합 기록**: `Departments/Quality/docs/nonconformance/NCR-032_01.md`

## 2. 판정 기준별 결과
| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절의 원문 R·S·T·U, 요구 항목 2·18, 「REQ에서 정할 사항」 「공통」·요구 항목 18, 3절 28·29항을 `ORD-012_v08.md` 150~165행, 332행, 384~391행, 394~396행, 412행, 443~444행과 대조해 글자가 같음을 확인. `setup.cmd`·`.gitignore`를 scope에서 뺀 사유(경로 없음)는 Read(`.gitignore`)·Grep(`setup.cmd`, 패턴 `\\|/`와 `Departments`)으로 확인해 사실과 맞음 |
| 2 | 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 이 REQ가 맡는 요구 항목은 18 하나이고 5절 체크리스트도 18 한 행이다. 요구 항목 2는 인용만 하며 `REQ-031`이 맡는다(1절 머리 설명) |
| 3 | scope가 요구를 모두 덮고 요구 밖 경로가 없다 | PASS | `Departments`, `AGENTS.md`, `Workflow`, `.claude`, `.githooks`, `.gitattributes`로 요구 항목 18의 대상(규정 문서, 서식, 검사 스크립트, 배포본 제외 규칙, 서브에이전트 정의, 권한 설정, 훅)을 덮는다. scope 밖에서 `Departments/`를 가리키는 파일은 `CEO/References/VibeOffice_시안_통합화면_v01.html`(2곳), `Lab/` 실험기록 3개(8곳), `Audits/`·`_archive/` 기록이다(Grep 조회). 이들을 고칠 대상에 넣을지는 결함 D3의 문제로 따로 적었다 |
| 4 | 분류가 정의 기준과 맞고 `workflow:`가 2절과 맞다 | PASS | `classification: "Critical"`, 2절 「분류 근거」가 `Workflow/03` 2절 표 Critical 행(통제 붕괴, 거버넌스 파일·보안·권한)을 인용하며 ORDER `classification_proposal`(Critical)과 같다. `workflow:`는 EC 판단 → EC 작성 → EC 판정 → 명세 → 명세 판정 → 인수 시험 → 구현 → 최종 판정으로 2절 표와 같고, 실험·시각 디자인 단계를 두지 않은 사유가 1절 「참고」에 있다 |
| 5 | 완료 기준을 실행이나 열람으로 확인할 수 있다 | FAIL | 5절 ②는 운영부·마케팅부 처리와 모순되어 확인 결과가 정해지지 않고(D2), ⑥의 「대상 파일 전체」는 범위가 정해지지 않아 0건 여부를 확인할 수 없다(D3) |
| 6 | 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 결함 D1~D4 |
| 7 | Critical REQ의 「대상」 위치에 구현 방법이 없다 | PASS | 2절 「목적」은 문구·위치·수단을 EC로 넘긴다. 3절 D1~D11은 이름 규칙, 시점, 범위, 위치, 판단 근거 같은 정책 선택이고, D7은 ORDER가 정할 일로 지정한 「작성 파트를 가리는 근거」다. 4절 「작업」 열은 산출물 이름(적용본, 이동 목록, 대조 결과, 반영 명령)만 적는다 |
| 8 | 체크리스트·실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 5절 머리 설명과 3절 표 아래 둘째 항목에 「D1~D11의 권고안을 전제로 한다」는 전제를 적었다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음(REQ 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 완료 시각 조회 | PowerShell `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"` | 2026-10-15T02:38:02+09:00 | `2026-10-15T02:38:02+09:00`(머리말 `completed_at`과 같다) |
| 대신한 명령(시각 조회) | Bash `date -Iseconds` 실행하지 못함 → PowerShell `Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"`로 대신함 | 2026-10-15T02:37:58+09:00 | 메시지 원문: 「Permission to use Bash has been denied.」 대신한 명령 결과: `2026-10-15T02:37:58+09:00` |
| scope 밖 경로 조회 | Bash `git ls-files ... ; git grep -l "Departments" -- . ':!Departments' ...`(첫 호출, 실행됨) | 2026-10-15T02:3x+09:00(실행 시각을 따로 조회하지 않음) | scope 밖에서 `Departments`를 담은 추적 파일은 `Audits/AUDIT_20261006_표준v03환경검토및과제분석_v01.md`, `CEO/References/VibeOffice_시안_통합화면_v01.html`, `Lab/` 실험기록 3개, `_archive/` 아래 파일이다. `setup.cmd`, `.gitignore`, `CLAUDE.md`는 나오지 않았다 |
| 대신한 명령(경로 재확인) | Bash `git grep -n "Departments" -- setup.cmd .gitignore CLAUDE.md; ...` 실행하지 못함 → Grep 도구로 대신함 | 2026-10-15T02:3x+09:00 | 메시지 원문: 「Permission to use Bash has been denied.」 대신한 결과: `setup.cmd`·`.gitignore`·`CLAUDE.md`에서 `Departments` 일치 없음, `CEO/` 2건(1개 파일), `Lab/` 8건(3개 파일), `AGENTS.md` 10건, `Workflow/0*.md` 92건(6개 파일) |
| 커밋 전 검사 대조 제외 확인 | Read `Departments/Development/assets/scripts/check_standard.py` 49~55행, 120~126행 | 해당 없음(열람) | `WHITELIST_PREFIXES`에 `"Departments/Secretariat/docs/requests/REQ-"`가 있고, `is_whitelisted()`가 `Departments/<부서>/workspace/` 아래를 뺀다 |
| 운영부·마케팅부 폴더 조회 | Glob `Departments/{Operations,Marketing}/**/*` | 해당 없음(조회) | 두 부서 폴더에는 `assets/…/.gitkeep`, `docs/.gitkeep`, `results/.gitkeep`, `workspace/.gitkeep` 14개만 있다 |
| 팀 상태 조회 | Read `Departments/Secretariat/assets/research/조사_20261013_조직도개선안_v02.md` 76~108행 | 해당 없음(열람) | 운영부(배포팀 O01, 보안팀 O02)와 마케팅부(디자인팀 M01, 콘텐츠팀 M02·M03, 홍보팀 M04)의 파트가 모두 「대기」 |

- 「scope 밖 경로 조회」와 「대신한 명령(경로 재확인)」 행의 시각은 실행 시각을 따로 조회하지 않아 「2026-10-15T02:3x+09:00」로 적었다. 이 두 행은 판정 근거인 파일 목록과 건수만 쓰며, `completed_at`의 근거가 아니다.

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
> 「구분」은 `Workflow/03_라이프사이클` 「재작업 구분」 1항에 따라 REQ 판정이므로 모두 「해당 없음」이다.

| 번호 | 위치 | 결함 | 구분 | 반려 부서 |
| :---: | :--- | :--- | :---: | :--- |
| D1 | 5절 ⑧, 3절 D4 | 서로 모순된다. D4 권고안은 「곳마다 지금 덮는 파일의 종류를 그대로 덮도록 … 넓히거나 좁히지 않는다」고 하고, PM팀 REQ·실행 기록을 빼지 않는 대상으로는 판정 전제 제외(`AGENTS.md` 「불변 원칙」 5항)만 든다. 그런데 ⑧은 「PM팀 폴더의 REQ·실행 기록이 판정 전제 제외와 **커밋 전 검사의 대조 제외**에 들지 않는다」를 요구한다. 지금 `check_standard.py`는 `WHITELIST_PREFIXES`의 `"Departments/Secretariat/docs/requests/REQ-"`(승인 전 초안 포함)와 `is_whitelisted()`의 부서 직속 `workspace/` 제외로 REQ와 실행 기록을 커밋 전 검사 대조에서 뺀다. ⑧대로 구현하면 이 범위가 좁아져 D4와 어긋나고, 어느 scope에도 들지 않는 승인 전 REQ 초안과 실행 기록의 커밋이 막힐 수 있다. ORDER의 예(「PM팀 폴더의 REQ는 판정 전제에서 빼지 않음」)도 판정 전제 제외만 가리킨다. ⑧의 대상을 판정 전제 제외로 줄이거나, 커밋 전 검사 대조 제외에서도 빼려면 D4와 맞추고 그 영향(승인 전 REQ·실행 기록의 커밋 경로)을 정할 일로 적어야 한다 | 해당 없음 | PM(비서실) |
| D2 | 3절 D2·D3, 5절 ② | 운영부(`Departments/Operations/`)와 마케팅부(`Departments/Marketing/`)는 팀이 모두 대기 팀이다(배포팀·보안팀, 디자인팀·콘텐츠팀·홍보팀. `조직도개선안_v02` 4절). D3 권고안대로면 두 부에는 팀 폴더가 생기지 않는다. 그런데 D2는 기존 파일을 모두 새 경로로 옮긴다고 하고, 두 부서 폴더의 기존 파일(`assets/live/.gitkeep` 등 14개)은 옮길 팀 폴더가 없다. 그대로 두면 부서 직속 `results/`·`workspace/`·`assets/` 같은 옛 구조와 옛 경로가 남고, 지우면 Git이 빈 폴더를 추적하지 않아 5절 ②의 「부서 폴더 이름 여섯 개가 그대로」를 충족할 수 없다. 대기 팀만 있는 부의 부서 폴더와 기존 자리를 어떻게 처리할지(예: 부서 폴더에 자리 표시 파일만 남김, 그 부의 팀 폴더는 예외로 만듦)를 정할 일이나 전제로 적고 ②를 그에 맞춰야 한다 | 해당 없음 | PM(비서실) |
| D3 | 5절 ⑥, 1절 요구 항목 18 여섯째 하위 항목, 4절 표 아래 셋째 항목 | 옛 경로 잔존 검사의 「대상 파일 전체」가 무엇인지 정해지지 않아 두 가지로 읽힌다. (가) 저장소 전체로 읽으면 scope 밖의 `CEO/References/VibeOffice_시안_통합화면_v01.html`(AI 읽기 전용, `Departments/` 2곳)처럼 「이미 작성된 기록」인지 분명하지 않은 파일이 남아 0건이 될 수 없고, D8로 이 검사가 커밋을 막으면 그 뒤 모든 커밋이 막힐 수 있다. (나) scope 안의 파일이나 경로를 가리키는 곳(규정 문서, 서식, 장치 파일 등)으로 읽으면 0건을 확인할 수 있다. 4절은 `CEO/`, `_archive/`, `Lab/`, `Storage/`, `Audits/`를 scope에서 뺀 사유만 적고, 잔존 검사의 대상에서 빠지는지는 적지 않았다. 검사 대상 범위(또는 대상에서 빼는 구역)를 정할 일이나 전제로 적어야 한다 | 해당 없음 | PM(비서실) |
| D4 | 3절 D7, 5절 ④ | D7 권고안은 작성 파트를 「머리말의 작성 주체 칸」으로 가리고, 머리말이 없는 파일은 대조하지 않는다고만 한다. 머리말은 있지만 작성 주체 칸이 없는 파일(예: `ORD-012_v08.md`의 머리말은 `order_id`·`created`·`ceo_checked_at`·`classification_proposal`·`related_req`뿐이다)의 처리가 빠져, 커밋 전 검사가 이런 파일을 실패시키는지 건너뛰는지 두 가지로 읽힌다. 실패시키면 ORDER·종결 기록 같은 비서팀 기록의 커밋이 막힌다. 이 경우의 처리를 D7에 적어야 한다 | 해당 없음 | PM(비서실) |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음

## 8. 인수 시험 판정 (최종 판정, 인수 시험 단계가 있는 경우만)
해당 없음
