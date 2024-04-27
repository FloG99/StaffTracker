from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QDesktopWidget, QSizePolicy
from PyQt5.QtCore import Qt, QCoreApplication, QTimer
from PyQt5.QtGui import QFontDatabase, QFont, QCursor
import datetime
import json
import requests
import os

staff_states = {}

# Load config
def read_config(filename):
    with open(filename, 'r') as file:
        return json.load(file)
config = read_config('config.json')

def get_greeting():
    now = datetime.datetime.now()
    current_hour = now.hour
    for greeting in config["greetings"]:
        if greeting["start"] <= current_hour < greeting["end"]:
            return greeting["message"]
    return config["greetings"][-1]["message"]

def get_nickname(staffID):
    return config["staff"][staffID]["nickname"]

class MainWindow(QMainWindow):
    def __init__(self, staffID):
        super().__init__()
        self.setWindowTitle("Staff Tracker")
        self.resize(600, 0)
        self.center()

        widget = QWidget()
        widget.setStyleSheet("background-color: #222222;")
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 10, 10, 70)
        src_path,_ = os.path.split(os.path.realpath(__file__))
        fontID = QFontDatabase.addApplicationFont(os.path.join(src_path, "resources/Rubik-VariableFont_wght.ttf"))
        print(fontID, QFontDatabase.applicationFontFamilies(fontID))
        font = QFontDatabase.applicationFontFamilies(fontID)[0]
        font40 = QFont(font, 40)
        font20 = QFont(font, 20)
        t1 = QLabel(f"{get_greeting()},\n{get_nickname(staffID)}")
        t1.setFont(font40)
        t1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        t1.setContentsMargins(0, 10, 0, 50)
        layout.addWidget(t1)

        for action in config["actions"]:
            if staff_states.get(staffID, 0) not in action["requiredState"]:
                continue
            button = QPushButton(action["text"])    
            button.setStyleSheet("background-color: #6000FF; border: 1px solid white; border-radius: 3px; color: white;")
            button.setFont(font20)
            button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
            button.setFixedSize(300, 50)
            button.setContentsMargins(30, 40, 30, 40)
            button.setCursor(QCursor(Qt.PointingHandCursor))
            button.clicked.connect(lambda click, staffID=staffID, state=action["state"]: self.action_clicked(staffID, state))
            layout.addWidget(button)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def center(self):
        screen_geometry = QDesktopWidget().screenGeometry()
        position = screen_geometry.center() - self.rect().center()
        position.setY(0)
        self.move(position)

    def action_clicked(self, staffID, state):
        staff_states[staffID] = state
        send_api_signal()
        print("Quit")
        close(self)

def send_api_signal():
    requests.post(config["api"]["url"])

def close(window):
    window.close()
    QCoreApplication.instance().quit()

def open(staffID):
    app = QApplication([])
    window = MainWindow(staffID)
    window.show()
    QTimer.singleShot(10000, lambda window=window: close(window)) # auto-close after 10 seconds
    app.exec()

