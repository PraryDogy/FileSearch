import os
import subprocess
import sys
from time import sleep

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import (QCloseEvent, QDragEnterEvent, QDropEvent,
                         QGuiApplication, QIcon, QKeyEvent, QMouseEvent)
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QListWidgetItem,
                             QPushButton, QSpacerItem, QVBoxLayout, QWidget)

from cfg import Cfg


def get_finder_path():
    script = '''
    tell application "Finder"
        if (count of Finder windows) is not 0 then
            set thePath to (target of front window) as alias
            return POSIX path of thePath
        else
            return "No Finder window open"
        end if
    end tell
    '''
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output.decode('utf-8').strip()


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
                    sleep(0.5)

                if self.stop_flag:
                    return

        self.finished.emit()


class DraggableLabel(QWidget):
    path_selected_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.selected_path = None
        self.setAcceptDrops(True)

        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.v_layout)

        h_wid = QWidget(parent=self)
        self.v_layout.addWidget(h_wid)

        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_wid.setLayout(h_layout)

        self.browse_btn = QPushButton(parent=self, text="Обзор")
        self.browse_btn.clicked.connect(self.browse_cmd)
        h_layout.addWidget(self.browse_btn)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.finder_btn = QPushButton(parent=self, text="Получить из Finder")
        self.finder_btn.clicked.connect(self.finder_cmd)
        h_layout.addWidget(self.finder_btn)

        self.path_label = QLabel(text="Укажите место поиска")
        self.path_label.setStyleSheet("padding-left: 6px;")
        self.path_label.setWordWrap(True)
        self.v_layout.addWidget(self.path_label)

        self.v_layout.addStretch()

    def finder_cmd(self, event):
        path = get_finder_path()
        
        if os.path.isdir(path):
            self.path_selected_signal.emit(path)
            self.selected_path = path
            self.path_label.setText(self.selected_path)

    def dashed_border(self):
        return "border: 2px dashed gray; padding-left: 5px;; border-radius: 5px;"

    def dragEnterEvent(self, a0: QDragEnterEvent | None) -> None:
        if a0.mimeData().hasUrls():
            a0.accept()
        else:
            a0.ignore()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0: QDropEvent | None) -> None:
        path = a0.mimeData().urls()[0].toLocalFile()
        if os.path.isdir(path):
            self.path_selected_signal.emit(path)
            self.selected_path = path
            self.path_label.setText(self.selected_path)
            return super().dropEvent(a0)
        
    def browse_cmd(self, ev: QMouseEvent | None) -> None:
        if not self.selected_path:
            direc = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            direc = self.selected_path

        dialog = QFileDialog(parent=self, directory=direc)
        dest = dialog.getExistingDirectory()

        if dest and os.path.isdir(dest):
            self.path_selected_signal.emit(dest)
            self.selected_path = dest
            self.path_label.setText(self.selected_path)


