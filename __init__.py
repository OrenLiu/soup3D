"""
调用：soup3D
这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可
用于3D游戏开发、数据可视化、3D图形的绘制等开发。
"""
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
from math import *

import soup3D.event
import soup3D.camera
import soup3D.light
import soup3D.ui
from soup3D.name import *
from soup3D.img import *


__all__ = [
    'Shape', 'Group', 'Texture',
    'init', 'background_color', 'update', 'open_obj',
    'event', 'camera', 'light', 'name'
]

stable_shapes = {}

_current_fov = 45
_current_far = 1024


class Shape:
    def __init__(self, shape_type, *args: tuple[float, ...], texture=None, generate_normals=False):
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
                           (x, y, z, r, g, b)
                           或
                           (x, y, z, texture_x, texture_y)
        :param texture:    使用的纹理对象，默认为None
        :param generate_normals: 是否自动生成法线，仅适用于三角形类型
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
        self.normals = []
        self.display_list = None
        if generate_normals:
            self.calculate_normals()

    def _generate_display_list(self):
        self.display_list = glGenLists(1)
        glNewList(self.display_list, GL_COMPILE)

        # 设置纹理状态
        if self.texture is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture.tex_id)
            glColor3f(1.0, 1.0, 1.0)  # 新增行：设置颜色为白色
        else:
            glDisable(GL_TEXTURE_2D)

        # 确定绘制类型
        type_menu = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }
        glBegin(type_menu[self.type])

        for i, point in enumerate(self.points):
            # 验证参数完整性
            if self.texture:
                if len(point) < 5:
                    raise ValueError(f"Texture shape requires 5 parameters per point, got {len(point)}")
                glTexCoord2f(point[3], point[4])
            else:
                if len(point) < 6:
                    raise ValueError(f"Color shape requires 6 parameters per point, got {len(point)}")
                glColor3f(point[3], point[4], point[5])

            # 设置法线
            if self.normals and i < len(self.normals):
                glNormal3f(*self.normals[i])

            # 顶点坐标（原始坐标）
            glVertex3f(point[0], point[1], point[2])

        glEnd()
        glEndList()

    def calculate_normals(self):
        """
        自动计算三角形面的法线（仅支持triangle_b类型）
        :return: None
        """
        if not self.type.startswith("triangle"):
            raise ValueError("Automatic normal generation is only supported for triangle types.")

        if self.type == "triangle_b":
            num_points = len(self.points)
            if num_points % 3 != 0:
                raise ValueError("For triangle_b type, the number of vertices must be a multiple of 3.")

            self.normals = []
            for i in range(0, num_points, 3):
                # 获取三个顶点坐标
                v0 = self.points[i]
                v1 = self.points[i + 1]
                v2 = self.points[i + 2]

                # 转换为三维坐标
                p0 = (v0[0], v0[1], v0[2])
                p1 = (v1[0], v1[1], v1[2])
                p2 = (v2[0], v2[1], v2[2])

                # 计算两个边向量
                e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
                e2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])

                # 叉乘计算法线
                normal = (
                    e1[1] * e2[2] - e1[2] * e2[1],
                    e1[2] * e2[0] - e1[0] * e2[2],
                    e1[0] * e2[1] - e1[1] * e2[0]
                )

                # 归一化
                length = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5
                if length == 0:
                    normal = (0.0, 0.0, 0.0)
                else:
                    normal = (normal[0] / length, normal[1] / length, normal[2] / length)

                # 为每个顶点分配相同的面法线
                self.normals.extend([normal, normal, normal])
        else:
            raise NotImplementedError("Automatic normal generation is only supported for triangle_b type.")

    def resize(self, width, height, length, generate_normals=False):
        """
        改变物体大小或长宽高的比例
        :param width:            宽度(沿X轴)拉伸多少倍
        :param height:           高度(沿Y轴)拉伸多少倍
        :param length:           长度(沿Z轴)拉伸多少倍
        :param generate_normals: 是否计算发线
        :return: None
        """
        new_points = tuple((point[0]*width, point[1]*height, point[2]*length, *point[3:])
                           for i, point in enumerate(self.points))
        return Shape(self.type,
                     *new_points,
                     texture=self.texture,
                     generate_normals=generate_normals)

    def turn(self, yaw, pitch, roll, generate_normals=False):
        """
        旋转物体
        :param yaw:   图形旋转偏移角
        :param pitch: 图形旋转俯仰角
        :param roll:  图形旋转横滚角
        :return: None
        """
        new_points = tuple(
            (
                rotated(point[0], point[1], 0, 0, roll)[0],
                rotated(point[0], point[1], 0, 0, roll)[1],
                point[2],
                *point[3:]
            )
            for i, point in enumerate(self.points)
        )
        new_points = tuple(
            (
                point[0],
                rotated(point[1], point[2], 0, 0, pitch)[0],
                rotated(point[1], point[2], 0, 0, pitch)[1],
                *point[3:]
            )
            for i, point in enumerate(new_points)
        )
        new_points = tuple(
            (
                rotated(point[0], point[2], 0, 0, yaw)[0],
                point[1],
                rotated(point[0], point[2], 0, 0, yaw)[1],
                *point[3:]
            )
            for i, point in enumerate(new_points)
        )
        return Shape(self.type,
                     *new_points,
                     texture=self.texture,
                     generate_normals=generate_normals)

    def paint(self, x, y, z):
        """
        在单帧渲染该图形，当图形需要频繁切换形态、位置等参数时使用。
        :param x: 坐标x增值
        :param y: 坐标y增值
        :param z: 坐标z增值
        :return: None
        """
        if not self.display_list:  # 延迟初始化
            self._generate_display_list()

        glPushMatrix()
        glTranslatef(x, y, z)  # 动态应用坐标偏移
        glCallList(self.display_list)  # 复用显示列表
        glPopMatrix()

    def stable(self, x, y, z):
        """
        每帧固定渲染该图形，可以用于渲染固定场景，可提升性能。
        :param x: 坐标x增值
        :param y: 坐标y增值
        :param z: 坐标z增值
        :return: None
        """
        global stable_shapes

        if not self.display_list:  # 确保显示列表存在
            self._generate_display_list()

            # 注册坐标信息到全局字典
        stable_shapes[id(self)] = (self, x, y, z)

    def unstable(self):
        """
        取消stable的渲染
        :return: None
        """
        global stable_shapes
        if self.display_list is not None:
            stable_shapes.pop(id(self))
            glDeleteLists(self.display_list, 1)
            self.display_list = None


