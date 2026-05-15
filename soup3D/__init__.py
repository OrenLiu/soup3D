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


def gen_skeleton_model(_skeleton: soup3D.skeleton.Skeleton | dict, bone_color=None, size=0.01):
    """
    生成骨架模型，在屏幕中用线条叠加渲染骨架，用于调试。警告：该操作比较占用性能，只建议在调试时使用。
    :param _skeleton: 骨架对象或骨骼字典
    :param bone_color:  骨骼颜色字典，键为骨骼名称，值为颜色元组
    :param size:        骨骼模型的大小，默认0.01
    :return: 模型(Model类)
    """
    print("warning: skeleton model is not stable, use it in debug mode only.")

    if bone_color is None:
        bone_color = {}

    if isinstance(_skeleton, soup3D.skeleton.Skeleton):
        _skeleton = _skeleton.bones

    faces = []
    for bone_name in _skeleton:
        bone = _skeleton[bone_name]
        color = (1, 0, 0)
        if bone_name in bone_color:
            color = bone_color[bone_name]
        end_pos = bone._get_end_position()
        faces.append(
            Face(
                TRIANGLE_B,
                soup3D.shader.AutoSP(
                    soup3D.shader.MixChannel((1, 1), *color)
                ),
                [
                    (
                        bone.pos.x + size,
                        bone.pos.y,
                        bone.pos.z,
                        0, 0
                    ),
                    (
                        bone.pos.x - size,
                        bone.pos.y,
                        bone.pos.z,
                        0, 0)
                    ,
                    (*end_pos, 0, 0),
                    (
                        bone.pos.x,
                        bone.pos.y + size,
                        bone.pos.z,
                        0, 0
                    ),
                    (
                        bone.pos.x,
                        bone.pos.y - size,
                        bone.pos.z,
                        0, 0
                    ),
                    (*end_pos, 0, 0),
                    (
                        bone.pos.x,
                        bone.pos.y,
                        bone.pos.z + size,
                        0, 0
                    ),
                    (
                        bone.pos.x,
                        bone.pos.y,
                        bone.pos.z - size,
                        0, 0
                    ),
                    (*end_pos, 0, 0),
                ]
            )
        )
    model = Model(0, 0, 0, *faces)
    return model


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


def _gltf_component_size(component_type: int) -> int:
    """获取GLTF组件类型的字节大小"""
    size_map = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    return size_map.get(component_type, 4)


def _gltf_component_count(accessor_type: str) -> int:
    """获取GLTF访问器类型的分量数量"""
    count_map = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
    return count_map.get(accessor_type, 1)


def _gltf_read_accessor(gltf_data: dict, buffers_data: list, accessor_idx: int) -> list:
    """
    读取GLTF访问器数据
    :param gltf_data:    GLTF JSON数据
    :param buffers_data: 已加载的缓冲区数据列表
    :param accessor_idx: 访问器索引
    :return: 数据列表
    """
    accessor = gltf_data["accessors"][accessor_idx]
    buffer_view = gltf_data["bufferViews"][accessor["bufferView"]]

    component_type = accessor["componentType"]
    accessor_type = accessor["type"]
    count = accessor["count"]
    comp_size = _gltf_component_size(component_type)
    comp_count = _gltf_component_count(accessor_type)

    buffer_idx = buffer_view.get("buffer", 0)
    byte_offset = buffer_view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    byte_stride = buffer_view.get("byteStride", 0)

    raw = buffers_data[buffer_idx]

    # 根据组件类型确定struct格式字符
    fmt_map = {5126: 'f', 5123: 'H', 5121: 'B', 5122: 'h', 5120: 'b', 5125: 'I'}
    fmt_char = fmt_map.get(component_type, 'f')

    if byte_stride and byte_stride > comp_count * comp_size:
        # 有字节步幅，逐元素读取
        result = []
        for i in range(count):
            offset = byte_offset + i * byte_stride
            vals = struct.unpack_from(f"<{comp_count}{fmt_char}", raw, offset)
            if comp_count == 1:
                result.append(vals[0])
            else:
                result.append(vals)
        return result
    else:
        # 连续数据，直接读取
        elem_size = comp_count * comp_size
        result = []
        for i in range(count):
            offset = byte_offset + i * elem_size
            vals = struct.unpack_from(f"<{comp_count}{fmt_char}", raw, offset)
            if comp_count == 1:
                result.append(vals[0])
            else:
                result.append(vals)
        return result


