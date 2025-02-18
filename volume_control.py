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
        self.root = tk.Tk()
        self.root.withdraw()  # 메인 윈도우 숨기기
        
        devices = pycaw.AudioUtilities.GetSpeakers()
        interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
        
        self.volume_display = VolumeDisplay(self.root)
        self.screen_blocker = ScreenSaverBlocker()
        self.system_tray = SystemTray(self)
        
        self.listener = mouse.Listener(on_scroll=self.on_scroll)
        self.listener.start()

        self.last_volume_update = 0
        self.volume_update_interval = 0.05  # 50ms

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
                
                try:
                    current_volume = self.volume.GetMasterVolumeLevelScalar()
                    new_volume = min(1.0, current_volume + 0.02) if dy > 0 else max(0.0, current_volume - 0.02)
                    self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                    self.show_volume(new_volume)
                except Exception as e:
                    print(f"볼륨 조절 오류: {e}")
                    try:
                        devices = pycaw.AudioUtilities.GetSpeakers()
                        interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                        self.volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
                    except Exception:
                        pass

if __name__ == "__main__":
    controller = VolumeController()
    controller.root.mainloop() 