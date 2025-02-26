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
import ctypes
import threading
import time
from volume_display import VolumeDisplay
from system_tray import SystemTray
from screen_saver_blocker import ScreenSaverBlocker
import pythoncom  # COM 초기화를 위해 추가

def is_fullscreen_app_running():
    """전체화면 앱/게임 실행 여부 확인"""
    try:
        foreground_hwnd = win32gui.GetForegroundWindow()
        if foreground_hwnd:
            # 현재 활성 창의 크기 가져오기
            window_rect = win32gui.GetWindowRect(foreground_hwnd)
            # 현재 모니터의 크기 가져오기
            monitor_info = win32api.GetMonitorInfo(win32api.MonitorFromWindow(foreground_hwnd))
            monitor_rect = monitor_info['Monitor']
            
            # 창 크기가 모니터 크기와 같으면 전체화면으로 간주
            return (window_rect == monitor_rect and 
                    win32gui.GetWindowText(foreground_hwnd) != "Program Manager")
    except:
        pass
    return False

class VolumeController:
    def __init__(self):
        # COM 초기화 추가
        pythoncom.CoInitialize()
        
        self.root = tk.Tk()
        self.root.withdraw()
        
        # 볼륨 컨트롤 초기화 - 더 안정적인 방식으로
        self.init_volume_control()
        
        self.volume_display = VolumeDisplay(self.root)
        self.screen_blocker = ScreenSaverBlocker()
        self.system_tray = SystemTray(self)
        
        self.listener = mouse.Listener(on_scroll=self.on_scroll)
        self.listener.start()

        self.last_volume_update = 0
        self.volume_update_interval = 0.05  # 50ms

    def init_volume_control(self):
        try:
            devices = pycaw.AudioUtilities.GetSpeakers()
            interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
        except Exception as e:
            print(f"볼륨 초기화 오류: {e}")
            self.volume = None

    def check_startup(self):
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
        if self.check_startup():
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Run", 
                                   0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, "VolumeControl")
                winreg.CloseKey(key)
            except WindowsError:
                pass
        else:
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
            self.listener.stop()
            if self.screen_blocker.prevent_sleep:
                self.screen_blocker.toggle_prevent_sleep()
            self.root.quit()
            if hasattr(self.system_tray, 'hwnd'):
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.system_tray.hwnd, 0))
                except:
                    pass
                win32gui.DestroyWindow(self.system_tray.hwnd)
            # COM 해제
            pythoncom.CoUninitialize()
            os._exit(0)
        except Exception as e:
            print(f"종료 중 오류 발생: {e}")
            os._exit(1)

    def show_volume(self, volume_level):
        self.root.after(0, self.volume_display.show_volume, volume_level)

    def on_scroll(self, x, y, dx, dy):
        # 전체화면 앱/게임이 실행 중이면 볼륨 조절하지 않음
        if is_fullscreen_app_running():
            return
            
        current_time = time.time()
        if current_time - self.last_volume_update < self.volume_update_interval:
            return
        self.last_volume_update = current_time
        
        taskbar_hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if taskbar_hwnd:
            taskbar_rect = win32gui.GetWindowRect(taskbar_hwnd)
            
            if (x >= taskbar_rect[0] and x <= taskbar_rect[2] and 
                y >= taskbar_rect[1] and y <= taskbar_rect[3]):
                
                # 마우스 리스너 스레드에서 COM 초기화
                pythoncom.CoInitialize()
                
                try:
                    # 볼륨이 None인 경우 재초기화
                    if self.volume is None:
                        self.init_volume_control()
                        
                    # 볼륨 정보 가져오기
                    current_volume = self.volume.GetMasterVolumeLevelScalar()
                    
                    # 새 볼륨 계산
                    delta = 0.02  # 2%씩 조절
                    if dy > 0:  # 휠 위로
                        new_volume = min(1.0, current_volume + delta)
                    else:  # 휠 아래로
                        new_volume = max(0.0, current_volume - delta)
                    
                    # 볼륨 설정 - Windows API 직접 호출
                    self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                    
                    # UI 표시
                    self.show_volume(new_volume)
                except Exception as e:
                    print(f"볼륨 조절 오류: {e}")
                    # 오류 발생 시 재초기화
                    try:
                        self.init_volume_control()
                        if self.volume:
                            current_volume = self.volume.GetMasterVolumeLevelScalar()
                            self.show_volume(current_volume)
                    except:
                        pass
                finally:
                    # 항상 COM 해제
                    pythoncom.CoUninitialize()

if __name__ == "__main__":
    controller = VolumeController()
    controller.root.mainloop() 