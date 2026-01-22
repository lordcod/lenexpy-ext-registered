from pathlib import Path
from typing import TYPE_CHECKING
from tkinter import messagebox as mb
import customtkinter as ctk
from lenexpy import tofile
import openpyxl

if TYPE_CHECKING:
    from .view import HeaderView


def get_file_name(path: str) -> str:
    if path is None:
        return None
    return Path(path).name[:21]


def notify_nf(nf: set):
    match len(nf):
        case 0:
            return
        case 1:
            t = f"Столбец {next(iter(nf))} не был найден во время обработки."
        case _:
            t = f"Столбецы {', '.join(nf)} не были найдены во время обработки."
    mb.showinfo(
        'Не найдено',
        t
    )


def init_auto_location(xlsx, config, location_obj):
    location = config['location']
    auto_location = config['auto_location']

    workbook = openpyxl.load_workbook(xlsx)
    sheet = workbook.active

    nf = set(location.keys())

    for i, r in enumerate(sheet[1]):
        if r.value in auto_location:
            key = auto_location[r.value]
            location[key] = i
            nf.remove(key)

    location_obj.upload_location()

    notify_nf(nf)


class FilesTab:
    def __init__(self, parent: 'HeaderView', subname: str):
        self.parent = parent
        tab = self.parent.tab(subname)
        self.data = self.parent.parent.data

        self.info_lxf = ctk.CTkLabel(tab,
                                     text='Файл не выбран')
        self.info_lxf.grid(row=0, column=0, padx=20)
        self.button_lxf = ctk.CTkButton(tab,
                                        text="Открыть LXF, LEF",
                                        command=self.open_lxf)
        self.button_lxf.grid(row=1, column=0, padx=20)

        self.info_xlsx = ctk.CTkLabel(tab,
                                      text='Файл не выбран', height=10)
        self.info_xlsx.grid(row=0, column=1, padx=20)
        self.button_xlsx = ctk.CTkButton(tab,
                                         text="Открыть XLSX",
                                         command=self.open_xlsx)
        self.button_xlsx.grid(row=1, column=1, padx=20)

        self.button_saved = ctk.CTkButton(tab,
                                          text="Сохрнаить LXF, LEF",
                                          command=self.save_lxf)
        self.button_saved.grid(row=1, column=2, padx=20)

    def open_lxf(self):
        button_start = self.parent.parent.header_view.process.button_start

        file = ctk.filedialog.askopenfilename(
            filetypes=[('Lenex file', ('.lxf', '.lef')),
                       ('XML file', '.xml')],
            initialdir=Path(self.data.get('lxf')).parent,
            initialfile=self.data.get('lxf')
        )
        if not file:
            return

        self.data['lxf'] = file

        button_start.configure(state='normal' if self.data.get('lxf') is not None
                               and self.data.get('xlsx') is not None else 'disabled')
        self.info_lxf.configure(text=get_file_name(file))

    def open_xlsx(self):
        button_start = self.parent.parent.header_view.process.button_start

        file = ctk.filedialog.askopenfilename(
            filetypes=[('XLSX', '.xlsx')],
            initialdir=Path(self.data.get('xlsx')).parent,
            initialfile=self.data.get('xlsx')
        )
        if not file:
            return

        self.data['xlsx'] = file

        button_start.configure(state='normal' if self.data.get('lxf') is not None
                               and self.data.get('xlsx') is not None else 'disabled')
        self.info_xlsx.configure(text=get_file_name(file))

        init_auto_location(
            file,
            self.data,
            self.parent.parent.footer_view.location_obj
        )

    def save_lxf(self):
        file = ctk.filedialog.asksaveasfilename(
            filetypes=[('Lenex file', ('.lxf', '.lef')),
                       ('XML file', '.xml')],
            defaultextension='*.lxf'
        )
        if not file:
            return

        print(self.data['lenex'], file)
        tofile(self.data['lenex'], file)

        self.button_saved.configure(state='disabled')
        mb.showinfo(
            'Успешно',
            'Файл успешно сохранен!'
        )
