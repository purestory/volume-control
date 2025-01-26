import win32gui
import win32con
import win32api
import pycaw.pycaw as pycaw
from comtypes import CLSCTX_ALL
from pynput import mouse
import winreg
import os
import sys
import tkinter as tk
from PIL import Image, ImageTk
import math
import pystray

class VolumeDisplay:
    def __init__(self):
        self.window = tk.Tk()
        self.window.withdraw()  # 초기에는 숨김
        
        # 창 설정
        self.window.overrideredirect(True)  # 타이틀바 제거
        self.window.attributes('-topmost', True)  # 항상 위에 표시
        self.window.attributes('-alpha', 0.9)  # 약간 투명하게
        
        # 창 크기와 위치
        self.width = 300
        self.height = 50
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = screen_height - 150  # 화면 하단에서 약간 위
        self.window.geometry(f'{self.width}x{self.height}+{x}+{y}')
        
        # 볼륨 바 생성
        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height,
                              bg='#2b2b2b', highlightthickness=0)
        self.canvas.pack()
        
        self.hide_timer = None

    def show_volume(self, volume_level):
        # 볼륨 레벨을 0-100 사이로 변환
        volume_percent = int(volume_level * 100)
        
        # 캔버스 초기화 
        self.canvas.delete('all')
        
        # 볼륨 바 그리기
        bar_width = int((self.width - 40) * volume_level)
        self.canvas.create_rectangle(20, 20, self.width-20, 30,
                                   fill='#404040', outline='')
        self.canvas.create_rectangle(20, 20, 20 + bar_width, 30,
                                   fill='#ffffff', outline='')
        
        # 볼륨 텍스트 표시
        self.canvas.create_text(self.width//2, 40, 
                              text=f'볼륨: {volume_percent}%',
                              fill='white', font=('Arial', 10))
        
        # 창 표시
        self.window.deiconify()
        
        # 이전 타이머 취소
        if self.hide_timer is not None:
            self.window.after_cancel(self.hide_timer)
        
        # 1.5초 후 창 숨기기
        self.hide_timer = self.window.after(1500, self.hide)
        
        # 창 업데이트
        self.window.update()

    def hide(self):
        self.window.withdraw()

