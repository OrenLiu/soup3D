"""
调用：soup3D
这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可
用于3D游戏开发、数据可视化、3D图形的绘制等开发。
"""
from OpenGL.GLU import *
from pyglm import glm
import os
import shlex
import imageio.v2 as imageio
import json
import struct
import base64
import math

import soup3D.shader
import soup3D.camera
import soup3D.light
import soup3D.ui
import soup3D.skeleton
from soup3D.name import *

render_queue: list["Model"] = []  # 单次渲染队列
stable_shapes = {}                # 固定渲染队列
EAU = []                          # 更新执行队列


proj_fov = 45
proj_near = 0.1
proj_far = 1024

proj_width = 1920
proj_height = 1080


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

        self.list_id = None
        self.surfaces = None

    def __add__(self, other: "Model"):
        """
        将多个模型组合成一个模型，当使用“model1 + model2”时，model2将会被组合到model1。需要注意的是，模型组合后，模型中其他模型的部分将与模
        型2共享资源，所以模型组合后，不建议继续使用参与计算的模型，建议使用返回值进行操作，比如“model3 = model1 + model2”,则建议抛弃model1
        和model2，使用model3执行后续操作。当模型因为不可抗因素需要分开倒入时，可以用该方法进行合并。
        :param other: 组合到该模型的模型
        :return: 修改后的本模型
        """
        self.faces += other.faces

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

        if self.list_id is not None:
            self.gen_dis_list()

        return self

    def gen_dis_list(self):
        """
        创建显示列表，该操作开销较大，不建议实时使用
        :return: None
        """
        self.list_id = glGenLists(1)
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
                if i == len(faces) - 1 and hasattr(surface, "unuse"):
                    surface.unuse()
        glEndList()

    def del_dis_list(self):
        """
        删除显示列表
        :return: None
        """
        global render_queue
        global stable_shapes

        # 清理顶点列表
        if self.list_id is not None:
            glDeleteLists(self.list_id, 1)
            self.list_id = None

        # 从全局渲染队列中移除（如果存在）
        if self in render_queue:
            render_queue.remove(self)

        # 从稳定形状中移除（如果存在）
        if id(self) in stable_shapes:
            stable_shapes.pop(id(self))

    def mk_shadow(self) -> "Model":
        """
        创建模型的影子数据，可用于多个相似模型的创建。影子对象将会与原对象共用网格数据、着色器代码，但是拥有独立的位置、朝向和尺寸等。
        :return: 影子模型
        """
        new_faces = [
            Face(old_face.shape_type, old_face.surface.mk_shadow(), old_face.vertex)
            for old_face in self.faces
        ]
        result = Model(self.x, self.y, self.z, *new_faces)
        result.goto(self.x, self.y, self.z)
        result.turn(self.yaw, self.pitch, self.roll)
        result.size(self.width, self.height, self.length)
        return result

    def paint(self) -> None:
        """
        在单帧绘制该模型
        :return: None
        """
        if self.list_id is None:
            self.gen_dis_list()
        render_queue.append(self)

    def show(self) -> None:
        """
        固定每帧渲染该模型
        :return: None
        """
        global stable_shapes

        if self.list_id is None:
            self.gen_dis_list()
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
        for face in self.faces:
            surface = face.surface
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
        for face in self.faces:
            surface = face.surface
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
        for face in self.faces:
            surface = face.surface
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
        self.del_dis_list()


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
    global proj_fov, proj_near, proj_far
    global proj_width, proj_height
    proj_fov = fov
    proj_near = near
    proj_far = far

    proj_width = width
    proj_height = height

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
    global proj_width, proj_height

    proj_width = width
    proj_height = height

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = width / height
    gluPerspective(proj_fov, aspect_ratio, proj_near, proj_far)
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


