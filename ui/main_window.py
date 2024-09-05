from datetime import datetime, timedelta

from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import QMainWindow

from videosync import intersection

from .uic.main_window import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        vid1 = QFileInfo('video/2024-09-05_14-26-47.277_cam1.mp4')
        vid2 = QFileInfo('video/2024-09-05_14-26-47.297_cam2.mp4')

        self.ready = [False] * 2

        self.v1_begin = datetime.strptime(vid1.completeBaseName()[:23], '%Y-%m-%d_%H-%M-%S.%f')
        self.v2_begin = datetime.strptime(vid2.completeBaseName()[:23], '%Y-%m-%d_%H-%M-%S.%f')

        self.ui.cam1.open_video(vid1, self.v1_begin)
        self.ui.cam2.open_video(vid2, self.v2_begin)

        self.ui.cam1.duration_available.connect(lambda: self.on_duration_available(0))
        self.ui.cam2.duration_available.connect(lambda: self.on_duration_available(1))
        self.ui.horizontalSlider.valueChanged.connect(self.on_slider_changed)
        self.ui.horizontalSlider.setSingleStep(33)

    def on_duration_available(self, vid):
        self.ready[vid] = True
        if all(self.ready):
            self.start, self.end = intersection(self.v1_begin, self.v2_begin, self.ui.cam1.duration, self.ui.cam2.duration)
            self.duration = self.end - self.start
            self.ui.horizontalSlider.setMaximum(round(self.duration.total_seconds() * 1000))

    def go_to(self, dt):
        self.ui.cam1.go_to(dt)
        self.ui.cam2.go_to(dt)

    def on_slider_changed(self, value):
        dt = self.start + timedelta(milliseconds=value)
        print(dt)
        self.go_to(dt)