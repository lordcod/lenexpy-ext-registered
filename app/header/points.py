import contextlib
from typing import TYPE_CHECKING
import customtkinter as ctk

if TYPE_CHECKING:
    from .view import HeaderView


def generate_point_info(
    tab: ctk.CTkTabview,
    text,
    value,
    column,
    update,
    validate
):
    point_info = ctk.CTkLabel(tab, text=text)
    point_info.grid(row=0, column=column, padx=20, sticky="n")

    point_entry = ctk.CTkEntry(tab)
    point_entry.grid(row=1, column=column, padx=20, sticky="n")

    point_entry.insert(1, value)
    point_entry.bind("<KeyRelease>", update)
    point_entry.configure(
        validate='all',
        validatecommand=(tab.register(validate), '%P')
    )

    return point_info, point_entry


class PointsTab:
    def __init__(self, parent: 'HeaderView', subname: str):
        tab = parent.tab(subname)
        self.data = parent.parent.data

        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=1)
        tab.grid_columnconfigure(2, weight=1)

        self.min_point_info, self.min_point_entry = generate_point_info(
            tab,
            "Мин очки",
            self.data['points']['min'],
            0,
            self.update_min_point,
            self.validate_points
        )

        self.max_point_info, self.max_point_entry = generate_point_info(
            tab,
            "Макс очки",
            self.data['points']['max'],
            2,
            self.update_max_point,
            self.validate_points
        )

        self.switch_point = ctk.CTkSwitch(
            tab, text=None, command=self.update_switch_point)
        self.switch_point.grid(row=0, column=1, padx=20, sticky="")

        self.switch_point_info = ctk.CTkLabel(
            tab, text="Политика очков")
        self.switch_point_info.grid(row=1, column=1, padx=20, sticky="n")

        if self.data['points']['enabled']:
            self.switch_point.select()
        else:
            self.switch_point.deselect()

    def update_switch_point(self):
        self.data['points']['enabled'] = bool(self.switch_point.get())

    def update_min_point(self, event):
        content = self.min_point_entry.get()
        with contextlib.suppress(ValueError):
            self.data['points']['min'] = float(content)

    def update_max_point(self, event):
        content = self.max_point_entry.get()
        with contextlib.suppress(ValueError):
            self.data['points']['max'] = float(content)

    def validate_points(self, content):
        if content == "":
            return True
        try:
            float(content)
            return True
        except ValueError:
            return False
