# 01. 바이브 코딩 표준 v02 개요 (Overview)

> 본 문서는 표준 v02의 목적, 구성, 고객 작업 공간 격리 원칙, 배포본 복제 규칙을 정의한다. 규정의 원천은 `AGENTS.md`이며 본 문서는 해설과 절차만 둔다.

## 1. 표준의 정의

표준 v02는 여러 AI 에이전트가 한 저장소에서 소프트웨어를 함께 만들 때 생기는 무단 수정, 범위 이탈, 자가 판정을 막는 작업 표준이다. 세 가지 수단으로 구성한다.

1. **문서 체계**: 모든 작업은 승인된 안건(REQ)에서 시작해 품질 판정서(RES)로 끝난다. 긴급 결함은 핫픽스 기록(HOTFIX)으로 처리한다.
2. **폴더 체계**: 부서별 작업 공간을 나누고 모든 부서가 같은 1차 하위폴더 4개를 쓴다.
3. **기계적 통제**: Claude Code 권한 설정(`.claude/settings.json`)과 커밋 전 검사(`.githooks/pre-commit` → `check_standard.py`)로 규칙 위반을 차단한다.

대표님은 REQ를 승인할 때와 최종 결과를 확인할 때 두 번만 개입한다. 그 사이 단계는 원스톱 파이프라인이 무인으로 진행한다(`Workflow/03_라이프사이클_및_워크플로우` 「원스톱 파이프라인」).

## 2. 고객 작업 공간 격리 원칙

표준 v02는 고객이 배포본을 복제해 자기 프로젝트를 시작하는 상품이다. 저장소를 두 구역으로 나눈다.

| 구역 | 경로 | 내용 | 배포본 상태 |
| :--- | :--- | :--- | :--- |
| 표준 매뉴얼 구역 | `Workflow/`, `AGENTS.md`, `CLAUDE.md`, `.claude/`, `.githooks/`, `setup.cmd` | 표준 자체의 규정과 매뉴얼 | 그대로 포함하며 고객은 열람만 한다 |
| 고객 작업 구역 | `Departments/` | 고객 프로젝트의 안건, 명세, 코드, 판정서 | 서식 템플릿(`*_TEMPLATE.md`), 표준 검사 스크립트, 빈 폴더(`.gitkeep`)만 포함한다 |

- 표준 자체의 설계는 `Departments/Design/docs/prd/`·`tad/`에 기록하지 않는다. 두 폴더는 고객 제품의 PRD·TAD 전용이며, 배포본에는 `PRD_TEMPLATE.md`, `TAD_TEMPLATE.md`, `EC_TEMPLATE.md`만 둔다.
- 표준을 개발하며 생긴 기록 문서(REQ·EC·DEV·RES·HOTFIX)는 배포본에서 뺀다(「배포본 복제 규칙」).

## 3. 배포본 복제 규칙

배포본(`Vibe Standard_v02_sample`)은 Git 기본 기능인 `git archive`와 `.gitattributes`의 `export-ignore` 규칙으로 만든다. `robocopy /MIR`은 받는 쪽에 이미 있는 제외 대상 파일을 지우지 않고, 커밋하지 않은 파일과 `.gitignore` 대상까지 복사하므로 사용하지 않는다.

1. **제외 규칙**: 제외 패턴의 원천은 저장소 루트 `.gitattributes`다. 규칙은 `_archive/`, `Claude outputs/`, `Departments/` 아래 표준 기록 문서(REQ·EC·DEV·RES·HOTFIX와 구 명칭 개발 결과서), 부서 `workspace/`와 `Departments/Secretariat/assets/inbox/` 아래 파일을 빼고 각 폴더의 `.gitkeep`은 남긴다. 커밋하지 않은 파일은 `git archive`에 원래 포함되지 않는다.
   - 폴더 규칙은 `workspace/`가 아니라 `workspace/**` 형태로 쓴다. 폴더 형태로 쓰면 `.gitkeep`을 되살리는 규칙이 적용되지 않아 폴더가 배포본에서 사라진다.
   - `Claude?outputs/**`의 `?`는 경로의 공백 한 글자에 일치시키기 위한 표기다.
