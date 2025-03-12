import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from controller import Controller
from ui.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication([])

    cam_names = 'cam1', 'cam2'
    window = MainWindow()
    window.closed.connect(app.quit, Qt.ConnectionType.QueuedConnection)

    controller = Controller(window, cam_names)


    controller.load_file('video/test copy.json')

    window.show()
    sys.exit(app.exec())
