import customtkinter as ctk
from .baseframe import BaseFrame


class AutoLocation(BaseFrame):
    def __init__(self, parent, subname):
        self.config = parent.parent.data
        super().__init__(parent, subname,
                         self.config['auto_location'],
                         self.save_location)

    def save_location(self):
        self.config['auto_location'].clear()
        for _, a, b, _ in self.entries:
            self.config['auto_location'][a.get()] = b.get()
        self.btn_save.configure(state='disabled')
