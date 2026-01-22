from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Dict, List

import openpyxl
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QListWidget,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from lenexpy import tofile

from reg.main import TranslatorLenex
from reg.issues import IssueCollector


def _muted_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setProperty("role", "muted")
    return label


class IssuesDialog(QDialog):
    CATEGORY_LABELS = {
        "points_policy": "Политика очков",
        "incorrect_distance": "Дистанции",
        "age_exh": "Возраст/EXH",
        "duplicate_entry": "Дубликаты",
        "parse_error": "Ошибки строк",
    }

    def __init__(self, collector: IssueCollector, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Отчет об обработке")
        self.resize(720, 480)

        layout = QVBoxLayout(self)
        grouped = collector.by_category()
        if not grouped:
            layout.addWidget(QLabel("Замечаний нет."))
        else:
            tabs = QTabWidget()
            for cat, items in grouped.items():
                tab = QWidget()
                tab_layout = QVBoxLayout(tab)
                list_widget = QListWidget()
                detail = QTextEdit()
                detail.setReadOnly(True)
                detail.setFont(QFont("Consolas", 10))
                list_widget.setFont(QFont("Segoe UI", 10))

                for issue in items:
                    prefix = f"Строка {issue['row_index']}: " if issue["row_index"] else ""
                    list_widget.addItem(prefix + issue["message"])

                def on_select(index: int, issues=items, detail_widget=detail):
                    if index < 0 or index >= len(issues):
                        detail_widget.clear()
                        return
                    issue = issues[index]
                    parts = []
                    if issue.get("row_data"):
                        parts.append("Данные строки:")
                        for key, value in issue["row_data"].items():
                            parts.append(f"  - {key}: {value}")
                    elif issue.get("row_repr"):
                        parts.append(f"Row: {issue['row_repr']}")
                    if issue.get("extra"):
                        for k, v in issue["extra"].items():
                            parts.append(f"{k}: {v}")
                    detail_widget.setPlainText("\n".join(parts))

                list_widget.currentRowChanged.connect(on_select)
                if items:
                    list_widget.setCurrentRow(0)

                tab_layout.addWidget(list_widget)
                tab_layout.addWidget(detail)
                tabs.addTab(tab, self.CATEGORY_LABELS.get(cat, cat))

            layout.addWidget(tabs)

        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


class ProcessTab(QWidget):
    def __init__(self, on_start: Callable[[], None]):
        super().__init__()
        self._ready = False
        self._busy = False
        self.on_start = on_start

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(6)

        title = QLabel("Запуск обработки")
        title.setProperty("role", "title")
        subtitle = _muted_label(
            "Выберите файлы, настроите фильтры и запустите конвертацию. Пока идёт обработка, кнопка блокируется."
        )

        steps = _muted_label(
            "Чек-лист:\n1) Исходный LENEX/LEF\n2) Таблица XLSX\n3) Колонки и замены")

        self.button_start = QPushButton("Запустить конвертацию")
        self.button_start.setProperty("accent", True)
        self.button_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button_start.setEnabled(False)
        self.button_start.setMinimumHeight(34)
        self.button_start.clicked.connect(self.on_start)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(steps)
        card_layout.addStretch(1)
        card_layout.addWidget(self.button_start)
        layout.addWidget(card)
        layout.addStretch(1)

    def _sync_state(self):
        self.button_start.setEnabled(self._ready and not self._busy)

    def set_ready(self, ready: bool):
        self._ready = ready
        self._sync_state()

    def set_busy(self, busy: bool):
        self._busy = busy
        self._sync_state()


class FilesTab(QWidget):
    def __init__(
        self,
        data: dict,
        on_files_changed: Callable[[], None],
        on_auto_location: Callable[[str], None],
    ):
        super().__init__()
        self.data = data
        self.on_files_changed = on_files_changed
        self.on_auto_location = on_auto_location

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        header = QLabel("Файлы и экспорт")
        header.setProperty("role", "title")
        layout.addWidget(header)
        layout.addWidget(_muted_label(
            "Укажите исходный LENEX/LEF и таблицу XLSX. После обработки сохраните новый файл."))

        cards = QGridLayout()
        cards.setHorizontalSpacing(10)
        cards.setVerticalSpacing(10)
        layout.addLayout(cards)

        self.lxf_label = QLabel("Файл не выбран")
        self.lxf_label.setProperty("role", "muted")
        btn_lxf = QPushButton("Открыть LXF / LEF")
        btn_lxf.setProperty("accent", True)
        btn_lxf.setMinimumHeight(32)
        btn_lxf.clicked.connect(self.choose_lxf)

        self.xlsx_label = QLabel("Файл не выбран")
        self.xlsx_label.setProperty("role", "muted")
        btn_xlsx = QPushButton("Открыть XLSX")
        btn_xlsx.setProperty("accent", True)
        btn_xlsx.setMinimumHeight(32)
        btn_xlsx.clicked.connect(self.choose_xlsx)

        self.btn_save = QPushButton("Сохранить LXF / LEF")
        self.btn_save.setProperty("secondary", True)
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_lxf)

        cards.addWidget(self._build_file_card(
            "Исходный LXF / LEF", self.lxf_label, btn_lxf), 0, 0)
        cards.addWidget(self._build_file_card(
            "Таблица XLSX", self.xlsx_label, btn_xlsx), 0, 1)
        cards.setColumnStretch(0, 1)
        cards.setColumnStretch(1, 1)

        save_card = QFrame()
        save_card.setProperty("card", True)
        save_layout = QHBoxLayout(save_card)
        save_layout.setContentsMargins(12, 12, 12, 12)
        save_layout.setSpacing(8)
        save_layout.addWidget(_muted_label(
            "Сохранение станет доступно после успешной обработки."))
        save_layout.addStretch(1)
        save_layout.addWidget(self.btn_save)
        layout.addWidget(save_card)

        if self.data.get("lxf"):
            self._update_label(self.lxf_label, self.data["lxf"])
        if self.data.get("xlsx"):
            self._update_label(self.xlsx_label, self.data["xlsx"])

    @staticmethod
    def _build_file_card(title: str, path_label: QLabel, button: QPushButton) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setProperty("role", "subtitle")
        card_layout.addWidget(title_label)
        card_layout.addWidget(path_label)
        card_layout.addStretch(1)
        card_layout.addWidget(button)
        return card

    @staticmethod
    def _update_label(label: QLabel, path: str):
        name = Path(path).name
        label.setText(name)
        label.setToolTip(path)

    def choose_lxf(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Выбрать LXF / LEF", "", "Lenex (*.lxf *.lef *.xml);;Все файлы (*)"
        )
        if not file:
            return
        self.data["lxf"] = file
        self._update_label(self.lxf_label, file)
        self.on_files_changed()

    def choose_xlsx(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Выбрать XLSX", "", "Excel (*.xlsx);;Все файлы (*)"
        )
        if not file:
            return
        self.data["xlsx"] = file
        self._update_label(self.xlsx_label, file)
        self.on_files_changed()
        self.on_auto_location(file)

    def save_lxf(self):
        file, _ = QFileDialog.getSaveFileName(
            self, "Сохранить LXF / LEF", filter="Lenex (*.lxf *.lef *.xml)"
        )
        if not file:
            return
        tofile(self.data["lenex"], file)
        self.btn_save.setEnabled(False)
        QMessageBox.information(self, "Готово", "Файл успешно сохранён.")

    def set_save_enabled(self, enabled: bool):
        self.btn_save.setEnabled(enabled)


