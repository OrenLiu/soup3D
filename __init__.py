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
import os

import soup3D.shader
import soup3D.event
import soup3D.camera
import soup3D.light
import soup3D.ui
from soup3D.name import *

render_queue: list["Model"] = []  # 全局渲染队列
stable_shapes = {}

_current_fov = 45
_current_far = 1024


class Face:
    def __init__(self,
                 shape_type: str,
                 surface: soup3D.shader.FPL | soup3D.shader.ShaderProgram,
                 vertex: list | tuple) -> None:
        """
        表面，可用于创建模型(Model类)的线段和多边形
        :param shape_type: 绘制方式，可以填写这些内容：
                           "line_b": 不相连线段
                           "line_s": 连续线段
                           "line_l": 头尾相连的连续线段
                           "triangle_b": 不相连三角形
                           "triangle_s": 相连三角形
                           "triangle_l": 头尾相连的连续三角形
        :param surface:    表面使用的BSDF着色器
        :param vertex:     表面中所有的端点，格式为：
                           [(x, y, z, u, v), ...]
        """
        # 初始化类成员
        self.shape_type = shape_type  # 绘制方式
        self.surface = surface        # 表面着色单元
        self.vertex = vertex          # 表面端点

        # 设置OpenGL绘制模式
        self.mode_map = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }

        if shape_type not in self.mode_map:  # 确认绘制方式是否存在
            raise ValueError(f"unknown shape_type: {shape_type}")  # 抛出未知绘制方式的异常

        self.mode = self.mode_map[shape_type]  # 转换为OpenGL绘制模式

        # 3. 计算平面法线方向
        if len(vertex) >= 3:
            v0 = vertex[0]
            v1 = vertex[1]
            v2 = vertex[2]

            # 计算两个向量
            u = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            v = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

            # 叉乘得到法线
            self.normal = (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0]
            )
        else:
            self.normal = (0, 0, 1)  # 默认Z轴正向