class ChildWindow(QWidget):
    closed = pyqtSignal()
    change_title = pyqtSignal()

    def __init__(self, parent: QWidget, title: str):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Поиск: " + f"\"{title}\"")
        self.title = title
        self.change_title.connect(self.set_title)

        self.setMinimumSize(400, 380)
        geo = self.geometry()
        geo.moveCenter(parent.geometry().center())
        self.setGeometry(geo)

        self.v_layout = QVBoxLayout()
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.v_layout)

        self.v_layout.addSpacerItem(QSpacerItem(0, 5))

        self.v_layout.addSpacerItem(QSpacerItem(0, 5))
        self.main_title = QLabel(parent=self)
        self.main_title.setStyleSheet("padding-left: 5px;")
        self.v_layout.addWidget(self.main_title)
        self.v_layout.addSpacerItem(QSpacerItem(0, 5))

        self.list_widget = QListWidget(parent=self)
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.verticalScrollBar().setSingleStep(15)
        self.v_layout.addWidget(self.list_widget)

        self.dots_count = 0
        self.dynamic_text()

    def dynamic_text(self):
        if "Результаты" in self.main_title.text():
            return

        t = f"Идет поиск: \"{self.title}\"" + " " + "." * self.dots_count
        self.dots_count += 1

        self.main_title.setText(t)

        if self.dots_count > 10:
            self.dots_count = 0

        QTimer.singleShot(200, self.dynamic_text)

    def add_btn(self, path: str):
        filename = os.path.basename(path)

        wid = QLabel(text=filename)
        wid.setStyleSheet("padding-left: 5px;")
        wid.setFixedHeight(25)
        list_item = QListWidgetItem()

        list_item.setSizeHint(wid.sizeHint())
        self.list_widget.addItem(list_item)
        self.list_widget.setItemWidget(list_item, wid)

        wid.mouseReleaseEvent = lambda e: self.article_btn_cmd(widget=wid, path=path)

    def article_btn_cmd(self, widget: QLabel, path: str):
        widget.setStyleSheet("background-color: #a7a7a7; padding-left: 5px;")
        QTimer.singleShot(200, lambda: widget.setStyleSheet("padding-left: 5px;"))
        if os.path.exists(path):
            subprocess.run(["open", "-R", path])

    def set_title(self):
        t = f"Результаты поиска: \"{self.title}\""
        self.main_title.setText(t)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.closed.emit()
        return super().closeEvent(a0)
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.closed.emit()
            self.close()
        return super().keyPressEvent(a0)


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
        self.get_path_wid.path_selected_signal.connect(self.get_path_wid_cmd)
        self.base_layout.addWidget(self.get_path_wid, alignment=Qt.AlignmentFlag.AlignCenter)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))

        # SEARCH INPUT
        self.input_text = QLineEdit()
        self.input_text.setFixedSize(self.base_w - 20, 30)
        self.input_text.setStyleSheet("padding-left: 5px;")
        self.input_text.setPlaceholderText("Вставьте имя файла")
        self.base_layout.addWidget(self.input_text)

        self.base_layout.addSpacerItem(QSpacerItem(0, 10))

        self.search_button = QPushButton("Поиск")
        self.search_button.setFixedWidth(self.base_w // 2)
        self.search_button.clicked.connect(self.btn_search_cmd)
        self.base_layout.addWidget(self.search_button, alignment=Qt.AlignmentFlag.AlignCenter)

        self.btns_count = 0

    def input_default_style(self):
        self.input_text.setStyleSheet("padding-left: 5px;")

    def input_selected_style(self):
        self.input_text.setStyleSheet("padding-left: 5px; background-color: #a7a7a7;")

    def get_path_wid_cmd(self, value: str):
        self.path = value

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.btn_search_cmd()
        return super().keyPressEvent(a0)

    def btn_search_cmd(self):
        if not self.path or not os.path.exists(self.path):
            return

        text: str = self.input_text.text()

        if not text:
            self.input_selected_style()
            QTimer.singleShot(300, self.input_default_style)
            return
        else:
            text = text.strip()

        self.child_win = ChildWindow(parent=self, title=text)
        self.child_win.show()

        self.search_thread = SearchThread(self.path, text)
        self.search_thread.found_file.connect(lambda path: self.child_win.add_btn(path=path))
        self.search_thread.finished.connect(self.child_win.change_title.emit)
        self.child_win.closed.connect(lambda: self.cancel_search(self.search_thread))
        self.search_thread.start()

    def cancel_search(self, task: SearchThread):
        if task.isRunning():
            task.force_stop_thread.emit()

    def center(self):
        screens = QGuiApplication.screens()
        screen_geometry = screens[0].availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())

    
if os.path.exists("lib"): 
    #lib folder appears when we pack this project to .app with py2app
    plugin_path = "lib/python3.11/PyQt5/Qt5/plugins"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

else:
    plugin_path = "env/lib/python3.11/site-packages/PyQt5/Qt5/plugins"
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

app = QApplication(sys.argv)
app.setStyle('macos')

if os.path.dirname(__file__) != "Resources":
    app.setWindowIcon(QIcon("icon/MiuzSearch.icns"))

window = SearchApp()
window.show()

app.exec_()
