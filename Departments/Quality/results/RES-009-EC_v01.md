---
task_id: "009"
gate: "EC"
result: "fail"
completed_at: "2026-10-08T17:18:32+09:00"
auditor:
  agent: "Quality"
  model: "Claude Opus 5.5"
  effort: "확인 불가"
---

# RES-009-EC: EC 판정서

## 1. 판정 요약
- **판정 결과**: `fail`
- **대상 문서**: `Departments/Design/docs/tad/EC-009_v01.md` (기준 REQ: `Departments/Secretariat/docs/requests/REQ-009_v06.md`)
- **판정 차수**: 1차
- **판정 기준**: `Workflow/03_라이프사이클` 5절 「단계별 통과 조건과 판정 기준」 EC 판정 행 ①~④

## 2. 판정 기준별 결과
| 번호 | 판정 기준 | 결과 | 근거(파일·절·명령 결과) |
| :---: | :--- | :---: | :--- |
| 1 | REQ 목적의 누락·왜곡 없음 | FAIL | 요청 원문 1~9번과 REQ 체크리스트 1~8번은 EC 3.3절 1~5번, 3.4절, 5절 완료 기준 1~8·10번에 빠짐없이 대응한다. D1~D4 권고안도 EC 3.1절 표·3.3절 2번·⑧ 표·2.3절에 반영되어 있다. 다만 체크리스트 9번 ②의 확인 방법(EC 3.5절 ②, 4절 위험 7)이 REQ의 「착수 시점 기준과 같다」라는 기준과 어긋나게 읽힌다(결함 D1) |
| 2 | EC scope가 REQ scope 안 | PASS | EC 머리말 `scope:` 세 항목(`EC-009`, `RPT-009`, `DEV-009`)이 REQ 머리말 `scope:` 세 항목과 같다. EC 2.1절 신규 파일 두 건과 2.2절 「없음」도 이 안에 있다 |
| 3 | 요청하지 않은 기능·추상화 없음 | PASS | 설계 결정 E1(PM이 메인 세션에서 REQ 작성)은 요청 원문 3·6번에서 도출되고 근거가 적혀 있다. ORDER 머리말 필드는 메모 4절 구성 1항과 1:1이고 추가 필드가 없다(EC 3.3절 2번). `ceo_checked_at` 재기재 시 새 버전, `related_req` 갱신 시 버전 유지 규칙은 메모 4절 구성의 필드를 운용하는 데 필요한 범위다. 새 검사·새 폴더를 더하지 않는다(3.3절 2번 「여러 REQ로 나뉘는 경우」, D1) |
| 4 | 완료 기준을 확인할 수 있음 | FAIL | EC 5절 완료 기준 1~8·10~12번은 `RPT-009`·`DEV-009`·최종 판정서 열람으로 확인할 수 있다. 9번은 3.5절 ②의 판정 결과가 정해져 있지 않아 확인 결과가 판정자마다 달라질 수 있다(결함 D1). 3.3절 4번 검색 범위의 사실 오류(결함 D2)로 반영 대상 목록의 완전성 기준이 흔들린다 |

### 2.1 사실 대조 (EC가 인용한 현행 값)
| 항목 | EC 기재 | 확인 결과 |
| :--- | :--- | :--- |
| `check_standard.py` 행 번호 | 35·36·148·152행, `RECORD_NAME` 58행 | 일치. Grep 결과 35행 REQ 경로, 36행 `Departments/Secretariat/assets/`(주석 「요구 메모」), 58행 `RECORD_NAME`, 148행 `requests`, 152행 `results` HOTFIX |
| `.gitattributes` 15~17행 | `Departments/Secretariat/` 배포본 제외 규칙 | 일치. 15행 `Departments/Secretariat/assets/*/** export-ignore`, 16·17행 |
| `.claude/` 정의 파일 | `settings.json`, `agents/*.md` 일곱 개 | 일치. Glob 결과 `design.md`, `development.md`, `marketing.md`, `operations.md`, `quality.md`, `secretariat.md`, `visual.md` |
| `allow` 목록의 `git ls-files`·`check_standard.py` 실행, `git check-attr` 부재 | EC 3.4절 1·2·3번 | 일치. `.claude/settings.json` 8·15행에 있고 `git check-attr`는 없다 |
| 인용 절 | `Workflow/02` 2.1절·4절, `03` 9절 2항, `05` 2절, `06` 1절 계층 1 한계·5절 1항·6.3절 3항, `07` 3.1절 3항, `01` 「용어」 오케스트레이터 행 | 모두 해당 위치에 같은 내용이 있다 |
| 템플릿의 `Departments/Secretariat/` 예시 경로 | `DEV_TEMPLATE.md`·`EC_TEMPLATE.md` | 일치(DEV 13행, EC 22행) |

