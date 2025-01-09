from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QGraphicsItem, QGraphicsView


class GraphicsView(QGraphicsView):

    def __init__(self, parent):
        super().__init__(parent)
        self._zoom_factor = 1

        self.setTransformationAnchor(self.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event: QWheelEvent) -> None:
        angle = event.angleDelta().y()
        zoom_factor = 1 + angle / 1000

        # Restrict zooming out too much
        current_scale = min(self.transform().m11(), self.transform().m22());
        fit_in_view_scale = min(self._fitInView_scale_x, self._fitInView_scale_y);
        if current_scale * zoom_factor < fit_in_view_scale:
            zoom_factor = fit_in_view_scale / current_scale;

        self._zoom_factor *= zoom_factor;
        self.scale(zoom_factor, zoom_factor)
        event.accept()

    def fitInView(self, item: QGraphicsItem, aspectRatioMode: Qt.AspectRatioMode):
        viewport_center_scene = self.mapToScene(self.viewport().rect().center())
        super().fitInView(item, aspectRatioMode)
        self._fitInView_scale_x = self.transform().m11()
        self._fitInView_scale_y = self.transform().m22()

        self.scale(self._zoom_factor, self._zoom_factor)  # Restore zoom
        self.centerOn(viewport_center_scene)

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
