import os
import subprocess

from PyQt6.QtCore import QObject, pyqtSignal


class RevealFiles(QObject):
    finished = pyqtSignal()

    def __init__(self, files_list: list) -> None:
        super().__init__()

        reveal_script = "reveal_files.scpt"
        
        command = ["osascript", reveal_script] + files_list
        # subprocess.run(command)
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.finished.emit()