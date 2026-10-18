---
task_id: "017"
gate: "REQ"
result: "pass"
completed_at: "확인 불가" # 작성일 2026-10-09. 이 판정 세션에서 Bash·PowerShell 실행 권한이 거부되어 시각을 조회하지 못했다
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-017: 판정서

## 1. 판정 요약
- **판정 결과**: `pass`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-017_v04.md`(출처 ORDER `Departments/Secretariat/assets/inbox/ORD-005_v04.md`)
- **판정 차수**: 1차(ORDER 변경으로 생긴 REQ 새 버전이므로 `Workflow/03_라이프사이클` 8절 「적용 제외」에 따라 최초 판정부터 센다. 직전 버전 `REQ-017_v03`의 판정서는 `Departments/Quality/results/RES-017-REQ_v03.md`). 최초 판정이므로 REQ 전체를 판정했다.

## 2. 판정 기준별 결과
> 판정 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | ① 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | 1절의 요구 항목 3·4·5, 확정 사항 2·3·4항, 9항 머리 문장과 ②, 10항이 ORD-005_v04 2절·3절(186~188행, 206~208행, 213·215·217행)과 글자 그대로 같다. 원문 M 인용 두 줄은 ORDER 117·120행(빈 인용 줄을 포함해 여섯째·아홉째 줄), 원문 N 인용은 128행과 같다. 1절 참고 「v03 결정의 반영」 D1은 `REQ-017_v03` 103행 D1 권고안(시점, 적용 분류, `workflow:`에 늘 넣음, 실행 확인 항목, 「대상 없음」)에 ORDER 9항 ②의 수정안(명세 전 실험은 실험실, 명세 후 시험은 시험실)을 더한 것이고, D2~D7은 `REQ-017_v03` 104~109행의 권고안과 뜻이 같다(D4는 각 중단 조건의 괄호 풀이만 줄였다). ORDER 2절 「REQ에서 정할 사항」 가운데 이 REQ와 관련된 「파이프라인 안의 실험 단계」는 ORDER가 허용한 대로(198행 괄호) `REQ-016_v04` D6~D10에 두었고 이 REQ 1절 참고(105행)에 그 위치를 적었다. `REQ-016_v04` 154행·186~190행에서 같은 배정을 확인했다 |
| 2 | ② 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 5절 체크리스트 3·4·5가 요구 항목 3·4·5와 번호·내용이 대응한다. 요구 항목 3에 새로 들어온 「명세 전에 필요한 실험은 실험실에서 한다」는 체크리스트 3③이 확인한다 |
| 3 | ③ scope가 요구를 모두 덮고 요구 밖 경로가 없다 | PASS | 4절 「scope 경로별 사유」가 머리말 `scope:`의 경로마다 요구 항목 번호와 개정 대상 절을 적는다. 사유에 적힌 절은 현행 문서에 있다(Grep `^##? `: `Workflow/02` 2절·4절, `Workflow/03` 2·4·5·7·8절, `Workflow/05` 1.1절 6번·4절·5절, `Workflow/06` 3·4절, `Workflow/07` 1~3절, `Workflow/01` 3절 33행 배포본 제외 문장). 체크리스트가 확인하는 파일(`AGENTS.md`, `Workflow/01`·`02`·`03`·`05`·`06`·`07`, 서식, `quality.md`, `development.md`, `.gitattributes`, `check_standard.py`, 품질 폴더)은 모두 `scope:`에 있다. scope에서 뺀 `Workflow/04`, `.claude/settings.json`, `Lab/`은 사유와 구현 단계 대조 계획이 4절에 있다 |
| 4 | ④ 분류와 `workflow:`가 2절과 맞다 | PASS | 거버넌스 파일 개정이므로 `Workflow/03` 2절 표의 Critical에 해당하고, `workflow:`(10~15행)는 「EC 작성 → EC 판정 → 명세 → 구현 → 최종 판정」으로 같은 표의 Critical 단계와 같다. 이 REQ에 인수 시험 단계를 넣지 않은 사유(규정이 이 REQ 반영 뒤에 효력이 생김)는 3절 끝(131행)에 있다. 실험 단계는 `REQ-016_v04` 217행에서 선택 단계이므로 없어도 어긋나지 않는다 |
| 5 | ⑤ 완료 기준을 실행이나 열람으로 확인할 수 있다 | PASS | 체크리스트 3①~⑧, 4①~⑧, 5①~③은 적용본 열람과 결과서의 대조 결과로, 5④는 Grep `판정서만`으로 확인한다. 「한 문서에만 있다」의 확인 방법과 「v03 Dn」의 지칭 대상은 5절 머리 안내(148행)에 있다. 「중단 조건」 번호가 `REQ-016` 반영 뒤 바뀌는 경우의 대조 방법도 4②에 있다 |
| 6 | ⑥ 뜻이 둘 이상으로 읽히는 문장이 없다 | PASS | 요구·실행 계획·체크리스트에서 두 뜻으로 읽혀 실행이 갈리는 문장을 찾지 못했다. 배경 119행 괄호의 「권고」는 표현만 다듬을 문장으로 보아 6절 S1에 적었다(배경 서술이며 실행 계획·체크리스트의 뜻에 영향이 없다) |
| 7 | ⑦ Critical·Major REQ는 「구현 방법」 기준의 「대상」 위치에 구현 방법이 없다 | PASS | 3절 결정 표는 effort 선택(D1)만 있다. 2절 「목적」은 바꿀 내용과 달성할 결과만 적고 반영 문구·절 구성·서식·폴더 안 구성·검사 규칙을 EC로 넘긴다(120행). 4절 「작업」 열은 「적용본 작성」, 「품질 폴더 안 자리 작성」, 「대조」, 「결과서에 기재」처럼 할 일과 산출물 이름만 적는다. 인수 시험·부적합 기록의 하위 경로와 원인 분류 방식은 EC로 넘겼다(109행, 103행) |
| 8 | ⑧ 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 결정 표는 effort(D1)뿐이며, 130행이 D1 선택에 따라 뜻이 달라지는 항목이 없다고 적는다. 체크리스트와 실행 계획이 전제로 쓰는 「v03 결정의 반영」은 ORDER 3절 9항으로 이미 정해진 사항이다 |
| - | 「판정 지적의 구분」 1항(실행 실패·지칭 오류) | PASS | 6절 실행 명령(160행)이 `Departments/Secretariat/docs/requests/REQ-017_v04.md`를 가리키며 이 파일명과 같다. 1절 참고 105행이 가리키는 「`REQ-016_v04` 1절 참고 「v03 결정의 반영」 v03 D1」은 `REQ-016_v04` 142행에 있다 |

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
> 이 판정 세션에서는 Bash·PowerShell 실행 권한이 거부되어(Bash로 `git log`, `git status`를 요청했을 때 거부 응답) 셸 명령의 실행 시각을 조회하지 못했다. 시각 열은 「확인 불가」로 적고, 조회는 Read·Grep·Glob으로 했다. 첫 행의 `diff`만 거부 전에 Bash로 실행했다.

| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 직전 버전과의 차이(참고) | `diff REQ-017_v03.md REQ-017_v04.md`(`Departments/Secretariat/docs/requests`) | 확인 불가(같은 명령의 `date`는 출력이 잘려 확인하지 못함) | 출력 36.7KB. 첫 차이 `37c37`(출처 ORDER가 `ORD-005_v03.md`에서 `ORD-005_v04.md`로 바뀜), `69a70,79`(원문 M·N 인용 추가). 최초 판정이므로 판정은 v04 전체로 했다 |
| 최신 커밋 | Read `.git/HEAD`, Read `.git/refs/heads/master` | 확인 불가 | `ref: refs/heads/master`, `610558bdedf80e94220076a04169169394df8fe2`(배경 113행의 `610558b`와 같다) |
| 판정 결과 이력 | Grep `^result:`(`Departments/Quality/results`, count) | 확인 불가 | `Found 76 total occurrences across 76 files.` |
| `fail`·`rejected` 건수 | Grep `^result: "(fail\|rejected)"`, Grep `^result: "rejected"`(같은 폴더, count) | 확인 불가 | `Found 32 total occurrences across 32 files.`(파일명 기준 REQ 판정 23건, EC 판정 7건, 최종 판정 `RES-012_v01`·`RES-014_v02` 2건), `No matches found`. 배경 117행과 같다 |
| 품질 폴더 자리 | Glob `Departments/Quality/*/.gitkeep` | 확인 불가 | `assets`, `docs`, `results`, `workspace`의 `.gitkeep` 네 건 |
| 배포본 제외 규칙 | Grep `Quality\|results\|workspace\|REQ-\|EC-`(`.gitattributes`) | 확인 불가 | 9~14행: `REQ-*.md`, `EC-*.md`, `Departments/*/results/**`, `Departments/*/workspace/**` 제외(`.gitkeep`은 포함). `Departments/Quality/assets/`·`docs/` 제외 규칙 없음. 배경 116행과 같다 |
| 현행 품질·개발 책무와 조건부 테스트 | Grep `품질\|개발 \\\|\|pytest`(`Workflow/02`·`06`), Grep `테스트`(`.claude/agents/development.md`) | 확인 불가 | `Workflow/02` 32·33행(개발 「승인된 범위의 구현과 테스트」, 품질 「REQ 판정, EC 판정, 최종 판정」·`results/RES-*`), `Workflow/06` 47행(순서 6 조건부 테스트), `development.md` 13행 「구현과 테스트」. 배경 114·115행과 같다 |
| scope 사유의 절 존재 | Grep `^##? `(`Workflow/01`·`02`·`03`·`06`·`07`), Grep(`Workflow/05`) | 확인 불가 | 4절 사유에 적힌 절이 모두 있다(2절 기준 3 근거) |
| 실험 단계 배정 | Grep `^\\\| D\d+ \|v03 D1\|실험 단계`(`REQ-016_v04.md`) | 확인 불가 | 142행 v03 D1, 154행 「파이프라인 안 실험 단계 항목의 위치」, 186~190행 D6~D10, 217행 「실험 단계가 선택 단계」 |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
해당 없음

## 6. 문체 지적
> 지적의 구분과 처리는 `Workflow/03_라이프사이클` 「판정 지적의 구분과 문체 지적 처리」를 따른다.

| 번호 | 위치 | 원문 | 수정 문안 | 대상 부서 |
| :---: | :--- | :--- | :--- | :--- |
| S1 | `REQ-017_v04.md` 2절 배경 「실험 단계」(119행) | `REQ-016_v04`가 실험실(`Lab/`)과 파이프라인 안 실험 단계(Critical·Major는 EC 작성 전 권고)를 정한다. | `REQ-016_v04`가 실험실(`Lab/`)과 파이프라인 안 실험 단계(선택 단계. Critical·Major에서 EC 작성 전에 두는 것이 권고안)를 정한다. | PM |

## 7. 삭제 대상 (최종 판정만)
해당 없음
