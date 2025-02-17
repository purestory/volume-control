# Volume Control

마우스 휠로 간편하게 볼륨을 조절할 수 있는 Windows 프로그램입니다.

## 주요 기능

- 작업 표시줄에서 마우스 휠로 볼륨 조절
- 볼륨 조절 시 현재 볼륨을 프로그레스 바로 표시
- 2초 후 자동으로 사라지는 투명한 볼륨 표시
- 시스템 트레이에 상주하며 자동 실행 설정 가능
- 볼륨을 2%씩 조절
- 화면 보호기 및 절전 모드 차단 기능

## 설치 방법

### 직접 실행
1. Python 3.6 이상 설치
2. 필요한 패키지 설치: `pip install -r requirements.txt`
3. 프로그램 실행: `python volume_control.py`

### 가상환경 사용
1. `run.bat` 실행 (자동으로 가상환경 생성 및 패키지 설치)

## 사용 방법

1. 프로그램을 실행하면 시스템 트레이에 아이콘이 생성됩니다.
2. 작업 표시줄 위에서 마우스 휠을 위/아래로 돌려 볼륨을 조절합니다.
3. 볼륨 조절 시 화면에 현재 볼륨이 표시됩니다.
4. 시스템 트레이 아이콘 우클릭으로 다음 기능을 사용할 수 있습니다:
   - 자동실행: 윈도우 시작 시 자동 실행
   - 화면 보호기 차단: 화면 보호기 및 절전 모드 방지
   - 종료: 프로그램 종료

## 시스템 요구사항

- Windows 10 이상
- Python 3.6 이상
- requirements.txt에 명시된 패키지들

## 파일 구조

- `volume_control.py`: 메인 프로그램
- `volume_display.py`: 볼륨 표시 UI
- `system_tray.py`: 시스템 트레이 관리
- `screen_saver_blocker.py`: 화면 보호기 차단 기능
- `requirements.txt`: 필요한 패키지 목록
- `run.bat`: 가상환경 실행 스크립트
- `volume_control.ico`: 프로그램 아이콘

## 라이선스

MIT License

## 제작자

purestory (https://github.com/purestory)