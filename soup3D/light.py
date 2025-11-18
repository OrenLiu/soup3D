"""
调用：soup3D.light
光源处理方法库，可在soup3D空间中添加7个光源
"""
from OpenGL.GL import *
from math import *

import soup3D


__all__ : list[str] = [
    "Cone", "Direct", "ambient"
]

dirty = False
EAU = []

light_queue = {}


class Cone:
    def __init__(self,
                 place: tuple[int | float, int | float, int | float],
                 toward: tuple[int | float, int | float, int | float],
                 color: tuple[int | float, int | float, int | float],
                 attenuation: float, angle=180):
        """
        锥形光线，类似灯泡光线
        :param place:        光源位置(x, y, z)
        :param toward:       光源朝向(yaw, pitch, roll)
        :param color:        光源颜色(red, green, blue)
        :param attenuation:  线性衰减率
        :param angle:        锥形光线锥角
        """
        global dirty

        self.on = False
        self.place = place
        self.toward = toward
        self.color = color
        self.attenuation = attenuation
        self.angle = angle

        light_queue[id(self)] = self
        if not dirty:
            dirty = True

    def _calc_direction(self) -> tuple[int | float, int | float, int | float]:
        """根据欧拉角计算方向向量"""
        x, y, z = 0, 0, -1  # 初始Z轴负方向
        yaw, pitch, roll = self.toward

        # 应用旋转顺序：roll -> pitch -> yaw
        x, y = rotated(x, y, 0, 0, roll)
        y, z = rotated(y, z, 0, 0, pitch)
        x, z = rotated(x, z, 0, 0, yaw)

        # 归一化
        length = sqrt(x ** 2 + y ** 2 + z ** 2)
        return (x / length, y / length, z / length) if length != 0 else (0, 0, 1)

    def goto(self, x : int | float, y : int | float, z : int | float) -> None:
        """
        更改光源位置
        :param x: 光源x坐标
        :param y: 光源y坐标
        :param z: 光源z坐标
        :return: None
        """
        global dirty

        self.place = (x, y, z)
        if not dirty:
            dirty = True

    def turn(self, yaw : int | float, pitch : int | float, roll : int | float) -> None:
        """
        更改光线朝向
        :param yaw:   光线偏移角度
        :param pitch: 光线府仰角度
        :param roll:  光线横滚角度
        :return: None
        """
        global dirty

        self.toward = (yaw, pitch, roll)
        if not dirty:
            dirty = True

    def dye(self, r : int | float, g : int | float, b : int | float) -> None:
        """
        更改光线颜色
        :param r: 红色
        :param g: 绿色
        :param b: 蓝色
        :return: None
        """
        global dirty

        self.color = (r, g, b)
        if not dirty:
            dirty = True

    def turn_off(self) -> None:
        """
        熄灭光源
        :return: None
        """
        global dirty

        self.on = False
        if not dirty:
            dirty = True

    def turn_on(self) -> None:
        """
        点亮光源
        :return: None
        """
        global dirty

        self.on = True
        if not dirty:
            dirty = True

    def destroy(self) -> None:
        """
        摧毁光源，并归还光源编号
        :return: None
        """
        global dirty

        del light_queue[id(self)]
        if not dirty:
            dirty = True


class Direct:
    def __init__(self,
                 toward: tuple[int | float, int | float, int | float],
                 color: tuple[int | float, int | float, int | float]) -> None:
        """
        方向光线，类似太阳光线
        :param toward: 光源朝向(yaw, pitch, roll)
        :param color:  光源颜色(red, green, blue)
        """
        global dirty

        self.on = False
        self.toward = toward
        self.color = color

        light_queue[id(self)] = self
        if not dirty:
            dirty = True

    def _calc_direction(self) -> tuple[int | float, int | float, int | float]:
        """计算逆向方向向量"""
        x, y, z = 0, 0, -1  # OpenGL方向光约定方向
        yaw, pitch, roll = self.toward

        x, y = rotated(x, y, 0, 0, roll)
        y, z = rotated(y, z, 0, 0, pitch)
        x, z = rotated(x, z, 0, 0, yaw)

        length = sqrt(x ** 2 + y ** 2 + z ** 2)
        return (-x / length, -y / length, -z / length) if length != 0 else (0, 0, 1)

    def turn(self, yaw : int | float, pitch : int | float, roll : int | float) -> None:
        """
        更改光线朝向
        :param yaw:   光线偏移角度
        :param pitch: 光线府仰角度
        :param roll:  光线横滚角度
        :return: None
        """
        global dirty

        self.toward = (yaw, pitch, roll)
        if not dirty:
            dirty = True

    def dye(self, r : int | float, g : int | float, b : int | float) -> None:
        """
        更改光线颜色
        :param r: 红色
        :param g: 绿色
        :param b: 蓝色
        :return: None
        """
        global dirty

        self.color = (r, g, b)
        if not dirty:
            dirty = True

    def turn_off(self) -> None:
        """
        熄灭光源
        :return: None
        """
        global dirty

        self.on = False
        if not dirty:
            dirty = True

    def turn_on(self) -> None:
        """
        点亮光源
        :return: None
        """
        global dirty

        self.on = True
        if not dirty:
            dirty = True

    def destroy(self) -> None:
        """
        摧毁光源，并归还光源编号
        :return: None
        """
        global dirty

        del light_queue[id(self)]
        if not dirty:
            dirty = True


def ambient(R: int | float, G: int | float, B: int | float) -> None:
    """
    更改环境光亮度
    :param R: 红色环境光
    :param G: 绿色环境光
    :param B: 蓝色环境光
    :return: None
    """
    global dirty

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (R, G, B, 1))
    dirty = True


def set_surface_light():
    global dirty

    for surface_id in soup3D.shader.set_mat_queue:
        surface = soup3D.shader.set_mat_queue[surface_id]
        if hasattr(surface, "set_light"):
            surface.set_light(light_queue)
    dirty = False


def rotated(Xa: int | float, Ya: int | float,
            Xb: int | float, Yb: int | float,
            degree: int | float) -> tuple[float, float]:
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
