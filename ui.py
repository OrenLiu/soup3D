"""
调用：soup3D.ui
soup3D的ui子库，用于绘制2D图形，可绘制HUD叠加显示、GUI用户界面等。
"""
from OpenGL.GL import *
from OpenGL.GLU import *
from math import*
from PIL import Image

import soup3D.shader

render_queue : list[tuple["Shape", float, float]] = []  # 全局渲染队列


class Shape:
    def __init__(self, shape_type,
                 texture: soup3D.shader.Img,
                 vertex: list | tuple):
        """
        图形，可以批量生成线段、三角形
        :param shape_type: 绘制方式，可以填写这些内容：
                           "line_b": 不相连线段
                           "line_s": 连续线段
                           "line_l": 头尾相连的连续线段
                           "triangle_b": 不相连三角形
                           "triangle_s": 相连三角形
                           "triangle_l": 头尾相连的连续三角形
        :param texture:    使用的纹理对象，默认为None
        :param vertex:     图形中所有的端点，每个参数的格式为：(x, y, u, v)
        """
        type_menu = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }
        if shape_type not in type_menu:
            raise TypeError(f"unknown type: {shape_type}")
        self.type = shape_type
        self.texture = texture
        self.vertex = vertex
        self.display_list = None
        self.tex_id = self.texture.get_texture_id()

    def _setup_projection(self) -> None:
        """设置正交投影"""
        viewport = glGetIntegerv(GL_VIEWPORT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, viewport[2], viewport[3], 0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _restore_projection(self) -> None:
        """恢复投影矩阵"""
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def paint(self, x : float, y : float) -> None:
        """在单帧渲染该图形"""
        global render_queue
        render_queue.append((self, x, y))


class Group:
    def __init__(self, *arg: Shape, origin : tuple[float, float]=(0.0, 0.0)):
        """
        图形组
        :param arg:    组中所有的图形
        :param origin: 图形组在屏幕中的位置
        """
        self.shapes = list(arg)
        self.origin = list(origin)

    def goto(self, x : float, y : float) -> None:
        """设置绝对位置"""
        self.origin[0] = x
        self.origin[1] = y

    def move(self, x : float, y : float) -> None:
        """相对移动"""
        self.origin[0] += x
        self.origin[1] += y

    def display(self) -> None:
        """单帧显示"""
        for shape in self.shapes:
            shape.paint(*self.origin)