def _gltf_load_buffers(gltf_data: dict, base_dir: str) -> list:
    """
    加载GLTF缓冲区数据
    :param gltf_data: GLTF JSON数据
    :param base_dir:  GLTF文件所在目录
    :return: 缓冲区数据列表（bytes对象）
    """
    buffers = []
    for buf in gltf_data.get("buffers", []):
        uri = buf.get("uri", "")
        if uri.startswith("data:"):
            # data URI
            split_idx = uri.index(",")
            raw = base64.b64decode(uri[split_idx + 1:])
        else:
            buf_path = os.path.join(base_dir, uri)
            with open(buf_path, "rb") as f:
                raw = f.read()
        buffers.append(raw)
    return buffers


def _gltf_load_materials(gltf_data: dict, base_dir: str, double_side: bool, max_light_count: int, surface) -> dict:
    """
    加载GLTF材质，返回材质索引到着色器的映射
    :param gltf_data:      GLTF JSON数据
    :param base_dir:       GLTF文件所在目录
    :param double_side:    是否启用双面渲染
    :param max_light_count: 最大光源数量
    :param surface:        表面着色器类型
    :return: 材质字典 {材质索引: 着色器对象}
    """
    materials_dict = {}

    images_data = gltf_data.get("images", [])
    textures_data = gltf_data.get("textures", [])
    materials_data = gltf_data.get("materials", [])

    # 加载所有图像
    loaded_images = []
    for img_info in images_data:
        uri = img_info.get("uri", "")
        if uri.startswith("data:"):
            split_idx = uri.index(",")
            img_bytes = base64.b64decode(uri[split_idx + 1:])
            img_array = imageio.imread(img_bytes)
        else:
            img_path = os.path.join(base_dir, uri)
            img_array = imageio.imread(img_path)
        loaded_images.append(img_array)

    for mat_idx, mat_info in enumerate(materials_data):
        mat_double_side = mat_info.get("doubleSided", double_side)

        # 尝试获取base color纹理
        base_color = soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0)
        pbr = mat_info.get("pbrMetallicRoughness", {})
        base_color_tex = pbr.get("baseColorTexture", {})
        if base_color_tex:
            tex_idx = base_color_tex.get("index", -1)
            if 0 <= tex_idx < len(textures_data):
                source_idx = textures_data[tex_idx].get("source", -1)
                if 0 <= source_idx < len(loaded_images):
                    img_array = loaded_images[source_idx]
                    h, w = img_array.shape[:2]
                    if len(img_array.shape) == 3 and img_array.shape[2] == 4:
                        fmt = "RGBA"
                    elif len(img_array.shape) == 3:
                        fmt = "RGB"
                    else:
                        fmt = "L"
                    tex = soup3D.shader.Texture(img_array.tobytes(), width=w, height=h, format=fmt)
                    r_ch = soup3D.shader.Channel(tex, 0)
                    g_ch = soup3D.shader.Channel(tex, 1)
                    b_ch = soup3D.shader.Channel(tex, 2)
                    a_ch = soup3D.shader.Channel(tex, 3) if fmt == "RGBA" else 1.0
                    base_color = soup3D.shader.MixChannel((w, h), r_ch, g_ch, b_ch, a_ch)

        # 尝试获取emissive纹理
        emission = (0, 0, 0)
        emissive_tex = mat_info.get("emissiveTexture", {})
        if emissive_tex:
            tex_idx = emissive_tex.get("index", -1)
            if 0 <= tex_idx < len(textures_data):
                source_idx = textures_data[tex_idx].get("source", -1)
                if 0 <= source_idx < len(loaded_images):
                    img_array = loaded_images[source_idx]
                    h, w = img_array.shape[:2]
                    fmt = "RGB" if len(img_array.shape) == 3 else "L"
                    tex = soup3D.shader.Texture(img_array.tobytes(), width=w, height=h, format=fmt)
                    emission = tex

        # 检查base color因子
        base_color_factor = pbr.get("baseColorFactor", None)

        materials_dict[mat_idx] = surface(
            base_color=base_color,
            emission=emission,
            normal=(0.5, 0.5, 1),
            double_side=mat_double_side,
            max_light_count=max_light_count
        )

    return materials_dict