class Group:
    def __init__(self, *args: Shape, origin=(0.0, 0.0, 0.0)):
        """
        图形组，图形组中的所有图形的坐标都以组的原点为原点
        :param args:   组中所有的图形
        :param origin: 图形组在世界坐标的位置
        """
        self.shapes: list[Shape] = [i for i in args if type(i) is Shape]
        """
        图形列表，数据格式：
        [
            Shape1,
            Shape2,
            ...
        ]
        """
        self.origin = [float(i) for i in origin]

    def goto(self, x, y, z):
        """
        以世界坐标更改图形组位置
        :param x: 图形组x坐标
        :param y: 图形组y坐标
        :param z: 图形组z坐标
        :return: None
        """
        self.origin = [float(x), float(y), float(z)]

    def move(self, x, y, z):
        """
        以相对坐标更改图形组位置
        :param x: x增加多少
        :param y: y增加多少
        :param z: z增加多少
        :return: None
        """
        self.origin[0] += x
        self.origin[1] += y
        self.origin[2] += z

    def resize(self, width, height, length, generate_normals=False):
        """
        改变物体大小或长宽高的比例
        :param width:            宽度(沿X轴)拉伸多少倍
        :param height:           高度(沿Y轴)拉伸多少倍
        :param length:           长度(沿Z轴)拉伸多少倍
        :param generate_normals: 是否计算发线
        :return: None
        """
        new_shapes = [shape.resize(width, height, length, generate_normals) for i, shape in enumerate(self.shapes)]
        return Group(*new_shapes, origin=self.origin)

    def turn(self, yaw, pitch, roll, generate_normals=False):
        """
        旋转物体
        :param yaw:   图形旋转偏移角
        :param pitch: 图形旋转俯仰角
        :param roll:  图形旋转横滚角
        :return:
        """
        new_shapes = [shape.turn(yaw, pitch, roll, generate_normals) for i, shape in enumerate(self.shapes)]
        return Group(*new_shapes, origin=self.origin)

    def display(self):
        """
        单帧显示图形组
        :return: None
        """
        for shape in self.shapes:
            shape.paint(*self.origin)

    def display_stable(self):
        """
        每帧显示图形组
        :return: None
        """
        for shape in self.shapes:
            shape.stable(*self.origin)

    def hide(self):
        """
        隐藏图形组，相当于撤销display_stable操作
        :return: None
        """
        for shape in self.shapes:
            shape.unstable()


