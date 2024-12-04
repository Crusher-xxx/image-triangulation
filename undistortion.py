import cv2 as cv
import numpy as np


class ImageUndistorter:
    """This class is responsible for eliminating image distortion"""
    def __init__(self, mtx, distortion_coeffs):
        self.mtx = mtx
        self.distortion_coeffs = distortion_coeffs

    def undistort(self, array: np.ndarray) -> np.ndarray:
        img_undistorted = cv.undistort(array, self.mtx, self.distortion_coeffs)
        return img_undistorted