class Model:
    def __init__(self, x: int | float, y: int | float, z: int | float, *face: Face) -> None:
        """
        模型，由多个面(Face类)组成，建议将场景中的面组合成尽量少的模型
        :param x:    模型原点对应x坐标
        :param y:    模型原点对应y坐标
        :param z:    模型原点对应z坐标
        :param face: 面
        """
        self.x, self.y, self.z = x, y, z
        self.yaw, self.pitch, self.roll = 0, 0, 0
        self.width, self.height, self.length = 1, 1, 1
        self.faces = list(face)

        self.list_id = glGenLists(1)
        self._generate_display_list()

    def paint(self) -> None:
        """
        在单帧绘制该模型
        :return: None
        """
        render_queue.append(self)

    def _generate_display_list(self) -> None:
        """生成OpenGL显示列表，应用材质属性"""
        # 创建显示列表
        glNewList(self.list_id, GL_COMPILE)
        for face in self.faces:

            # 材质贴图
            texture_id = face.surface.base_color_id

            # 启用必要的OpenGL功能
            glEnable(GL_DEPTH_TEST)

            # 设置材质属性
            if texture_id:
                # 使用纹理时不设置颜色
                glColor4f(1.0, 1.0, 1.0, 1.0)
            else:
                # 如果没有纹理，使用基色
                if isinstance(face.surface.base_color, tuple):
                    base_color = face.surface.base_color
                else:
                    base_color = (1.0, 1.0, 1.0)  # 默认白色
                glColor4f(base_color[0], base_color[1], base_color[2], 1.0)

            # 开启纹理
            if texture_id:
                glEnable(GL_TEXTURE_2D)

            # 激活并绑定材质贴图（纹理单元0）
            if texture_id:
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, texture_id)
                glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

            # 自发光处理
            if face.surface.emission != 0.0:
                emission = max(0.0, min(1.0, float(face.surface.emission)))
                glMaterialfv(GL_FRONT, GL_EMISSION, (emission, emission, emission, 1.0))

            # 绘制几何图形
            glBegin(face.mode)
            glNormal3f(face.normal[0], face.normal[1], face.normal[2])
            for v in face.vertex:
                if len(v) == 5:
                    # 设置纹理坐标
                    if texture_id:
                        glMultiTexCoord2f(GL_TEXTURE0, v[3], v[4])  # base_color纹理
                    glVertex3f(v[0], v[1], v[2])
                else:
                    # 没有纹理坐标的情况
                    glVertex3f(v[0], v[1], v[2])
            glEnd()

            # 清理OpenGL状态
            if texture_id:
                glDisable(GL_TEXTURE_2D)
                glActiveTexture(GL_TEXTURE0)

            if face.surface.emission != 0.0:
                glMaterialfv(GL_FRONT, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

        glEndList()

    def show(self) -> None:
        """
        固定每帧渲染该模型
        :return: None
        """
        global stable_shapes
        stable_shapes[id(self)] = self

    def hide(self) -> None:
        """
        取消固定渲染
        :return: None
        """
        global stable_shapes
        stable_shapes.pop(id(self))

    def goto(self, x: int | float, y: int | float, z: int | float) -> None:
        """
        传送模型
        :param x: 新x坐标
        :param y: 新y坐标
        :param z: 新z坐标
        :return: None
        """
        self.x, self.y, self.z = x, y, z

    def turn(self, yaw: int | float, pitch: int | float, roll: int | float) -> None:
        """
        旋转模型
        :param yaw:   偏移角度，绕世界z轴旋转
        :param pitch: 俯仰角度，绕模型x轴旋转
        :param roll:  横滚角度，绕模型y轴旋转
        :return: None
        """
        self.yaw, self.pitch, self.roll = yaw, pitch, roll

    def size(self, width: int | float, height: int | float, length: int | float) -> None:
        """
        模型尺寸缩放
        :param width:  模型宽度倍数，沿模型x轴缩放的倍数
        :param height: 模型高度倍数，沿模型y轴缩放的倍数
        :param length: 模型长度倍数，沿模型z轴缩放的倍数
        :return: None
        """
        self.width, self.height, self.length = width, height, length

    def deep_del(self) -> None:
        """
        深度清理模型，清理该模型本身及所有该模型用到的元素。在确定不再使用该模型时可使用该方法释放内存。
        :return: None
        """
        global render_queue
        global stable_shapes

        # 1. 清理顶点列表
        glDeleteLists(self.list_id, 1)

        # 2. 清理所有面使用的纹理资源
        for face in self.faces:
            # 清理基础色纹理
            if face.surface.base_color_id:
                glDeleteTextures([face.surface.base_color_id])

        # 3. 从全局渲染队列中移除（如果存在）
        if self in render_queue:
            render_queue.remove(self)

        # 4. 从稳定形状中移除（如果存在）
        if id(self) in stable_shapes:
            stable_shapes.pop(id(self))


def _get_channel_value(channel : soup3D.shader.Channel) -> float:
    """从Channel对象或浮点数获取通道值"""
    if isinstance(channel, soup3D.shader.Channel):
        # 对于纹理通道，我们不再使用平均值，而是使用纹理
        return 0.5  # 返回中间值，实际值将由纹理提供
    elif isinstance(channel, float) or isinstance(channel, int):
        return float(channel)
    return 1.0


def init(width : int | float=1920, height : int | float=1080, fov : int | float=45, bg_color: tuple[float, float, float] = (0.0, 0.0, 0.0), far : int | float=1024) -> None:
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
    pygame.display.set_caption("soup3D")
    current_file = os.path.abspath(__file__)
    package_dir = os.path.dirname(current_file)
    soup3D.set_ico(os.path.join(package_dir, "osoup.png"))
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


def resize(width : int | float, height : int | float) -> None:
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


def set_title(title: str) -> None:
    """
    设置窗口标题
    :param title: 窗口标题
    :return: None
    """
    pygame.display.set_caption(title)


def set_ico(path : str) -> None:
    """
    设置窗口图标
    :param path: 图标所在位置
    :return: None
    """
    icon = pygame.image.load(path)
    pygame.display.set_icon(icon)


def background_color(r : float, g : float, b : float) -> None:
    """
    设定背景颜色
    :param r: 红色(0.0-1.0)
    :param g: 绿色(0.0-1.0)
    :param b: 蓝色(0.0-1.0)
    :return: None
    """
    glClearColor(r, g, b, 1)


def _paint_ui(shape : soup3D.ui.Shape, x : int | float, y : int | float) -> None:
    """在单帧渲染该图形"""
    type_menu = {
        "line_b": GL_LINES,
        "line_s": GL_LINE_STRIP,
        "line_l": GL_LINE_LOOP,
        "triangle_b": GL_TRIANGLES,
        "triangle_s": GL_TRIANGLE_STRIP,
        "triangle_l": GL_TRIANGLE_FAN
    }
    shape._setup_projection()
    glPushMatrix()
    glTranslatef(x, y, 0)

    # 保存当前状态并禁用光照和深度测试
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)  # 新增：禁用深度测试

    if shape.texture:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, shape.tex_id)

        # 使用混合处理透明度
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    else:
        glDisable(GL_TEXTURE_2D)

    glBegin(type_menu[shape.type])
    for point in shape.vertex:
        glTexCoord2f(point[2], 1-point[3])
        glVertex2f(point[0], point[1])
    glEnd()

    glDisable(GL_BLEND)

    # 恢复之前的状态
    glPopAttrib()

    glPopMatrix()
    shape._restore_projection()