def _render_fullscreen_image(img: soup3D.shader.Img) -> None:
    """渲染全屏叠加图像"""
    # 获取视口尺寸
    viewport = glGetIntegerv(GL_VIEWPORT)
    width, height = viewport[2], viewport[3]
    
    # 获取纹理 ID
    tex_id = img.get_texture_id()
    
    # 保存当前矩阵状态
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # 设置正交投影（与 UI 渲染一致）
    gluOrtho2D(0, width, height, 0)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # 保存当前状态并禁用光照和深度测试
    glPushAttrib(GL_ENABLE_BIT)
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    
    # 启用纹理和混合
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 绘制全屏四边形
    glBegin(GL_QUADS)
    # 左上角
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)
    # 右上角
    glTexCoord2f(1.0, 0.0)
    glVertex2f(width, 0.0)
    # 右下角
    glTexCoord2f(1.0, 1.0)
    glVertex2f(width, height)
    # 左下角
    glTexCoord2f(0.0, 1.0)
    glVertex2f(0.0, height)
    glEnd()
    
    # 恢复状态
    glDisable(GL_BLEND)
    glPopAttrib()
    
    # 恢复矩阵
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


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
    EAU += soup3D.light.EAU

    EAU_len = len(EAU)  # 调用列队前列队的长度
    for args in EAU:
        args[0](*args[1:])
        if EAU_len != len(EAU):
            raise Exception(f"EAU length changed while running: {args[0].__name__}{(*args[1:],)}")

    EAU = []
    light.EAU = []

    # 渲染固定渲染物体
    for shape_id in stable_shapes:
        model = stable_shapes[shape_id]
        for shape in model.faces:
            surface: soup3D.shader.Surface = shape.surface
            if surface.is_dirty():
                surface.update()
        glCallList(model.list_id)

    # 渲染单帧渲染物体
    for model in render_queue:
        for shape in model.faces:
            surface: soup3D.shader.Surface = shape.surface
            if surface.is_dirty():
                surface.update()
        glCallList(model.list_id)

    # 清空渲染队列
    render_queue = []

    # 渲染 ui 界面
    for i in soup3D.ui.render_queue:
        _paint_ui(*i)
    
    # 渲染全屏叠加图像
    if soup3D.ui.fullscreen_img is not None:
        _render_fullscreen_image(soup3D.ui.fullscreen_img)
    
    # 清空 ui 渲染列队
    soup3D.ui.render_queue = []


