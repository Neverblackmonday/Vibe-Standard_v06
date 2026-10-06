@echo off
chcp 65001 > nul
echo [바이브 코딩 표준 v02] 프로젝트 초기 설정을 시작합니다...

:: 1. Git 저장소 초기화
if not exist ".git" (
    git init
    echo - Git 저장소 초기화 완료.
)

:: 2. 한글 파일명 및 훅 경로 설정
git config core.quotepath false
git config core.hooksPath .githooks
echo - Git 환경 설정(core.quotepath, core.hooksPath) 완료.

:: 3. 초기 커밋 생성
git rev-parse --verify HEAD > nul 2>&1
if %errorlevel% neq 0 (
    git add .
    git commit -m "chore: 바이브 코딩 표준 v02 초기화"
    echo - 초기 커밋 완료.
) else (
    echo - 기존 커밋이 이미 존재합니다.
)

echo.
echo [성공] 프로젝트 환경 설정이 완료되었습니다.