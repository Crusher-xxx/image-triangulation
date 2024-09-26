from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import QGraphicsItem, QGraphicsSceneMouseEvent


class GraphicsVideoItem(QGraphicsVideoItem):

    mouse_pressed = Signal(QPointF)

    def __init__(self, parent: QGraphicsItem | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.CrossCursor)

        self.nativeSizeChanged.connect(self._match_pixels)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() is Qt.MouseButton.LeftButton:
            self.mouse_pressed.emit(event.pos())

    def _match_pixels(self):
        # Bring item's size to native video size so that the mouse position represents pixel in the video
        self.setSize(self.nativeSize())
