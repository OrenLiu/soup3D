"""
调用：soup3D.light
光源处理方法库，可在soup3D空间中添加7个光源
"""
from OpenGL.GL import *
from math import *
from pyglm import glm

import soup3D
import soup3D.s3dm
from soup3D.s3dm import rotated


__all__ : list[str] = [
    "Cone", "Direct", "ambient"
]

dirty = False
EAU = []

light_queue = {}

# 环境光颜色缓存(RGB)。ambient() 是引擎内唯一的环境光写入点,着色器侧直接读取该值,
# 避免每个脏 surface 每帧都走 glGetFloatv 读回 GL 状态。
# 默认值取 OpenGL 默认环境光 (0.2, 0.2, 0.2, 1) 的 RGB 分量,与未调用 ambient() 时的 GL 状态一致
ambient_val = (0.2, 0.2, 0.2)


class Cone:
    def __init__(self,
                 place: tuple[int | float, int | float, int | float],
                 toward: tuple[int | float, ...],
                 color: tuple[int | float, int | float, int | float],
                 attenuation: float, angle=180):
        """
        锥形光线，类似灯泡光线
        :param place:        光源位置(x, y, z)
        :param toward:       光源朝向，欧拉角(yaw, pitch, roll)或四元数(w, x, y, z)
        :param color:        光源颜色(red, green, blue)
        :param attenuation:  线性衰减率
        :param angle:        锥形光线锥角
        """
        if not isinstance(place, (list, tuple)) or len(place) != 3:
            raise TypeError("place must be a list or tuple of 3 numbers")
        for p in place:
            if not isinstance(p, (int, float)):
                raise TypeError("place elements must be int or float")
        if not isinstance(toward, (list, tuple)) or len(toward) not in (3, 4):
            raise TypeError("toward must be a list or tuple of 3 or 4 numbers")
        for t in toward:
            if not isinstance(t, (int, float)):
                raise TypeError("toward elements must be int or float")
        self.quat = soup3D.s3dm.parse_rotation(toward)
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            raise TypeError("color must be a list or tuple of 3 numbers")
        for c in color:
            if not isinstance(c, (int, float)):
                raise TypeError("color elements must be int or float")
        if not isinstance(attenuation, (int, float)):
            raise TypeError("attenuation must be an int or float")
        if not isinstance(angle, (int, float)):
            raise TypeError("angle must be an int or float")

        global dirty

        self.on = False
        self.place = place
        self.color = color
        self.attenuation = attenuation
        self.angle = angle

        light_queue[id(self)] = self
        if not dirty:
            dirty = True

    def _calc_direction(self) -> tuple:
        """根据四元数计算方向向量"""
        d = self.quat * glm.vec3(0, 0, -1)
        length = sqrt(d.x ** 2 + d.y ** 2 + d.z ** 2)
        return (d.x / length, d.y / length, d.z / length) if length != 0 else (0, 0, 1)

    def goto(self, x : int | float, y : int | float, z : int | float) -> None:
        """
        更改光源位置
        :param x: 光源x坐标
        :param y: 光源y坐标
        :param z: 光源z坐标
        :return: None
        """
        if not isinstance(x, (int, float)):
            raise TypeError("x must be an int or float")
        if not isinstance(y, (int, float)):
            raise TypeError("y must be an int or float")
        if not isinstance(z, (int, float)):
            raise TypeError("z must be an int or float")

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
        if not isinstance(yaw, (int, float)):
            raise TypeError("yaw must be an int or float")
        if not isinstance(pitch, (int, float)):
            raise TypeError("pitch must be an int or float")
        if not isinstance(roll, (int, float)):
            raise TypeError("roll must be an int or float")

        global dirty

        self.quat = soup3D.s3dm.euler_to_quat(yaw, pitch, roll)
        if not dirty:
            dirty = True

    def turn_quat(self, quat) -> None:
        """
        更改光线朝向（四元数）
        :param quat: 四元数，接受 glm.quat 或 (w, x, y, z) 的 list/tuple
        :return: None
        """
        if not isinstance(quat, (glm.quat, list, tuple)):
            raise TypeError("quat must be a glm.quat or a list/tuple of 4 numbers")
        if isinstance(quat, (list, tuple)) and len(quat) != 4:
            raise ValueError("quat must be a list/tuple of 4 numbers")
        global dirty
        self.quat = soup3D.s3dm.parse_rotation(quat)
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
        if not isinstance(r, (int, float)):
            raise TypeError("r must be an int or float")
        if not isinstance(g, (int, float)):
            raise TypeError("g must be an int or float")
        if not isinstance(b, (int, float)):
            raise TypeError("b must be an int or float")

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
                 toward: tuple[int | float, ...],
                 color: tuple[int | float, int | float, int | float]) -> None:
        """
        方向光线，类似太阳光线
        :param toward: 光源朝向，欧拉角(yaw, pitch, roll)或四元数(w, x, y, z)
        :param color:  光源颜色(red, green, blue)
        """
        if not isinstance(toward, (list, tuple)) or len(toward) not in (3, 4):
            raise TypeError("toward must be a list or tuple of 3 or 4 numbers")
        for t in toward:
            if not isinstance(t, (int, float)):
                raise TypeError("toward elements must be int or float")
        self.quat = soup3D.s3dm.parse_rotation(toward)
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            raise TypeError("color must be a list or tuple of 3 numbers")
        for c in color:
            if not isinstance(c, (int, float)):
                raise TypeError("color elements must be int or float")

        global dirty

        self.on = False
        self.color = color

        light_queue[id(self)] = self
        if not dirty:
            dirty = True

    def _calc_direction(self) -> tuple:
        """根据四元数计算逆向方向向量"""
        d = self.quat * glm.vec3(0, 0, -1)
        length = sqrt(d.x ** 2 + d.y ** 2 + d.z ** 2)
        return (-d.x / length, -d.y / length, -d.z / length) if length != 0 else (0, 0, 1)

    def turn(self, yaw : int | float, pitch : int | float, roll : int | float) -> None:
        """
        更改光线朝向
        :param yaw:   光线偏移角度
        :param pitch: 光线府仰角度
        :param roll:  光线横滚角度
        :return: None
        """
        if not isinstance(yaw, (int, float)):
            raise TypeError("yaw must be an int or float")
        if not isinstance(pitch, (int, float)):
            raise TypeError("pitch must be an int or float")
        if not isinstance(roll, (int, float)):
            raise TypeError("roll must be an int or float")

        global dirty

        self.quat = soup3D.s3dm.euler_to_quat(yaw, pitch, roll)
        if not dirty:
            dirty = True

    def turn_quat(self, quat) -> None:
        """
        更改光线朝向（四元数）
        :param quat: 四元数，接受 glm.quat 或 (w, x, y, z) 的 list/tuple
        :return: None
        """
        if not isinstance(quat, (glm.quat, list, tuple)):
            raise TypeError("quat must be a glm.quat or a list/tuple of 4 numbers")
        if isinstance(quat, (list, tuple)) and len(quat) != 4:
            raise ValueError("quat must be a list/tuple of 4 numbers")
        global dirty
        self.quat = soup3D.s3dm.parse_rotation(quat)
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
        if not isinstance(r, (int, float)):
            raise TypeError("r must be an int or float")
        if not isinstance(g, (int, float)):
            raise TypeError("g must be an int or float")
        if not isinstance(b, (int, float)):
            raise TypeError("b must be an int or float")

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
    if not isinstance(R, (int, float)):
        raise TypeError("R must be an int or float")
    if not isinstance(G, (int, float)):
        raise TypeError("G must be an int or float")
    if not isinstance(B, (int, float)):
        raise TypeError("B must be an int or float")

    global dirty, ambient_val

    glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (R, G, B, 1))
    # 同步 Python 侧缓存,着色器上传环境光 uniform 时直接读它,不再做 GL 读回
    ambient_val = (R, G, B)
    dirty = True


def set_surface_light():
    """
    自动调用函数，无需手动调用。在有光源变动时让所有着色器响应。
    :return: None
    """
    global dirty

    soup3D.shader.light_queue = light_queue
    for surface_id in soup3D.shader.set_mat_queue:
        surface = soup3D.shader.set_mat_queue[surface_id]
        if hasattr(surface, "set_light"):
            surface.set_light()
    dirty = False
