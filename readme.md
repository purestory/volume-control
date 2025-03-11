# Volume Control

작업 표시줄에서 마우스 휠로 볼륨을 조절할 수 있는 Windows 프로그램입니다.

## 주요 기능

- 작업 표시줄에서 마우스 휠로 볼륨 조절 (4% 단위)
- 볼륨 조절 시 현재 볼륨 레벨 표시
- 시스템 트레이 아이콘으로 실행
- 전체 화면 프로그램 실행 중에는 비활성화
- 2초 후 자동으로 볼륨 표시 숨김

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/purestory/volume-control.git
cd volume-control
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
venv\Scripts\activate
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

### 소스 코드로 실행
```bash
python volume_control.py
```

### 실행 파일 생성
```bash
pip install pyinstaller
pyinstaller --noconfirm --noconsole --onefile volume_control.py
```
생성된 `dist/volume_control.exe` 파일을 실행하면 됩니다.

## 시작 프로그램 등록

1. 프로그램 실행
2. 시스템 트레이 아이콘 우클릭
3. "시작 프로그램 등록" 선택

## 라이선스

MIT License

## 제작자

purestory (https://github.com/purestory)