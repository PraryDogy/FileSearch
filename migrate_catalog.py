import json
from collections import defaultdict

from PyQt6.QtCore import QThread, pyqtSignal

from cfg import Cfg


class MigrateCatalog(QThread):
    finished = pyqtSignal()

    def __init__(self, old_dir: str, new_dir: str):
        super().__init__()
        self.old_dir = old_dir
        self.new_dir = new_dir
            
    def run(self):
        data: dict = Cfg.read_catalog_json_file()
        new_data = defaultdict(list)

        for k, v in data.items():
            for i in v:
                i: str = i.replace(self.old_dir, self.new_dir)
                new_data[k].append(i)

        Cfg.write_catalog_json_file(new_data)
        self.finished.emit()