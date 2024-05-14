import os
import subprocess
import sys
from functools import partial

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication, QKeyEvent
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QSpacerItem, QVBoxLayout,
                             QWidget)

from catalog_mirgrate import CatalogMigrateThread
from catalog_search import catalog_search_file
from catalog_update import CatalogUpdateThread
from cfg import Cfg


class Warning(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setFixedSize(320, 90)
        self.setWindowTitle("Каталог недоступен")

        self.init_ui()

        main_window_pos = parent.pos()
        main_window_rect = parent.geometry()
        center_x = main_window_pos.x() + main_window_rect.width() // 2
        center_y = main_window_pos.y() + main_window_rect.height() // 2
        self.move(center_x - self.width() // 2, center_y - self.height() // 2)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 5, 15, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        lbl = QLabel("Каталог недоступен.\nНажмите кнопку \"Обзор\" и укажите каталог")
        main_layout.addWidget(lbl)

        btn = QPushButton("Понятно", self)
        btn.setFixedWidth(100)
        btn.clicked.connect(self.deleteLater)
        main_layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)



class SearchApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(Cfg.app_name)
        self.base_w, self.base_h = 290, 210
        self.setFixedSize(self.base_w, self.base_h)
        self.init_ui()
        self.setFocus()
        self.center()

        after = QTimer(self)
        after.setSingleShot(True)
        after.timeout.connect(self.error_check)
        after.start(300)

    def init_ui(self):
        self.base_layout = QVBoxLayout()
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)
        self.setLayout(self.base_layout)

        self.fixed_widget = QWidget()
        self.fixed_widget.setFixedSize(self.base_w - 10, self.base_h)
        self.base_layout.addWidget(self.fixed_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.fixed_layout = QVBoxLayout()
        self.fixed_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_layout.setSpacing(0)
        self.fixed_widget.setLayout(self.fixed_layout)

        # BROWSE CATALOG PATH
        self.browse_cat_layout = QHBoxLayout()
        self.browse_cat_layout.setContentsMargins(0, 0, 0, 0)
        self.browse_cat_layout.setSpacing(0)
        self.fixed_layout.addLayout(self.browse_cat_layout)

        self.browse_btn = QPushButton("Обзор", self)
        self.browse_btn.setFixedWidth(70)
        self.browse_btn.clicked.connect(self.choose_catalog)
        self.browse_cat_layout.addWidget(self.browse_btn)

        self.browse_cat_layout.addSpacerItem(QSpacerItem(10, 0))

        self.browse_lbl = QLabel(Cfg.images_dir)
        self.browse_lbl.setWordWrap(True)
        self.set_browse_lbl_h()
        self.browse_cat_layout.addWidget(self.browse_lbl)

        # UPDATE CATALOG JSON
        self.update_btn = QPushButton("Обновить каталог")
        self.update_btn.clicked.connect(self.update_btn_cmd)
        self.update_btn.setFixedWidth(150)
        self.fixed_layout.addWidget(self.update_btn)

        # SEARCH INPUT
        self.input_text = QLineEdit()
        self.input_text.setFixedHeight(30)
        self.input_text.setStyleSheet(
            f"""
            padding-left: 5px;
            border-radius: 5px;
            """)
        self.input_text.setPlaceholderText("Вставьте артикул или ссылку")
        self.input_text.mouseReleaseEvent = self.select_all_text
        self.fixed_layout.addWidget(self.input_text)

        # SEARCH BUTTON
        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(partial(self.btn_search_cmd))
        self.fixed_layout.addWidget(self.search_button)
        
        self.btns_widget = QWidget()
        self.base_layout.addWidget(self.btns_widget)

        self.btns_layout = QVBoxLayout()
        self.btns_widget.setLayout(self.btns_layout)

        self.base_layout.addStretch()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self.btn_search_cmd()
        return super().keyPressEvent(a0)

    def select_all_text(self, e):
        if not self.input_text.hasFocus():
            self.input_text.selectAll()

    def error_check(self):
        if Cfg.first_load:
            self.warning()

    def choose_catalog(self):
        new_dir = QFileDialog.getExistingDirectory(self)

        if new_dir:
            old_dir = Cfg.images_dir
            Cfg.images_dir = new_dir
            Cfg.first_load = False
            Cfg.write_cfg_json_file()

            self.migrate_thread = CatalogMigrateThread(old_dir, new_dir)
            self.migrate_thread.finished.connect(self.finalize_choose_catalog)
            self.migrate_thread.start()

    def finalize_choose_catalog(self):
        self.gui_switch(setDisabled=False)
        self.browse_lbl.setText(Cfg.images_dir)
        self.set_browse_lbl_h()

    def gui_switch(self, setDisabled: bool):
        self.remove_article_btns()
        for i in (self.update_btn, self.input_text, self.search_button):
            i.setDisabled(setDisabled)

    def remove_article_btns(self):
        for i in reversed(range(self.btns_layout.count())):
            self.btns_layout.itemAt(i).widget().close()

    def update_btn_cmd(self):
        self.update_btn.setText("Подождите...")
        self.t1 = CatalogUpdateThread()
        self.t1.finished.connect(self.finalize_update_btn_cmd)
        self.t1.start()

    def finalize_update_btn_cmd(self):
        self.update_btn.setText("Обновить базу данных")
    
    def warning(self):
        self.gui_switch(setDisabled=True)
        self.win = Warning(self)
        self.win.show()

    def btn_search_cmd(self):
        if not os.path.exists(Cfg.images_dir):
            self.warning()
            return

        self.remove_article_btns()
        self.setFocus()
        text: str = self.input_text.text()
        
        if "miuz.ru" in text:
            text = text.strip("/").split("/")[-1]

        if not text or len(text) < 5:
            lbl = QLabel ("Не найдено")
            self.btns_layout.addWidget(lbl)
            self.setFixedSize(self.base_w, self.base_h + 20)
            return

        res: dict = catalog_search_file(text)

        if res:
            advanved_size = 0
            for name, src in res:
                btn = QPushButton(name, self)
                btn.clicked.connect(partial(self.article_btn_cmd, src))
                btn.setStyleSheet("text-align:left")
                self.btns_layout.addWidget(btn)
                advanved_size += btn.height() + 20

            
            self.setFixedSize(self.base_w, self.base_h + advanved_size)

        elif not res:
            lbl = QLabel ("Не найдено")
            self.btns_layout.addWidget(lbl)
            self.setFixedSize(self.base_w, self.base_h + 20)


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

    def set_browse_lbl_h(self):
        lbl_h = 30
        num_lines = self.browse_lbl.text().count('\n') + 1
        self.browse_lbl.setFixedHeight(lbl_h * num_lines)
    
if __name__ == "__main__":
    Cfg.check_files()

    if os.path.exists("lib"): 
        #lib folder appears when we pack this project to .app with py2app

        py_ver = sys.version_info
        py_ver = f"{py_ver.major}.{py_ver.minor}"

        plugin_path = os.path.join(
            "lib",
            f"python{py_ver}",
            "PyQt6",
            "Qt6",
            "plugins",
            )
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

    app = QApplication(sys.argv)
    app.setStyle('macos')
    
    window = SearchApp()
    window.show()

    sys.exit(app.exec())
