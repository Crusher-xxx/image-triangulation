import cv2 as cv
import numpy as np
import pymap3d as pm


def pixel2dirvec(p, cam_mtx):
    """Преобразование координат в пикселях в направляющий вектор
    относительно камеры
    """
    return np.linalg.inv(cam_mtx) @ [*p, 1.0]


def direction_cosine_matrix(a_v1, a_v2, b_v1, b_v2):
    """Матрица направляющих косинусов, поворачивающая вектор из координатной
    системы a в координатную систему b
    """
    # Определяем третий вектор как векторное произведение
    a_v12 = np.cross(a_v1, a_v2)
    b_v12 = np.cross(b_v1, b_v2)

    # Детерминированная система уравнений
    a_d = np.array([a_v1, a_v2, a_v12]).T
    b_d = np.array([b_v1, b_v2, b_v12]).T

    dcm_a2b = b_d @ np.linalg.inv(a_d)
    return dcm_a2b


def closest_points_along_two_lines(r1, r2, e1, e2):
    'Возвращает координаты двух точек, образующих кратчайший отрезок между двумя линиями'
    n = np.cross(e1, e2)
    t1 = np.dot(np.cross(e2, n), r2-r1) / np.dot(n, n)
    t2 = np.dot(np.cross(e1, n), r2-r1) / np.dot(n, n)
    p1 = r1 + t1 * e1
    p2 = r2 + t2 * e2
    return p1, p2


def normalize(v):
    'Нормализованный вектор является последовательностью направляющих косинусов'
    return v / np.linalg.norm(v)


class Camera:
    def __init__(self, cam_geodetic, cam_mtx, distortion_coeffs, resolution, cp1_geodetic, cp2_geodetic, cp1_pix, cp2_pix) -> None:
        self.cam_mtx = cam_mtx
        self.distortion_coeffs = distortion_coeffs
        self.resolution = resolution
        self.cam_geodetic = cam_geodetic

        self.alpha = 0
        self.cam_mtx_new, roi = cv.getOptimalNewCameraMatrix(self.cam_mtx, self.distortion_coeffs, self.resolution, self.alpha, self.resolution)

        cp1_geodetic = np.array(cp1_geodetic)
        cp2_geodetic = np.array(cp2_geodetic)
        self.cam_geodetic = np.array(cam_geodetic)
        cp1_enu = np.array(pm.geodetic2enu(*cp1_geodetic, *self.cam_geodetic))
        cp2_enu = np.array(pm.geodetic2enu(*cp2_geodetic, *self.cam_geodetic))
        
        cp1_dirvec_cam = pixel2dirvec(cp1_pix, self.cam_mtx_new)
        cp2_dirvec_cam = pixel2dirvec(cp2_pix, self.cam_mtx_new)

        cp1_unitvec_cam = normalize(cp1_dirvec_cam)
        cp2_unitvec_cam = normalize(cp2_dirvec_cam)
        cp1_unitvec_enu = normalize(cp1_enu)
        cp2_unitvec_enu = normalize(cp2_enu)

        self.rot_mtx_cam2enu = direction_cosine_matrix(cp1_unitvec_cam, cp2_unitvec_cam, cp1_unitvec_enu, cp2_unitvec_enu)

    def pixel2dirvec_enu(self, pixel):
        dir_vec_cam = pixel2dirvec(pixel, self.cam_mtx_new)
        dir_vec_enu = self.rot_mtx_cam2enu @ dir_vec_cam
        return dir_vec_enu
    
    def undistort(self, array: np.ndarray) -> np.ndarray:
        img_undistorted = cv.undistort(array, self.cam_mtx, self.distortion_coeffs, None, self.cam_mtx_new)
        return img_undistorted


class Triangulator:
    def __init__(self, cam1: Camera, cam2: Camera) -> None:
        self.cam1 = cam1
        self.cam2 = cam2
        self.cam1_enu = np.array([0.0, 0.0, 0.0])
        self.cam2_enu = pm.geodetic2enu(*self.cam1.cam_geodetic, *self.cam2.cam_geodetic)

    def triangulate(self, pix1, pix2):
        p1_dirvec_enu = self.cam1.pixel2dirvec_enu(pix1)
        p2_dirvec_enu = self.cam2.pixel2dirvec_enu(pix2)
        p1_enu, p2_enu = closest_points_along_two_lines(self.cam1_enu, self.cam2_enu, p1_dirvec_enu, p2_dirvec_enu)
        p_mean_enu = np.mean([p1_enu, p2_enu], axis=0)
        return p_mean_enu
