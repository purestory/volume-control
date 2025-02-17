@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo [빌드 환경을 준비합니다...]

if not exist "venv" (
    echo [가상환경을 생성합니다...]
    python -m venv venv
    call venv\Scripts\activate
    echo [필요한 패키지를 설치합니다...]
    pip install -r requirements.txt
    pip install pyinstaller
) else (
    call venv\Scripts\activate
)

echo [실행 파일을 생성합니다...]
pyinstaller --clean volume_control.spec

echo [빌드가 완료되었습니다.]
echo [실행 파일은 dist\VolumeControl 폴더에 있습니다.]
pause 