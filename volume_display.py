import tkinter as tk

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
        x = (screen_width - self.width) - 20
        y = screen_height - 110  # 화면 하단에서 약간 위
        self.window.geometry(f'{self.width}x{self.height}+{x}+{y}')
        
        # 볼륨 바 생성
        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height,
                              bg='#2b2b2b', highlightthickness=0)
        self.canvas.pack()
        
        self.hide_timer = None

    def show_volume(self, volume_level):
        volume_percent = int(volume_level * 100)
        self.canvas.delete('all')
        
        bar_width = int((self.width - 40) * volume_level)
        self.canvas.create_rectangle(20, 20, self.width-20, 30,
                                   fill='#404040', outline='')
        self.canvas.create_rectangle(20, 20, 20 + bar_width, 30,
                                   fill='#ffffff', outline='')
        
        self.canvas.create_text(self.width//2, 40, 
                              text=f'볼륨: {volume_percent}%',
                              fill='white', font=('Arial', 10))
        
        self.window.deiconify()
        
        if self.hide_timer is not None:
            self.window.after_cancel(self.hide_timer)
        
        self.hide_timer = self.window.after(1500, self.hide)
        self.window.update()

    def hide(self):
        self.window.withdraw() 