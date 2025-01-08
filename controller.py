import csv
import json
from datetime import datetime

import numpy as np
import pymap3d as pm
from PySide6.QtCore import QFileInfo, QPointF
from PySide6.QtWidgets import QFileDialog

from triangulation import Camera, Triangulator
from ui.main_window import MainWindow
from undistortion import ImageUndistorter


class Controller:
    """This class is responsible for communication between UI and Math"""
    def __init__(self, window: MainWindow, cam_keys) -> None:
        self.window = window
        self.cam_keys = cam_keys
        self.triangulated_frames: dict[datetime, tuple] = {}

        window.both_frames_clicked.connect(self.triangulate_frame)
        window.ui.action_open_file.triggered.connect(self.load_file_gui)
        window.ui.action_export_data.triggered.connect(self.export_data_gui)
        window.anchor_clicked.connect(self.update_anchor_point)

    def load_file_gui(self):
        file_path, _ = QFileDialog.getOpenFileName(self.window, filter='JSON (*.json)')
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        # Clear previous data
        self.triangulated_frames.clear()

        with open(file_path) as f:
            self.data: dict = json.load(f)
        cp1_geodetic = self.data['cp1_geodetic']
        cp2_geodetic = self.data['cp2_geodetic']

        self.cams: list[Camera] = []
        videos: list[str] = []
        undistorters: list[ImageUndistorter] = []
        for cam in self.cam_keys:
            video = self.data[cam]['file']
            videos.append(video)

            # Form matrix of intrinsic parameters
            fx = self.data[cam]['fx']
            fy = self.data[cam]['fy']
            cx = self.data[cam]['cx']
            cy = self.data[cam]['cy']
            cam_mtx = np.array([
                [fx,  0, cx],
                [ 0, fy, cy],
                [ 0,  0,  1],
            ])

            distortion_coeffs = np.array(self.data[cam]['distortion_coeffs'])
            undistorter = ImageUndistorter(cam_mtx, distortion_coeffs)
            undistorters.append(undistorter)

            cam_geodetic = self.data[cam]['cam_geodetic']
            cp1_pix = self.data[cam]['cp1_pix']
            cp2_pix = self.data[cam]['cp2_pix']
            cp1_world = np.array(pm.geodetic2enu(*cp1_geodetic, *cam_geodetic))
            cp2_world = np.array(pm.geodetic2enu(*cp2_geodetic, *cam_geodetic))

            camera = Camera(undistorter.mtx, [cp1_world, cp2_world], [cp1_pix, cp2_pix])
            self.cams.append(camera)

        self.file_info = QFileInfo(file_path)
        videos = [f'{self.file_info.dir().path()}/{video}' for video in videos]
        undistorters_callbacks = [x.undistort for x in undistorters]
        
        cam1_world = np.array([0.0, 0.0, 0.0])
        cam2_world = pm.geodetic2enu(*self.data['cam2']['cam_geodetic'], *self.data['cam1']['cam_geodetic'])
        self.triangulator = Triangulator(*self.cams, cam1_world, cam2_world)

        self.window.open_files(videos, undistorters_callbacks)

    def triangulate_frame(self, frame_datetime: datetime, pix1: QPointF, pix2: QPointF):
        pix1 = pix1.toTuple()
        pix2 = pix2.toTuple()
        enu = self.triangulator.triangulate(pix1, pix2)
        geodetic = np.array(pm.enu2geodetic(*enu, *self.data['cam1']['cam_geodetic']))
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

    def update_anchor_point(self, cam_id: int, point_id: int, pos: QPointF):
        print(locals())
        self.cams[cam_id].update_anchor_point(point_id, pos.toTuple())
