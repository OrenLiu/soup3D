"""
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
from soup3D.name import *


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
        self.type_menu = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }
        if shape_type not in self.type_menu:
            raise TypeError(f"unknown type: {shape_type}")
        self.type = shape_type
        self.points = args
        self.texture = texture
        self.normals = []
        if generate_normals:
            self.calculate_normals()

    def calculate_normals(self):
        """自动计算三角形面的法线（仅支持triangle_b类型）"""
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

    def paint(self, x, y, z):
        # 状态设置必须在glBegin/glEnd之外
        if self.texture is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, self.texture.tex_id)
            tex_coord_dim = 2  # 纹理坐标维度
        else:
            glDisable(GL_TEXTURE_2D)
            color_dim = 3  # 颜色维度

        glBegin(self.type_menu[self.type])
        for i, point in enumerate(self.points):
            # 参数完整性验证
            if self.texture:
                if len(point) < 5:
                    raise ValueError(f"Texture shape requires 5 parameters per point, got {len(point)}")
                glTexCoord2f(*point[3:5])
            else:
                if len(point) < 6:
                    raise ValueError(f"Color shape requires 6 parameters per point, got {len(point)}")
                glColor3f(*point[3:6])

            # 设置法线（如果存在）
            if self.normals and i < len(self.normals):
                glNormal3f(*self.normals[i])

            glVertex3f(
                x + point[0],
                y + point[1],
                z + point[2]
            )
        glEnd()


class Group:
    def __init__(self, *args: Shape, origin: tuple[float] = (0.0, 0.0, 0.0)):
        """
        图形组，图形组中的所有图形的坐标都以组的原点为原点
        :param args: 组中所有的图形
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

    def display(self):
        """
        显示图形组
        """
        for shape in self.shapes:
            shape.paint(*self.origin)


class Texture:
    def __init__(self, img, width, height, wrap_x="edge", wrap_y="edge", linear=False):
        """
        材质纹理贴图，当图形需要贴图时，在Shape的texture
        赋值该类型

        :param img:    贴图的二进制数据（需为RGB格式）
        :param width:  贴图的宽度（像素）
        :param height: 贴图的高度（像素）
        :param wrap_x: x轴环绕方式，当取色坐标超出图片范
                       围时的取色方案，可为：
                       "repeat" -> 重复图像
                       "mirrored" -> 镜像图像
                       "edge" -> 延生边缘像素
                       "border" -> 纯色图像
        :param wrap_y: y轴环绕方式（参数同wrap_x）
        :param linear: 是否使用抗锯齿，True使用
                       GL_LINEAR插值，False使用
                       GL_NEAREST[6](@ref)
        """
        # 转换参数为OpenGL常量
        wrap_map = {
            "repeat": GL_REPEAT,
            "mirrored": GL_MIRRORED_REPEAT,
            "edge": GL_CLAMP_TO_EDGE,
            "border": GL_CLAMP_TO_BORDER
        }

        # 生成纹理对象
        self.tex_id = glGenTextures(1)  # 生成纹理ID[6,7](@ref)
        glBindTexture(GL_TEXTURE_2D, self.tex_id)

        # 设置纹理参数
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_map[wrap_x])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_map[wrap_y])
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR if linear else GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                        GL_LINEAR if linear else GL_NEAREST)

        # 加载纹理数据
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height,
                     0, GL_RGB, GL_UNSIGNED_BYTE, img)  # [6,7](@ref)


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
    pygame.init()  # 初始化pygame
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)  # 创建OpenGL上下文
    glClearColor(*bg_color, 1)  # 在上下文创建后设置背景颜色
    glEnable(GL_DEPTH_TEST)  # 启用深度测试
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, (width / height), 0.1, far)
    soup3D.camera.goto(0, 0, 0)
    soup3D.camera.turn(0, 0, 0)


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
    soup3D.event.check_event(pygame.event.get())
    pygame.display.flip()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


def open_obj(obj, mtl) -> Group:
    """
    打开一个obj模型文件和mtl纹理文件，并生成图形组(Group类)
    :param obj: 模型文件位置
    :param mtl: 纹理文件位置
    :return: 图形组(Group类)
    """

    # 材质数据结构
    class Material:
        def __init__(self):
            self.diffuse = (1, 1, 1)  # 默认白色
            self.texture = None
            self.ambient = (0.2, 0.2, 0.2)

    # === 1. 解析MTL材质文件 ===
    materials = {}
    current_mat = None

    with open(mtl, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue

            parts = line.split()
            if parts[0] == 'newmtl':
                current_mat = parts[1]
                materials[current_mat] = Material()
            elif parts[0] == 'Kd':  # 漫反射颜色
                materials[current_mat].diffuse = tuple(map(float, parts[1:4]))
            elif parts[0] == 'map_Kd':  # 纹理贴图
                try:
                    img_path = line.split(' ', 1)[1].replace('\\', '/')
                    with Image.open(img_path) as img:
                        img = img.convert('RGB')
                        texture = Texture(
                            img.tobytes(),
                            img.width,
                            img.height,
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
