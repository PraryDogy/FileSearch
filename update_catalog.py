import os
import json
from collections import defaultdict
from cfg import Cfg
from PyQt6.QtCore import QThread, pyqtSignal


class UpdateCatalogThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        exts = (".png", ".tif", ".tiff", ".psd", ".psb", ".jpg", ".jpeg")
        new_data = defaultdict(list)

        for root, dirs, files in os.walk(Cfg.images_dir):

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
                new_data[filename].append(src)

        Cfg.write_catalog_json_file(new_data)
        self.finished.emit()