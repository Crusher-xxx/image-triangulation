from datetime import datetime

from araviq6 import VideoFrameProcessor, VideoFrameWorker
from PySide6.QtCore import QFileInfo, QPointF, Qt, Signal
from PySide6.QtGui import QCloseEvent, QResizeEvent
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
from PySide6.QtWidgets import QGraphicsScene, QWidget

from .graphicsvideoitem import GraphicsVideoItem
from .uic.video_player import Ui_VideoPlayer


class VideoPlayer(QWidget):
    loaded = Signal()
    mouse_pressed = Signal(QPointF)

    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_VideoPlayer()
        self.ui.setupUi(self)

        # Unprocessed video frames go here
        self._video_sink_raw = QVideoSink()
        # Processed video frames are displayed here
        self._graphics_video_item = GraphicsVideoItem()

        # Frame processing
        self._frame_worker = VideoFrameWorker()
        self._frame_processor = VideoFrameProcessor()
        self._frame_processor.setWorker(self._frame_worker)
        self._frame_processor.videoFrameProcessed.connect(lambda f: self._graphics_video_item.videoSink().setVideoFrame(f))

        self._video_sink_raw.videoFrameChanged.connect(self._frame_processor.processVideoFrame)
        
        self._graphics_scene = QGraphicsScene(self.ui.graphicsView)
        self._graphics_scene.addItem(self._graphics_video_item)
        self.ui.graphicsView.setScene(self._graphics_scene)

        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._video_sink_raw)

        # Styling
        self._graphics_scene.setBackgroundBrush(Qt.GlobalColor.gray)

        self._graphics_video_item.nativeSizeChanged.connect(self.fit2video)
        self._player.metaDataChanged.connect(self._on_metadata_changed)
        self._graphics_video_item.mouse_pressed.connect(self.mouse_pressed.emit)

    def open_video(self, video: QFileInfo, start: datetime, undistorter):
        # Block signals so that frame processor doesn't get None as a frame
        self._video_sink_raw.blockSignals(True)
        self._player.setSource(video.filePath())
        self._video_sink_raw.blockSignals(False)
        self._player.pause()

        self.duration = None
        self._frame_worker.processArray = undistorter
        self.ui.labelVideoFileName.setText(video.fileName())
        self.start = start

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.fit2video()
        return super().resizeEvent(event)
    
    def fit2video(self):
        self.ui.graphicsView.fitInView(self._graphics_video_item, Qt.AspectRatioMode.KeepAspectRatio)
    
    def _on_metadata_changed(self):
        self.duration = self._player.duration()
        self.loaded.emit()

    def go_to(self, dt: datetime):
        target = dt - self.start
        pos = round(target.total_seconds() * 1000)
        self._player.setPosition(pos)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._frame_processor.stop()
        return super().closeEvent(event)
