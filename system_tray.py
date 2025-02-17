import win32gui
import win32con
import os
import sys
import winreg

class SystemTray:
    def __init__(self, controller):
        self.controller = controller
        self.setup_tray_icon()

    def setup_tray_icon(self):
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "VolumeControlTray"
        wc.lpfnWndProc = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            win32con.WM_USER + 20: self.on_tray_notification,
        }
        
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(classAtom, "VolumeControl", style,
            0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0, hinst, None)
        
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(application_path, "volume_control.ico")
        
        if os.path.exists(icon_path):
            try:
                icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                hicon = win32gui.LoadImage(hinst, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
                
                flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
                nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "볼륨 컨트롤")
                win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
                self.hicon = hicon
            except Exception as e:
                print(f"아이콘 로드 실패: {e}")

    def on_destroy(self, hwnd, msg, wparam, lparam):
        try:
            if hasattr(self, 'hwnd'):
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self.hwnd, 0))
        except:
            pass
        win32gui.PostQuitMessage(0)
        return True

    def on_command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        if id == 1023:
            self.controller.quit_app()
        elif id == 1024:
            self.controller.toggle_startup()
        elif id == 1025:
            self.controller.screen_blocker.toggle_prevent_sleep()
            # 메뉴 상태를 즉시 반영하기 위해 메뉴 다시 그리기
            win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, 0)
        return True

    def on_tray_notification(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            
            # 자동실행 메뉴
            is_startup = self.controller.check_startup()
            win32gui.AppendMenu(menu, win32con.MF_STRING | 
                (win32con.MF_CHECKED if is_startup else 0), 1024, "자동실행")
            
            # 화면 보호기 차단 메뉴
            win32gui.AppendMenu(menu, win32con.MF_STRING | 
                (win32con.MF_CHECKED if self.controller.screen_blocker.prevent_sleep else 0), 
                1025, "화면 보호기 차단")
            
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "종료")
            
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        
        return True 