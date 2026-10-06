# AGENTS.md 개정안 (REQ-002 3단계)

- 작성: Design 에이전트 (Claude Opus 5.5), 2026-10-06
- 대상: 저장소 루트 `AGENTS.md`
- 상태: 대표님 승인 대기. 승인 전에는 원본 `AGENTS.md`를 수정하지 않는다.
- 반영 방법: 승인 후 대표님이 B절의 개정 전문으로 `AGENTS.md`를 교체한다. 에이전트는 `.claude/settings.json`의 `deny`(`Edit(AGENTS.md)`, `Write(AGENTS.md)`)로 원본을 수정할 수 없다.

## A. 변경 요지

| 번호 | 위치 | 변경 내용 | 사유 |
| :---: | :--- | :--- | :--- |
| 1 | 머리말 아래 | 「0. 표준 매뉴얼 참조」 절 신설: `Workflow/` 7종 경로와, 규정 원천은 `AGENTS.md`라는 관계 명시 | REQ-002 목적 1, 3.2절 |
| 2 | 1절 표 설계·품질 행 | 설계에 `docs/tad/EC-xxx.md`·템플릿 3종, 품질에 `results/RES-xxx-EC.md` 추가 | EC 도입 |
| 3 | 1절 하단 | `Departments/Design/docs/prd/`·`tad/`는 고객 제품 전용이며 표준 자체 설계는 `Workflow/`에 둔다는 규칙 추가 | REQ-002 배경 |
| 4 | 2절 2항 | 거버넌스 파일 목록에 `Workflow/` 추가. 「scope에 기재할 수 없다」를 「개정안 작성 후 대표님 반영」 절차로 변경 | REQ-002가 `AGENTS.md`·`.claude/settings.json`·`check_standard.py`를 scope에 기재하여 현행 2절 2항과 충돌 |
| 5 | 2절 5항 | 품질 판정을 EC 사전 판정(1차 게이트)과 최종 삼중 판정(2차 게이트)으로 구분 | 5단계 라이프사이클 |
| 6 | 4절 1항 | 라이프사이클을 5단계 Closed-Loop로 교체 | REQ-002 3.2절, EC-002 3.2절 |
| 7 | 4절 2항 | 네이밍에 EC, EC 사전 판정서 추가 | EC 도입 |

변경하지 않는 절: 2절 1·3·4·6항, 3절, 4절 3항.

## B. 개정 전문

````markdown
# 바이브 코딩 에이전트 거버넌스 규정 (AGENTS.md)

> 본 문서는 모든 AI 세션과 서브에이전트가 준수해야 하는 저장소 단일 규정이며, 승인·커밋·보안의 절대 원칙은 사용자 전역 개발 지침을 따른다.

---

## 0. 표준 매뉴얼 참조

본 규정의 해설과 세부 절차는 `Workflow/` 매뉴얼을 참조한다. 규정의 원천은 본 문서이며, 매뉴얼과 본 문서가 어긋나면 본 문서를 따르고 대표님께 보고한다.

| 문서 | 내용 |
| :--- | :--- |
| `Workflow/01_vibe_standard_overview` | 표준 개요와 저장소 구조 |
| `Workflow/02_5대_도메인_구조_및_역할` | 부서별 책임, 폴더 규격, 작업 구역 권한 |
| `Workflow/03_라이프사이클_및_워크플로우` | 5단계 Closed-Loop 라이프사이클 |
| `Workflow/04_모델_운용_기준` | 단계별 권고 모델과 모델 메타데이터 |
| `Workflow/05_비서실_클로드cli_인수인계_정책` | 비서실 역할 한계와 실행 명령 규격 |
| `Workflow/06_거버넌스_엔지니어링_아키텍처` | 권한 설정, Git 훅, 표준 검사의 구조 |
| `Workflow/07_엔지니어링_변경통제_및_서식_명세` | REQ·EC·PRD·TAD·RES 서식 규격 |

---

## 1. 7대 부서 구조 및 역할 (통일 4대 1차 폴더 규격)

모든 부서는 예외 없이 1차 하위폴더로 `docs/`, `assets/`, `results/`, `workspace/` 4개만을 운영하며, 세부 기능은 2차 하위폴더로 관리한다.

