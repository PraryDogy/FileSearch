from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
import sys

class Test(QWidget):
    def __init__(self):
        super().__init__()

        self.v_layout = QVBoxLayout()
        self.setLayout(self.v_layout)

        self.test_btn = QPushButton("Тест")
        self.test_btn.setFixedWidth(140)
        self.test_btn.setStyleSheet("text-align: center;")
        self.test_btn.clicked.connect(self.start_timer)
        self.v_layout.addWidget(self.test_btn)

        self.my_timer = QTimer(self)
        self.my_timer.timeout.connect(self.change_text)

        self.count = 0

    def change_text(self):
        if self.test_btn.text().count(".") == 3:
            self.test_btn.setText("Тест")
        else:
            self.test_btn.setText(" " + self.test_btn.text() + ".")

        self.count += 1
        # if self.count == 16:
        #     self.my_timer.stop()

    def start_timer(self):
        self.my_timer.start(300)


app = QApplication(sys.argv)
widget = Test()
widget.show()

app.exec_()