class PointsTab(QWidget):
    def __init__(self, data: dict, on_change: Callable[[], None]):
        super().__init__()
        self.data = data
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QGridLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setHorizontalSpacing(8)
        card_layout.setVerticalSpacing(6)

        header = QLabel("Фильтр по очкам")
        header.setProperty("role", "subtitle")
        card_layout.addWidget(header, 0, 0, 1, 2)

        helper = _muted_label(
            "Укажите диапазон, чтобы оставить только нужных участников. Отключите, чтобы выгрузить всех.")
        card_layout.addWidget(helper, 1, 0, 1, 2)

        self.enabled = QCheckBox("Включить фильтр")
        self.enabled.setChecked(bool(self.data["points"]["enabled"]))
        self.enabled.stateChanged.connect(self.toggle_enabled)

        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(0, 10000)
        self.min_spin.setDecimals(2)
        self.min_spin.setValue(float(self.data["points"]["min"]))
        self.min_spin.valueChanged.connect(self.update_min)

        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(0, 10000)
        self.max_spin.setDecimals(2)
        self.max_spin.setValue(float(self.data["points"]["max"]))
        self.max_spin.valueChanged.connect(self.update_max)

        card_layout.addWidget(self.enabled, 2, 0, 1, 2)
        card_layout.addWidget(QLabel("Мин. очки"), 3, 0)
        card_layout.addWidget(self.min_spin, 3, 1)
        card_layout.addWidget(QLabel("Макс. очки"), 4, 0)
        card_layout.addWidget(self.max_spin, 4, 1)

        card_layout.setColumnStretch(1, 1)
        layout.addWidget(card)
        layout.addStretch(1)

    def _notify_change(self):
        if self.on_change:
            self.on_change()

    def toggle_enabled(self):
        self.data["points"]["enabled"] = self.enabled.isChecked()
        self._notify_change()

    def update_min(self, val: float):
        self.data["points"]["min"] = float(val)
        self._notify_change()

    def update_max(self, val: float):
        self.data["points"]["max"] = float(val)
        self._notify_change()


