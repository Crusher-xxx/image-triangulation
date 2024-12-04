import numpy as np


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
    t1 = np.dot(np.cross(e2, n), r2 - r1) / np.dot(n, n)
    t2 = np.dot(np.cross(e1, n), r2 - r1) / np.dot(n, n)
    p1 = r1 + t1 * e1
    p2 = r2 + t2 * e2
    return p1, p2


def normalize(v):
    'Нормализованный вектор является последовательностью направляющих косинусов'
    return v / np.linalg.norm(v)


class Camera:
    def __init__(self, mtx, cp1_world, cp2_world, cp1_pix, cp2_pix) -> None:
        self.mtx = mtx
        
        cp1_dirvec_cam = pixel2dirvec(cp1_pix, self.mtx)
        cp2_dirvec_cam = pixel2dirvec(cp2_pix, self.mtx)

        cp1_unitvec_cam = normalize(cp1_dirvec_cam)
        cp2_unitvec_cam = normalize(cp2_dirvec_cam)
        cp1_unitvec_world = normalize(cp1_world)
        cp2_unitvec_world = normalize(cp2_world)

        self.rotation_mtx_cam2world = direction_cosine_matrix(cp1_unitvec_cam, cp2_unitvec_cam, cp1_unitvec_world, cp2_unitvec_world)

    def pixel2dirvec_world(self, pixel):
        dir_vec_cam = pixel2dirvec(pixel, self.mtx)
        dir_vec_enu = self.rotation_mtx_cam2world @ dir_vec_cam
        return dir_vec_enu


class Triangulator:
    def __init__(self, cam1: Camera, cam2: Camera, cam1_world, cam2_world) -> None:
        self.cam1 = cam1
        self.cam2 = cam2
        self.cam1_world = cam1_world
        self.cam2_world = cam2_world

    def triangulate(self, img1_point_pix, img2_point_pix):
        p1_dirvec_world = self.cam1.pixel2dirvec_world(img1_point_pix)
        p2_dirvec_world = self.cam2.pixel2dirvec_world(img2_point_pix)
        p1_world, p2_world = closest_points_along_two_lines(self.cam1_world, self.cam2_world, p1_dirvec_world, p2_dirvec_world)
        world = np.mean([p1_world, p2_world], axis=0)
        return world