| 도메인 | 폴더 | 주요 책임 및 2차 하위폴더 산출물 | 비고 |
| :--- | :--- | :--- | :--- |
| **대표실** | `CEO/` (`References/`) | 대표님이 직접 관리하는 전략 문서 및 참고 자료(`CEO/References/`) | 대표님 전용. AI는 읽기만 가능하며 파일 수정·삭제를 전면 금지한다. |
| **비서실** | `Departments/Secretariat/` | `docs/requests/`: REQ 안건 문서 (안건당 1개)<br>`assets/inbox/`: 대표님 요구사항 메모<br>`assets/research/`: 조사 원자료<br>`assets/briefings/`: 대표님 보고용 브리핑 문서 | 비서실 에이전트 중심 운영. 최종 산출물은 승인된 REQ와 Claude CLI 실행 명령이며, 코드나 명세를 직접 구현하지 않는다. |
| **설계** | `Departments/Design/` | `docs/tad/EC-xxx.md`: 엔지니어링 변경 계획서 (안건당 1개)<br>`docs/prd/`: 제품 요구사항 정의서<br>`docs/tad/`: 기술 아키텍처 명세서 (버전 없는 파일명)<br>`docs/prd/PRD_TEMPLATE.md`, `docs/tad/TAD_TEMPLATE.md`, `docs/tad/EC_TEMPLATE.md`: 표준 서식<br>`assets/live/`: 수시 갱신 비즈니스/설계 파라미터<br>`results/`: RES-설계 | 명세는 항상 구현보다 선행한다. |
| **개발** | `Departments/Development/` | `assets/src/`: 제품 소스코드<br>`assets/tests/`: 시험 코드<br>`assets/scripts/`: 표준 검사 스크립트<br>`docs/`: 개발 가이드 및 API 명세 | 승인된 REQ의 `scope:` 안에서만 코드를 작성한다. |
| **품질** | `Departments/Quality/` | `results/RES-001-EC.md`: EC 사전 판정서 (1차 게이트)<br>`results/RES-001.md`: 최종 독립 품질 판정서 (2차 게이트)<br>`docs/`: 품질 기준서 및 체크리스트<br>`assets/`: 검증용 픽스처 데이터 | 통과 기준 미달 시 `result: fail` 또는 반려 판정. |
| **운영** | `Departments/Operations/` | `assets/live/`: 런타임 수시 갱신 파라미터<br>`assets/logs/`: 운영 기록<br>`assets/releases/`: 배포 패키지 번들<br>`docs/`: 운영 매뉴얼 및 절차서 | 실제 배포 및 런타임 설정 운영. |
| **마케팅** | `Departments/Marketing/` | `assets/banners/`, `assets/media/`: 마케팅 미디어 자산<br>`docs/`: 마케팅 전략 및 기획서<br>`results/`: 성과 보고서 | 마케팅 및 대외 콘텐츠 담당. |
| **비주얼** | `Departments/Visual/` | `assets/icons/`, `assets/fonts/`, `assets/images/`: 디자인 에셋<br>`docs/`: 디자인 시스템 및 가이드라인<br>`results/`: 디자인 결과서 | UI/UX 및 그래픽 리소스 담당. |

* **통일 1차 폴더 규칙**:
  - `docs/`: 기획, 명세, 문서, 가이드라인 (정제된 텍스트 문서)
  - `assets/`: 부서별 실제 자산 (코드, 테스트, 이미지, 파라미터, 조사자료, 배포본 등)
  - `results/`: 공식 결과서 및 판정서
  - `workspace/`: 임시 작업 산출물 및 스크래치 공간
* **표준 매뉴얼과 고객 작업 공간의 분리**:
  - `Departments/Design/docs/prd/`와 `Departments/Design/docs/tad/`에는 이 저장소로 개발하는 제품의 명세만 작성한다.
  - 바이브 코딩 표준 자체의 설계와 매뉴얼은 `Workflow/`에만 둔다.

---

## 2. 핵심 엔지니어링 원칙

1. **선구현 엄격 금지 (Fail-Closed) 및 승인 기록 의무**:
   - 사용자의 명시적 승인 없이는 코드 파일(`Development/assets/src/`) 및 명세 파일(`Design/docs/`) 수정을 엄격히 금지한다.
   - 대표님의 승인은 REQ 머리말 `approved: "YYYY-MM-DD"` 필드 기재로 확정한다. `approved:` 필드가 누락되었거나 비어 있는 REQ는 미승인 안건으로 분류되며 모든 후속 작업 및 커밋이 차단된다.
   - 승인 전 허용 구역: `Secretariat/assets/inbox/`, `Secretariat/docs/requests/`(REQ 초안 작성), 각 부서 `workspace/`.
2. **범위 통제 (Scope Quarantine) 및 거버넌스 불변 구역**:
   - 승인된 REQ 머리말 `scope:`에 명시된 파일 이외의 수정을 금지한다.
   - 거버넌스 파일(`AGENTS.md`, `CLAUDE.md`, `setup.cmd`, `.claude/`, `.githooks/`, `Departments/Development/assets/scripts/`, `Workflow/`) 및 `CEO/References/`는 에이전트가 직접 수정하지 않는다 (대표님 단독 수정 구역).
   - 거버넌스 파일 개정이 필요하면 REQ `scope:`에 해당 파일을 기재할 수 있다. 이 경우 설계팀이 자기 부서 `workspace/`에 개정안을 작성하고, 품질팀 판정과 대표님 승인을 거쳐 대표님이 원본에 반영한다. `CEO/References/`는 REQ `scope:`에 기재할 수 없다.
   - 각 단계 서브에이전트는 scope 가운데 자기 단계 경로와 자기 부서 `results/`·`workspace/`만 수정한다.
   - 품질 서브에이전트는 `git status --porcelain`을 확인하여 scope 밖의 파일이 수정되거나 새로 생성된 경우 즉시 반려(`fail`)한다.