## 3. 체크리스트 대조 (최종 판정만)
- 해당 없음(EC 판정).

## 4. 검증 기록
| 항목 | 명령 | 시각 | 결과 원문 |
| :--- | :--- | :--- | :--- |
| 판정 시각 | `date "+%Y-%m-%dT%H:%M:%S%z"` | 2026-10-08T17:18:32+09:00 | `2026-10-08T17:18:32+0900` |
| 작업 트리 상태(참고) | `git status --porcelain -uall` | 2026-10-08T17:18:32+09:00 직후 | EC 1.1절 출력 14줄과 같은 줄에 `?? Departments/Design/docs/tad/EC-009_v01.md` 한 줄이 더해진 15줄. 거버넌스 파일 변경 줄 없음 |
| 행 번호 대조 | Grep `Secretariat\|RECORD_NAME\|WHITELIST\|요구 메모` (`check_standard.py`) | 2026-10-08 | 12·34·35·36·58·69·114·148·152행 일치 |
| 통제장치 존재 | Glob `{.claude/**,.githooks/**,setup.cmd}` | 2026-10-08 | `.claude/settings.json`, `.claude/agents/` 일곱 개, `.githooks/pre-commit`, `setup.cmd` |
| 배포 자리 확인 | Glob `Package_*/**` | 2026-10-08 | `Package_update/.gitkeep`, `Package_sample/.gitkeep` |

- 커밋 전 검사(`check_standard.py`)는 EC 판정 기준에 없어 실행하지 않았다.

## 5. 결함 목록과 반려 부서
| 번호 | 위치 | 결함 | 반려 부서 |
| :---: | :--- | :--- | :--- |
| D1 | `EC-009_v01` 3.5절 ②, 4절 위험 7 | REQ 체크리스트 9번 ②의 완료 기준은 최종 판정 시점의 거버넌스 파일 변경 줄·`index` 줄이 착수 시점 기준과 「같다」이다. EC 3.5절 ②는 차이가 있으면 「차이로 다룬다」고만 적어 그 경우 9번 ②를 충족하지 못한 것으로 보는지 정하지 않았다. 4절 위험 7은 「그 차이가 이 안건에서 생겼는지는 산출물 경로와 대조해 판단한다」고 적는데, 이 안건의 산출물은 `results/` 결과서뿐이므로 이 방법을 따르면 어떤 거버넌스 파일 차이도 이 안건과 무관하다고 판단되어 9번 ②가 사실상 무력화된다. 최종 판정자가 같은 차이를 두고 충족·불충족 어느 쪽으로도 판정할 수 있다(중의성, REQ 완료 기준 왜곡). 차이가 있을 때의 판정 결과를 REQ 9번 ②와 같은 뜻으로 확정해야 한다 | 설계 |
| D2 | `EC-009_v01` 3.3절 4번 「목록 작성 방법」 검색 범위 | 검색 범위를 「저장소 전체에서 `_archive/`, `Departments/`, `Audits/`, `CEO/`를 뺀 곳(거버넌스 파일 전체가 들어간다)」으로 정했으나, `Departments/`를 빼면 거버넌스 파일 `Departments/Development/assets/scripts/`(`AGENTS.md` 「불변 원칙」 3항)가 검색에서 빠진다. 괄호 안 설명은 사실과 다르다. 같은 폴더의 `check_standard.py` 36행 주석 「요구 메모」 같은 일치 위치가 명세 단계 검색 결과에 나오지 않아, 4절 위험 2의 대응(검색으로 일치 위치마다 반영 여부를 적는다)이 이 폴더에서 성립하지 않는다. 검색 범위에 이 폴더를 넣거나 괄호 안 설명을 실제 범위에 맞게 고쳐야 한다 | 설계 |

- 위 두 건 밖의 판정 기준 항목에서는 결함을 찾지 못했다. 재판정은 변경분만 판정한다(`Workflow/03_라이프사이클` 8절).
