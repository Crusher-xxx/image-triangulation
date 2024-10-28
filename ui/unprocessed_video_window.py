from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QWidget

from .uic.unprocessed_video_window import Ui_UnprocessedVideoWindow


class UnprocessedVideoWindow(QWidget):
    closed = Signal()

    def __init__(self):
        super().__init__(None, Qt.WindowType.Window)

        self.ui = Ui_UnprocessedVideoWindow()
        self.ui.setupUi(self)

        self.cams = self.ui.cam1, self.ui.cam2

    def closeEvent(self, event: QCloseEvent) -> None:
        return self.closed.emit()