def update() -> None:
    """
    更新画布，包括处理渲染队列
    """
    global render_queue

    # 将所有固定渲染场景加入全局渲染列队
    for shape_id in stable_shapes:
        shape = stable_shapes[shape_id]
        shape.paint()

    # 处理事件
    soup3D.event.check_event(pygame.event.get())

    # 渲染所有物体
    for model in render_queue:
        # 获取位置
        x, y, z = model.x, model.y, model.z
        yaw, pitch, roll = model.yaw, model.pitch, model.roll
        width, height, length = model.width, model.height, model.length

        # 实际渲染
        glPushMatrix()

        # 应用模型位置
        glTranslatef(x, y, z)
        # 应用模型旋转
        glRotatef(roll, 1, 0, 0)
        glRotatef(pitch, 0, 0, 1)
        glRotatef(yaw, 0, 1, 0)
        # 应用模型缩放
        glScalef(width, height, length)

        glCallList(model.list_id)
        glPopMatrix()

    # 清空渲染队列
    render_queue = []

    # 渲染ui界面
    for i in soup3D.ui.render_queue:
        _paint_ui(*i)

    # 清空ui渲染列队
    soup3D.ui.render_queue = []

    # 刷新显示
    pygame.display.flip()
    # 清空画布
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)


def open_obj(obj : str, mtl : str=None) -> Model:
    """
    从obj文件导入模型
    :param obj: *.obj模型文件路径
    :param mtl: *.mtl纹理文件路径
    :return: 生成出来的模型数据(Model类)
    """
    # 处理mtl文件
    mtl_dict = {}
    if mtl is not None:
        mtl_file = open(mtl, "r")
        mtl_str = mtl_file.read()
        mtl_file.close()
        command_lines = mtl_str.split("\n")
        line_count = 1
        now_mtl = None

        R, G, B, A = 1.0, 1.0, 1.0, 1.0
        width, height = 1, 1
        emission = 0
        for row in command_lines:
            command = row.split("#")[0]
            args = command.split()
            if len(args) > 0:
                if args[0] == "newmtl":
                    if now_mtl is not None:
                        mtl_dict[now_mtl] = soup3D.shader.FPL(
                            soup3D.shader.MixChannel((width, height), R, G, B, A),
                            emission=emission
                        )

                        R, G, B, A = 1.0, 1.0, 1.0, 1.0
                        width, height = 1, 1
                        emission = 0
                    now_mtl = args[1]
                if args[0] == "Kd":
                    R, G, B = float(args[1]), float(args[2]), float(args[3])
                if args[0] == "d":
                    A = float(args[1])
                if args[0] == "Ke":
                    # 使用RGB中的最大值作为自发光强度
                    emission = max(float(args[1]), float(args[2]), float(args[3]))
                if args[0] == "map_Kd":
                    # 处理带空格的纹理路径：获取命令后的全部字符串作为路径
                    tex_path = command.split()[1:]  # 获取文件名部分(可能包含空格)
                    tex_path = " ".join(tex_path)  # 重新组合路径
                    # 处理可能的引号包裹的路径
                    if tex_path.startswith('"') and tex_path.endswith('"'):
                        tex_path = tex_path[1:-1]
                    # 构建完整的相对路径
                    base_dir = os.path.dirname(mtl)
                    tex_path = os.path.join(base_dir, tex_path)
                    pil_pic = Image.open(tex_path)
                    width, height = pil_pic.width, pil_pic.height
                    texture = soup3D.shader.Texture(pil_pic)
                    R = soup3D.shader.Channel(texture, 0)
                    G = soup3D.shader.Channel(texture, 1)
                    B = soup3D.shader.Channel(texture, 2)
                if args[0] == "map_d":
                    # 同样处理map_d命令的路径
                    tex_path = command.split()[1:]
                    tex_path = " ".join(tex_path)
                    if tex_path.startswith('"') and tex_path.endswith('"'):
                        tex_path = tex_path[1:-1]
                    base_dir = os.path.dirname(mtl)
                    tex_path = os.path.join(base_dir, tex_path)
                    texture = soup3D.shader.Texture(Image.open(tex_path))
                    A = soup3D.shader.Channel(texture, 3)
            line_count += 1

        # 添加最后一个材质
        if now_mtl is not None:
            mtl_dict[now_mtl] = soup3D.shader.FPL(
                soup3D.shader.MixChannel((width, height), R, G, B, A),
                emission=emission
            )

    # 创建默认材质（如果未提供MTL或材质未定义时使用）
    default_material = soup3D.shader.FPL(
        soup3D.shader.MixChannel((1, 1), 1.0, 1.0, 1.0, 1.0),
        emission=0.0
    )

    # 处理obj文件
    vertices = []  # 顶点坐标 (x, y, z)
    tex_coords = []  # 纹理坐标 (u, v)
    normals = []  # 法线向量 (nx, ny, nz)
    faces = []  # 存储解析出的面数据

    # 当前使用的材质
    current_material = None

    with open(obj, 'r') as obj_file:
        for line in obj_file:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if not parts:
                continue

            prefix = parts[0]
            data = parts[1:]

            # 处理顶点数据
            if prefix == 'v':
                # 顶点坐标 (x, y, z [, w])
                if len(data) >= 3:
                    x, y, z = map(float, data[:3])
                    vertices.append((x, y, z))

            # 处理纹理坐标
            elif prefix == 'vt':
                # 纹理坐标 (u, v [, w])
                if len(data) >= 2:
                    u, v = map(float, data[:2])
                    tex_coords.append((u, v))

            # 处理法线
            elif prefix == 'vn':
                # 法线向量 (x, y, z)
                if len(data) >= 3:
                    nx, ny, nz = map(float, data[:3])
                    normals.append((nx, ny, nz))

            # 处理材质库引用
            elif prefix == 'mtllib':
                # 已在外部处理，无需二次处理
                pass

            # 处理材质使用
            elif prefix == 'usemtl':
                # 切换当前使用的材质
                if data:
                    material_name = data[0]
                    # 如果材质在库中未定义，使用默认材质
                    current_material = mtl_dict.get(material_name, default_material)

            # 处理面定义
            elif prefix == 'f':
                if len(data) < 3:
                    continue  # 至少需要3个顶点构成面

                face_vertices = []

                # 多边形三角剖分（简单实现，适合凸多边形）
                base_indexes = []
                for vertex_def in data:
                    # 解析顶点/纹理/法线索引（格式如：v/vt/vn 或 v//vn 等）
                    indexes = vertex_def.split('/')

                    # 处理缺少纹理坐标的情况（填充空值）
                    while len(indexes) < 3:
                        indexes.append('')

                    # 转换索引为整数（索引从1开始，需要转为0开始）
                    # 支持负数索引（从末尾开始计数）
                    v_idx = int(indexes[0]) - 1 if indexes[0] else -1
                    vt_idx = int(indexes[1]) - 1 if indexes[1] else -1
                    vn_idx = int(indexes[2]) - 1 if indexes[2] else -1

                    # 处理负索引（相对索引）
                    if v_idx < 0: v_idx = len(vertices) + v_idx
                    if vt_idx < 0: vt_idx = len(tex_coords) + vt_idx
                    if vn_idx < 0: vn_idx = len(normals) + vn_idx

                    # 获取顶点数据（确保索引在有效范围内）
                    vert = list(vertices[v_idx])

                    # 如果有纹理坐标，添加纹理坐标
                    if 0 <= vt_idx < len(tex_coords):
                        u, v = tex_coords[vt_idx]
                        vert.extend([u, v])

                    base_indexes.append(tuple(vert))

                # 简单三角剖分：使用第一个顶点为基准，连接其他顶点形成三角形
                for i in range(1, len(base_indexes) - 1):
                    # 每个三角形由第一个顶点和连续的两个顶点组成
                    triangle = [
                        base_indexes[0],
                        base_indexes[i],
                        base_indexes[i + 1]
                    ]
                    # 添加到面的顶点列表
                    face_vertices.append(triangle)

                # 创建面对象（使用当前材质）
                material = current_material if current_material else default_material

                # 将三角剖分后的所有三角形面加入列表
                for tri_vertices in face_vertices:
                    face = Face(
                        shape_type="triangle_b",  # 分离的三角形
                        surface=material,
                        vertex=tri_vertices
                    )
                    faces.append(face)

    # 创建模型对象（原点设置为0,0,0）
    model = Model(0, 0, 0, *faces)
    return model


def _rotated(Xa : int | float, Ya : int | float, Xb : int | float, Yb : int | float, degree : int | float) -> tuple[float, float]:
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
    ...
