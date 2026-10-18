---
task_id: "017"
gate: "REQ"
result: "fail"
completed_at: "2026-10-09T13:21:40+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "medium (실행 명령 기준)"
---

# RES-017: 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Secretariat/docs/requests/REQ-017_v01.md`(입력 ORDER `Departments/Secretariat/assets/inbox/ORD-005_v03.md`, 요구 항목 배정 확인용 `REQ-016_v01.md` D1·`REQ-018_v01.md`)
- **판정 차수**: 1차

## 2. 판정 기준별 결과
> 판정 기준은 `Workflow/03_라이프사이클` 「REQ 작성 파이프라인」 2항 ①~⑧이다.

| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | ① 요청 원문의 요구가 빠지거나 바뀌지 않았다 | PASS | REQ 1절이 ORDER 2절 요구 항목 3·4·5와 3절 2·3·4항을 원형대로 인용한다(ORDER 144~146행, 179~181행과 대조). 배정은 `REQ-016_v01` D1 권고안(016: 1·2·7·8·9, 017: 3·4·5, 018: 6)과 같고, ORDER 2절 「REQ에서 정할 사항」 가운데 품질 관련 항목(인수 시험 시점·적용 분류, 단위 테스트 관계, 세션 분리, 하위 경로, 부적합 대상, 소급, 개정 제안 기준·경로)이 D1~D6으로 옮겨졌다. 하위 경로 항목을 EC로 넘긴 것은 `Workflow/03` 3절 1항 「구현 방법」(파일·폴더의 내부 구성)에 따른 처리이며 1절 참고에 사유가 있다. 3절 3항 「파트로 나누지 않는다」는 체크리스트 5②에서 확인한다 |
| 2 | ② 체크리스트가 요청 원문 항목과 1:1로 대응한다 | PASS | 체크리스트 번호 3·4·5가 요구 항목 3·4·5와 1:1이다 |
| 3 | ③ scope가 요구를 모두 덮고 요구 밖 경로가 없다 | PASS | 4절 「scope 경로별 사유」가 scope 항목 15개 각각을 요구 항목에 연결한다. 체크리스트 5④의 Grep `판정서만` 대상은 거버넌스 파일 가운데 `AGENTS.md`(26행)와 `.claude/agents/quality.md`(19행) 두 곳뿐이며 둘 다 scope 안이다(Grep, `_archive/`·`CEO/`·`Departments/` 제외). `Workflow/04`·`settings.json` 제외 사유(4절 둘째 항목)는 `settings.json` `deny` 목록(거버넌스 파일·`CEO/`·`_archive/`)과 `Workflow/04` 1절 표 「파이프라인 안의 모든 서브에이전트」를 조회해 사실과 맞음을 확인했다 |
| 4 | ④ 분류와 `workflow:`가 2절과 맞다 | PASS | `classification: "Critical"`(거버넌스 파일 개정, 품질 권한 한계 변경). `workflow:`가 `Workflow/03` 2절 Critical 단계(EC 작성 → EC 판정 → 명세 → 구현 → 최종 판정)와 같다. 이 REQ 자체에 인수 시험 단계를 넣지 않는 사유가 3절 표 아래에 있다 |
| 5 | ⑤ 완료 기준을 실행이나 열람으로 확인할 수 있다 | FAIL | 결함 D1. 체크리스트 3⑤는 인수 시험의 배포본 제외와 커밋 전 검사 처리(scope 대조)를 확인하지만, 체크리스트 4에는 부적합 기록에 대한 같은 확인이 없다. 4절 scope 사유는 `.gitattributes`를 「인수 시험·부적합 기록을 배포본에서 빼는 규칙」으로, `Workflow/02`를 「4절 작업 구역」으로 들고 있으나 최종 판정에서 이를 확인할 항목이 없다 |
| 6 | ⑥ 뜻이 둘 이상으로 읽히는 문장이 없다 | FAIL | 결함 D2. D1 권고안의 「적용 분류: Critical·Major만」과 「인수 시험 대상은 체크리스트 항목 가운데 실행으로 확인하는 항목」이 함께 있어, 실행으로 확인하는 항목이 없는 Critical·Major REQ에서 인수 시험 단계를 거치는지 두 가지로 읽힌다 |
| 7 | ⑦ Critical·Major REQ는 「구현 방법」 기준의 대상 위치에 구현 방법이 없다 | PASS | 2절 목적은 달성할 결과와 「반영 문구, 절 구성, 서식, 폴더 안 구성, 검사 스크립트의 규칙은 EC에서 정한다」만 적는다. 3절 D1~D8은 시점·적용 범위·책임 주체·대상 범위·소급 여부·기준·경로·effort의 정책 선택이다. 4절 「작업」 열은 단계의 할 일과 산출물 이름만 적는다 |
| 8 | ⑧ 체크리스트와 실행 계획의 뜻이 결정 표의 선택에 따라 달라지지 않는다 | PASS | 3절 표 아래 둘째 항목에 「4절 실행 계획과 5절 체크리스트는 D1~D8의 권고안을 전제로 작성했다」와 결정 우선 규정이 있다. 체크리스트 항목은 「D? 권고안대로」로 전제를 밝힌다 |

**배경 사실 확인**(2절 배경 대조, 모두 일치)
- 최신 커밋 `610558b 2026-10-09T13:01:07+09:00`(`git log -1`).
- `Departments/Quality/` 추적 파일: `assets/.gitkeep`, `docs/.gitkeep`, `results/.gitkeep`과 판정서, `workspace/.gitkeep`(`git ls-files Departments/Quality`).
- `.gitattributes`는 `Departments/*/results/**`, `Departments/*/workspace/**`, REQ·EC를 `export-ignore`하고 `Departments/Quality/assets/`·`docs/`는 대상이 아니다.
- 판정서 69건, `fail` 28건(REQ 판정 19건, EC 판정 7건, 최종 판정 2건), `rejected` 0건(Grep `^result:` `Departments/Quality/results`).
- `Workflow/02` 2절 품질 행(33행)·개발 행(32행), `Workflow/03` 5절 구현 행, `Workflow/06` 4절 순서 6, `Workflow/03` 7절 1~7·8절, `Workflow/07` 3절 「`result` 값」(91행)이 배경 서술과 같다.

