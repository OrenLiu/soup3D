"""
调用：soup3D
这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可
用于3D游戏开发、数据可视化、3D图形的绘制等开发。
"""
from OpenGL.GLU import *
from pyglm import glm
from PIL import Image
import os
import shlex

import soup3D.shader
import soup3D.camera
import soup3D.light
import soup3D.ui
from soup3D.name import *

render_queue: list["Model"] = []  # 单次渲染队列
stable_shapes = {}                # 固定渲染队列
EAU = []                          # 更新执行队列


_current_fov = 45
_current_near = 0.1
_current_far = 1024

_current_width = 1920
_current_height = 1080


class Face:
    def __init__(self,
                 shape_type: str,
                 surface: soup3D.shader.Surface,
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
        :param surface:    表面使用的着色器
        :param vertex:     表面中所有的顶点，格式由surface参数指定的着色器决定
        """
        # 初始化类成员
        self.shape_type = shape_type  # 绘制方式
        self.surface = surface  # 表面着色器元
        self.vertex = vertex  # 表面端点

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

        # 将表面按照表面着色器分类
        self.face_groups = {}
        for face in self.faces:
            surface = face.surface
            if id(surface) not in self.face_groups:
                self.face_groups[id(surface)] = []
            self.face_groups[id(surface)].append(face)
            if hasattr(surface, "set_model_mat"):
                surface.set_model_mat(self.get_model_mat())
            if hasattr(surface, "set_projection_mat"):
                surface.set_projection_mat(get_projection_mat())
            if hasattr(surface, "set_view_mat"):
                surface.set_view_mat(soup3D.camera.get_view_mat())

        self.list_id = glGenLists(1)

        # 创建显示列表
        self.surfaces = {}
        glNewList(self.list_id, GL_COMPILE)
        for surface_id in self.face_groups:
            faces = self.face_groups[surface_id]
            for i, face in enumerate(faces):
                surface = face.surface
                if id(surface) not in self.surfaces:
                    self.surfaces[id(surface)] = surface
                if i == 0 and hasattr(surface, "use"):
                    surface.use()
                surface.rend(face.mode, face.vertex)
                if i == len(faces)-1 and hasattr(surface, "unuse"):
                    surface.unuse()

        glEndList()

    def paint(self) -> None:
        """
        在单帧绘制该模型
        :return: None
        """
        render_queue.append(self)

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
        for surface_id in self.surfaces:
            surface = self.surfaces[surface_id]
            if hasattr(surface, "set_model_mat"):
                surface.set_model_mat(self.get_model_mat())

    def turn(self, yaw: int | float, pitch: int | float, roll: int | float) -> None:
        """
        旋转模型
        :param yaw:   偏移角度，绕世界z轴旋转
        :param pitch: 俯仰角度，绕模型x轴旋转
        :param roll:  横滚角度，绕模型y轴旋转
        :return: None
        """
        self.yaw, self.pitch, self.roll = yaw, pitch, roll
        for surface_id in self.surfaces:
            surface = self.surfaces[surface_id]
            if hasattr(surface, "set_model_mat"):
                surface.set_model_mat(self.get_model_mat())

    def size(self, width: int | float, height: int | float, length: int | float) -> None:
        """
        模型尺寸缩放
        :param width:  模型宽度倍数，沿模型x轴缩放的倍数
        :param height: 模型高度倍数，沿模型y轴缩放的倍数
        :param length: 模型长度倍数，沿模型z轴缩放的倍数
        :return: None
        """
        self.width, self.height, self.length = width, height, length
        for surface_id in self.surfaces:
            surface = self.surfaces[surface_id]
            if hasattr(surface, "set_model_mat"):
                surface.set_model_mat(self.get_model_mat())

    def get_model_mat(self) -> glm.mat4:
        """
        获取模型矩阵，可用于代码着色器
        :return: 模型变换矩阵
        """
        # 创建单位矩阵
        model = glm.mat4(1.0)

        # 应用平移变换
        model = glm.translate(model, glm.vec3(self.x, self.y, self.z))

        # 应用旋转变换
        # Yaw旋转（绕y轴）
        model = glm.rotate(model, glm.radians(-self.yaw), glm.vec3(0.0, 1.0, 0.0))
        # Pitch旋转（绕x轴）
        model = glm.rotate(model, glm.radians(self.pitch), glm.vec3(1.0, 0.0, 0.0))
        # Roll旋转（绕z轴）
        model = glm.rotate(model, glm.radians(self.roll), glm.vec3(0.0, 0.0, 1.0))

        # 应用缩放变换
        model = glm.scale(model, glm.vec3(self.width, self.height, self.length))

        return model

    def __del__(self) -> None:
        """
        深度清理模型，清理该模型本身及所有该模型用到的元素。在确定不再使用该模型时可使用该方法释放内存。
        :return: None
        """
        global render_queue
        global stable_shapes

        # 清理顶点列表
        glDeleteLists(self.list_id, 1)

        # 从全局渲染队列中移除（如果存在）
        if self in render_queue:
            render_queue.remove(self)

        # 从稳定形状中移除（如果存在）
        if id(self) in stable_shapes:
            stable_shapes.pop(id(self))


def init(width: int | float = 1920,
         height: int | float = 1080,
         fov: int | float = 45,
         bg_color: tuple[int | float, int | float, int | float] = (0.0, 0.0, 0.0),
         near: int | float = 0.1,
         far: int | float = 1024) -> None:
    """
    初始化3D引擎
    :param width:    视网膜宽度
    :param height:   视网膜高度
    :param fov:      视野
    :param bg_color: 背景颜色
    :param near:     最近渲染距离
    :param far:      最远渲染距离
    :return: None
    """
    global _current_fov, _current_near, _current_far
    global _current_width, _current_height
    _current_fov = fov
    _current_near = near
    _current_far = far

    _current_width = width
    _current_height = height

    glClearColor(*bg_color, 1)  # 在上下文创建后设置背景颜色
    glEnable(GL_DEPTH_TEST)  # 启用深度测试
    glEnable(GL_BLEND)  # 启用混合
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)  # 设置混合函数
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fov, (width / height), near, far)
    soup3D.camera.goto(0, 0, 0)
    soup3D.camera.turn(0, 0, 0)


def resize(width: int | float, height: int | float) -> None:
    """
    重新定义窗口尺寸
    :param width:  窗口宽度
    :param height: 窗口高度
    :return: None
    """
    global _current_width, _current_height

    _current_width = width
    _current_height = height

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = width / height
    gluPerspective(_current_fov, aspect_ratio, _current_near, _current_far)
    glMatrixMode(GL_MODELVIEW)

    for surface_id in soup3D.shader.set_mat_queue:
        surface = soup3D.shader.set_mat_queue[surface_id]
        if hasattr(surface, "set_projection_mat"):
            surface.set_projection_mat(get_projection_mat())


def background_color(r: int | float, g: int | float, b: int | float) -> None:
    """
    设定背景颜色
    :param r: 红色(0.0-1.0)
    :param g: 绿色(0.0-1.0)
    :param b: 蓝色(0.0-1.0)
    :return: None
    """
    glClearColor(r, g, b, 1)


def _paint_ui(shape: soup3D.ui.Shape, x: int | float, y: int | float) -> None:
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
        glTexCoord2f(point[2], 1 - point[3])
        glVertex2f(point[0], point[1])
    glEnd()

    glDisable(GL_BLEND)

    # 恢复之前的状态
    glPopAttrib()

    glPopMatrix()
    shape._restore_projection()


def update():
    """
    更新画布
    """
    global render_queue, EAU

    # 清空画布
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 设置光源
    if soup3D.light.dirty:
        soup3D.light.set_surface_light()

    # 执行更新执行列队
    EAU += soup3D.shader.EAU
    EAU += soup3D.light.EAU

    EAU_len = len(EAU)  # 调用列队前列队的长度
    for args in EAU:
        args[0](*args[1:])
        if EAU_len != len(EAU):
            raise Exception(f"EAU length changed while running: {args[0].__name__}{(*args[1:],)}")

    EAU = []
    shader.EAU = []
    light.EAU = []

    # 将所有固定渲染场景加入全局渲染列队
    for shape_id in stable_shapes:
        shape = stable_shapes[shape_id]
        glCallList(shape.list_id)

    # 渲染所有物体
    for model in render_queue:
        glCallList(model.list_id)

    # 清空渲染队列
    render_queue = []

    # 渲染ui界面
    for i in soup3D.ui.render_queue:
        _paint_ui(*i)

    # 清空ui渲染列队
    soup3D.ui.render_queue = []


def open_mtl(mtl: str,
             double_side: bool = True,
             roll_funk=None,
             encoding: str = "utf-8",
             max_light_count: int = 8,
             surface = soup3D.shader.AutoSP) -> dict[str: soup3D.shader.Surface]:
    """
    根据mtl文件生成多个着色器
    :param mtl:             *.mtl纹理文件路径
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取mtl文件时使用的字符集
    :param max_light_count: 这些着色器出现时会同时出现的最多的光源数量
    :param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side, max_light_count等
                            参数
    :return: 所有生成出的表面着色器
    """
    mtl_dict = {}

    mtl_file = open(mtl, "r", encoding=encoding)
    mtl_str = mtl_file.read()
    mtl_file.close()

    command_lines = mtl_str.split("\n")
    now_mtl = None

    R, G, B, A = 1.0, 1.0, 1.0, 1.0
    width, height = 1, 1
    emission = 0, 0, 0
    bump_texture = None
    roll_count = 0

    for row in command_lines:
        if roll_funk is not None:
            roll_funk(roll_count)
            roll_count += 1
        command = row.split("#")[0]
        args = smart_split(command)
        if len(args) > 0:
            if args[0] == "newmtl":
                if now_mtl is not None:
                    mtl_dict[now_mtl] = surface(
                        base_color=soup3D.shader.MixChannel((width, height), R, G, B, A),
                        emission=emission,
                        normal=bump_texture if bump_texture else (0.5, 0.5, 1),
                        double_side=double_side,
                        max_light_count=max_light_count
                    )

                    R, G, B, A = 1.0, 1.0, 1.0, 1.0
                    width, height = 1, 1
                    emission = 0
                    bump_texture = None  # 重置法线贴图
                now_mtl = args[1]
            if args[0] == "Kd":
                R, G, B = float(args[1]), float(args[2]), float(args[3])
            if args[0] == "d":
                A = float(args[1])
            if args[0] == "Ke":
                emission = (float(args[1]), float(args[2]), float(args[3]))
            if args[0] == "map_Kd":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                pil_pic = Image.open(tex_path)
                width, height = pil_pic.width, pil_pic.height
                texture = soup3D.shader.Texture(pil_pic)
                R = soup3D.shader.Channel(texture, 0)
                G = soup3D.shader.Channel(texture, 1)
                B = soup3D.shader.Channel(texture, 2)
            if args[0] == "map_d":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                texture = soup3D.shader.Texture(Image.open(tex_path))
                A = soup3D.shader.Channel(texture, 3)
            if args[0] == "map_Ke":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                emission = soup3D.shader.Texture(Image.open(tex_path))
            # 新增：处理map_Bump命令
            if args[0] == "map_Bump":
                tex_path = None
                arg_name = None
                for arg in args[1:]:
                    if arg.startswith("-"):
                        arg_name = arg
                        continue
                    if arg_name is None:
                        base_dir = os.path.dirname(mtl)
                        tex_path = (os.path.join(base_dir, arg))
                    else:
                        # 处理选项(“-”或“--”开头)，目前没有任何支持的选项需要处理，直接恢复默认
                        arg_name = None
                        continue
                bump_texture = soup3D.shader.Texture(Image.open(tex_path))

    # 添加最后一个材质
    if now_mtl is not None:
        mtl_dict[now_mtl] = surface(
            base_color=soup3D.shader.MixChannel((width, height), R, G, B, A),
            emission=emission,
            normal=bump_texture if bump_texture else (0.5, 0.5, 1),
            double_side=double_side,
            max_light_count=max_light_count
        )

    return mtl_dict


def open_obj(obj: str,
             mtl: str | dict[str: soup3D.shader.Surface] | None = None,
             double_side: bool = True,
             roll_funk=None,
             encoding: str = "utf-8",
             max_light_count: int = 8) -> "Model":
    """
    从obj文件导入模型
    :param obj:             *.obj模型文件路径
    :param mtl:             *.mtl纹理文件路径或已加载的材质字典
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取obj或mtl文件时使用的字符集
    :param max_light_count: 该模型出现时会同时出现的最多的光源数量
    :return: 生成出来的模型数据(Model类)
    """
    # 处理mtl文件
    mtl_dict = {}

    # 如果mtl是字符串路径，则调用load_mtl加载
    if isinstance(mtl, str):
        mtl_dict = open_mtl(mtl, double_side, roll_funk, encoding, max_light_count)
    elif isinstance(mtl, dict):
        # 如果已经是字典，则直接使用
        mtl_dict = mtl

    # 创建默认材质（如果未提供MTL或材质未定义时使用）
    default_material = soup3D.shader.AutoSP(
        base_color=soup3D.shader.MixChannel((1, 1), 1.0, 1.0, 1.0, 1.0),
        emission=(0, 0, 0),
        normal=(0.5, 0.5, 1),
        double_side=double_side,
        max_light_count=max_light_count
    )

    # 处理obj文件
    obj_file = open(obj, 'r', encoding=encoding)
    obj_str = obj_file.read()
    obj_file.close()

    vertices = []  # 顶点坐标 (x, y, z)
    tex_coords = []  # 纹理坐标 (u, v)
    normals = []  # 法线向量 (nx, ny, nz)
    faces_by_material = {}  # 按材质分组存储面数据

    # 当前使用的材质
    current_material = None

    command_lines = obj_str.split("\n")
    roll_count = 0

    for row in command_lines:
        if roll_funk is not None:
            roll_funk(roll_count)
            roll_count += 1

        row = row.strip()
        if not row or row.startswith('#'):
            continue

        tokens = smart_split(row)
        if not tokens:
            continue

        prefix = tokens[0]
        data = tokens[1:]

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
            # 如果mtl参数未提供，但obj文件中指定了mtl文件，则自动加载
            if mtl is None and data:
                mtl_path = os.path.join(os.path.dirname(obj), data[0])
                if os.path.exists(mtl_path):
                    mtl_dict = open_mtl(mtl_path, double_side, roll_funk, encoding, max_light_count)

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

            # 获取当前材质的标识符
            material_id = id(current_material) if current_material else id(default_material)
            
            # 确保材质分组存在
            if material_id not in faces_by_material:
                faces_by_material[material_id] = {
                    'material': current_material if current_material else default_material,
                    'vertices': []
                }

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
                if v_idx < 0:
                    v_idx = len(vertices) + v_idx
                if vt_idx < 0:
                    vt_idx = len(tex_coords) + vt_idx
                if vn_idx < 0:
                    vn_idx = len(normals) + vn_idx

                # 获取顶点数据（确保索引在有效范围内）
                vert = list(vertices[v_idx])

                # 如果有纹理坐标，添加纹理坐标
                if 0 <= vt_idx < len(tex_coords):
                    u, v = tex_coords[vt_idx]
                    vert.extend([u, v])
                else:
                    vert.extend([0.0, 0.0])  # 默认纹理坐标

                # 如果有法线，添加法线数据
                if 0 <= vn_idx < len(normals):
                    nx, ny, nz = normals[vn_idx]
                    vert.extend([nx, ny, nz])
                else:
                    vert.extend([0.0, 0.0, 0.0])  # 默认法线

                base_indexes.append(tuple(vert))

            # 简单三角剖分：使用第一个顶点为基准，连接其他顶点形成三角形
            for i in range(1, len(base_indexes) - 1):
                # 每个三角形由第一个顶点和连续的两个顶点组成
                triangle = [
                    base_indexes[0],
                    base_indexes[i],
                    base_indexes[i + 1]
                ]
                # 添加到对应材质的顶点列表
                faces_by_material[material_id]['vertices'].extend(triangle)

    # 创建面对象，每个材质对应一个面
    faces = []
    for material_id, face_data in faces_by_material.items():
        if face_data['vertices']:  # 只有当有顶点数据时才创建面
            face = Face(
                shape_type="triangle_b",  # 分离的三角形
                surface=face_data['material'],
                vertex=face_data['vertices']
            )
            faces.append(face)

    # 创建模型对象（原点设置为0,0,0）
    model = Model(0, 0, 0, *faces)
    return model


def get_projection_mat() -> glm.fmat4x4:
    """
    获取透视矩阵，可用于代码着色器
    :return: 矩阵
    """
    return glm.perspective(
        glm.radians(_current_fov),
        _current_width/_current_height,
        _current_near,
        _current_far
    )


def smart_split(line):
    """
    高效的字符串分割函数，用于替代shlex.split处理OBJ/MTL文件行解析
    针对OBJ/MTL文件格式进行了优化，比shlex.split快得多
    :param line: 要分割的行
    :return: 分割后的字符串列表
    """
    # 快速路径：如果不包含引号或转义字符，直接使用split()
    if '"' not in line and "'" not in line and '\\' not in line:
        return line.split()

    # 处理包含引号的情况
    result = []
    current_token = ""
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(line):
        char = line[i]

        # 处理转义字符
        if char == '\\' and i + 1 < len(line):
            # 如果在引号内，保留转义字符和下一个字符
            if in_single_quote or in_double_quote:
                current_token += char + line[i + 1]
            else:
                # 如果不在引号内，跳过转义字符（按照普通空格分隔处理）
                current_token += line[i + 1]
            i += 2
            continue

        # 处理单引号
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            i += 1
            continue

        # 处理双引号
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            i += 1
            continue

        # 处理空格分隔符
        if char.isspace() and not in_single_quote and not in_double_quote:
            if current_token:
                result.append(current_token)
                current_token = ""
        else:
            current_token += char

        i += 1

    # 添加最后一个token
    if current_token:
        result.append(current_token)

    return result


if __name__ == '__main__':
    ...