class BirthdayTab(QWidget):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(5)

        card_layout.addWidget(QLabel("Формат даты рождения (strftime)"))
        card_layout.addWidget(_muted_label(
            "Например: %d.%m.%Y или %Y-%m-%d. Пустое значение вернёт формат по умолчанию."))

        self.edit = QLineEdit(self.data.get("birthday", "%d.%m.%Y"))
        self.edit.textChanged.connect(self.update_value)
        card_layout.addWidget(self.edit)
        layout.addWidget(card)
        layout.addStretch(1)

    def update_value(self, value: str):
        self.data["birthday"] = value.strip() or "%d.%m.%Y"


class LocationTab(QWidget):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.entries: Dict[str, QLineEdit] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(6)

        helper = _muted_label(
            "Номера колонок в XLSX (1 — первая). Оставьте поле пустым, чтобы колонка игнорировалась."
        )
        card_layout.addWidget(helper)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(5)
        card_layout.addLayout(grid)

        keys = list(self.data["location"].keys())
        for i, key in enumerate(keys):
            row = i // 3
            col = i % 3
            label = QLabel(key)
            grid.addWidget(label, row * 2, col)

            edit = QLineEdit()
            edit.setPlaceholderText("?")
            edit.setMaximumWidth(130)
            value = self.data["location"].get(key, -1)
            if value is not None and value >= 0:
                edit.setText(str(value + 1))
            edit.textChanged.connect(self._make_updater(key))
            grid.addWidget(edit, row * 2 + 1, col)
            self.entries[key] = edit

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        layout.addWidget(card)

    def _make_updater(self, key: str) -> Callable[[str], None]:
        def update(val: str):
            val = val.strip()
            if not val:
                self.data["location"][key] = -1
                return
            if val.isdigit():
                self.data["location"][key] = int(val) - 1

        return update

    def refresh(self):
        for key, edit in self.entries.items():
            value = self.data["location"].get(key, -1)
            edit.blockSignals(True)
            edit.clear()
            if value is not None and value >= 0:
                edit.setText(str(value + 1))
            edit.blockSignals(False)


