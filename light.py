"""
调用：soup3D.light
光源处理方法库，可在soup3D空间中添加7个光源
"""
from OpenGL.GL import *
from OpenGL.GLU import *

from math import *


__all__ = [
    "init", "Cone", "Direct"
]

light_list = [GL_LIGHT0, GL_LIGHT1, GL_LIGHT2, GL_LIGHT3, GL_LIGHT4, GL_LIGHT5, GL_LIGHT6, GL_LIGHT7]


def init(ambientR=0, ambientG=0, ambientB=0):
    """
    初始化光源，启用全局光照
    :param ambientR: 红环境光亮度
    :param ambientG: 绿环境光亮度
    :param ambientB: 蓝环境光亮度
    :return:
    """
    glEnable(GL_LIGHTING)  # 启用光照
    glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)  # 启用双面光照
    glEnable(GL_NORMALIZE)
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (ambientR, ambientG, ambientB, 1))
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)


class Cone:
    def __init__(self,
                 place: (float, float, float),
                 toward: (float, float, float),
                 color: (float, float, float),
                 attenuation: float, angle=180):
        """
        锥形光线，类似灯泡光线
        :param place:        光源位置(x, y, z)
        :param toward:       光源朝向(yaw, pitch, roll)
        :param color:        光源颜色(red, green, blue)
        :param attenuation:  线性衰减率
        :param angle:        锥形光线锥角
        """
        self.light_id = light_list.pop(0)
        self.place = place
        self.toward = toward
        self.color = color
        self.attenuation = attenuation
        self.angle = angle

        glEnable(self.light_id)

    def display(self):
        """更新光源参数到OpenGL"""
        # 位置和方向计算
        direction = self._calc_direction()

        glLightfv(self.light_id, GL_POSITION, (*self.place, 1.0))
        glLightfv(self.light_id, GL_SPOT_DIRECTION, direction)

        # 颜色参数
        glLightfv(self.light_id, GL_DIFFUSE, (*self.color, 1.0))
        glLightfv(self.light_id, GL_SPECULAR, (*self.color, 1.0))

        # 聚光灯参数
        glLightf(self.light_id, GL_SPOT_CUTOFF, self.angle / 2)
        glLightf(self.light_id, GL_SPOT_EXPONENT, 10.0)

        # 衰减参数
        glLightf(self.light_id, GL_LINEAR_ATTENUATION, self.attenuation)

    def _calc_direction(self):
        """根据欧拉角计算方向向量"""
        x, y, z = 0, 0, 1  # 初始Z轴正方向
        yaw, pitch, roll = self.toward

        # 应用旋转顺序：roll -> pitch -> yaw
        x, y = rotated(x, y, 0, 0, roll)
        y, z = rotated(y, z, 0, 0, pitch)
        x, z = rotated(x, z, 0, 0, yaw)

        # 归一化
        length = sqrt(x ** 2 + y ** 2 + z ** 2)
        return (x / length, y / length, z / length) if length != 0 else (0, 0, 1)

    def goto(self, x, y, z):
        """
        更改光源位置
        :param x: 光源x坐标
        :param y: 光源y坐标
        :param z: 光源z坐标
        :return: None
        """
        self.place = (x, y, z)

    def turn(self, yaw, pitch, roll):
        """
        更改光线朝向
        :param yaw:   光线偏移角度
        :param pitch: 光线府仰角度
        :param roll:  光线横滚角度
        :return: None
        """
        self.toward = (yaw, pitch, roll)

    def color(self, r, g, b):
        """
        更改光线颜色
        :param r: 红色
        :param g: 绿色
        :param b: 蓝色
        :return: None
        """
        self.color = (r, g, b)


class Direct:
    def __init__(self,
                 toward: (float, float, float),
                 color: (float, float, float)):
        """
        方向光线，类似太阳光线
        :param toward: 光源朝向(yaw, pitch, roll)
        :param color:  光源颜色(red, green, blue)
        """
        self.light_id = light_list.pop(0)
        self.toward = toward
        self.color = color

        glEnable(self.light_id)

    def display(self):
        """更新方向光源参数"""
        direction = self._calc_direction()
        glLightfv(self.light_id, GL_POSITION, (*direction, 0.0))
        glLightfv(self.light_id, GL_DIFFUSE, (*self.color, 1.0))
        glLightfv(self.light_id, GL_SPECULAR, (*self.color, 1.0))

    def _calc_direction(self):
        """计算逆向方向向量"""
        x, y, z = 0, 0, 1  # OpenGL方向光约定方向
        yaw, pitch, roll = self.toward

        x, y = rotated(x, y, 0, 0, roll)
        y, z = rotated(y, z, 0, 0, pitch)
        x, z = rotated(x, z, 0, 0, yaw)

        length = sqrt(x ** 2 + y ** 2 + z ** 2)
        return (-x / length, -y / length, -z / length) if length != 0 else (0, 0, 1)

    def turn(self, yaw, pitch, roll):
        """
        更改光线朝向
        :param yaw:   光线偏移角度
        :param pitch: 光线府仰角度
        :param roll:  光线横滚角度
        :return: None
        """
        self.toward = (yaw, pitch, roll)

    def color(self, r, g, b):
        """
        更改光线颜色
        :param r: 红色
        :param g: 绿色
        :param b: 蓝色
        :return: None
        """
        self.color = (r, g, b)


def ambient(R, G, B):
    """
    更改环境光亮度
    :param R: 红色环境光
    :param G: 绿色环境光
    :param B: 蓝色环境光
    :return: None
    """
    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (R, G, B, 1))


def rotated(Xa, Ya, Xb, Yb, degree):
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