def init(width=1920, height=1080, fov=45, bg_color: tuple[float, float, float] = (0.0, 0.0, 0.0), far=1024):
    """
    初始化3D引擎
    :param width:    视网膜宽度
    :param height:   视网膜高度
    :param fov:      视野
    :param bg_color: 背景颜色
    :param far:      最远渲染距离
    :return: None
    """
    global _current_fov, _current_far
    _current_fov = fov
    _current_far = far

    pygame.init()  # 初始化pygame
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)  # 创建OpenGL上下文
    glClearColor(*bg_color, 1)  # 在上下文创建后设置背景颜色
    glEnable(GL_DEPTH_TEST)  # 启用深度测试
    glEnable(GL_BLEND)  # 启用混合
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合函数
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, (width / height), 0.1, far)
    soup3D.camera.goto(0, 0, 0)
    soup3D.camera.turn(0, 0, 0)


def resize(width, height):
    """
    重新定义窗口尺寸
    :param width:  窗口宽度
    :param height: 窗口高度
    :return: None
    """
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = width / height
    gluPerspective(_current_fov, aspect_ratio, 0.1, _current_far)
    glMatrixMode(GL_MODELVIEW)


def background_color(r, g, b):
    """
    设定背景颜色
    :param r: 红色(0.0-1.0)
    :param g: 绿色(0.0-1.0)
    :param b: 蓝色(0.0-1.0)
    :return:
    """
    glClearColor(r, g, b, 1)


def update():
    """
    更新画布
    """
    global stable_shapes

    # 先渲染所有不透明物体
    for shape_id in list(stable_shapes.keys()):
        shape, x, y, z = stable_shapes[shape_id]
        if not (shape.texture and shape.texture.transparent):
            glPushMatrix()
            glTranslatef(x, y, z)
            glCallList(shape.display_list)
            glPopMatrix()

    # 开启Alpha测试并渲染透明物体
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.1)  # 可根据需要调整阈值

    for shape_id in list(stable_shapes.keys()):
        shape, x, y, z = stable_shapes[shape_id]
        if shape.texture and shape.texture.transparent:
            glPushMatrix()
            glTranslatef(x, y, z)
            glCallList(shape.display_list)
            glPopMatrix()

    glDisable(GL_ALPHA_TEST)

    # 处理事件和刷新显示
    soup3D.event.check_event(pygame.event.get())
    pygame.display.flip()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


