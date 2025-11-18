"""
调用：soup3D.camera
相机方法库，可在soup3D空间内移动相机位置
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from pyglm import glm
from math import *

import soup3D.shader

__all__ : list[str] = [
    "X", "Y", "Z", "YAW", "PITCH", "ROLL",
    "goto",
    "turn",
    "update",
]

X : int | float = 0.0
Y : int | float = 0.0
Z : int | float = 0.0
YAW : int | float = 0.0
PITCH : int | float = 0.0
ROLL : int | float = 0.0


def goto(x: int | float, y: int | float, z: int | float) -> None:
    """
    移动相机位置
    :param x: 相机x坐标位置
    :param y: 相机y坐标位置
    :param z: 相机z坐标位置
    :return: None
    """
    global X, Y, Z, YAW, PITCH, ROLL
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
    global X, Y, Z, YAW, PITCH, ROLL
    YAW, PITCH, ROLL = yaw, pitch, roll
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    update()


def update() -> None:
    """
    更新相机
    :return: None
    """
    centerX, centerY, centerZ = 0, 0, -1
    upX, upY, upZ = 0, 1, 0
    # 进行横滚旋转
    centerX, centerY = _rotated(centerX, centerY, 0, 0, ROLL)
    upX, upY = _rotated(upX, upY, 0, 0, ROLL)

    # 进行俯仰旋转
    centerY, centerZ = _rotated(centerY, centerZ, 0, 0, PITCH)
    upY, upZ = _rotated(upY, upZ, 0, 0, PITCH)

    # 进行偏行旋转
    centerX, centerZ = _rotated(centerX, centerZ, 0, 0, YAW)
    upX, upZ = _rotated(upX, upZ, 0, 0, YAW)

    gluLookAt(X, Y, Z, centerX+X, centerY+Y, centerZ+Z, upX, upY, upZ)

    for surface_id in soup3D.shader.set_mat_queue:
        surface = soup3D.shader.set_mat_queue[surface_id]
        if hasattr(surface, "set_view_mat"):
            surface.set_view_mat(get_view_mat())


def get_view_mat() -> glm.mat4x4:
    """
    获取相机矩阵，可用于代码着色器
    :return: 矩阵
    """
    centerX, centerY, centerZ = 0, 0, -1
    upX, upY, upZ = 0, 1, 0
    # 进行横滚旋转
    centerX, centerY = _rotated(centerX, centerY, 0, 0, ROLL)
    upX, upY = _rotated(upX, upY, 0, 0, ROLL)

    # 进行俯仰旋转
    centerY, centerZ = _rotated(centerY, centerZ, 0, 0, PITCH)
    upY, upZ = _rotated(upY, upZ, 0, 0, PITCH)

    # 进行偏行旋转
    centerX, centerZ = _rotated(centerX, centerZ, 0, 0, YAW)
    upX, upZ = _rotated(upX, upZ, 0, 0, YAW)

    camera_pos = glm.vec3(X, Y, Z)
    camera_target = glm.vec3(centerX+X, centerY+Y, centerZ+Z)
    camera_up = glm.vec3(upX, upY, upZ)

    return glm.lookAt(camera_pos, camera_target, camera_up)


def _rotated(Xa : int | float, Ya : int | float, Xb : int | float, Yb : int | float, degree : int | float) -> tuple[int | float, int | float]:
    """
    点A绕点B旋转特定角度后，点A的坐标
    :param Xa:     环绕点(点A)X坐标
    :param Ya:     环绕点(点A)Y坐标
    :param Xb:     被环绕点(点B)X坐标
    :param Yb:     被环绕点(点B)Y坐标
    :param degree: 旋转角度
    :return: 点A旋转后的X坐标, 点A旋转后的Y坐标
    """
    degree = degree * pi / 180
    outx = (Xa - Xb) * cos(degree) - (Ya - Yb) * sin(degree) + Xb
    outy = (Xa - Xb) * sin(degree) + (Ya - Yb) * cos(degree) + Yb
    return outx, outy