class KeyValueEditor(QWidget):
    def __init__(self, title: str, data: dict, on_save: Callable[[], None]):
        super().__init__()
        self.data = data
        self.rows: List[Dict[str, QWidget]] = []
        self.on_save = on_save

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        card = QFrame()
        card.setProperty("card", True)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        card_layout.setSpacing(6)

        header = QLabel(title)
        header.setProperty("role", "subtitle")
        card_layout.addWidget(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(5)
        self.scroll.setWidget(self.container)
        self.scroll.setFixedHeight(300)
        card_layout.addWidget(self.scroll)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить правило")
        self.btn_add.setProperty("secondary", True)
        self.btn_add.clicked.connect(self.add_row)
        self.btn_save = QPushButton("Сохранить изменения")
        self.btn_save.setProperty("accent", True)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save)
        btn_row.addWidget(self.btn_add)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_save)
        card_layout.addLayout(btn_row)

        layout.addWidget(card)

        for key, value in self.data.items():
            self._create_row(key, value)

        self._renumber()

    def _create_row(self, key: str = "", value: str = ""):
        row_widget = QFrame()
        row_widget.setProperty("card", False)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        lbl_index = QLabel("0")
        lbl_index.setFixedWidth(18)
        edit_key = QLineEdit(key)
        edit_key.setPlaceholderText("Что ищем")
        edit_key.setMinimumHeight(32)
        edit_value = QLineEdit(value)
        edit_value.setPlaceholderText("На что заменить")
        edit_value.setMinimumHeight(32)
        btn_del = QPushButton("Удалить")
        btn_del.setProperty("secondary", True)
        btn_del.setFixedWidth(70)

        for edit in (edit_key, edit_value):
            edit.textChanged.connect(lambda _: self.btn_save.setEnabled(True))

        def delete_row():
            row_widget.setParent(None)
            self.rows = [r for r in self.rows if r["widget"] is not row_widget]
            self._renumber()
            self.btn_save.setEnabled(True)

        btn_del.clicked.connect(delete_row)

        row_layout.addWidget(lbl_index)
        row_layout.addWidget(edit_key)
        row_layout.addWidget(edit_value)
        row_layout.addWidget(btn_del)

        self.container_layout.addWidget(row_widget)
        self.rows.append(
            {"widget": row_widget, "index": lbl_index,
                "key": edit_key, "value": edit_value}
        )

    def _renumber(self):
        for i, row in enumerate(self.rows, start=1):
            row["index"].setText(str(i))

    def add_row(self):
        self._create_row()
        self._renumber()
        self.btn_save.setEnabled(True)

    def save(self):
        new_data: Dict[str, str] = {}
        for row in self.rows:
            key = row["key"].text().strip()
            val = row["value"].text()
            if key:
                new_data[key] = val
        self.data.clear()
        self.data.update(new_data)
        self.btn_save.setEnabled(False)
        self.on_save()


class ReplacementTab(KeyValueEditor):
    def __init__(self, data: dict):
        super().__init__("Автозамена значений",
                         data["replacement"], on_save=lambda: None)


class AutoLocationTab(KeyValueEditor):
    def __init__(self, data: dict):
        super().__init__("Авто-определение колонок",
                         data["auto_location"], on_save=lambda: None)


