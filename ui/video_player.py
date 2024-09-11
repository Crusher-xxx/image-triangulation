from datetime import datetime

import cv2 as cv
import numpy as np
import numpy.typing as npt
from araviq6 import VideoFrameProcessor, VideoFrameWorker
from PySide6.QtCore import QEvent, QFileInfo, QObject, QSize, Qt, Signal
from PySide6.QtGui import QCloseEvent, QResizeEvent
from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer, QVideoFrame, QVideoSink
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem, QVideoWidget
from PySide6.QtWidgets import QGraphicsScene, QGraphicsSceneMouseEvent, QWidget

from .uic.video_player import Ui_VideoPlayer


class UndistortionWorker(VideoFrameWorker):
    """Class responsible for image undistortion"""
    
    def __init__(self, cam_mtx: npt.NDArray, distortion_coeffs: npt.NDArray, resolution: tuple[int, int]):
        super().__init__()
        self.alpha = 1
        self.cam_mtx = cam_mtx
        self.distortion_coeffs = distortion_coeffs
        self.new_cam_mtx, roi = cv.getOptimalNewCameraMatrix(self.cam_mtx, self.distortion_coeffs, resolution, self.alpha, resolution)

    def processArray(self, array: np.ndarray) -> np.ndarray:
        img_undistorted = cv.undistort(array, self.cam_mtx, self.distortion_coeffs, None, self.new_cam_mtx)
        return img_undistorted


class VideoPlayer(QWidget):
    loaded = Signal()

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

        self._frame_processor = VideoFrameProcessor()

        self._frame_processor.videoFrameProcessed.connect(lambda f: self._graphics_video_item.videoSink().setVideoFrame(f))
        self._video_sink_raw.videoFrameChanged.connect(self._frame_processor.processVideoFrame)
        self._video_sink_raw.videoFrameChanged.connect(lambda f: self._video_widget_raw.videoSink().setVideoFrame(f))
        
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

    def open_video(self,
                   video: QFileInfo,
                   start: datetime,
                   cam_mtx: npt.NDArray,
                   distortion_coeffs: npt.NDArray):
        self._player.setSource(video.filePath())
        self._player.pause()
        self.ui.labelVideoFileName.setText(video.fileName())

        self.start = start
        self.cam_mtx = cam_mtx
        self.distortion_coeffs = distortion_coeffs

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
                        print(gsmp.pos())
        return super().eventFilter(watched, event)
    
    def _on_metadata_changed(self):
        self.duration = self._player.duration()

        resolution: QSize = self._player.metaData().value(QMediaMetaData.Key.Resolution)
        resolution = resolution.toTuple()
        self._undistortion_worker = UndistortionWorker(self.cam_mtx, self.distortion_coeffs, resolution)
        self._frame_processor.setWorker(self._undistortion_worker)

        self.loaded.emit()

    def go_to(self, dt: datetime):
        target = dt - self.start
        pos = round(target.total_seconds() * 1000)
        self._player.setPosition(pos)

    def undistort_frame(self, frame: QVideoFrame):
        img = frame.toImage()
        buffer = np.frombuffer(img.constBits(), np.uint8).reshape(img.height(), img.width(), 4)
        buffer = cv.cvtColor(buffer, cv.COLOR_RGBA2BGR)
        img_undistorted = cv.undistort(buffer, self.cam_mtx, self.distortion_coeffs, None, self.new_cam_mtx)

        img_resized = cv.resize(img_undistorted, (1280, 720))
        cv.imshow(self.ui.labelVideoFileName.text(), img_resized)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._frame_processor.stop()
        return super().closeEvent(event)
