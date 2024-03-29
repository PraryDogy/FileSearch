import os
import subprocess
import sys
from functools import partial

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QVBoxLayout,
                             QWidget)

from catalog_mirgrate import CatalogMigrateThread
from catalog_search import catalog_search_file
from catalog_update import CatalogUpdateThread
from cfg import Cfg
from reveal_files import RevealFiles


class SearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Cfg.app_name)
        self.btns = []

        # self.setGeometry(100, 100, 300, 150)

        self.init_ui()
        self.setFocus()
        self.center()

        after = QTimer(self)
        after.setSingleShot(True)
        after.timeout.connect(self.error_check)
        after.start(300)

    def init_ui(self):
        self.v_layout = QVBoxLayout()

        self.h_layout = QHBoxLayout()
        self.v_layout.addLayout(self.h_layout)

        self.browse_btn = QPushButton("Обзор", self)
        self.browse_btn.clicked.connect(self.choose_catalog)
        self.h_layout.addWidget(self.browse_btn)

        self.browse_lbl = QLabel(Cfg.images_dir)
        self.h_layout.addWidget(self.browse_lbl)

        self.update_btn = QPushButton("Обновить базу данных", self)
        self.update_btn.clicked.connect(self.update_btn_cmd)
        
        self.input_text = QLineEdit(self)
        self.input_text.setPlaceholderText("Вставьте артикул или ссылку")
        
        self.search_button = QPushButton("Поиск", self)
        self.search_button.clicked.connect(partial(self.btn_search_cmd))
        
        self.v_layout.addWidget(self.update_btn)
        self.v_layout.addWidget(self.input_text)
        self.v_layout.addWidget(self.search_button)
        
        self.setLayout(self.v_layout)

    def error_check(self):
        if Cfg.first_load:
            self.gui_switch(setDisabled=True)
            self.warning(
                "Приложение обновлено\n"
                "Нажмите кнопку \"Обзор\" и укажите каталог изображений"
                )

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

    def gui_switch(self, setDisabled: bool):
        self.remove_article_btns()
        for i in (self.update_btn, self.input_text, self.search_button):
            i.setDisabled(setDisabled)

    def remove_article_btns(self):
        for i in self.btns:
            try:
                i: QPushButton
                i.deleteLater()
            except Exception:
                pass
        self.btns.clear()

    def update_btn_cmd(self):
        self.update_btn.setText("Подождите...")
        self.t1 = CatalogUpdateThread()
        self.t1.finished.connect(self.finalize_update_btn_cmd)
        self.t1.start()

    def finalize_update_btn_cmd(self):
        self.update_btn.setText("Обновить базу данных")
    
    def warning(self, text):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setText(text)
        message_box.exec()

    def btn_search_cmd(self):
        if not os.path.exists(Cfg.images_dir):
            self.warning("Сетевой диск не подключен")
            return

        self.remove_article_btns()
        self.setFocus()
        text: str = self.input_text.text()
        
        if not text or len(text) < 5:
            return

        if "miuz.ru" in text:
            text = text.strip("/").split("/")[-1]

        res: dict = catalog_search_file(text)

        if res:
            for name, src in res:
                btn = QPushButton(name, self)
                btn.clicked.connect(partial(self.article_btn_cmd, src))
                btn.setStyleSheet("text-align:left")
                self.v_layout.addWidget(btn)
                self.btns.append(btn)

    def article_btn_cmd(self, path: str):
        print("open", path)
        subprocess.run(["open", "-R", path])

        if not os.path.exists(Cfg.images_dir):
            self.warning("Сетевой диск не подключен")

        # RevealFiles(files_list=[path])

    def center(self):
        screens = QGuiApplication.screens()
        screen_geometry = screens[0].availableGeometry()
        window_geometry = self.frameGeometry()
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())
        

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