def _quat_to_euler(qx, qy, qz, qw):
    """
    将四元数转换为欧拉角(yaw, pitch, roll)，单位为角度
    :param qx: 四元数x分量
    :param qy: 四元数y分量
    :param qz: 四元数z分量
    :param qw: 四元数w分量
    :return: (yaw, pitch, roll) 角度
    """
    # Yaw (绕Y轴)
    siny_cosp = 2 * (qw * qy + qx * qz)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = math.degrees(math.atan2(siny_cosp, cosy_cosp))

    # Pitch (绕X轴)
    sinp = 2 * (qw * qx - qz * qy)
    sinp = max(-1.0, min(1.0, sinp))
    pitch = math.degrees(math.asin(sinp))

    # Roll (绕Z轴)
    sinr_cosp = 2 * (qw * qz + qx * qy)
    cosr_cosp = 1 - 2 * (qz * qz + qy * qy)
    roll = math.degrees(math.atan2(sinr_cosp, cosr_cosp))

    return yaw, pitch, roll


def _quat_to_mat4(qx, qy, qz, qw):
    """
    将四元数转换为4x4旋转矩阵
    :param qx: 四元数x分量
    :param qy: 四元数y分量
    :param qz: 四元数z分量
    :param qw: 四元数w分量
    :return: 4x4矩阵
    """
    mat = glm.mat4(1.0)
    mat[0][0] = 1 - 2 * (qy * qy + qz * qz)
    mat[0][1] = 2 * (qx * qy + qw * qz)
    mat[0][2] = 2 * (qx * qz - qw * qy)
    mat[1][0] = 2 * (qx * qy - qw * qz)
    mat[1][1] = 1 - 2 * (qx * qx + qz * qz)
    mat[1][2] = 2 * (qy * qz + qw * qx)
    mat[2][0] = 2 * (qx * qz + qw * qy)
    mat[2][1] = 2 * (qy * qz - qw * qx)
    mat[2][2] = 1 - 2 * (qx * qx + qy * qy)
    return mat


def _gltf_build_node_transform(node: dict) -> glm.mat4:
    """
    根据GLTF节点的TRS属性构建局部变换矩阵
    :param node: GLTF节点数据
    :return: 4x4变换矩阵
    """
    mat = glm.mat4(1.0)

    # 平移
    t = node.get("translation", [0, 0, 0])
    mat = glm.translate(mat, glm.vec3(*t))

    # 旋转（四元数）
    r = node.get("rotation", [0, 0, 0, 1])
    rot_mat = _quat_to_mat4(r[0], r[1], r[2], r[3])
    mat = mat * rot_mat

    # 缩放
    s = node.get("scale", [1, 1, 1])
    mat = glm.scale(mat, glm.vec3(*s))

    return mat


def _gltf_compute_world_transforms(nodes: list) -> list:
    """
    计算所有节点的世界变换矩阵
    :param nodes: GLTF节点列表
    :return: 世界变换矩阵列表
    """
    world_transforms = [None] * len(nodes)
    root_nodes = []

    # 找出所有有父节点的节点
    has_parent = set()
    for i, node in enumerate(nodes):
        for child_idx in node.get("children", []):
            has_parent.add(child_idx)

    # 没有父节点的就是根节点
    for i in range(len(nodes)):
        if i not in has_parent:
            root_nodes.append(i)

    # 如果有场景定义，使用场景的根节点
    # 这里简单处理：所有根节点都用单位矩阵作为父变换
    def _compute(idx, parent_transform):
        local = _gltf_build_node_transform(nodes[idx])
        world = parent_transform * local
        world_transforms[idx] = world
        for child_idx in nodes[idx].get("children", []):
            _compute(child_idx, world)

    for root_idx in root_nodes:
        _compute(root_idx, glm.mat4(1.0))

    return world_transforms


