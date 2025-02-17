import threading
import ctypes
import time
import winreg

class ScreenSaverBlocker:
    def __init__(self):
        self.prevent_sleep = self.load_state()
        self.prevent_sleep_thread = None
        if self.prevent_sleep:
            self.start_blocking()

    def load_state(self):
        """레지스트리에서 화면 보호기 차단 상태 로드"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                r"Software\VolumeControl", 
                                0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "PreventSleep")
            winreg.CloseKey(key)
            return bool(value)
        except WindowsError:
            return False

    def save_state(self):
        """레지스트리에 화면 보호기 차단 상태 저장"""
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\VolumeControl")
            winreg.SetValueEx(key, "PreventSleep", 0, 
                            winreg.REG_DWORD, int(self.prevent_sleep))
            winreg.CloseKey(key)
        except WindowsError as e:
            print(f"상태 저장 실패: {e}")

    def start_blocking(self):
        """화면 보호기 차단 시작"""
        if not self.prevent_sleep_thread:
            self.prevent_sleep_thread = threading.Thread(target=self.keep_system_active, daemon=True)
            self.prevent_sleep_thread.start()

    def toggle_prevent_sleep(self):
        self.prevent_sleep = not self.prevent_sleep
        if self.prevent_sleep:
            self.start_blocking()
        else:
            if self.prevent_sleep_thread:
                self.prevent_sleep_thread.join(timeout=1)
                self.prevent_sleep_thread = None
        
        # 상태 변경 후 저장
        self.save_state()
        
    def keep_system_active(self):
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        
        while self.prevent_sleep:
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
            time.sleep(30)
            
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS) 