class App(QMainWindow):
    def __init__(self, data: dict):
        super().__init__()
        self.data = data
        self.worker: threading.Thread | None = None
        self.issue_collector: IssueCollector | None = None

        self.setWindowTitle("Lenex Converter")
        self.resize(880, 760)
        self.setMinimumSize(820, 680)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        self.banner = self._build_banner()
        main_layout.addWidget(self.banner)

        self.header_tabs = QTabWidget()
        self.process_tab = ProcessTab(self.handle_start)
        self.files_tab = FilesTab(
            self.data, on_files_changed=self.refresh_start_state, on_auto_location=self.init_auto_location
        )
        self.points_tab = PointsTab(
            self.data, on_change=self._update_status_badges)
        self.birthday_tab = BirthdayTab(self.data)

        self.header_tabs.addTab(self.process_tab, "Процесс")
        self.header_tabs.addTab(self.files_tab, "Файлы")
        self.header_tabs.addTab(self.points_tab, "Очки")
        self.header_tabs.addTab(self.birthday_tab, "Д/Р")
        main_layout.addWidget(self.header_tabs)

        self.footer_tabs = QTabWidget()
        self.replacement_tab = ReplacementTab(self.data)
        self.location_tab = LocationTab(self.data)
        self.auto_location_tab = AutoLocationTab(self.data)

        self.footer_tabs.addTab(self.location_tab, "Локация")
        self.footer_tabs.addTab(self.replacement_tab, "Автозамена")
        self.footer_tabs.addTab(self.auto_location_tab, "Авто-выбор")
        main_layout.addWidget(self.footer_tabs)

        self.refresh_start_state()

    def _build_banner(self) -> QWidget:
        card = QFrame()
        card.setProperty("card", True)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(6)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        title = QLabel("Lenex Converter")
        title.setProperty("role", "hero")
        text_col.addWidget(title)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        self.lxf_badge = QLabel("LXF/LEF: не выбран")
        self.xlsx_badge = QLabel("XLSX: не выбран")
        self.points_badge = QLabel("")
        for badge in (self.lxf_badge, self.xlsx_badge, self.points_badge):
            badge.setProperty("role", "chip")
            badge_row.addWidget(badge)
        badge_row.addStretch(1)
        text_col.addLayout(badge_row)
        layout.addLayout(text_col, 1)

        self.primary_start_button = QPushButton("Запустить обработку")
        self.primary_start_button.setProperty("accent", True)
        self.primary_start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary_start_button.setMinimumHeight(34)
        self.primary_start_button.clicked.connect(self.handle_start)
        layout.addWidget(self.primary_start_button,
                         alignment=Qt.AlignmentFlag.AlignVCenter)
        return card

    def _format_points_badge(self) -> str:
        points = self.data.get("points", {})
        if not points.get("enabled"):
            return "Фильтр по очкам: выкл."
        return f"Фильтр: {points.get('min', 0):.0f}–{points.get('max', 0):.0f}"

    def _update_status_badges(self):
        lxf = self.data.get("lxf")
        xlsx = self.data.get("xlsx")
        self.lxf_badge.setText(
            f"LXF/LEF: {Path(lxf).name}" if lxf else "LXF/LEF: не выбран")
        self.lxf_badge.setToolTip(lxf or "")
        self.xlsx_badge.setText(
            f"XLSX: {Path(xlsx).name}" if xlsx else "XLSX: не выбран")
        self.xlsx_badge.setToolTip(xlsx or "")
        self.points_badge.setText(self._format_points_badge())

    def refresh_start_state(self):
        ready = bool(self.data.get("lxf")) and bool(self.data.get("xlsx"))
        self.process_tab.set_ready(ready)
        self.primary_start_button.setEnabled(ready and self.worker is None)
        self._update_status_badges()

    def init_auto_location(self, xlsx_path: str):
        location = self.data["location"]
        auto_location = self.data.get("auto_location", {})

        nf = set(location.keys())
        try:
            workbook = openpyxl.load_workbook(xlsx_path)
            sheet = workbook.active
            for i, cell in enumerate(sheet[1]):
                if cell.value in auto_location:
                    key = auto_location[cell.value]
                    location[key] = i
                    nf.discard(key)
            self.location_tab.refresh()
            if nf:
                QMessageBox.information(
                    self,
                    "Авто-локация",
                    f"Не удалось определить колонки: {', '.join(sorted(nf))}",
                )
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка XLSX",
                                f"Не удалось прочитать файл: {exc}")

    def handle_start(self):
        if self.worker is not None:
            return
        self.issue_collector = IssueCollector()
        self.process_tab.set_busy(True)
        self.primary_start_button.setEnabled(False)
        self.worker = threading.Thread(
            target=self._run_translation, daemon=True)
        self.worker.start()

    def _run_translation(self):
        try:
            translator = TranslatorLenex(
                self.data["lxf"], self.data["xlsx"], self.data, collector=self.issue_collector)
            lenex = translator.parse()
            self.data["lenex"] = lenex
        except Exception as exc:  # noqa: BLE001
            QMetaObject.invokeMethod(
                self,
                "_notify_error",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(object, exc),
            )
        else:
            QMetaObject.invokeMethod(
                self,
                "_notify_success",
                Qt.ConnectionType.QueuedConnection,
            )

    @pyqtSlot()
    def _notify_success(self):
        self.worker = None
        self.process_tab.set_busy(False)
        self.primary_start_button.setEnabled(True)
        self.files_tab.set_save_enabled(True)
        QMessageBox.information(self, "Готово", "Обработка завершена.")
        if self.issue_collector:
            IssuesDialog(self.issue_collector, self).exec()

    @pyqtSlot(object)
    def _notify_error(self, exc: object):
        self.worker = None
        self.process_tab.set_busy(False)
        self.primary_start_button.setEnabled(True)
        QMessageBox.critical(
            self, "Ошибка", f"Не удалось обработать: {exc}")
        if self.issue_collector and self.issue_collector.has_items():
            IssuesDialog(self.issue_collector, self).exec()