def _gltf_build_skeleton(gltf_data: dict, world_transforms: list) -> soup3D.skeleton.Skeleton:
    """
    从GLTF数据构建骨架
    :param gltf_data:      GLTF JSON数据
    :param world_transforms: 节点世界变换矩阵列表
    :return: Skeleton对象
    """
    nodes = gltf_data["nodes"]
    skeleton = soup3D.skeleton.Skeleton()

    # 如果没有skin，返回空骨架
    skins = gltf_data.get("skins", [])
    if not skins:
        return skeleton

    skin = skins[0]
    joints = skin["joints"]
    joint_names = {}
    for joint_idx in joints:
        joint_names[joint_idx] = nodes[joint_idx].get("name", f"bone_{joint_idx}")

    # 构建每个关节到其子关节的映射
    children_map = {}
    for joint_idx in joints:
        children_map[joint_idx] = []
        for child_idx in nodes[joint_idx].get("children", []):
            if child_idx in joint_names:
                children_map[joint_idx].append(child_idx)

    # 找到根关节（没有在joints中有父关节的关节）
    joint_set = set(joints)
    root_joints = []
    for joint_idx in joints:
        is_root = True
        for other_idx in joints:
            if joint_idx in nodes[other_idx].get("children", []):
                is_root = False
                break
        if is_root:
            root_joints.append(joint_idx)

    # 递归构建骨骼
    def _build_bone(joint_idx, parent_bone=None):
        name = joint_names[joint_idx]
        world_mat = world_transforms[joint_idx]

        # 从世界矩阵提取位置
        pos = glm.vec3(world_mat[3])
        rot_mat = glm.mat3(world_mat)

        # 确定骨骼方向和长度
        # Blender骨骼在GLTF中沿局部+Y轴延伸
        child_joints = children_map.get(joint_idx, [])
        if child_joints:
            # 有子关节：方向从骨骼位置指向子关节位置
            child_pos = glm.vec3(world_transforms[child_joints[0]][3])
            direction = child_pos - pos
            length = glm.length(direction)
            if length < 1e-6:
                direction = rot_mat * glm.vec3(0, 1, 0)
                length = 1.0
            else:
                direction = direction / length
        else:
            # 叶子骨骼：使用世界旋转矩阵提取局部+Y轴方向
            direction = rot_mat * glm.vec3(0, 1, 0)
            length = 1.0

        # 将方向向量转换为Bone类的(yaw, pitch, roll)约定
        # Bone类沿+Z延伸，先绕Y轴旋转-yaw，再绕X轴旋转pitch
        # 合成方向：D = (-sin(yaw)*cos(pitch), -sin(pitch), cos(yaw)*cos(pitch))
        dx, dy, dz = direction.x, direction.y, direction.z
        h = math.sqrt(dx * dx + dz * dz)
        if h > 1e-6:
            yaw = math.degrees(math.atan2(-dx, dz))
            pitch = math.degrees(math.atan2(-dy, h))
        else:
            yaw = 0.0
            pitch = -90.0 if dy > 0 else 90.0

        bone = soup3D.skeleton.Bone(
            (pos.x, pos.y, pos.z),
            length,
            (yaw, pitch, 0.0)
        )

        # 构建子骨骼
        for child_idx in child_joints:
            child_bone = _build_bone(child_idx, bone)
            bone.children.append(child_bone)

        skeleton.add_bone(name, bone)
        return bone

    for root_idx in root_joints:
        _build_bone(root_idx)

    return skeleton


