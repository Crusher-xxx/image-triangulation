import json
from datetime import datetime, timedelta

import numpy as np
from PySide6.QtCore import QFileInfo, Signal
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow

from videosync import intersection

from .uic.main_window import Ui_MainWindow


class MainWindow(QMainWindow):

    closed = Signal()

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon('res/coordinates.png'))

        self.ui.cam1.loaded.connect(lambda: self.on_duration_available(0))
        self.ui.cam2.loaded.connect(lambda: self.on_duration_available(1))
        self.ui.horizontalSlider.valueChanged.connect(self.on_slider_changed)
        self.ui.horizontalSlider.setSingleStep(1000)

        self.open_file('video/test.json')

    def open_file(self, json_file_path: str):
        json_file_info = QFileInfo(json_file_path)
        with open(json_file_path) as f:
            data = json.load(f)

        self.ready = [False] * len(data)

        cams = self.ui.cam1, self.ui.cam2
        for cam_name, cam in zip(data, cams):
            video_file_info = QFileInfo(json_file_info.dir(), data[cam_name]['file'])
            video_start = datetime.strptime(video_file_info.completeBaseName()[:23], '%Y-%m-%d_%H-%M-%S.%f')
            fx = data[cam_name]['fx']
            fy = data[cam_name]['fy']
            cx = data[cam_name]['cx']
            cy = data[cam_name]['cy']
            cam_mtx = np.array([
                [fx, 0, cx],
                [0, fy, cy],
                [0, 0, 1]
            ])
            distortion_coeffs = np.array(data[cam_name]['distortion_coeffs'])
            cam.open_video(video_file_info, video_start, cam_mtx, distortion_coeffs)

    def on_duration_available(self, vid):
        self.ready[vid] = True
        if all(self.ready):
            self.start, self.end = intersection(self.ui.cam1.start, self.ui.cam2.start,
                                                self.ui.cam1.duration, self.ui.cam2.duration)
            self.duration = self.end - self.start
            self.ui.horizontalSlider.setMaximum(round(self.duration.total_seconds() * 1000))
            self.go_to(self.start)

    def go_to(self, dt):
        self.ui.cam1.go_to(dt)
        self.ui.cam2.go_to(dt)

    def on_slider_changed(self, value):
        dt = self.start + timedelta(milliseconds=value)
        print(dt)
        self.go_to(dt)

    def closeEvent(self, event: QCloseEvent):
        self.closed.emit()
        return super().closeEvent(event)
