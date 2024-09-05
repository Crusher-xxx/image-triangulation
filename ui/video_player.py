from datetime import datetime

from PySide6.QtCore import QEvent, QFileInfo, QObject, Qt, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QWidget

from .uic.video_player import Ui_VideoPlayer


class VideoPlayer(QWidget):

    duration_available = Signal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.ui = Ui_VideoPlayer()
        self.ui.setupUi(self)
        
        self.graphics_scene = QGraphicsScene(self.ui.graphicsView)
        self.graphics_video_item = QGraphicsVideoItem()

        self.ui.graphicsView.setScene(self.graphics_scene)
        self.graphics_scene.addItem(self.graphics_video_item)

        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.graphics_video_item)

        # Styling
        self.graphics_video_item.setCursor(Qt.CursorShape.CrossCursor)
        self.graphics_scene.setBackgroundBrush(Qt.GlobalColor.gray)

        self.graphics_video_item.nativeSizeChanged.connect(self.repositionScene)
        self.graphics_video_item.installEventFilter(self)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)

    def open_video(self, video: QFileInfo, start: datetime):
        self.player.setSource(video.filePath())
        self.ui.labelVideoFileName.setText(video.fileName())
        self.player.pause()
        self.start = start

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.ui.graphicsView.fitInView(self.graphics_video_item, Qt.AspectRatioMode.KeepAspectRatio)
        return super().resizeEvent(event)
    
    def repositionScene(self):
        # Bring item's size to native video size so that the mouse position represents pixel in the video
        self.graphics_video_item.setSize(self.graphics_video_item.nativeSize())
        self.ui.graphicsView.fitInView(self.graphics_video_item, Qt.AspectRatioMode.KeepAspectRatio)
    
    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        match event.type():
            case QGraphicsSceneMouseEvent.Type.GraphicsSceneMousePress:
                match event.button():
                    case Qt.MouseButton.LeftButton:
                        print(event.pos(), self)
        return super().eventFilter(watched, event)
    
    def _on_media_status_changed(self, status):
        match status:
            case QMediaPlayer.MediaStatus.LoadedMedia:
                self.duration = self.player.duration()
                self.duration_available.emit(self.player.duration())

    def go_to(self, dt: datetime):
        target = dt - self.start
        pos = round(target.total_seconds() * 1000)
        self.player.setPosition(pos)