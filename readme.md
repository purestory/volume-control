# Volume Control

마우스 휠로 간편하게 볼륨을 조절할 수 있는 Windows 프로그램입니다.

## 주요 기능

- 작업 표시줄에서 마우스 휠로 볼륨 조절
- 볼륨 조절 시 현재 볼륨을 프로그레스 바로 표시
- 2초 후 자동으로 사라지는 투명한 볼륨 표시
- 시스템 트레이에 상주하며 자동 실행 설정 가능
- 볼륨을 2%씩 조절

## 설치 방법

1. 필요한 패키지 설치:

pip install pynput pycaw pywin32 pillow pystray

2. 프로그램 실행:

python volume_control.py


## 사용 방법

1. 프로그램을 실행하면 시스템 트레이에 아이콘이 생성됩니다.
2. 작업 표시줄 위에서 마우스 휠을 위/아래로 돌려 볼륨을 조절합니다.
3. 볼륨 조절 시 화면에 현재 볼륨이 표시됩니다.
4. 시스템 트레이 아이콘 우클릭으로 자동 실행 설정 및 프로그램 종료가 가능합니다.

## 시스템 요구사항

- Windows 10 이상
- Python 3.6 이상

## 라이선스

MIT License

## 제작자

purestory (https://github.com/purestory)