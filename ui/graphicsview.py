from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsView


class GraphicsView(QGraphicsView):

    def __init__(self, parent):
        super().__init__(parent)

        self.setTransformationAnchor(self.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent) -> None:
        angle = event.angleDelta().y()
        zoom_factor = 1 + (angle/1000)
        self.scale(zoom_factor, zoom_factor)
        event.accept()
        # return super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.RightButton:
            self.pan_start_x = event.x()
            self.pan_start_y = event.y()

        return super().mousePressEvent(event)
    
    # def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    #     # if event.button() == Qt.MouseButton.RightButton:
    #     #     self.rmb_pressed = False
    #     return super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() is Qt.MouseButton.RightButton:
            hsb_new = self.horizontalScrollBar().value() - (event.x() - self.pan_start_x)
            vsb_new = self.verticalScrollBar().value() - (event.y() - self.pan_start_y)
            self.horizontalScrollBar().setValue(hsb_new)
            self.verticalScrollBar().setValue(vsb_new)
            self.pan_start_x = event.x()
            self.pan_start_y = event.y()
        return super().mouseMoveEvent(event)
