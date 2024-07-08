import os
import subprocess
import sys

from PyQt5.QtCore import QEvent, Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import (QCloseEvent, QDragEnterEvent, QDragLeaveEvent, QDropEvent,
                         QGuiApplication, QKeyEvent, QIcon, QMouseEvent)
from PyQt5.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
                             QScrollArea, QSpacerItem, QVBoxLayout, QWidget, QFileDialog)

from cfg import Cfg


class SearchThread(QThread):
    found_file = pyqtSignal(str)
    finished = pyqtSignal()
    force_stop_thread = pyqtSignal()

    def __init__(self, path: str, filename: str):
        super().__init__()
        self.path = path
        self.filename = filename
        self.stop_flag = False
        self.force_stop_thread.connect(self.stop_thread)

    def stop_thread(self):
        self.stop_flag = True

    def run(self):
        self.stop_flag = False
        name_a = self.filename.lower()

        for root, dirs, files in os.walk(self.path):
            for file in files:

                name_b = file.lower()

                if name_a in name_b or name_a == name_b:
                    self.found_file.emit(os.path.join(root, file))

                if self.stop_flag:
                    return

        self.finished.emit()


class DraggableLabel(QLabel):
    path_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dashed_text = "Перетяните сюда папку или\nнажмите для выбора места поиска"
        self.selected_path = None
        self.setText(self.dashed_text)
        self.setAcceptDrops(True)
        self.setStyleSheet(self.dashed_border())
        self.setWordWrap(True)

    def dashed_border(self):
        return "border: 2px dashed gray; padding-left: 20px;; border-radius: 5px;"

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0.mimeData().hasUrls():
            self.setText(self.dashed_text)
            self.setStyleSheet(self.dashed_border())
            a0.accept()
        else:
            a0.ignore()
        return super().dragEnterEvent(a0)
    
    def dragLeaveEvent(self, a0: QDragLeaveEvent | None) -> None:
        if self.selected_path:
            self.setText(f"Место поиска:\n\n{self.selected_path}")
            self.setStyleSheet("border: none; padding-left: 5px;;")

        return super().dragLeaveEvent(a0)

    def dropEvent(self, a0: QDropEvent | None) -> None:
        path = a0.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(path):
            self.path_selected.emit(path)
            self.setStyleSheet("""
                               border: none;
                               padding-left: 5px;;
                               """)
            self.selected_path = path
            self.setText(f"Место поиска:\n\n{self.selected_path}")
            return super().dropEvent(a0)
        
    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() != Qt.MouseButton.LeftButton:
            return

        if not self.selected_path:
            direc = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            direc = self.selected_path

        dialog = QFileDialog(parent=self, directory=direc)
        dest = dialog.getExistingDirectory()

        if dest and os.path.isdir(dest):
            self.path_selected.emit(dest)
            self.setStyleSheet(
                """
                border: none;
                padding-left: 5px;
                """)
            self.selected_path = dest
            self.setText(f"Место поиска:\n\n{self.selected_path}")

        return super().mouseReleaseEvent(ev)
    
    def enterEvent(self, a0: QEvent | None) -> None:
        self.setText(self.dashed_text)
        self.setStyleSheet(
            f"""
            {self.dashed_border()};
            background-color: #656565;
            """)
        return super().enterEvent(a0)
    
    def leaveEvent(self, a0: QEvent | None) -> None:
        if self.selected_path:
            self.setText(f"Место поиска:\n\n{self.selected_path}")
            self.setStyleSheet(
                """
                border: none;
                background-color: transparent;
                padding-left: 5px;
                """)
        else:
            self.setStyleSheet(
                f"""
                {self.dashed_border()};
                background-color: transparent;
                """)
        return super().leaveEvent(a0)


class ChildWindow(QWidget):
    closed = pyqtSignal()
    change_title = pyqtSignal()

    def __init__(self, parent: QWidget, title: str):
        super().__init__()
        self.title = title
        self.change_title.connect(self.set_title)

        self.setMinimumSize(400, 215)
        self.move(parent.x() + parent.width() + 10, parent.y())

        scroll_layout = QVBoxLayout()
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        self.setLayout(scroll_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.horizontalScrollBar().setDisabled(True)
        scroll_layout.addWidget(self.scroll_area)

        in_scroll_widget = QWidget()
        self.scroll_area.setWidget(in_scroll_widget)

        self.base_layout = QVBoxLayout()
        self.base_layout.setContentsMargins(10, 0, 0, 0)
        in_scroll_widget.setLayout(self.base_layout)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))
        t = f"Идет поиск \"{title}\""
        self.main_title = QLabel(text=t)
        self.setWindowTitle(t)
        self.base_layout.addWidget(self.main_title)

    def add_btn(self, path: str):
        filename = os.path.basename(path)
        btn = QPushButton(text=filename)
        btn.setStyleSheet("QPushButton { text-align: left;}")
        self.base_layout.addWidget(btn)
        btn.clicked.connect(lambda: self.article_btn_cmd(path=path))

    def article_btn_cmd(self, path: str):
        if os.path.exists(path):
            subprocess.run(["open", "-R", path])

    def set_title(self):
        t = f"Результаты поиска: \"{self.title}\""
        self.main_title.setText(t)
        self.setWindowTitle(t)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.closed.emit()
        return super().closeEvent(a0)


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
        self.base_layout = QVBoxLayout()
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)
        self.setLayout(self.base_layout)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))

        self.get_path_wid = DraggableLabel()
        self.get_path_wid.setFixedSize(self.base_w - 20, 100)
        self.get_path_wid.path_selected.connect(self.get_path_wid_cmd)
        self.base_layout.addWidget(self.get_path_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))

        # SEARCH INPUT
        self.input_text = QLineEdit()
        self.input_text.setFixedSize(self.base_w - 20, 30)
        self.input_text.setStyleSheet("padding-left: 5px; border-radius: 5px;")
        self.input_text.setPlaceholderText("Вставьте имя файла")
        self.base_layout.addWidget(self.input_text)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))

        self.search_button = QPushButton("Поиск")
        self.search_button.setFixedWidth(self.base_w // 2)
        self.search_button.clicked.connect(self.btn_search_cmd)
        self.base_layout.addWidget(self.search_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btns_count = 0

    def get_path_wid_cmd(self, value: str):
        self.path = value

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.btn_search_cmd()
        return super().keyPressEvent(a0)

    def btn_search_cmd(self):
        if not self.path or not os.path.exists(self.path):
            print("Укажите место поиска")
            return

        text: str = self.input_text.text()

        if not text:
            print("Введите текст")
            return
        else:
            text = text.strip()

        self.child_win = ChildWindow(parent=self, title=text)
        self.child_win.show()

        self.search_thread = SearchThread(self.path, text)
        self.search_thread.found_file.connect(lambda path: self.child_win.add_btn(path=path))
        self.search_thread.finished.connect(self.child_win.change_title.emit)
        self.child_win.closed.connect(self.search_thread.force_stop_thread.emit)
        self.search_thread.start()


    def center(self):
        screens = QGuiApplication.screens()
        screen_geometry = screens[0].availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    
if __name__ == "__main__":
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

    if os.path.dirname(__file__) != "Resources":
        app.setWindowIcon(QIcon("icon/MiuzSearch.icns"))
    
    window = SearchApp()
    window.show()

    sys.exit(app.exec())