def open_obj(obj, mtl=None) -> Group:
    """
    打开一个obj模型文件和mtl纹理文件，并生成图形组(Group类)
    :param obj: 模型文件位置
    :param mtl: 纹理文件位置
    :return: 图形组(Group类)
    """
    import os  # 新增导入

    class Material:
        def __init__(self):
            self.diffuse = (1, 1, 1)
            self.texture = None
            self.ambient = (0.2, 0.2, 0.2)

    materials = {}
    current_mat = None
    mtl_dir = ""  # 新增变量存储mtl文件目录

    if mtl is not None:
        # 获取mtl文件的绝对路径和目录
        mtl_abspath = os.path.abspath(mtl)
        mtl_dir = os.path.dirname(mtl_abspath)

        with open(mtl, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split(maxsplit=1)
                if not parts:
                    continue

                key = parts[0]
                if key == 'newmtl':
                    current_mat = parts[1].strip()
                    materials[current_mat] = Material()
                elif key == 'Kd' and current_mat:
                    materials[current_mat].diffuse = tuple(map(float, parts[1].split()[:3]))
                elif key == 'map_Kd' and current_mat:
                    # 处理可能包含空格的路径
                    texture_file = parts[1].strip().replace('\\', '/')
                    # 拼接绝对路径
                    texture_path = os.path.normpath(os.path.join(mtl_dir, texture_file))
                    try:
                        with Image.open(texture_path) as img:
                            img = img.convert('RGBA').transpose(Image.FLIP_TOP_BOTTOM)
                            texture = Texture(
                                img.tobytes(),
                                img.width,
                                img.height,
                                img_type=RGBA,
                                wrap_x=REPEAT,
                                wrap_y=REPEAT
                            )
                        materials[current_mat].texture = texture
                    except Exception as e:
                        print(f"加载纹理失败: {e}")

        # === 2. 解析OBJ模型文件 ===
        vertices = []
        tex_coords = []
        groups = {}
        current_mat = None

    with open(obj, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            if line.startswith('v '):
                x, orig_y, orig_z = map(float, line.split()[1:4])
                vertices.append((x, orig_z, orig_y))  # 坐标系转换
            elif line.startswith('vt '):  # 纹理坐标
                tex_coords.append(tuple(map(float, line.split()[1:3])))
            elif line.startswith('usemtl'):  # 使用材质
                current_mat = line.split()[1]
                if current_mat not in groups:
                    groups[current_mat] = []
            elif line.startswith('f '):  # 面定义
                face = []
                for vertex in line.split()[1:]:
                    indices = vertex.split('/')
                    # 解析顶点索引（支持v/vt/vn格式）
                    v_idx = int(indices[0]) - 1
                    vt_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else None

                    # 获取材质属性
                    mat = materials.get(current_mat, Material())

                    # 构建顶点数据
                    if mat.texture:  # 纹理模式
                        tex = tex_coords[vt_idx] if vt_idx is not None else (0, 0)
                        face.append((
                            *vertices[v_idx],  # x,y,z
                            *tex  # u,v
                        ))
                    else:  # 颜色模式
                        face.append((
                            *vertices[v_idx],  # x,y,z
                            *mat.diffuse  # r,g,b
                        ))

                # 三角剖分（处理四边形面）
                for i in range(2, len(face)):
                    groups[current_mat].extend([face[0], face[i - 1], face[i]])

    # === 3. 创建Shape对象 ===
    shapes = []
    for mat_name, points in groups.items():
        mat = materials.get(mat_name, Material())

        # 每3个点组成一个三角形
        shape_type = "triangle_b"
        shapes.append(Shape(
            shape_type,
            *points,
            texture=mat.texture,
            generate_normals=True
        ))

    return Group(*shapes)


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


if __name__ == '__main__':
    init(bg_color=(1, 1, 1))

    running = True
    soup3D.event.bind(MOUSE_WHEEL, print)
    tri = Shape(TRIANGLE_L,
                (1, 0, 0, 1, 1, 1),
                (0, 0, 0, 1, 1, 1),
                (0, 1, 0, 1, 1, 1))
    while running:
        tri.paint(0, 0, -5)
        update()
