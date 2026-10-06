@echo off
chcp 65001 > nul
echo [바이브 코딩 표준 v03] 프로젝트 초기 설정을 시작합니다.

:: 1. Git 저장소 초기화
if not exist ".git" (
    git init
    if errorlevel 1 goto :fail
    echo - Git 저장소를 초기화했습니다.
)

:: 2. 한글 파일명 및 훅 경로 설정
git config core.quotepath false
if errorlevel 1 goto :fail
git config core.hooksPath .githooks
if errorlevel 1 goto :fail
echo - Git 환경(core.quotepath, core.hooksPath)을 설정했습니다.

:: 3. 초기 커밋 생성 (훅 파일에 실행 권한을 기록한다)
git rev-parse --verify HEAD > nul 2>&1
if errorlevel 1 (
    git add .
    if errorlevel 1 goto :fail
    git update-index --chmod=+x .githooks/pre-commit
    if errorlevel 1 goto :fail
    git commit -m "chore: 바이브 코딩 표준 v03 초기화"
    if errorlevel 1 goto :fail
    echo - 초기 커밋을 생성했습니다.
) else (
    echo - 기존 커밋이 있어 초기 커밋을 생략했습니다.
)

echo.
echo [성공] 프로젝트 환경 설정을 마쳤습니다.
exit /b 0

:fail
echo.
echo [실패] 위 Git 명령이 실패해 설정을 중단했습니다. 오류 내용을 확인하십시오. 예: git config user.name, user.email 미설정
exit /b 1