class VolumeController:
    def __init__(self):
        # 오디오 세션 매니저 초기화
        devices = pycaw.AudioUtilities.GetSpeakers()
        interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
        
        # 볼륨 표시기 추가
        self.volume_display = VolumeDisplay()
        
        # 시스템 트레이 아이콘 설정
        self.setup_tray_icon()
        
        # 마우스 리스너 설정
        self.listener = mouse.Listener(on_scroll=self.on_scroll)
        self.listener.start()

    def setup_tray_icon(self):
        # 윈도우 메시지 처리를 위한 윈도우 클래스 등록
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "VolumeControlTray"
        wc.lpfnWndProc = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            win32con.WM_USER + 20: self.on_tray_notification,
        }
        
        # 윈도우 클래스 등록
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom, "VolumeControl", style,
            0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0, hinst, None)
        
        # 아이콘 파일의 절대 경로 얻기
        if getattr(sys, 'frozen', False):
            # PyInstaller로 생성된 실행 파일일 경우
            application_path = sys._MEIPASS
        else:
            # 일반 Python 스크립트일 경우
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, "volume_control.ico")
        
        if os.path.exists(icon_path):
            try:
                # 아이콘 로드
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                hicon = win32gui.LoadImage(hinst, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
                
                # 트레이 아이콘 생성
                flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
                nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "볼륨 컨트롤")
                win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
                self.hicon = hicon  # 아이콘 핸들 저장
            except Exception as e:
                print(f"아이콘 로드 실패: {e}")
                print(f"아이콘 경로: {icon_path}")

    def on_destroy(self, hwnd, msg, wparam, lparam):
        try:
            # 트레이 아이콘이 아직 존재하는 경우에만 제거 시도
            if hasattr(self, 'hwnd'):
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
        except:
            pass  # 에러 무시
        win32gui.PostQuitMessage(0)
        return True

    def on_command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        if id == 1023:  # 종료 메뉴 선택 시
            self.quit_app()
        elif id == 1024:  # 자동 실행 메뉴 선택 시
            self.toggle_startup()
        return True

    def on_tray_notification(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            
            # 자동 실행 상태 확인
            is_startup = self.check_startup()
            
            # 메뉴 아이템 추가 (체크 표시 포함)
            win32gui.AppendMenu(menu, win32con.MF_STRING | (win32con.MF_CHECKED if is_startup else 0), 1024, "자동실행")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")  # 구분선 추가
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "종료")
            
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        
        return True

    def check_startup(self):
        """시작 프로그램 등록 여부 확인"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "VolumeControl")
            winreg.CloseKey(key)
            return True
        except WindowsError:
            return False

    def toggle_startup(self):
        """시작 프로그램 등록/해제 토글"""
        if self.check_startup():
            # 자동 실행 해제
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                   0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, "VolumeControl")
                winreg.CloseKey(key)
            except WindowsError:
                pass
        else:
            # 자동 실행 등록
            exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                   0, winreg.KEY_ALL_ACCESS)
                winreg.SetValueEx(key, "VolumeControl", 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
            except WindowsError:
                pass

    def quit_app(self):
        try:
            # 마우스 리스너 중지
            self.listener.stop()
            # tkinter 윈도우 종료
            self.volume_display.window.destroy()
            # 트레이 아이콘이 존재하는 경우에만 제거 시도
            if hasattr(self, 'hwnd'):
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
                except:
                    pass
                win32gui.DestroyWindow(self.hwnd)
            # 프로그램 종료
            os._exit(0)
        except Exception as e:
            print(f"종료 중 오류 발생: {e}")
            os._exit(1)

    def on_scroll(self, x, y, dx, dy):
        # 작업 표시줄 핸들 찾기
        taskbar_hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if taskbar_hwnd:
            # 작업 표시줄의 위치와 크기 가져오기
            taskbar_rect = win32gui.GetWindowRect(taskbar_hwnd)
            
            # 마우스가 작업 표시줄 영역 안에 있는지 확인
            if (x >= taskbar_rect[0] and x <= taskbar_rect[2] and 
                y >= taskbar_rect[1] and y <= taskbar_rect[3]):
                
                # 현재 볼륨 가져오기
                current_volume = self.volume.GetMasterVolumeLevelScalar()
                
                # 볼륨 조절
                if dy > 0:
                    new_volume = min(1.0, current_volume + 0.02)
                else:
                    new_volume = max(0.0, current_volume - 0.02)
                    
                # 새로운 볼륨 설정
                self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                
                # 볼륨 표시
                self.volume_display.show_volume(new_volume)

def add_to_startup():
    # 현재 실행 파일의 경로
    exe_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    
    # 레지스트리 키 설정
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    try:
        # 레지스트리 키 열기
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                            winreg.KEY_ALL_ACCESS)
        
        # 프로그램 등록
        winreg.SetValueEx(key, "VolumeControl", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False

def show_volume_window():
    # 화면 크기 가져오기
    screen_width = GetSystemMetrics(0)
    screen_height = GetSystemMetrics(1)
    
    # 창 크기 설정
    window_width = 200
    window_height = 50
    
    # 오른쪽 끝에서 약간 안쪽으로
    x_position = screen_width - window_width - 20  # 20픽셀 여백
    y_position = screen_height - 150  # 화면 하단에서 약간 위로
    
    # 창 위치 및 크기 설정
    root.geometry(f'{window_width}x{window_height}+{x_position}+{y_position}')
    
    # 창 보이기
    root.deiconify()
    root.lift()
    root.focus_force()

def create_menu(icon):
    # 메뉴 생성
    menu = (
        item('볼륨조절', show_volume_window),  # 새로운 메뉴 항목 추가
        item('종료', lambda: icon.stop()),
    )
    return menu

def main():
    image = Image.open("volume_control.ico")
    icon = pystray.Icon(
        "volume_control",
        image,
        "Volume Control",
        create_menu(icon)  # 메뉴 설정
    )
    
    icon.run()

if __name__ == "__main__":
    # 시작 프로그램에 등록
    add_to_startup()
    
    # 볼륨 컨트롤러 실행
    controller = VolumeController()
    
    try:
        # tkinter 메인 루프 실행
        tk.mainloop()
    except KeyboardInterrupt:
        controller.quit_app() 