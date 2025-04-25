import threading
import customtkinter as ctk
from tkinter import messagebox as mb
from reg.main import TranslatorLenex


class ProcessTab:
    def __init__(self, parent: ctk.CTkTabview, subname: str):
        self.parent = parent
        self.data = self.parent.parent.data
        self.thread = None

        self.button_start = ctk.CTkButton(self.parent.tab(subname),
                                          text="Начать!",
                                          command=self.click_start,
                                          state='disabled',
                                          width=210)
        self.button_start.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

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
            mb.showinfo(None, 'Файл готов к импорту!')

            self.thread = None

        self.thread = threading.Thread(target=_start)
        self.thread.start()
