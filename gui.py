import json
import os
import subprocess
import sys
from functools import partial

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (QApplication, QFileDialog, QLineEdit, QMessageBox,
                             QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel)

from cfg import Cfg
from migrate_catalog import MigrateCatalog
from reveal_files import RevealFiles
from scaner import Scaner
from search_file import search_file


class SearchApp(QWidget):
    def __init__(self):
        Cfg
        super().__init__()
        self.setWindowTitle(Cfg.app_name)
        self.setGeometry(100, 100, 300, 150)
        
        self.v_layout = QVBoxLayout()

        self.h_layout = QHBoxLayout()
        self.v_layout.addLayout(self.h_layout)

        self.browse_btn = QPushButton("Обзор", self)
        self.browse_btn.clicked.connect(self.choose_catalog)
        self.h_layout.addWidget(self.browse_btn)

        self.browse_lbl = QLabel(Cfg.data["catalog"])
        self.h_layout.addWidget(self.browse_lbl)

        self.update_btn = QPushButton("Обновить базу данных", self)
        self.update_btn.clicked.connect(self.update_db)
        
        self.input_text = QLineEdit(self)
        self.input_text.setPlaceholderText("Вставьте артикул или ссылку")
        
        
        self.search_button = QPushButton("Поиск", self)
        self.search_button.clicked.connect(partial(self.btn_search_cmd))
        # self.search_button.mouseReleaseEvent = lambda e: self.search()
        
        self.v_layout.addWidget(self.update_btn)
        self.v_layout.addWidget(self.input_text)
        self.v_layout.addWidget(self.search_button)
        
        self.setLayout(self.v_layout)
        self.setFocus()

        self.btns = []
        self.center()

        self.catalog_check()

    def catalog_check(self):
        if Cfg.data["first"]:
            new_dir = QFileDialog.getExistingDirectory(self)

            if new_dir:
                old_dir = Cfg.data["catalog"]

                Cfg.data["catalog"] = new_dir
                Cfg.data["first"] = False
                with open(Cfg.cfg_json_dir, "w", encoding="utf=8") as file:
                    json.dump(Cfg.data, file, ensure_ascii=False, indent=2)

            self.migrate_thread = MigrateCatalog(old_dir, new_dir)
            self.migrate_thread.finished.connect(self.finalize_migrate)
            self.setDisabled(True)
            self.migrate_thread.start()

    def update_db(self):
        self.update_btn.setText("Подождите...")
        self.t1 = Scaner()
        self.t1.finished.connect(self.finalize_update_db)
        self.t1.start()

    def finalize_update_db(self):
        self.setDisabled(False)
        self.update_btn.setText("Обновить базу данных")
    
    def warning(self):
        message_box = QMessageBox()
        message_box.setIcon(QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Предупреждение")
        message_box.setText("Сетевой диск не подключен")
        message_box.exec()

    def btn_search_cmd(self):
        if not os.path.exists(Cfg.data["catalog"]):
            self.warning()
            return

        for i in self.btns:
            try:
                i.deleteLater()
            except RuntimeError:
                pass

        self.setFocus()
        text: str = self.input_text.text()

        if "miuz.ru" in text:
            text = text.strip("/").split("/")[-1]
        
        if not text or len(text) < 5:
            return

        res: dict = search_file(text)

        if res:
            for name, src in res:
                btn = QPushButton(name, self)
                btn.clicked.connect(partial(self.open_btn, src))
                btn.setStyleSheet("text-align:left")
                self.v_layout.addWidget(btn)

                self.btns.append(btn)

        self.setFocus()

    def open_btn(self, path: str):
        print("open", path)
        subprocess.run(["open", "-R", path])

        if not os.path.exists(Cfg.data["catalog"]):
            self.warning()
            return

        # RevealFiles(files_list=[path])

    def center(self):
        # Получаем список экранов
        screens = QGuiApplication.screens()

        # Получаем геометрию первого экрана
        screen_geometry = screens[0].availableGeometry()

        # Получаем размеры окна
        window_geometry = self.frameGeometry()

        # Центрируем окно по центру экрана
        window_geometry.moveCenter(screen_geometry.center())
        self.move(window_geometry.topLeft())
        
    def choose_catalog(self):
        new_dir = QFileDialog.getExistingDirectory(self)

        if new_dir:
            old_dir = Cfg.data["catalog"]
            Cfg.data["catalog"] = new_dir
            self.browse_lbl.setText(new_dir)

            with open(Cfg.cfg_json_dir, "w", encoding="utf=8") as file:
                json.dump(Cfg.data, file, ensure_ascii=False, indent=2)

            self.migrate_thread = MigrateCatalog(old_dir, new_dir)
            self.migrate_thread.finished.connect(self.finalize_migrate)
            self.setDisabled(True)
            self.migrate_thread.start()

    def finalize_migrate(self):
        self.setDisabled(False)

if __name__ == "__main__":
    Cfg.check()

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
    
    # Установка системного стиля для macOS
    app.setStyle('macos')
    
    window = SearchApp()
    window.show()
    sys.exit(app.exec())
