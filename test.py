import sys
from typing import Dict, List
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow, QAction, QMenu, QFileDialog,
    QDialog, QVBoxLayout, QComboBox, QSpinBox, QLabel,
    QPushButton, QHBoxLayout, QToolBar, QInputDialog
)
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap
from PyQt5.QtCore import Qt, QRect, QPoint


class BlockDialog(QDialog):
    """Окно параметров блока."""

    def __init__(self, block=None):
        super().__init__()
        self.setWindowTitle("Настройки блока")
        self.block = block or {}

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Тип объекта:"))

        self.typeBox = QComboBox()
        self.typeBox.addItems(
            ["lane", "start", "finish", "camera", "timer", "label"])
        if block:
            self.typeBox.setCurrentText(block.get("type", "lane"))
        layout.addWidget(self.typeBox)

        layout.addWidget(QLabel("Номер дорожки:"))
        self.laneSpin = QSpinBox()
        self.laneSpin.setRange(1, 16)
        self.laneSpin.setValue(self.block.get("laneNumber", 1))
        layout.addWidget(self.laneSpin)

        btns = QHBoxLayout()
        save = QPushButton("Сохранить")
        cancel = QPushButton("Отмена")
        btns.addWidget(save)
        btns.addWidget(cancel)

        layout.addLayout(btns)

        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        self.setLayout(layout)

    def getData(self):
        return {
            "type": self.typeBox.currentText(),
            "laneNumber": self.laneSpin.value(),
        }


