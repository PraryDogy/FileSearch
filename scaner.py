import os
import json
from collections import defaultdict
from cfg import Cfg
from PyQt6.QtCore import QThread, pyqtSignal


class Scaner(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        exts = (".png", ".tif", ".tiff", ".psd", ".psb", ".jpg", ".jpeg")
        data = defaultdict(list)

        for root, dirs, files in os.walk(Cfg.data["catalog"]):

            files = [
                i
                for i in files
                if i.lower().endswith(exts)
                ]

            if len(files) == 0:
                continue

            for file in files:
                src = os.path.join(root, file)
                filename = os.path.split(src)[-1].split(".")[0]
                data[filename].append(src)

        with open(Cfg.catalog_json_file, "w", encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2)

        self.finished.emit()