# v02 기록 보관

바이브 코딩 표준 v02(`D:\Vibe Coding\Vibe Standard_v02`)의 기록과 v03 재편 직전의 표준 파일 사본이다. 읽기 전용이며 v03 규정의 근거로 사용하지 않는다. 현행 규정은 저장소 루트의 `AGENTS.md`와 `Workflow/`다.

- `Departments/`: v02 안건 기록(REQ-001~006, RP-002, EC, DEV, RES, HOTFIX)과 부서 작업 산출물
- `Audits/`, `Claude outputs/`: v02 외부 검토 보고서
- `Update_Package/`, `Departments/Development/assets/scripts/build_update_package.py`: v02 업데이트 패키지와 빌더(v03에서 보류)
- 그 밖의 파일: v02 `AGENTS.md`, `CLAUDE.md.v02`, `Workflow/`, `_claude.v02/`(v02 `.claude/`), `setup.cmd`, `.gitattributes`, `.gitignore`, `.githooks/` 사본

v02 기록의 파일명은 v03 형식과 다르다. v03 번호 규칙은 `Workflow/07_문서_서식_및_번호` 「번호와 버전」을 따른다.

v02 `CLAUDE.md`·`.claude/` 사본은 Claude Code가 자동으로 불러오지 않도록 `CLAUDE.md.v02`·`_claude.v02/`로 이름을 바꿔 보관했다(루트와 `Update_Package/`).