def _apply_theme(app: QApplication):
    app.setStyle("Fusion")
    font = QFont("Segoe UI Variable Display", 10)
    app.setFont(font)
    app.setStyleSheet(
        """
        QMainWindow { background-color: #0b1220; }
        QWidget { background-color: #0b1220; color: #e5e7eb; selection-background-color: #10b981; selection-color: #0b1220; font-size: 10pt; }
        QLabel[role="muted"] { color: #94a3b8; }
        QLabel[role="subtitle"] { font-size: 10.5pt; font-weight: 600; }
        QLabel[role="title"] { font-size: 12pt; font-weight: 700; }
        QLabel[role="hero"] { font-size: 16pt; font-weight: 800; }
        QLabel[role="chip"] { background-color: #111827; border: 1px solid #1f2937; border-radius: 9px; padding: 3px 7px; color: #cbd5e1; }

        QFrame[card="true"] { background-color: #0f172a; border: 1px solid #1f2937; border-radius: 9px; }

        QTabWidget::pane { border: 1px solid #1f2937; border-radius: 9px; padding: 5px; margin-top: 2px; }
        QTabBar::tab { background: transparent; color: #94a3b8; border-radius: 8px; padding: 7px 10px; margin: 2px 3px; }
        QTabBar::tab:selected { background: #111827; color: #e5e7eb; }
        QTabBar::tab:hover { color: #e5e7eb; }

        QPushButton { background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 7px 11px; color: #e5e7eb; font-weight: 600; }
        QPushButton[accent="true"] { background-color: #10b981; border: 1px solid #10b981; color: #04101d; }
        QPushButton[secondary="true"] { background-color: #0f172a; }
        QPushButton:disabled { background-color: #0f172a; color: #475569; border-color: #1f2937; }
        QPushButton::hover { filter: brightness(1.1); }

        QLineEdit, QDoubleSpinBox, QSpinBox { background-color: #0b1628; border: 1px solid #1f2937; border-radius: 7px; padding: 5px 7px; color: #e5e7eb; selection-background-color: #10b981; selection-color: #0b1220; }
        QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus { border-color: #10b981; }
        QScrollArea { border: none; }

        QCheckBox { spacing: 6px; }
        QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #1f2937; border-radius: 5px; background: #0b1628; }
        QCheckBox::indicator:checked { background-color: #10b981; border-color: #10b981; }
        """
    )


def run_app(config: dict):
    app = QApplication([])
    _apply_theme(app)
    window = App(config)
    window.show()
    app.exec()
