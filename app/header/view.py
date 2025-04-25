from typing import TYPE_CHECKING
import customtkinter as ctk

from .birthday import BirthdayTab
from .files import FilesTab
from .points import PointsTab
from .process import ProcessTab

if TYPE_CHECKING:
    from ..menu import App


tabs = {
    'Process': 'Процесс',
    'Files': 'Файлы',
    'Points': 'Очки',
    'Birthday': 'Д/р',
}


class HeaderView(ctk.CTkTabview):
    def __init__(self, parent: 'App'):
        super().__init__(parent, width=580, height=120)
        self.grid(row=0, column=0, padx=20,
                  pady=(0, 0), sticky="nsew")

        self.parent = parent

        for name in tabs.values():
            self.add(name)
            for i in range(3):
                self.tab(name).grid_columnconfigure(i, weight=1)

        self.files = FilesTab(self, tabs['Files'])
        self.points = PointsTab(self, tabs['Points'])
        self.process = ProcessTab(self, tabs['Process'])
        self.birthday = BirthdayTab(self, tabs['Birthday'])
