from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from PySide6.QtCore import QFileInfo, QPointF, Signal
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import QMainWindow

from videosync import intersection

from .uic.main_window import Ui_MainWindow


class MainWindow(QMainWindow):

    closed = Signal()
    both_frames_clicked = Signal(datetime, QPointF, QPointF)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon('res/coordinates.png'))

        self.cams = self.ui.cam1, self.ui.cam2

        for i, cam in enumerate(self.cams):
            cam.loaded.connect(self.on_duration_available)
            cam.mouse_pressed.connect(lambda click_pos, i=i: self._handle_click(i, click_pos))

        self.ui.horizontal_slider.valueChanged.connect(self._on_slider_value_changed)
        self.ui.horizontal_slider.setSingleStep(1000)

    def open_files(self, videos: Sequence[str], undistorters: Sequence[Callable]):
        self.clicked_points = defaultdict(lambda: [None, None])

        for video, cam, undistorter in zip(videos, self.cams, undistorters):
            video_file_info = QFileInfo(video)
            if not video_file_info.exists():
                raise FileExistsError(video)
            
            video_start = datetime.strptime(video_file_info.completeBaseName()[:23], '%Y-%m-%d_%H-%M-%S.%f')
            cam.open_video(video_file_info, video_start, undistorter)

    def on_duration_available(self):
        # Check if all videos are loaded
        for cam in self.cams:
            if cam.duration is None:
                return

        starts = self.ui.cam1.start, self.ui.cam2.start
        ends = timedelta(milliseconds=self.ui.cam1.duration), timedelta(milliseconds=self.ui.cam2.duration)
        self.start, self.end = intersection(starts, ends)
        
        self.duration = self.end - self.start
        self.ui.horizontal_slider.setMaximum(round(self.duration.total_seconds() * 1000))
        self.current = self.start + timedelta(milliseconds=self.ui.horizontal_slider.value())
        self._go_to(self.current)
        self.ui.horizontal_slider.setValue(0)

    def _go_to(self, dt: datetime):
        self.ui.cam1.go_to(dt)
        self.ui.cam2.go_to(dt)

    def _on_slider_value_changed(self, value):
        self.current = self.start + timedelta(milliseconds=value)
        print(self.current)
        self._go_to(self.current)

    def closeEvent(self, event: QCloseEvent):
        self.closed.emit()
        return super().closeEvent(event)
    
    def _handle_click(self, cam_id: str, click_pos: QPointF):
        self.clicked_points[self.current][cam_id] = click_pos

        # Send signal only if both frames have been clicked
        if None in self.clicked_points[self.current]:
            return

        self.both_frames_clicked.emit(self.current, *self.clicked_points[self.current])