2. **묶음 생성**: Git Bash에서 저장소 루트(`D:\Vibe Coding\Vibe Standard_v02`)로 이동해 아래 명령을 실행한다. `<임시경로>`는 Git Bash 형식(예: `/d/tmp`)으로 적는다.
   ```bash
   git archive --format=tar -o "<임시경로>/vibe_v02_sample.tar" HEAD
   tar --force-local -tf "<임시경로>/vibe_v02_sample.tar"
   ```
   두 번째 명령으로 압축을 풀기 전에 목록이 읽히는지 확인한다. GNU tar는 `D:`처럼 드라이브 문자가 붙은 경로를 원격 호스트로 해석하므로 `--force-local`을 붙인다. zip 형식은 Git Bash의 GNU tar가 풀지 못하므로 쓰지 않는다.
3. **배포본 갱신**: 대표님 최종 승인과 커밋 뒤에 실행한다. `Vibe Standard_v02_sample` 내용을 비우는 작업은 삭제이므로 실행 시점에 대상 목록 승인을 받는다. 이어서 Git Bash에서 `D:\Vibe Coding`으로 이동해 아래 명령으로 푼다.
   ```bash
   tar --force-local -xf "<임시경로>/vibe_v02_sample.tar" -C "Vibe Standard_v02_sample"
   ```
4. **확인**: 목록에서 ① `_archive/`·`Claude outputs/` 아래 파일 0건 ② 표준 기록 문서 0건 ③ `workspace/`·`assets/inbox/` 아래는 `.gitkeep`만 존재 ④ `Departments/Design/docs/` 아래는 템플릿 3종과 `.gitkeep`만 존재하는지 확인한다.

## 4. 저장소 구조 (v03)

```text
[저장소 루트]
├── AGENTS.md            # 저장소 헌장 (모든 AI 세션 공통 규정)
├── CLAUDE.md            # Claude Code 진입 파일 (@AGENTS.md 한 줄)
├── setup.cmd            # 최초 1회: Git 초기화, 훅 경로 설정, 초기 커밋
├── .gitattributes       # 줄바꿈 규칙, 배포본 제외 규칙
├── .claude/             # settings.json(권한), agents/(부서 서브에이전트 7종)
├── .githooks/pre-commit # 커밋 전 check_standard.py 실행
├── Workflow/            # 표준 매뉴얼 7종 및 templates/
├── Audits/              # 외부 감사실 (비정기 감사 보고서 및 서식)
├── CEO/References/      # 대표님 전용 자료 (AI 읽기 전용)
└── Departments/         # Secretariat, Design, Development, Quality, Operations, Marketing, Visual
```

매뉴얼 목록과 규정·매뉴얼의 관계는 `AGENTS.md` 「표준 매뉴얼」을 따른다.

## 5. 표준 업데이트 및 프로젝트 동기화 절차 (방법 B) (v03)

표준 v02 프레임워크가 판올림되거나 거버넌스가 개선되었을 때, 기존 고객 프로젝트의 제품 소스코드나 문서를 전혀 손상시키지 않고 안전하게 최신 표준으로 갱신하는 절차다.

### 5.1 원클릭 마우스 복붙(Ctrl+C / Ctrl+V) 갱신 메커니즘
1. **패키지 위치**: 배포본 최상위에 제공되는 `Update_Package/` 폴더를 연다.
2. **전체 선택 및 복사**: `Update_Package/` 폴더 내부의 모든 항목을 선택(`Ctrl+A`)하고 복사(`Ctrl+C`)한다.
3. **고객 프로젝트 루트에 덮어쓰기**: 기존 개발 중인 고객 프로젝트의 루트 폴더로 이동하여 그대로 붙여넣기(`Ctrl+V`)하고 파일 덮어쓰기를 승인한다.

### 5.2 무손실 안전성 보장 원리
- `Update_Package/` 내부에는 거버넌스 파일(`Workflow/`, `AGENTS.md`, `CLAUDE.md`, `setup.cmd`, `.claude/`, `check_standard.py`, `Departments/Standard_Templates/`)만 거울 구조로 배치되어 있다.
- 고객의 실제 개발 구역(`assets/src/`, `assets/tests/`, `Design/docs/prd/`, `tad/`, `CEO/References/`)은 패키지에 **폴더 자체가 존재하지 않으므로**, 덮어쓰기를 실행해도 고객 자산이 100% 안전하게 보존된다.

---

## 📝 개정 이력

| REQ | 변경 요지 |
| :--- | :--- |
| REQ-002 | 최초 작성 |
| REQ-002 | 원스톱 개입 시점, 배포본 복제 규칙 신설, 매뉴얼 축소 |
| REQ-003 | 표준 업데이트 및 프로젝트 동기화 절차(방법 B 마우스 복붙 가이드) 신설 |