def open_mtl(mtl: str,
             double_side: bool = True,
             roll_funk=None,
             encoding: str = "utf-8",
             max_light_count: int = 8,
             surface = soup3D.shader.AutoSP) -> dict:
    """
    根据mtl文件生成多个着色器
    :param mtl:             *.mtl纹理文件路径
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)
    :param max_light_count: 这些着色器出现时会同时出现的最多的光源数量，大了会导致性能问题
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
                texture = soup3D.shader.Texture(tex_path)
                # 延迟加载纹理以获取尺寸
                try:
                    img = imageio.imread(tex_path)
                    height, width = img.shape[:2]
                except:
                    width, height = 1, 1
                R = soup3D.shader.Channel(texture, 0)
                G = soup3D.shader.Channel(texture, 1)
                B = soup3D.shader.Channel(texture, 2)
            if args[0] == "map_d":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                texture = soup3D.shader.Texture(tex_path)
                A = soup3D.shader.Channel(texture, 3)
            if args[0] == "map_Ke":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                emission = soup3D.shader.Texture(tex_path)
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
                        # 处理选项 ("-"或"--"开头)，目前没有任何支持的选项需要处理，直接恢复默认
                        arg_name = None
                        continue
                bump_texture = soup3D.shader.Texture(tex_path)

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
             mtl: str | dict | None = None,
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
    :param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)
    :param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题
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
                    vert.extend([u, -v])
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


def open_gltf(
        gltf: str,
        double_side: bool = True,
        roll_funk=None,
        encoding: str = "utf-8",
        max_light_count: int = 8,
        surface = soup3D.shader.AutoSP,
        skin = soup3D.shader.BoneBinderSP
    ):
    """
    从glb导入模型和骨骼
    :param gltf:            gltf模型文件路径
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)
    :param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题
    :param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side,max_light_count等参
                            数
    :param skin:            模型使用的蒙皮着色器类型，着色器需要有skeleton, base_color, emission, normal, double_side,
                            max_light_count等参数
    :return: 模型数据(Model类), 骨架数据(Skeleton类)
    """
    gltf_dir = os.path.dirname(gltf)

    # 解析glTF文件
    gltf_data = _parse_gltf_file(gltf)

    # 获取场景
    scene_index = gltf_data.get('scene', 0)
    scenes = gltf_data.get('scenes', [])
    if scene_index >= len(scenes):
        scene_index = 0

    scene = scenes[scene_index] if scenes else {}
    scene_nodes = scene.get('nodes', [])

    # 用于存储已创建的模型和骨架
    models = []
    skeletons = []

    # 处理场景中的所有节点
    for node_index in scene_nodes:
        _process_gltf_node(gltf_data, node_index, gltf_dir, double_side,
                            max_light_count, surface, skin, None, models, skeletons)

    # 合并所有模型
    if not models:
        return None, None

    result_model = models[0]
    for m in models[1:]:
        result_model = result_model + m

    # 返回模型和骨架
    result_skeleton = skeletons[0] if skeletons else soup3D.skeleton.Skeleton()

    return result_model, result_skeleton


def _process_gltf_node(gltf: dict, node_index: int, gltf_dir: str,
                        double_side: bool, max_light_count: int,
                        surface_class, skin_class, parent_skeleton,
                        models: list, skeletons: list):
    """递归处理glTF节点"""
    nodes = gltf.get('nodes', [])
    if node_index >= len(nodes):
        return

    node = nodes[node_index]
    mesh_index = node.get('mesh')
    skin_index = node.get('skin')
    children = node.get('children', [])

    # 获取skin数据（用于正确映射关节索引）
    skin = None
    if skin_index is not None and skin_index < len(gltf.get('skins', [])):
        skin = gltf['skins'][skin_index]

    # 处理骨骼
    node_skeleton = parent_skeleton
    if skin_index is not None:
        node_skeleton = _build_skeleton(gltf, skin_index, node_index, gltf_dir)
        skeletons.append(node_skeleton)

    # 处理网格
    if mesh_index is not None:
        meshes = gltf.get('meshes', [])
        if mesh_index < len(meshes):
            mesh = meshes[mesh_index]
            model = _process_mesh(gltf, mesh, gltf_dir, double_side,
                                   max_light_count, surface_class, skin_class, node_skeleton, skin)

            # 应用节点变换
            translation = node.get('translation', [0, 0, 0])
            rotation = node.get('rotation', [0, 0, 0, 1])
            scale = node.get('scale', [1, 1, 1])

            if translation != [0, 0, 0]:
                model.goto(*translation)

            # 处理旋转（四元数转欧拉角）
            if rotation != [0, 0, 0, 1]:
                yaw, pitch, roll = _quaternion_to_euler(*rotation)
                model.turn(yaw, pitch, roll)

            if scale != [1, 1, 1]:
                model.size(*scale)

            models.append(model)

    # 递归处理子节点
    for child_index in children:
        _process_gltf_node(gltf, child_index, gltf_dir, double_side,
                            max_light_count, surface_class, skin_class, node_skeleton,
                            models, skeletons)


def _process_mesh(gltf: dict, mesh: dict, gltf_dir: str, double_side: bool,
                  max_light_count: int, surface_class, skin_class, skeleton, skin=None) -> "Model":
    """处理网格数据"""
    primitives = mesh.get('primitives', [])
    faces = []

    for primitive in primitives:
        # 获取材质
        material_index = primitive.get('material', -1)
        material = _parse_material(gltf, material_index, gltf_dir,
                                    double_side, max_light_count, surface_class)

        # 获取属性
        attributes = primitive.get('attributes', {})

        # 获取顶点位置
        position_attr = attributes.get('POSITION')
        if position_attr is None:
            continue

        positions = _get_accessor_data(gltf, position_attr, gltf_dir)

        # 获取法线
        normal_attr = attributes.get('NORMAL')
        normals = _get_accessor_data(gltf, normal_attr, gltf_dir) if normal_attr is not None else None

        # 获取纹理坐标
        texcoord_attr = attributes.get('TEXCOORD_0')
        texcoords = _get_accessor_data(gltf, texcoord_attr, gltf_dir) if texcoord_attr is not None else None

        # 获取关节和权重（用于骨骼动画）
        joints_attr = attributes.get('JOINTS_0')
        weights_attr = attributes.get('WEIGHTS_0')

        # 获取索引
        indices_attr = primitive.get('indices')
        if indices_attr is not None:
            indices = _get_accessor_data(gltf, indices_attr, gltf_dir)
        else:
            indices = list(range(len(positions)))

        # 检查是否有皮肤（骨骼动画）
        has_skin = (joints_attr is not None and weights_attr is not None and skeleton is not None)

        # 获取关节和权重数据
        joints = []
        weights = []
        if has_skin:
            joints = _get_accessor_data(gltf, joints_attr, gltf_dir)
            weights = _get_accessor_data(gltf, weights_attr, gltf_dir)
            # 使用蒙皮着色器
            material = _create_skinned_material(gltf, primitive, gltf_dir, double_side,
                                                 max_light_count, skin_class, skeleton,
                                                 material)

        # 构建顶点数据
        vertices = []
        for i in indices:
            pos = positions[i]
            normal = normals[i] if normals and i < len(normals) else [0, 0, 1]
            texcoord = texcoords[i] if texcoords and i < len(texcoords) else [0, 0]

            if has_skin and i < len(joints) and i < len(weights):
                # 构建骨骼权重字典
                joint_list = joints[i]
                weight_list = weights[i]

                # 映射关节索引到骨骼名称
                # 在glTF中，顶点数据中的joint索引是相对于skin.joints数组的索引
                # 需要先通过skin.joints映射到实际的节点索引
                weight_dict = {}
                for j, w in zip(joint_list, weight_list):
                    # 获取实际的节点索引
                    if skin is not None and j < len(skin.get('joints', [])):
                        node_index = skin['joints'][j]
                    else:
                        node_index = j
                    bone_name = _get_joint_name(gltf, node_index)
                    weight_dict[bone_name] = w

                vertex = (weight_dict, *pos, texcoord[0], texcoord[1], *normal)
            else:
                vertex = (-pos[1], pos[0], pos[2], texcoord[0], texcoord[1], -normal[1], normal[0], normal[2])

            vertices.append(vertex)

        # 创建面
        if vertices:
            face = Face(
                shape_type="triangle_b",
                surface=material,
                vertex=vertices
            )
            faces.append(face)

    return Model(0, 0, 0, *faces)


def _get_joint_name(gltf: dict, joint_index: int) -> str:
    """获取关节名称"""
    nodes = gltf.get('nodes', [])
    if joint_index < len(nodes):
        node = nodes[joint_index]
        name = node.get('name')
        if name:
            return name
    return f'joint_{joint_index}'


def _create_skinned_material(gltf: dict, primitive: dict, gltf_dir: str,
                              double_side: bool, max_light_count: int,
                              skin_class, skeleton, base_material) -> "soup3D.shader.Surface":
    """创建蒙皮材质"""
    # 复制基础材质的属性
    return skin_class(
        base_color=base_material.base_color,
        normal=base_material.normal,
        emission=base_material.emission,
        double_side=double_side,
        max_light_count=max_light_count,
        skeleton=skeleton
    )


def get_projection_mat() -> glm.fmat4x4:
    """
    获取透视矩阵，可用于代码着色器
    :return: 矩阵
    """
    return glm.perspective(
        glm.radians(proj_fov),
        proj_width / proj_height,
        proj_near,
        proj_far
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


def _parse_gltf_file(gltf_path: str) -> dict:
    """解析glTF文件（支持.gltf和.glb格式）"""
    if gltf_path.endswith('.glb'):
        return _parse_glb_file(gltf_path)
    else:
        with open(gltf_path, 'r', encoding='utf-8') as f:
            return json.load(f)


def _parse_glb_file(glb_path: str) -> dict:
    """解析二进制glTF文件(.glb)"""
    with open(glb_path, 'rb') as f:
        # 读取glb头部 (12 bytes)
        header = f.read(12)
        magic = struct.unpack('<I', header[0:4])[0]
        version = struct.unpack('<I', header[4:8])[0]
        length = struct.unpack('<I', header[8:12])[0]

        # 验证glb文件格式
        if magic != 0x46546C67:  # "glTF"
            raise ValueError("Invalid glb file: wrong magic number")
        if version != 2:
            raise ValueError(f"Unsupported glb version: {version}")

        # 读取chunk信息
        json_length = 0
        json_data = None
        binary_data = None

        while f.tell() < length:
            chunk_header = f.read(8)
            if len(chunk_header) < 8:
                break
            chunk_length = struct.unpack('<I', chunk_header[0:4])[0]
            chunk_type = struct.unpack('<I', chunk_header[4:8])[0]

            chunk_data = f.read(chunk_length)

            if chunk_type == 0x4E4F534A:  # JSON chunk
                json_data = chunk_data.decode('utf-8')
            elif chunk_type == 0x004E4942:  # BIN chunk
                binary_data = chunk_data

        if json_data is None:
            raise ValueError("No JSON chunk found in glb file")

        gltf = json.loads(json_data)
        if binary_data is not None:
            gltf['_binary_data'] = binary_data

        return gltf


def _get_buffer_data(gltf: dict, buffer_index: int, gltf_dir: str) -> bytes:
    """获取缓冲区数据"""
    buffer = gltf['buffers'][buffer_index]
    if 'uri' in buffer:
        uri = buffer['uri']
        if uri.startswith('data:'):
            # Base64编码的数据
            header, data = uri.split(',', 1)
            return base64.b64decode(data)
        else:
            # 外部文件
            buffer_path = os.path.join(gltf_dir, uri)
            with open(buffer_path, 'rb') as f:
                return f.read()
    elif '_binary_data' in gltf:
        return gltf['_binary_data']
    else:
        raise ValueError(f"Cannot load buffer {buffer_index}")


def _get_accessor_data(gltf: dict, accessor_index: int, gltf_dir: str) -> list:
    """获取访问器数据"""
    accessor = gltf['accessors'][accessor_index]
    buffer_view = gltf['bufferViews'][accessor['bufferView']]
    buffer_data = _get_buffer_data(gltf, buffer_view['buffer'], gltf_dir)

    offset = buffer_view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = buffer_view.get('byteStride', 0)
    count = accessor['count']
    component_type = accessor['componentType']
    data_type = accessor['type']

    # 解析数据类型
    type_map = {
        'SCALAR': 1,
        'VEC2': 2,
        'VEC3': 3,
        'VEC4': 4,
        'MAT2': 4,
        'MAT3': 9,
        'MAT4': 16
    }
    num_components = type_map[data_type]

    # 解析组件类型
    # glTF componentType: 5120=BYTE, 5121=UNSIGNED_BYTE, 5122=SHORT, 5123=UNSIGNED_SHORT, 5125=UNSIGNED_INT, 5126=FLOAT
    component_size = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}[component_type]
    component_format = {5120: 'b', 5121: 'B', 5122: 'h', 5123: 'H', 5125: 'I', 5126: 'f'}[component_type]

    # 计算总字节大小
    total_bytes = count * num_components * component_size
    data_bytes = buffer_data[offset:offset + total_bytes]

    # 解包数据
    values = list(struct.unpack(f'<{count * num_components}{component_format}', data_bytes))

    # 归一化处理
    if accessor.get('normalized', False):
        if component_type == 5121:  # unsigned byte
            values = [v / 255.0 for v in values]
        elif component_type == 5123:  # unsigned short
            values = [v / 65535.0 for v in values]

    # 重塑数据
    result = []
    for i in range(count):
        if data_type == 'SCALAR':
            result.append(values[i])
        else:
            result.append(values[i * num_components:(i + 1) * num_components])

    return result


def _parse_material(gltf: dict, material_index: int, gltf_dir: str,
                    double_side: bool, max_light_count: int, surface_class) -> "soup3D.shader.Surface":
    """解析材质"""
    if material_index < 0 or material_index >= len(gltf.get('materials', [])):
        # 默认材质
        return surface_class(
            base_color=soup3D.shader.MixChannel((1, 1), 1.0, 1.0, 1.0, 1.0),
            emission=(0, 0, 0),
            normal=(0.5, 0.5, 1),
            double_side=double_side,
            max_light_count=max_light_count
        )

    material = gltf['materials'][material_index]
    pbr = material.get('pbrMetallicRoughness', {})

    # 基础颜色
    base_color_factor = pbr.get('baseColorFactor', [1.0, 1.0, 1.0, 1.0])
    base_color_texture = pbr.get('baseColorTexture')

    if base_color_texture:
        texture_info = _parse_texture(gltf, base_color_texture['index'], gltf_dir)
        R = soup3D.shader.Channel(texture_info, 0)
        G = soup3D.shader.Channel(texture_info, 1)
        B = soup3D.shader.Channel(texture_info, 2)
        A = soup3D.shader.Channel(texture_info, 3)
    else:
        R, G, B, A = base_color_factor
        A = soup3D.shader.MixChannel((1, 1), base_color_factor[0], base_color_factor[1],
                                     base_color_factor[2], base_color_factor[3])

    # 自发光
    emissive_factor = material.get('emissiveFactor', [0, 0, 0])
    emissive_texture = material.get('emissiveTexture')
    if emissive_texture:
        emission = _parse_texture(gltf, emissive_texture['index'], gltf_dir)
    else:
        emission = tuple(emissive_factor)

    # 法线贴图
    normal_texture = material.get('normalTexture')
    if normal_texture:
        normal = _parse_texture(gltf, normal_texture['index'], gltf_dir)
    else:
        normal = (0.5, 0.5, 1)

    return surface_class(
        base_color=soup3D.shader.MixChannel((1, 1), R, G, B, A),
        emission=emission,
        normal=normal,
        double_side=double_side,
        max_light_count=max_light_count
    )


def _parse_texture(gltf: dict, texture_index: int, gltf_dir: str) -> "soup3D.shader.Texture":
    """解析纹理"""
    texture = gltf['textures'][texture_index]
    image_index = texture.get('source')
    if image_index is None:
        return soup3D.shader.Texture(bytes([255, 255, 255, 255]), 1, 1, 'RGBA')

    image = gltf['images'][image_index]

    if 'uri' in image:
        uri = image['uri']
        if uri.startswith('data:'):
            header, data = uri.split(',', 1)
            image_data = base64.b64decode(data)
            return soup3D.shader.Texture(image_data, 1, 1, 'RGBA')
        else:
            image_path = os.path.join(gltf_dir, uri)
            return soup3D.shader.Texture(image_path)
    elif 'bufferView' in image:
        buffer_view_index = image['bufferView']
        buffer_view = gltf['bufferViews'][buffer_view_index]
        buffer = gltf['buffers'][buffer_view['buffer']]

        # 需要从buffer获取数据
        offset = buffer_view.get('byteOffset', 0)
        length = buffer_view['byteLength']

        if 'uri' in buffer:
            base_dir = gltf_dir
            buffer_path = os.path.join(base_dir, buffer['uri'])
            with open(buffer_path, 'rb') as f:
                f.seek(offset)
                image_data = f.read(length)
        else:
            # 使用嵌入的二进制数据
            image_data = gltf.get('_binary_data', b'')[offset:offset + length]

        return soup3D.shader.Texture(image_data, 1, 1, 'RGBA')
    else:
        return soup3D.shader.Texture(bytes([255, 255, 255, 255]), 1, 1, 'RGBA')


def _build_skeleton(gltf: dict, skin_index: int, node_index: int,
                    gltf_dir: str) -> soup3D.skeleton.Skeleton:
    """构建骨架"""
    skeleton = soup3D.skeleton.Skeleton()

    if skin_index < 0 or skin_index >= len(gltf.get('skins', [])):
        return skeleton

    skin = gltf['skins'][skin_index]
    joints = skin.get('joints', [])
    inverse_bind_matrices = skin.get('inverseBindMatrices')

    # 获取逆绑定矩阵
    ibm_data = []
    if inverse_bind_matrices is not None:
        ibm_data = _get_accessor_data(gltf, inverse_bind_matrices, gltf_dir)

    # 获取关节节点
    nodes = gltf.get('nodes', [])

    # 构建骨骼层级
    bones_dict = {}

    for i, joint_index in enumerate(joints):
        node = nodes[joint_index]
        bone_name = node.get('name', f'joint_{joint_index}')

        # 获取变换信息
        translation = node.get('translation', [0, 0, 0])
        rotation = node.get('rotation', [0, 0, 0, 1])  # 四元数
        scale = node.get('scale', [1, 1, 1])

        # 计算初始位置和方向
        init_pos = tuple(translation)

        # 从四元数转换为欧拉角
        q = rotation
        yaw, pitch, roll = _quaternion_to_euler(q[0], q[1], q[2], q[3])
        init_toward = (yaw, pitch, roll)

        # 计算骨骼长度（从逆绑定矩阵或缩放）
        init_length = scale[0] if len(scale) > 0 else 1.0

        bone = soup3D.skeleton.Bone(init_pos, init_length, init_toward)
        bones_dict[joint_index] = bone
        skeleton.add_bone(bone_name, bone)

    # 构建层级关系
    for joint_index, bone in bones_dict.items():
        node = nodes[joint_index]
        children = node.get('children', [])

        for child_index in children:
            if child_index in bones_dict:
                child_bone = bones_dict[child_index]
                # 子骨骼的初始位置由父骨骼决定，这里需要重新计算
                bone.children.append(child_bone)
                child_bone.parent = bone

    return skeleton


def _quaternion_to_euler(x: float, y: float, z: float, w: float) -> tuple:
    """将四元数转换为欧拉角"""
    roll = math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = math.asin(2 * (w * y - z * x))
    yaw = math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return (math.degrees(yaw), math.degrees(pitch), math.degrees(roll))


def _get_vertex_weights(gltf: dict, primitive: dict, gltf_dir: str) -> list:
    """获取顶点权重"""
    weights_attr = primitive.get('attributes', {}).get('JOINTS_0')
    weights_data_attr = primitive.get('attributes', {}).get('WEIGHTS_0')

    if weights_attr is None or weights_data_attr is None:
        return []

    joints = _get_accessor_data(gltf, weights_attr, gltf_dir)
    weights = _get_accessor_data(gltf, weights_data_attr, gltf_dir)

    result = []
    for j, w in zip(joints, weights):
        weight_dict = {}
        for i in range(4):
            if i < len(j) and i < len(w):
                weight_dict[f'joint_{j[i]}'] = w[i]
        result.append(weight_dict)

    return result


if __name__ == '__main__':
    ...