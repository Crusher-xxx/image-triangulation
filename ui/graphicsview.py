from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView


class GraphicsView(QGraphicsView):

    def __init__(self, parent):
        super().__init__(parent)

        self.setTransformationAnchor(self.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent) -> None:
        angle = event.angleDelta().y()
        zoom_factor = 1 + angle / 1000
        self.scale(zoom_factor, zoom_factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
        return super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() is Qt.MouseButton.RightButton:
            hsb_new = self.horizontalScrollBar().value() - (event.position().x() - self._pan_start_x)
            vsb_new = self.verticalScrollBar().value() - (event.position().y() - self._pan_start_y)
            self.horizontalScrollBar().setValue(hsb_new)
            self.verticalScrollBar().setValue(vsb_new)
            self._pan_start_x = event.position().x()
            self._pan_start_y = event.position().y()
        return super().mouseMoveEvent(event)
