import os
import subprocess
import sys
from functools import partial

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent, QGuiApplication, QKeyEvent
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QSpacerItem, QVBoxLayout, QWidget)

from cfg import Cfg


class SearchThread(QThread):
    result = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, path: str, filename: str):
        super().__init__()
        self.path = path
        self.filename = filename
        self.stop_flag = False

    def run(self):
        self.stop_flag = False
        name_a = self.filename.lower()

        for root, dirs, files in os.walk(self.path):
            for file in files:

                name_b = file.lower()

                if name_a in name_b or name_a == name_b:
                    self.result.emit(os.path.join(root, file))

                elif self.stop_flag:
                    self.finished.emit()
                    return

        self.finished.emit()


class DraggableLabel(QLabel):
    path_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_text = "Перетяните сюда папку для поиска"
        self.temp_path = None
        self.setText(self.base_text)
        self.setAcceptDrops(True)
        self.setStyleSheet("border: 2px dashed gray; padding: 20px; border-radius: 5px;")
        self.setWordWrap(True)

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0.mimeData().hasUrls():
            self.setText(self.base_text)
            self.setStyleSheet("border: 2px dashed gray; padding: 20px; border-radius: 5px;")
            a0.accept()
        else:
            a0.ignore()
        return super().dragEnterEvent(a0)
    
    def dragLeaveEvent(self, a0: QDragLeaveEvent | None) -> None:
        if self.temp_path:
            self.setText(self.temp_path)
            self.setStyleSheet("border: none;")

        return super().dragLeaveEvent(a0)

    def dropEvent(self, a0: QDropEvent | None) -> None:
        path = a0.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(path):
            self.setText(path)
            self.path_selected.emit(path)
            self.setStyleSheet("border: none;")
            self.temp_path = path
            return super().dropEvent(a0)


class GetPath(QLabel):
    def __init__(self):
        super().__init__()
        self.setText("Откройте папку, в которой хотите искать")
        self.setWordWrap(True)

    def get_path(self):
        result = subprocess.run(
            ["osascript", "get_path.scpt"],
            capture_output=True,
            text=True
            )
        self.setText("Откройте папку, в которой хотите искать" + "\n" + "Текущий путь:" + "\n" + result.stdout.strip())
        return result.stdout.strip()


class SearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.path = None
        self.search_thread: SearchThread = None

        self.setWindowTitle(Cfg.app_name)
        self.base_w, self.base_h = 290, 210
        self.temp_h = self.base_h
        self.setFixedSize(self.base_w, self.base_h)
        self.init_ui()
        self.setFocus()
        self.center()

    def init_ui(self):
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setFixedWidth(self.base_w)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setObjectName("scroll")
        self.scroll_area.setStyleSheet(f"#scroll {{border: 0px;}}")

        self.base_widget = QWidget()
        self.scroll_area.setWidget(self.base_widget)

        self.base_layout = QVBoxLayout()
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)
        self.base_widget.setLayout(self.base_layout)

        self.fixed_widget = QWidget()
        self.fixed_widget.setFixedSize(self.base_w - 10, self.base_h)
        self.base_layout.addWidget(self.fixed_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.fixed_layout = QVBoxLayout()
        self.fixed_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_layout.setSpacing(0)
        self.fixed_widget.setLayout(self.fixed_layout)

        # DRAGABLE EVENT

        self.fixed_layout.addSpacerItem(QSpacerItem(0, 10))
        self.get_path_wid = DraggableLabel()
        self.get_path_wid.setFixedSize(self.base_w - 20, 100)
        self.get_path_wid.path_selected.connect(self.get_path_wid_cmd)
        self.fixed_layout.addWidget(self.get_path_wid)
        self.fixed_layout.addSpacerItem(QSpacerItem(0, 10))

        # SEARCH INPUT
        self.input_text = QLineEdit()
        self.input_text.setFixedSize(self.base_w - 20, 30)
        self.input_text.setStyleSheet("padding-left: 5px; border-radius: 5px;")
        self.input_text.setPlaceholderText("Вставьте имя файла")
        self.fixed_layout.addWidget(self.input_text)

        self.fixed_layout.addSpacerItem(QSpacerItem(0, 10))

        self.search_button = QPushButton("Поиск")
        self.search_button.setFixedWidth(self.base_w // 2)
        self.search_button.clicked.connect(self.btn_search_cmd)
        self.fixed_layout.addWidget(self.search_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.fixed_layout.addStretch()
        
        self.btns_widget = QWidget()
        self.base_layout.addWidget(self.btns_widget)

        self.btns_layout = QVBoxLayout()
        self.btns_layout.setContentsMargins(0, 0, 0, 0)
        self.btns_widget.setLayout(self.btns_layout)

        self.btns_count = 0

    def get_path_wid_cmd(self, value: str):
        self.path = value

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.btn_search_cmd()
        return super().keyPressEvent(a0)

    def remove_article_btns(self):
        self.btns_count = 0
        for i in reversed(range(self.btns_layout.count())):
            self.btns_layout.itemAt(i).widget().hide()
            self.btns_layout.itemAt(i).widget().close()
        self.setFixedSize(self.base_w, self.base_h)
        self.scroll_area.resize(self.base_w, self.base_h)

    def btn_search_cmd(self):
        try:
            self.btn_search_cmd_actions()
        except Exception:
            pass

    def btn_search_cmd_actions(self):
        self.temp_h = self.base_h
        self.remove_article_btns()
        self.setFocus()

        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.stop_flag = True

        if not self.path or not os.path.exists(self.path):
            lbl = QLabel ("Укажите место поиска")
            self.btns_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setFixedSize(self.base_w, self.base_h + 50)
            self.scroll_area.resize(self.base_w, self.base_h + 50)
            return

        text: str = self.input_text.text()

        if not text:
            lbl = QLabel ("Введите текст")
            self.btns_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setFixedSize(self.base_w, self.base_h + 50)
            self.scroll_area.resize(self.base_w, self.base_h + 50)
            return
        
        self.search_thread = SearchThread(self.path, text)
        self.search_thread.result.connect(self.add_article_btn)
        self.search_thread.finished.connect(self.finish_search)
        self.search_button.setText("Ищу...")
        self.search_thread.start()

    def finish_search(self):
        self.search_button.setText("Поиск")

        if self.btns_count == 0:
            lbl = QLabel ("Не найдено")
            self.btns_layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setFixedSize(self.base_w, self.base_h + 50)
            self.scroll_area.resize(self.base_w, self.base_h + 50)

    def add_article_btn(self, path):
        filename = os.path.basename(path)

        btn = QPushButton(filename, self)
        btn.clicked.connect(partial(self.article_btn_cmd, path))
        btn.setStyleSheet("text-align:left")
        btn.setFixedWidth(self.base_w - 20)
        self.btns_layout.addWidget(btn)
        self.btns_count += 1

        self.temp_h += 35

        if self.temp_h < 600:
            self.setFixedSize(self.base_w, self.temp_h)
            self.scroll_area.resize(self.base_w, self.temp_h)

    def article_btn_cmd(self, path: str):
        if os.path.exists(path):
            subprocess.run(["open", "-R", path])
        else:
            self.warning()

    def center(self):
        screens = QGuiApplication.screens()
        screen_geometry = screens[0].availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    
if __name__ == "__main__":
    # Cfg.check_files()

    if os.path.exists("lib"): 
        #lib folder appears when we pack this project to .app with py2app

        py_ver = sys.version_info
        py_ver = f"{py_ver.major}.{py_ver.minor}"

        plugin_path = os.path.join(
            "lib",
            f"python{py_ver}",
            "PyQt5",
            "Qt5",
            "plugins",
            )
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

    app = QApplication(sys.argv)
    app.setStyle('macos')
    
    window = SearchApp()
    window.show()

    sys.exit(app.exec())
