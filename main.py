import csv
import json
import sys
from datetime import datetime

import numpy as np
from PySide6.QtCore import QFileInfo, QPointF
from PySide6.QtWidgets import QApplication, QFileDialog

from geomath import Camera, Triangulator
from ui.main_window import MainWindow


def read_cam_data(json_file_path: str, cam_keys):
    with open(json_file_path) as f:
        data: dict = json.load(f)

    cp1_geodetic = data['cp1_geodetic']
    cp2_geodetic = data['cp2_geodetic']
    
    cams: list[Camera] = []
    videos: list[str] = []
    for cam_key in cam_keys:
        video = data[cam_key]['file']

        fx = data[cam_key]['fx']
        fy = data[cam_key]['fy']
        cx = data[cam_key]['cx']
        cy = data[cam_key]['cy']

        cam_mtx = np.array([
            [fx,  0, cx],
            [ 0, fy, cy],
            [ 0,  0,  1],
        ])

        cam_geodetic = data[cam_key]['cam_geodetic']

        cp1_pix = data[cam_key]['cp1_pix']
        cp2_pix = data[cam_key]['cp2_pix']

        distortion_coeffs = np.array(data[cam_key]['distortion_coeffs'])
        resolution = data[cam_key]['resolution']
        cam = Camera(cam_geodetic, cam_mtx, distortion_coeffs, resolution, cp1_geodetic, cp2_geodetic, cp1_pix, cp2_pix)

        videos.append(video)
        cams.append(cam)
    return cams, videos


class Controller:
    def __init__(self, window: MainWindow, cam_keys) -> None:
        self.window = window
        self.cam_keys = cam_keys
        self.triangulated_frames: dict[datetime, tuple] = {}

    def load_file_gui(self):
        file_path, _ = QFileDialog.getOpenFileName(self.window, filter='JSON (*.json)')
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        self.file_info = QFileInfo(file_path)
        cams, videos = read_cam_data(file_path, self.cam_keys)
        videos = [f'{self.file_info.dir().path()}/{video}' for video in videos]

        self.triangulator = Triangulator(*cams)
        undistorters = self.triangulator.cam1.undistort, self.triangulator.cam2.undistort

        self.window.open_files(videos, undistorters)

    def triangulate_frame(self, frame_datetime: datetime, pix1: QPointF, pix2: QPointF):
        pix1 = pix1.toTuple()
        pix2 = pix2.toTuple()
        enu, geodetic = self.triangulator.triangulate(pix1, pix2)
        self.triangulated_frames[frame_datetime] = *enu.tolist(), *geodetic.tolist()
        print(frame_datetime, pix1, pix2, enu.tolist(), geodetic.tolist())

    def export_data_gui(self):
        file_path_no_ext = f'{self.file_info.dir().path()}/{self.file_info.baseName()}'
        print(123, file_path_no_ext)
        file_path, _ = QFileDialog.getSaveFileName(self.window, dir=file_path_no_ext, filter='Text file (*.txt)')
        if file_path:
            self.export_data(file_path)

    def export_data(self, file_path: str):
        headers = 'datetime', 'e', 'n', 'u', 'lat', 'lon', 'alt'
        rows = [(key, *val) for key, val in sorted(self.triangulated_frames.items())]

        with open(file_path, 'w', newline='') as f:
            w = csv.writer(f, delimiter='\t')
            w.writerow(headers)
            w.writerows(rows)
            # for key, val in self.triangulated_frames.items():
            #     row = key, *val
            #     w.writerow(row)



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
