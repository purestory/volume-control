@echo off
if not exist "venv" (
    echo 가상환경을 생성합니다...
    python -m venv venv
    call venv\Scripts\activate
    echo 필요한 패키지를 설치합니다...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate
)

echo 프로그램을 실행합니다...
python volume_control.py
pause 