## 3. 체크리스트 대조 (최종 판정만)
해당 없음

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 범위 대조 | `git status --porcelain -uall` | 2026-10-09T13:20:59+09:00 | `?? Departments/Design/workspace/REQ-014_결과서갱신_20261009d.py` / `?? Departments/Design/workspace/REQ-014_복사_20261009c.py` / `?? Departments/Secretariat/assets/inbox/ORD-005_v01.md` / `?? Departments/Secretariat/assets/inbox/ORD-005_v02.md` / `?? Departments/Secretariat/assets/inbox/ORD-005_v03.md` / `?? Departments/Secretariat/docs/requests/REQ-016_v01.md` / `?? Departments/Secretariat/docs/requests/REQ-017_v01.md` / `?? Departments/Secretariat/docs/requests/REQ-018_v01.md` / `?? Departments/Secretariat/workspace/실행기록_REQ-016.md` / `?? Departments/Secretariat/workspace/실행기록_REQ-017.md` / `?? Departments/Secretariat/workspace/실행기록_REQ-018.md` (이 판정서 작성 전) |
| 커밋 전 검사 | `python Departments/Development/assets/scripts/check_standard.py` | 2026-10-09T13:20:59+09:00 | `[PASS] 모든 변경 파일이 scope 대조 제외 구역 안에 있습니다.` / `[SUCCESS] 바이브 표준 v04 커밋 전 검사 통과.` |
| 최신 커밋 | `git log -1 --format="%h %cI"` | 2026-10-09T13:20:59+09:00 | `610558b 2026-10-09T13:01:07+09:00` |
| 판정 결과 이력 | Grep `^result:` (`Departments/Quality/results`) | 2026-10-09T13:20:59+09:00 | 69건 가운데 `fail` 28건(REQ 19, EC 7, FINAL 2), `rejected` 0건 |
| `판정서만` 사본 | Grep `판정서만` (`_archive/`·`CEO/`·`Departments/` 제외) | 2026-10-09T13:20:59+09:00 | `AGENTS.md:26`, `.claude\agents\quality.md:19` |

## 5. 결함 목록과 반려 부서 (`fail`·`rejected`일 때만)
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | REQ 5절 체크리스트 4, 4절 「scope 경로별 사유」 | 누락. 체크리스트 3⑤는 인수 시험의 배포본 제외(`.gitattributes`)와 커밋 전 검사 처리(조건부 테스트, scope 대조)를 확인하지만, 체크리스트 4에는 부적합 기록에 대한 같은 확인이 없다. 4절 scope 사유는 `.gitattributes`를 「안건마다 쌓이는 인수 시험·부적합 기록을 배포본에서 빼는 규칙」으로 들고 있어 부적합 기록의 배포본 제외 반영을 최종 판정에서 확인할 근거가 없다. 또 부적합 기록은 D4 ①대로 REQ 판정 `fail`(REQ 승인 전)에도 생기는데, 현행 `Workflow/02` 4절은 REQ 승인 전 품질의 수정 경로를 `results/`(REQ 판정서)와 `workspace/`로만 정하고, 현행 `check_standard.py`는 부서 직속 `results/`·`workspace/` 밖의 변경을 승인된 REQ의 scope와 대조한다(`Workflow/06` 4절 순서 4·5). EC가 부적합 기록을 품질 `docs/`·`assets/`에 두면, 기록 작성 권한(작업 구역)과 그 기록을 담은 커밋의 scope 대조(예: 다음 안건 `REQ-018`의 scope에는 품질 폴더가 없다) 처리가 필요하지만 체크리스트가 이를 확인하지 않아, 반영되지 않아도 최종 판정을 통과할 수 있다. 체크리스트 4에 부적합 기록의 작업 구역(REQ 승인 전 포함), 커밋 전 검사 처리, 배포본 제외 여부를 확인하는 항목을 더하거나, 배포본 제외 대상이 아니면 4절 scope 사유의 서술을 고친다 | PM(비서실 REQ 작성) |
| D2 | REQ 3절 D1 권고안, 5절 체크리스트 3② | 중의성. D1 권고안은 적용 분류를 「Critical·Major만」으로 하면서 인수 시험 대상을 「체크리스트 항목 가운데 실행으로 확인하는 항목」으로 한정한다. 실행으로 확인하는 항목이 없는 Critical·Major REQ(거버넌스 문서만 고치는 안건 등)에서 ⓐ 인수 시험 단계를 그대로 거치는지(빈 인수 시험 또는 「대상 없음」 기록) ⓑ `workflow:`에서 그 단계를 빼는지가 두 가지로 읽힌다. 체크리스트 3②의 「Critical·Major의 원스톱 파이프라인에 품질의 인수 시험 단계가 명세와 구현 사이에 있고」도 두 해석 모두에 맞아 EC의 선택을 판정할 기준이 되지 못한다. 이 선택은 단계 하나의 추가 여부로 절차 무게를 정하는 정책이므로(D1 대안 (나)의 사유와 같은 성격) 권고안에 처리 방법을 적거나 결정 표에 정할 일로 둔다 | PM(비서실 REQ 작성) |

## 6. 문체 지적
없음

## 7. 삭제 대상 (최종 판정만)
해당 없음
