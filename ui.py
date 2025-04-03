"""
调用：soup3D.ui
soup3D的ui子库，用于绘制2D图形，可绘制HUD叠加显示、GUI用户界面等。
"""
from OpenGL.GLU import *
from math import*

from soup3D.img import *


class Shape:
    def __init__(self, shape_type, *args: tuple[float, ...], texture=None):
        """
        图形，可以批量生成线段、三角形
        :param shape_type: 绘制方式，可以填写这些内容：
                           "line_b": 不相连线段
                           "line_s": 连续线段
                           "line_l": 头尾相连的连续线段
                           "triangle_b": 不相连三角形
                           "triangle_s": 相连三角形
                           "triangle_l": 头尾相连的连续三角形
        :param args:       图形中所有的端点，每个参数的格式为：
                           (x, y, r, g, b)
                           或
                           (x, y, texture_x, texture_y)
        :param texture:    使用的纹理对象，默认为None
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
        self.points = args
        self.texture = texture
        self.display_list = None

        # 参数验证
        required_len = 5 if texture is None else 4
        for point in args:
            if len(point) != required_len:
                raise ValueError(f"Invalid point format. Expected {required_len} elements, got {len(point)}")

    def resize(self, width, height):
        """
        改变图形大小或宽高的比例
        :param width:  宽度(沿X轴)拉伸多少倍
        :param height: 高度(沿Y轴)拉伸多少倍
        :return: 新Shape实例
        """
        new_points = []
        for point in self.points:
            x = point[0] * width
            y = point[1] * height
            if self.texture:
                new_point = (x, y, point[2], point[3])
            else:
                new_point = (x, y, point[2], point[3], point[4])
            new_points.append(new_point)
        return Shape(self.type, *new_points, texture=self.texture)

    def turn(self, angle):
        """
        旋转图形
        :param angle: 图形旋转角度（度）
        :return: 新Shape实例
        """
        rad = radians(angle)
        cos_theta = cos(rad)
        sin_theta = sin(rad)
        new_points = []
        for point in self.points:
            x = point[0]
            y = point[1]
            new_x = x * cos_theta - y * sin_theta
            new_y = x * sin_theta + y * cos_theta
            if self.texture:
                new_point = (new_x, new_y, point[2], point[3])
            else:
                new_point = (new_x, new_y, point[2], point[3], point[4])
            new_points.append(new_point)
        return Shape(self.type, *new_points, texture=self.texture)

    def _setup_projection(self):
        """设置正交投影"""
        viewport = glGetIntegerv(GL_VIEWPORT)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, viewport[2], viewport[3], 0)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

    def _restore_projection(self):
        """恢复投影矩阵"""
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def paint(self, x, y):
        """在单帧渲染该图形"""
        type_menu = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }
        self._setup_projection()
        glPushMatrix()
        glTranslatef(x, y, 0)

        # 保存当前状态并禁用光照和深度测试
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)  # 新增：禁用深度测试

        if self.texture:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture.tex_id)
            if self.texture.transparent:
                # 使用混合处理透明度
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_TEXTURE_2D)

        glBegin(type_menu[self.type])
        for point in self.points:
            if self.texture:
                glTexCoord2f(point[2], point[3])
                glVertex2f(point[0], point[1])
            else:
                glColor3f(point[2], point[3], point[4])
                glVertex2f(point[0], point[1])
        glEnd()

        if self.texture and self.texture.transparent:
            glDisable(GL_BLEND)

        # 恢复之前的状态
        glPopAttrib()

        glPopMatrix()
        self._restore_projection()


class Group:
    def __init__(self, *arg: Shape, origin=(0.0, 0.0)):
        """
        图形组
        :param arg:    组中所有的图形
        :param origin: 图形组在屏幕中的位置
        """
        self.shapes = list(arg)
        self.origin = list(origin)

    def goto(self, x, y):
        """设置绝对位置"""
        self.origin[0] = x
        self.origin[1] = y

    def move(self, x, y):
        """相对移动"""
        self.origin[0] += x
        self.origin[1] += y

    def resize(self, width, height):
        """整体缩放"""
        new_shapes = [shape.resize(width, height) for shape in self.shapes]
        return Group(*new_shapes, origin=self.origin)

    def turn(self, angle):
        """整体旋转"""
        new_shapes = [shape.turn(angle) for shape in self.shapes]
        return Group(*new_shapes, origin=self.origin)

    def display(self):
        """单帧显示"""
        for shape in self.shapes:
            shape.paint(*self.origin)
