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
        
        # 현재 오디오 장치 ID 저장 변수
        self.current_device_id = None
        
        # 볼륨 컨트롤 초기화
        self.init_volume_control()
        
        self.volume_display = VolumeDisplay(self.root)
        self.screen_blocker = ScreenSaverBlocker()
        self.system_tray = SystemTray(self)
        
        # 장치 변경 감지 스레드 제거
        
        self.listener = mouse.Listener(on_scroll=self.on_scroll)
        self.listener.start()

        self.last_volume_update = 0
        self.volume_update_interval = 0.05  # 50ms
        
        # 마지막 장치 검사 시간
        self.last_device_check = 0
        self.device_check_interval = 2.0  # 2초마다만 장치 변경 검사

    def init_volume_control(self):
        try:
            # 간단한 방식으로 볼륨 컨트롤 초기화
            devices = pycaw.AudioUtilities.GetSpeakers()
            interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            new_volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
            
            # 볼륨 객체가 변경되었는지 확인 (재초기화 필요 여부)
            is_new_init = (self.volume is None)  # 처음 초기화인 경우
            need_reinit = False  # 재초기화 필요 여부
            
            if not is_new_init:
                # 기존 볼륨 객체가 있으면, 현재 볼륨과 비교하여 변경 감지
                try:
                    old_vol = self.volume.GetMasterVolumeLevelScalar()
                    new_vol = new_volume.GetMasterVolumeLevelScalar()
                    # 볼륨 값이 크게 다르면 장치가 변경되었을 가능성이 높음
                    need_reinit = abs(old_vol - new_vol) > 0.1
                except:
                    # 오류 발생 시 재초기화 필요
                    need_reinit = True
            
            # 볼륨 컨트롤 객체 업데이트
            self.volume = new_volume
            
            # 적절한 메시지 출력
            if is_new_init:
                print("볼륨 컨트롤 초기화 성공")
            elif need_reinit:
                print("오디오 장치 변경 감지 - 볼륨 컨트롤 재초기화 성공")
            
            return True
        except Exception as e:
            print(f"볼륨 초기화 오류: {e}")
            
            # 실패 시 다른 방식으로 재시도
            try:
                # 기본 방식으로 다시 시도
                devices = pycaw.AudioUtilities.GetSpeakers()
                interface = devices.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self.volume = interface.QueryInterface(pycaw.IAudioEndpointVolume)
                print("기본 방식으로 볼륨 컨트롤 초기화 성공")
                return True
            except Exception as e2:
                print(f"두 번째 볼륨 초기화 시도 실패: {e2}")
                self.volume = None
                return False

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
            # 불필요한 스레드 종료 코드 제거
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
        
        # 일정 시간마다만 장치 변경 확인 (너무 자주하면 성능 저하)
        check_device = (current_time - self.last_device_check > self.device_check_interval)
        if check_device:
            self.last_device_check = current_time
        
        taskbar_hwnd = win32gui.FindWindow("Shell_TrayWnd", None)
        if taskbar_hwnd:
            taskbar_rect = win32gui.GetWindowRect(taskbar_hwnd)
            
            if (x >= taskbar_rect[0] and x <= taskbar_rect[2] and 
                y >= taskbar_rect[1] and y <= taskbar_rect[3]):
                
                # 마우스 리스너 스레드에서 COM 초기화
                pythoncom.CoInitialize()
                
                try:
                    # 일정 시간마다 또는 볼륨이 None인 경우 장치 변경 확인
                    if check_device or self.volume is None:
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
                    # 오류 발생 시 즉시 재초기화 시도
                    try:
                        if self.init_volume_control() and self.volume:
                            # 재초기화 성공 시 바로 볼륨 조절 재시도
                            current_volume = self.volume.GetMasterVolumeLevelScalar()
                            delta = 0.02
                            new_volume = min(1.0, current_volume + delta) if dy > 0 else max(0.0, current_volume - delta)
                            self.volume.SetMasterVolumeLevelScalar(new_volume, None)
                            self.show_volume(new_volume)
                    except:
                        pass
                finally:
                    # 항상 COM 해제
                    pythoncom.CoUninitialize()

    def get_default_device(self):
        try:
            # 현재 사용 중인 기본 오디오 장치 가져오기
            enumerator = pycaw.AudioUtilities.GetDeviceEnumerator()
            default_device = enumerator.GetDefaultAudioEndpoint(0, 1)  # eRender, eConsole
            
            # 장치 ID 저장
            self.default_device_id = default_device.GetId()
            
            # 오디오 엔드포인트 가져오기
            interface = default_device.Activate(pycaw.IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            return interface.QueryInterface(pycaw.IAudioEndpointVolume)
        except Exception as e:
            print(f"기본 오디오 장치 가져오기 실패: {e}")
            return None

if __name__ == "__main__":
    controller = VolumeController()
    controller.root.mainloop() 