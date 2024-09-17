from datetime import datetime

from araviq6 import VideoFrameProcessor, VideoFrameWorker
from PySide6.QtCore import QEvent, QFileInfo, QObject, QPointF, Qt, Signal
from PySide6.QtGui import QCloseEvent, QResizeEvent
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QWidget

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
        # Unprocessed video frames are displayed here
        self._video_widget_raw = QVideoWidget()
        self._video_widget_raw.show()
        # Processed video frames are displayed here
        self._graphics_video_item = QGraphicsVideoItem()

        # Frame processing
        self._frame_worker = VideoFrameWorker()
        self._frame_processor = VideoFrameProcessor()
        self._frame_processor.setWorker(self._frame_worker)
        self._frame_processor.videoFrameProcessed.connect(lambda f: self._graphics_video_item.videoSink().setVideoFrame(f))

        self._video_sink_raw.videoFrameChanged.connect(lambda f: self._video_widget_raw.videoSink().setVideoFrame(f))
        self._video_sink_raw.videoFrameChanged.connect(self._frame_processor.processVideoFrame)
        
        self._graphics_scene = QGraphicsScene(self.ui.graphicsView)
        self._graphics_scene.addItem(self._graphics_video_item)
        self.ui.graphicsView.setScene(self._graphics_scene)

        self._player = QMediaPlayer(self)
        self._player.setVideoOutput(self._video_sink_raw)

        # Styling
        self._graphics_video_item.setCursor(Qt.CursorShape.CrossCursor)
        self._graphics_scene.setBackgroundBrush(Qt.GlobalColor.gray)

        self._graphics_video_item.nativeSizeChanged.connect(self.repositionScene)
        self._graphics_video_item.installEventFilter(self)
        self._player.metaDataChanged.connect(self._on_metadata_changed)

    def open_video(self, video: QFileInfo, start: datetime, undistorter):
        # Block signals so that frame processor doesnt get None as a frame
        self._video_sink_raw.blockSignals(True)
        self._player.setSource(video.filePath())
        self._video_sink_raw.blockSignals(False)
        self._player.pause()

        self.duration = None
        self._frame_worker.processArray = undistorter
        self.ui.labelVideoFileName.setText(video.fileName())
        self.start = start

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ui.graphicsView.fitInView(self._graphics_video_item, Qt.AspectRatioMode.KeepAspectRatio)
        return super().resizeEvent(event)
    
    def repositionScene(self):
        # Bring item's size to native video size so that the mouse position represents pixel in the video
        self._graphics_video_item.setSize(self._graphics_video_item.nativeSize())
        self.ui.graphicsView.fitInView(self._graphics_video_item, Qt.AspectRatioMode.KeepAspectRatio)
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        match event.type():
            case QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress:
                gsmp: QGraphicsSceneMouseEvent = event
                match gsmp.button():
                    case Qt.MouseButton.LeftButton:
                        self.mouse_pressed.emit(gsmp.pos())
        return super().eventFilter(watched, event)
    
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
