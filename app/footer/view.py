import customtkinter as ctk

from .location import Location
from .auto_location import AutoLocation
from .replacement import Replacement


tabs = {
    'Replacement': 'Автозамена',
    'Location': 'Локация',
    'Auto-Location': 'Авто-выбор',
}


class FooterView(ctk.CTkTabview):
    def __init__(self, parent, frame):
        super().__init__(
            frame, width=350, height=275)
        self.grid(row=1, padx=115, pady=(10, 20), sticky="nsew")

        self.parent = parent

        for n in tabs.values():
            self.add(n)
            self.tab(n).grid_columnconfigure(0, weight=0)

        self.location_obj = Location(self, tabs['Location'])
        self.auto_location = AutoLocation(self, tabs['Auto-Location'])
        self.replacement = Replacement(self, tabs['Replacement'])
