import threading
import customtkinter as ctk
from tkinter import messagebox as mb
from reg.main import TranslatorLenex


class ProcessTab:
    def __init__(self, parent: ctk.CTkTabview, subname: str):
        self.parent = parent
        self.data = self.parent.parent.data
        self.thread = None

        tab = self.parent.tab(subname)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.grid(row=0, column=0, padx=16, pady=12, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            container,
            text="Готовы запустить обработку?",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.grid(row=0, column=0, pady=(8, 4), sticky="n")

        subtitle = ctk.CTkLabel(
            container,
            text="Выберите LXF/LEF и XLSX на вкладке «Файлы», затем нажмите «Начать».",
            text_color=("gray80", "gray70"),
            wraplength=420,
            justify="center"
        )
        subtitle.grid(row=1, column=0, pady=(0, 12), padx=8, sticky="n")

        self.button_start = ctk.CTkButton(container,
                                          text="Начать",
                                          command=self.click_start,
                                          state='disabled',
                                          width=220,
                                          height=38)
        self.button_start.grid(row=2, column=0, pady=(6, 0))

    def click_start(self):
        if self.thread:
            return

        def _start():
            button_saved = self.parent.parent.header_view.files.button_saved

            translator = TranslatorLenex(
                self.data['lxf'], self.data['xlsx'], self.data)
            lenex = translator.parse()
            self.data['lenex'] = lenex

            button_saved.configure(state='normal')
            mb.showinfo("Готово", "Файл готов к импорту!")

            self.thread = None

        self.thread = threading.Thread(target=_start)
        self.thread.start()
