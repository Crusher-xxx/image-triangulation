import sys

from PySide6.QtWidgets import QApplication

from controller import Controller
from ui.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication([])

    cam_names = 'cam1', 'cam2'
    window = MainWindow()
    controller = Controller(window, cam_names)

    window.closed.connect(app.quit)
    window.both_frames_clicked.connect(controller.triangulate_frame)
    window.ui.action_open_file.triggered.connect(controller.load_file_gui)
    window.ui.action_export_data.triggered.connect(controller.export_data_gui)

    controller.load_file('video/test copy.json')

    window.show()
    sys.exit(app.exec())