3. **단순성 우선 (KISS & YAGNI)**:
   - 요구하지 않은 기능 추가(Feature Creep), 미사용 추상화/인터페이스 생성, 실측 없는 조기 최적화를 금지한다.
4. **추측 금지 (Zero Assumption)**:
   - 요구사항이나 명세가 모호할 경우 임의로 구현하지 않고 명확히 역질문하거나, 반려 사유를 명시해 반려한다.
5. **생성과 판정의 분리**:
   - 본문을 작성한 세션(설계·개발·운영)은 스스로 판정하지 않으며, 독립된 품질 단계 서브에이전트가 검증과 판정을 수행한다.
   - 품질 판정은 EC 사전 판정(1차 게이트, `RES-xxx-EC.md`)과 최종 삼중 판정(2차 게이트, `RES-xxx.md`)으로 구분한다. 품질팀은 판정서만 작성하며, EC의 `status:` 변경은 사전 판정서의 `result: pass`를 근거로 설계팀이 수행한다.
6. **표준 개정 및 규칙 비대화 방지 3원칙**:
   - **새 규칙 조건**: 사고 근본 원인이 입증되고 플랫폼 기본 기능으로 막을 수 없는 경우에만 새 규칙을 추가한다.
   - **기존 규칙 유지 기준**: 사고 이력이 없거나 기본 기능으로 대체 가능한 규칙은 폐지하거나 권고로 완화한다.
   - **한 목적 원칙**: 하나의 REQ에는 반드시 단일 목적만 담아 범위를 집중한다.

---

## 3. 버전 관리 및 명세 문서 규칙

1. **명세 문서 (`docs/`)**:
   - 버전 번호 없는 파일명 하나로 유지한다 (예: `Design/docs/tad/01_아키텍처.md`).
   - 개정 이력은 Git 커밋 로그와 문서 최하단 「📝 개정 이력」 표(REQ 번호 및 변경 요지)로 관리한다.
2. **코드 버전 단일화**:
   - 개별 소스코드 파일마다 버전을 적는 행위를 금지하며, 패키지 설정 파일과 Git 태그로 단일화한다.
3. **문서 참조**:
   - 문서 간 상호 참조는 확장자 없는 상대 경로로 작성한다 (예: `Design/docs/tad/01_아키텍처`).

---

## 4. 라이프사이클 및 커밋 규칙

1. **5단계 Closed-Loop 라이프사이클**:
   `선행(접수 → REQ 작성 → 대표님 승인) → 1단계 EC 작성(설계) → 2단계 EC 사전 판정(품질, 1차 게이트) → 3단계 PRD·TAD 작성(설계, 대표님 검토) → 4단계 구현(개발) → 5단계 최종 삼중 판정(품질, 2차 게이트) → 후속(완료 보고 → 대표님 요청 시 커밋)`
   - 1단계와 2단계는 생략하지 않는다. 2단계 판정이 `fail`이면 1단계로 돌아간다.
   - 5단계 품질팀은 REQ 원문 대조, EC 범위 대조, PRD·TAD 정합성 대조를 모두 수행한다.
   - REQ 머리말 `workflow:`에 명시된 부서(예: Design, Development, Operations, Marketing, Visual, Quality)만 순서대로 기동된다. 단계별 세부 절차는 `Workflow/03_라이프사이클_및_워크플로우`를 따른다.
   - 비서실(Antigravity)은 대표님 승인 직후 REQ 6절의 단계별 Claude CLI 실행 명령을 대표님께 안내하고 업무를 인계한다. 명령 작성 규격은 `Workflow/05_비서실_클로드cli_인수인계_정책`을 따른다.
   - 실제 설계·개발·운영 작업은 Claude Code CLI가 REQ를 읽어 수행하며, 비서실이 코드를 직접 구현하는 행위를 엄격히 금지한다.
2. **네이밍 및 커밋 메시지 규격**:
   - 안건 문서: `Departments/Secretariat/docs/requests/REQ-001.md` (3자리 순번)
   - 엔지니어링 변경 계획서: `Departments/Design/docs/tad/EC-001.md` (REQ와 같은 번호)
   - EC 사전 판정서: `Departments/Quality/results/RES-001-EC.md`
   - 품질 판정서: `Departments/Quality/results/RES-001.md`
   - 커밋 메시지: `feat: [REQ-001] 요약`
   - 예외: `setup.cmd`가 프로젝트 초기화 시 생성하는 첫 커밋(`chore: 바이브 코딩 표준 v02 초기화`) 1건은 REQ 번호 기재 및 REQ 검사에서 면제된다.
3. **커밋 주체 및 승인**:
   - 모든 단계 검사와 품질 판정이 통과(`result: pass`)한 후 대표님께 완료를 보고하고, 명시적 요청 또는 확인 승인을 받아 커밋을 수행한다.
````