def open_gltf(
        gltf: str,
        double_side: bool = True,
        max_light_count: int = 8,
        surface = soup3D.shader.AutoSP,
        skin = soup3D.shader.BoneBinderSP
    ):
    """
    从gltf文件导入模型和骨骼
    :param gltf:            gltf模型文件路径
    :param double_side:     是否启用双面渲染
    :param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题
    :param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side,max_light_count等参
                            数
    :param skin:            模型使用的蒙皮着色器类型，着色器需要有skeleton, base_color, emission, normal, double_side,
                            max_light_count等参数
    :return: (模型数据(Model类), 骨架数据(Skeleton类))
    """
    base_dir = os.path.dirname(os.path.abspath(gltf))

    # 读取GLTF文件
    with open(gltf, "r", encoding="utf-8") as f:
        gltf_data = json.load(f)

    # 加载缓冲区数据
    buffers_data = _gltf_load_buffers(gltf_data, base_dir)

    nodes = gltf_data["nodes"]

    # 计算所有节点的世界变换矩阵
    world_transforms = _gltf_compute_world_transforms(nodes)

    # 加载材质
    materials_dict = _gltf_load_materials(gltf_data, base_dir, double_side, max_light_count, surface)

    # 检查是否有蒙皮数据
    skins_data = gltf_data.get("skins", [])
    has_skin = len(skins_data) > 0

    # 构建骨架
    skeleton = _gltf_build_skeleton(gltf_data, world_transforms)

    # 读取蒙皮的逆绑定矩阵和关节映射
    joint_name_map = {}
    if has_skin:
        skin_info = skins_data[0]
        joints = skin_info["joints"]
        for joint_idx in joints:
            joint_name_map[joint_idx] = nodes[joint_idx].get("name", f"bone_{joint_idx}")

    # 创建默认材质
    default_surface = surface(
        base_color=soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0),
        emission=(0, 0, 0),
        normal=(0.5, 0.5, 1),
        double_side=double_side,
        max_light_count=max_light_count
    )

    # 处理所有网格
    all_faces = []
    meshes = gltf_data.get("meshes", [])

    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            attributes = primitive.get("attributes", {})

            # 读取顶点数据
            positions = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("POSITION", -1)) if "POSITION" in attributes else []
            normals = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("NORMAL", -1)) if "NORMAL" in attributes else []
            texcoords = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("TEXCOORD_0", -1)) if "TEXCOORD_0" in attributes else []
            joints_data = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("JOINTS_0", -1)) if "JOINTS_0" in attributes else []
            weights_data = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("WEIGHTS_0", -1)) if "WEIGHTS_0" in attributes else []

            # 读取索引数据
            indices = []
            if "indices" in primitive:
                indices = _gltf_read_accessor(gltf_data, buffers_data, primitive["indices"])

            # 获取材质
            mat_idx = primitive.get("material", -1)
            if mat_idx >= 0 and mat_idx in materials_dict:
                prim_surface = materials_dict[mat_idx]
            else:
                prim_surface = default_surface

            # 构建顶点列表
            vertices = []
            if indices:
                index_list = indices
            else:
                index_list = list(range(len(positions)))

            for idx in index_list:
                # 位置
                pos = positions[idx] if idx < len(positions) else (0, 0, 0)

                # 纹理坐标
                uv = texcoords[idx] if idx < len(texcoords) else (0, 0)

                # 法线
                nrm = normals[idx] if idx < len(normals) else (0, 0, 1)

                if has_skin and joints_data and weights_data:
                    # 带骨骼权重的顶点
                    joint_indices = joints_data[idx] if idx < len(joints_data) else (0, 0, 0, 0)
                    joint_weights = weights_data[idx] if idx < len(weights_data) else (0, 0, 0, 0)

                    # 构建骨骼权重字典
                    bone_weights_dict = {}
                    for j in range(4):
                        if joint_weights[j] > 0.0 and joint_indices[j] in joint_name_map:
                            bone_weights_dict[joint_name_map[joint_indices[j]]] = joint_weights[j]

                    vertex = (
                        bone_weights_dict,
                        pos[0], pos[1], pos[2],
                        uv[0], uv[1],
                        nrm[0], nrm[1], nrm[2]
                    )
                else:
                    # 普通顶点
                    vertex = (
                        pos[0], pos[1], pos[2],
                        uv[0], uv[1],
                        nrm[0], nrm[1], nrm[2]
                    )
                vertices.append(vertex)

            if not vertices:
                continue

            # 根据是否有骨骼选择着色器类型
            if has_skin and joints_data and weights_data:
                face_surface = skin(
                    base_color=prim_surface.base_color if hasattr(prim_surface, 'base_color') else soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0),
                    normal=prim_surface.normal if hasattr(prim_surface, 'normal') else (0.5, 0.5, 1),
                    emission=prim_surface.emission if hasattr(prim_surface, 'emission') else (0, 0, 0),
                    double_side=prim_surface.double_side if hasattr(prim_surface, 'double_side') else double_side,
                    max_light_count=max_light_count,
                    skeleton=skeleton
                )
            else:
                face_surface = prim_surface

            face = Face(TRIANGLE_B, face_surface, vertices)
            all_faces.append(face)

    # 创建模型
    model = Model(0, 0, 0, *all_faces)

    return model, skeleton


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


if __name__ == '__main__':
    ...