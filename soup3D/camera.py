"""
调用：soup3D.camera
相机方法库，可在soup3D空间内移动相机位置
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from pyglm import glm
from math import *
import ctypes

import soup3D.s3dm
import soup3D.shader
from soup3D.s3dm import normalize, cross

__all__ : list[str] = [
    "X", "Y", "Z", "QUAT",
    "goto",
    "turn",
    "turn_quat",
    "update",
]

X : int | float = 0.0
Y : int | float = 0.0
Z : int | float = 0.0
QUAT : glm.quat = glm.quat(1.0, 0.0, 0.0, 0.0)
# 相机旋转的四元数主存储 (w, x, y, z)


def _glu_look_at_fallback(ex: int | float,
                          ey: int | float,
                          ez: int | float,
                          cx: int | float,
                          cy: int | float,
                          cz: int | float,
                          ux: int | float,
                          uy: int | float,
                          uz: int | float) -> None:
    """
    在 GLU 的 gluLookAt 不可用时，使用等价矩阵乘法回退实现。
    """
    f = normalize([cx - ex, cy - ey, cz - ez])
    up = normalize([ux, uy, uz])
    s = normalize(cross(f, up))
    u = cross(s, f)

    matrix = [
        s[0], u[0], -f[0], 0.0,
        s[1], u[1], -f[1], 0.0,
        s[2], u[2], -f[2], 0.0,
        0.0,  0.0,   0.0,  1.0,
    ]
    glMultMatrixf((ctypes.c_float * 16)(*matrix))
    glTranslatef(-ex, -ey, -ez)


def _safe_glu_look_at(ex: int | float,
                      ey: int | float,
                      ez: int | float,
                      cx: int | float,
                      cy: int | float,
                      cz: int | float,
                      ux: int | float,
                      uy: int | float,
                      uz: int | float) -> None:
    """优先使用 gluLookAt，不可用时自动回退。"""
    if bool(gluLookAt):
        gluLookAt(ex, ey, ez, cx, cy, cz, ux, uy, uz)
    else:
        _glu_look_at_fallback(ex, ey, ez, cx, cy, cz, ux, uy, uz)


def goto(x: int | float, y: int | float, z: int | float) -> None:
    """
    移动相机位置
    :param x: 相机x坐标位置
    :param y: 相机y坐标位置
    :param z: 相机z坐标位置
    :return: None
    """
    if not isinstance(x, (int, float)):
        raise TypeError("x must be an int or float")
    if not isinstance(y, (int, float)):
        raise TypeError("y must be an int or float")
    if not isinstance(z, (int, float)):
        raise TypeError("z must be an int or float")

    global X, Y, Z
    X, Y, Z = x, y, z
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    update()


def turn(yaw: int | float, pitch: int | float, roll: int | float) -> None:
    """
    旋转相机
    :param yaw:   相机旋转偏移角
    :param pitch: 相机旋转俯仰角
    :param roll:  相机旋转横滚角
    :return:
    """
    if not isinstance(yaw, (int, float)):
        raise TypeError("yaw must be an int or float")
    if not isinstance(pitch, (int, float)):
        raise TypeError("pitch must be an int or float")
    if not isinstance(roll, (int, float)):
        raise TypeError("roll must be an int or float")

    global X, Y, Z, QUAT
    QUAT = soup3D.s3dm.euler_to_quat(yaw, pitch, roll)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    update()


def turn_quat(quat) -> None:
    """
    旋转相机（四元数）
    :param quat: 四元数，接受 glm.quat 或 (w, x, y, z) 的 list/tuple
    :return: None
    """
    if not isinstance(quat, (glm.quat, list, tuple)):
        raise TypeError("quat must be a glm.quat or a list/tuple of 4 numbers")
    if isinstance(quat, (list, tuple)) and len(quat) != 4:
        raise TypeError("quat must be a list/tuple of 4 numbers")
    global X, Y, Z, QUAT
    QUAT = soup3D.s3dm.parse_rotation(quat)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    update()


def update() -> None:
    """
    更新相机
    :return: None
    """
    center = QUAT * glm.vec3(0, 0, -1)
    up = QUAT * glm.vec3(0, 1, 0)
    _safe_glu_look_at(X, Y, Z, X + center.x, Y + center.y, Z + center.z, up.x, up.y, up.z)

    for surface_id in soup3D.shader.set_mat_queue:
        surface = soup3D.shader.set_mat_queue[surface_id]
        if hasattr(surface, "set_view_mat"):
            surface.set_view_mat(get_view_mat())


def get_view_mat() -> glm.mat4x4:
    """
    获取相机矩阵，可用于代码着色器
    :return: 矩阵
    """
    center = QUAT * glm.vec3(0, 0, -1)
    up = QUAT * glm.vec3(0, 1, 0)
    camera_pos = glm.vec3(X, Y, Z)
    camera_target = glm.vec3(X + center.x, Y + center.y, Z + center.z)
    camera_up = glm.vec3(up.x, up.y, up.z)
    return glm.lookAt(camera_pos, camera_target, camera_up)
