import tkinter as tk
import ctypes
import random
import customtkinter as ctk
from start import init


def hide_from_taskbar(window):
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
    style |= 0x00000080  # WS_EX_TOOLWINDOW
    ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)


def get_work_area():
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long),
                    ("top", ctypes.c_long),
                    ("right", ctypes.c_long),
                    ("bottom", ctypes.c_long)]

    rect = RECT()
    SPI_GETWORKAREA = 0x0030
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    return width, height, rect.left, rect.top


def show_splash(callback_when_done, load_time=5):
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)

    splash_width = 400
    splash_height = 260  # немного увеличил высоту

    splash.update_idletasks()

    work_width, work_height, work_left, work_top = get_work_area()
    x = work_left + (work_width // 2) - (splash_width // 2)
    y = work_top + (work_height // 2) - (splash_height // 2)

    splash.geometry(f"{splash_width}x{splash_height}+{x}+{y}")

    # Прозрачный фон
    transparent_color = '#f0f0f0'
    splash.configure(bg=transparent_color)
    try:
        splash.wm_attributes('-transparentcolor', transparent_color)
    except tk.TclError:
        pass

    frame = ctk.CTkFrame(splash, corner_radius=30, fg_color="#3498db")
    frame.pack(expand=True, fill="both", padx=10, pady=10)

    label = ctk.CTkLabel(frame, text="Загрузка программы...",
                         font=("Segoe UI", 22, "bold"), text_color="white")
    label.pack(pady=(25, 15))

    progress = ctk.CTkProgressBar(
        frame, width=300, height=12, corner_radius=6, progress_color='#2980b9')
    progress.pack(pady=10)
    progress.set(0)

    status_label = ctk.CTkLabel(frame, text="Инициализация...",
                                font=("Segoe UI", 15), text_color="white")
    status_label.pack(pady=(5, 10))

    # Водяной знак
    watermark = ctk.CTkLabel(
        frame,
        text="Dybfuo.Media",
        font=("Segoe UI", 12, "bold"),
        text_color="#ffb347"  # сине-оранжевый оттенок (можешь заменить!)
    )
    watermark.pack(side="bottom", pady=(0, 8))

    splash.after(0, lambda: hide_from_taskbar(splash))

    phrases = [
        "Загружаем спортсменов...",
        "Синхронизируем результаты...",
        "Настраиваем интерфейс...",
        "Подключаем модули...",
        "Финальная подготовка...",
    ]

    progress_value = 0.0
    steps = 100  # количество шагов для прогресса
    interval = int((load_time * 1000) / steps)  # время между шагами в мс

    def update_progress():
        nonlocal progress_value
        if progress_value < 1.0:
            progress_value += 1 / steps
            progress.set(progress_value)
            if int(progress_value * 100) % 20 == 0:
                status_label.configure(text=random.choice(phrases))
            splash.after(interval, update_progress)
        else:
            splash.destroy()
            callback_when_done()

    splash.after(500, update_progress)
    splash.mainloop()


if __name__ == "__main__":

    def launch_main_app():
        app = init()
        app.mainloop()

    show_splash(launch_main_app, load_time=4)