class Canvas(QWidget):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.drawing = False
        self.edit_mode = False
        self.start_pos = None
        self.current_rect = None
        self.background = None

    def load_background(self, path):
        self.background = QPixmap(path)
        self.update()

    def toggle_edit_mode(self, state: bool):
        self.edit_mode = state
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()

        if self.edit_mode:
            for block in reversed(self.blocks):
                if block["rect"].contains(pos):
                    self.open_block_menu(block, event.globalPos())
                    return

            if event.button() == Qt.LeftButton:
                self.drawing = True
                self.start_pos = pos
                self.current_rect = QRect(self.start_pos, self.start_pos)
        else:
            # обычный режим — редактирование статуса
            for block in reversed(self.blocks):
                if block["rect"].contains(pos):
                    self.open_status_menu(block, event.globalPos())
                    return

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.current_rect = QRect(self.start_pos, event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            rect = self.current_rect.normalized()

            if rect.width() <= 30 or rect.height() <= 30:
                self.current_rect = None
                self.update()
                return

            dlg = BlockDialog()
            if dlg.exec_():
                data = dlg.getData()
                self.blocks.append({"rect": rect, **data})

            self.current_rect = None
            self.update()

    def open_block_menu(self, block, pos):
        menu = QMenu()
        edit_action = menu.addAction("Изменить")
        delete_action = menu.addAction("Удалить")

        act = menu.exec_(pos)
        if act == edit_action:
            dlg = BlockDialog(block)
            if dlg.exec_():
                block.update(dlg.getData())
                self.update()
        elif act == delete_action:
            self.blocks.remove(block)
            self.update()

    def open_status_menu(self, block, pos):
        menu = QMenu()
        edit_status_action = menu.addAction("Изменить статус")
        edit_time_action = menu.addAction("Изменить время")

        act = menu.exec_(pos)

        if act == edit_status_action:
            statuses = ["OK", "DSQ", "DNS"]
            status, ok = QInputDialog.getItem(self, "Выбор статуса",
                                              f"Выберите статус для {block['type']}:",
                                              statuses, 0, False)
            if ok and status:
                block["status"] = status
                self.update()

        elif act == edit_time_action:
            time_text, ok = QInputDialog.getText(self, "Изменить время",
                                                 "Введите время (например 00:32.45):",
                                                 text=block.get("time", ""))
            if ok and time_text:
                block["time"] = time_text
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.background:
            painter.drawPixmap(self.rect(), self.background)

        for block in self.blocks:
            color = QColor(0, 150, 255, 80)
            if block["type"] == "lane":
                color = QColor(0, 255, 0, 80)
            elif block["type"] == "camera":
                color = QColor(255, 200, 0, 80)

            painter.fillRect(block["rect"], color)
            painter.setPen(QPen(Qt.black, 2))
            painter.drawRect(block["rect"])

            text = f"{block['type']} ({block.get('laneNumber', '-')})"
            painter.drawText(block["rect"].topLeft() + QPoint(5, 15), text)

            if "status" in block:
                painter.drawText(
                    block["rect"].bottomLeft() + QPoint(5, -5), block["status"])

        if self.current_rect:
            painter.setPen(QPen(Qt.red, 2, Qt.DashLine))
            painter.drawRect(self.current_rect)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Разметка бассейна — PyQt5")

        self.canvas = Canvas()
        self.setCentralWidget(self.canvas)

        # Данные для дистанций и заплывов
        self.distances = ["50m", "100m", "200m", "400m"]
        self.heats = {
            "50m": ["Заплыв 1", "Заплыв 2"],
            "100m": ["Заплыв 1", "Заплыв 2", "Заплыв 3"],
            "200m": ["Заплыв 1", "Заплыв 2"],
            "400m": ["Заплыв 1"],
        }

        self.current_distance = None
        self.current_heat = None

        # Верхний тулбар для выбора дистанции/заплыва
        top_widget = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(5, 5, 5, 5)
        top_widget.setLayout(top_layout)

        top_layout.addWidget(QLabel("Дистанция:"))
        self.distanceBox = QComboBox()
        self.distanceBox.addItems(self.distances)
        self.distanceBox.currentTextChanged.connect(self.on_distance_change)
        top_layout.addWidget(self.distanceBox)

        top_layout.addWidget(QLabel("Заплыв:"))
        self.heatBox = QComboBox()
        top_layout.addWidget(self.heatBox)

        self.nextHeatBtn = QPushButton("Следующий заплыв")
        self.nextHeatBtn.clicked.connect(self.next_heat)
        top_layout.addWidget(self.nextHeatBtn)

        top_toolbar = QToolBar()
        top_toolbar.addWidget(top_widget)
        self.addToolBar(Qt.TopToolBarArea, top_toolbar)
        self.on_distance_change(self.distances[0])  # инициализация

        # Основной тулбар с инструментами
        toolbar = self.addToolBar("tools")

        editAct = QAction("Редактирование", self, checkable=True)
        editAct.triggered.connect(lambda s: self.canvas.toggle_edit_mode(s))
        toolbar.addAction(editAct)

        loadImgAct = QAction("Загрузить фото", self)
        loadImgAct.triggered.connect(self.load_image)
        toolbar.addAction(loadImgAct)

        cropAct = QAction("Сохранить блоки", self)
        cropAct.triggered.connect(self.crop_blocks)
        toolbar.addAction(cropAct)

    def on_distance_change(self, distance):
        self.current_distance = distance
        self.heatBox.clear()
        self.heatBox.addItems(self.heats.get(distance, []))
        if self.heats.get(distance):
            self.current_heat = self.heats[distance][0]

    def load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Выберите фото", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            self.canvas.load_background(path)

    def crop_blocks(self):
        if not self.canvas.background:
            return

        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку для сохранения блоков"
        )
        if not folder:
            return

        for i, block in enumerate(self.canvas.blocks, start=1):
            rect = block["rect"].normalized()
            cropped = self.canvas.background.copy(rect)
            file_path = f"{folder}/block_{i}_{block['type']}.png"
            cropped.save(file_path)
        print(f"Сохранено {len(self.canvas.blocks)} блоков в {folder}")

    def next_heat(self):
        if not self.current_distance:
            return
        heats = self.heats.get(self.current_distance, [])
        if not heats:
            return
        current_index = self.heatBox.currentIndex()
        if current_index + 1 >= len(heats):
            return
        next_index = current_index + 1
        self.heatBox.setCurrentIndex(next_index)
        self.current_heat = heats[next_index]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 700)
    w.show()
    sys.exit(app.exec_())
