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


class Data:
    def __init__(self, data_type: str, data):
        """
        数据结构，可通过该类创建的对象生成模型、着色器、骨骼等元素。该类通常通过文件加载器(如open_obj)创建对象。
        :param data_type: 数据类型标识，"obj"表示obj模型数据，"mtl"表示材质数据，"gltf"表示gltf模型数据
        :param data:      存储的原始数据
        """
        self._data_type = data_type
        self._data = data

    def make(self):
        """
        通过数据生成相关元素对象，每次调用都会生成全新的独立对象
        :return: 模型或其他元素对象，返回值类型和数量与生成该数据的文件加载器一致
        """
        if self._data_type == "mtl":
            return _make_mtl_data(self._data)
        elif self._data_type == "obj":
            return _make_obj_data(self._data)
        elif self._data_type == "gltf":
            return _make_gltf_data(self._data)
        raise Exception("Unsupported data type: " + self._data_type)


def _build_channel_value(val):
    """
    从存储的通道数据构建通道值，用于Data.make()内部调用
    :param val: 存储的通道数据，float或("channel", path, channel_idx)
    :return: 通道值，float或Channel对象
    """
    if isinstance(val, tuple) and len(val) == 3 and val[0] == "channel":
        texture = soup3D.shader.Texture(val[1])
        return soup3D.shader.Channel(texture, val[2])
    return val


def _build_base_color(bc_data: dict) -> soup3D.shader.MixChannel:
    """
    从存储的基础颜色数据构建MixChannel对象，用于Data.make()内部调用
    :param bc_data: 存储的基础颜色数据字典，包含width, height, R, G, B, A
    :return: MixChannel对象
    """
    R = _build_channel_value(bc_data["R"])
    G = _build_channel_value(bc_data["G"])
    B = _build_channel_value(bc_data["B"])
    A = _build_channel_value(bc_data["A"])
    return soup3D.shader.MixChannel((bc_data["width"], bc_data["height"]), R, G, B, A)


def _build_surface_arg(val):
    """
    从存储的数据构建表面参数值，用于Data.make()内部调用
    :param val: 存储的数据，tuple/None/("texture", path)
    :return: 表面参数值
    """
    if isinstance(val, tuple) and len(val) == 2 and val[0] == "texture":
        return soup3D.shader.Texture(val[1])
    return val


def _make_mtl_data(data: dict) -> dict:
    """
    从存储的材质数据生成着色器字典，用于Data.make()内部调用
    :param data: 存储的材质数据，键为材质名称，值为材质信息字典
    :return: 材质名称到着色器的映射字典
    """
    mtl_dict = {}
    for name, mat_info in data.items():
        base_color = _build_base_color(mat_info["base_color"])
        emission = _build_surface_arg(mat_info["emission"])
        normal = _build_surface_arg(mat_info["normal"])
        if normal is None:
            normal = (0.5, 0.5, 1)
        surface_class = mat_info["surface"]
        mtl_dict[name] = surface_class(
            base_color=base_color,
            emission=emission,
            normal=normal,
            double_side=mat_info["double_side"],
            max_light_count=mat_info["max_light_count"],
        )
    return mtl_dict


def _make_obj_data(data: dict) -> "Model":
    """
    从存储的obj数据生成模型，用于Data.make()内部调用
    :param data: 存储的obj数据字典
    :return: 模型对象
    """
    mtl_dict = _make_mtl_data(data["mtl_data"])
    default_bc = data["default_material"]["base_color"]
    default_material = data["default_material"]["surface"](
        base_color=soup3D.shader.MixChannel(
            (default_bc["width"], default_bc["height"]),
            default_bc["R"], default_bc["G"], default_bc["B"], default_bc["A"]
        ),
        emission=data["default_material"]["emission"],
        normal=data["default_material"]["normal"] or (0.5, 0.5, 1),
        double_side=data["default_material"]["double_side"],
        max_light_count=data["default_material"]["max_light_count"],
    )
    faces = []
    for group in data["face_groups"]:
        mat_name = group["material_name"]
        if mat_name is not None and mat_name in mtl_dict:
            surface = mtl_dict[mat_name]
        else:
            surface = default_material
        if group["vertices"]:
            face = Face(
                shape_type="triangle_b",
                surface=surface,
                vertex=group["vertices"],
            )
            faces.append(face)
    model = Model(0, 0, 0, *faces)
    return model


def _make_gltf_skeleton(data: dict) -> soup3D.skeleton.Skeleton:
    """
    从存储的骨骼数据生成骨架，用于Data.make()内部调用
    :param data: 存储的骨骼数据字典，包含bones和root_bones
    :return: 骨架对象
    """
    skeleton = soup3D.skeleton.Skeleton()
    all_bones = {}
    for name, bone_data in data["bones"].items():
        bone = soup3D.skeleton.Bone(
            bone_data["pos"],
            bone_data["length"],
            bone_data["toward"],
        )
        all_bones[name] = bone
    for name, bone_data in data["bones"].items():
        for child_name in bone_data["children"]:
            all_bones[name].add_child(all_bones[child_name])
    for name, bone in all_bones.items():
        skeleton.add_bone(name, bone)
    return skeleton


def _build_gltf_base_color(bc_data: tuple) -> soup3D.shader.MixChannel:
    """
    从存储的gltf基础颜色数据构建MixChannel对象，用于Data.make()内部调用
    :param bc_data: 存储的基础颜色数据元组
    :return: MixChannel对象
    """
    if bc_data[0] == "textured":
        _, img_bytes, w, h, fmt, has_alpha = bc_data
        tex = soup3D.shader.Texture(img_bytes, width=w, height=h, format=fmt)
        r_ch = soup3D.shader.Channel(tex, 0)
        g_ch = soup3D.shader.Channel(tex, 1)
        b_ch = soup3D.shader.Channel(tex, 2)
        a_ch = soup3D.shader.Channel(tex, 3) if has_alpha else 1.0
        return soup3D.shader.MixChannel((w, h), r_ch, g_ch, b_ch, a_ch)
    elif bc_data[0] == "solid":
        _, w, h, R, G, B, A = bc_data
        return soup3D.shader.MixChannel((w, h), R, G, B, A)
    return soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0)


def _build_gltf_emission(emi_data) -> tuple | soup3D.shader.Texture:
    """
    从存储的gltf自发光数据构建参数值，用于Data.make()内部调用
    :param emi_data: 存储的自发光数据
    :return: 自发光参数值
    """
    if isinstance(emi_data, tuple) and len(emi_data) == 5 and emi_data[0] == "image":
        _, img_bytes, w, h, fmt = emi_data
        return soup3D.shader.Texture(img_bytes, width=w, height=h, format=fmt)
    return emi_data


def _make_gltf_data(data: dict):
    """
    从存储的gltf数据生成模型和骨架，用于Data.make()内部调用
    :param data: 存储的gltf数据字典
    :return: (模型对象, 骨架对象)
    """
    skeleton = _make_gltf_skeleton(data["skeleton_data"])
    materials_dict = {}
    for mat_idx, mat_info in data["materials"].items():
        base_color = _build_gltf_base_color(mat_info["base_color"])
        emission = _build_gltf_emission(mat_info["emission"])
        surface_class = mat_info["surface"]
        materials_dict[mat_idx] = surface_class(
            base_color=base_color,
            emission=emission,
            normal=mat_info["normal"],
            double_side=mat_info["double_side"],
            max_light_count=mat_info["max_light_count"],
        )
    default_surface = data["default_surface_class"](
        base_color=soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0),
        emission=(0, 0, 0),
        normal=(0.5, 0.5, 1),
        double_side=data["double_side"],
        max_light_count=data["max_light_count"],
    )
    all_faces = []
    skin_class = data["skin"]
    for prim_data in data["primitives"]:
        has_skin = prim_data["has_skin"]
        mat_idx = prim_data["material_idx"]
        if mat_idx >= 0 and mat_idx in materials_dict:
            prim_surface = materials_dict[mat_idx]
        else:
            prim_surface = default_surface
        if has_skin and skin_class is not None:
            face_surface = skin_class(
                base_color=prim_surface.base_color if hasattr(prim_surface, 'base_color') else soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0),
                normal=prim_surface.normal if hasattr(prim_surface, 'normal') else (0.5, 0.5, 1),
                emission=prim_surface.emission if hasattr(prim_surface, 'emission') else (0, 0, 0),
                double_side=prim_surface.double_side if hasattr(prim_surface, 'double_side') else data["double_side"],
                max_light_count=data["max_light_count"],
                skeleton=skeleton,
            )
        else:
            face_surface = prim_surface
        face = Face(TRIANGLE_B, face_surface, prim_data["vertices"])
        all_faces.append(face)
    model = Model(0, 0, 0, *all_faces)
    return model, skeleton


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

    # 重置着色器管线状态，切换到固定功能管线
    glUseProgram(0)
    glActiveTexture(GL_TEXTURE0)
    glBindVertexArray(0)

    # 保存当前矩阵状态
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    # 设置正交投影
    gluOrtho2D(0, width, height, 0)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # 保存并重置 GL 状态
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glDisable(GL_LIGHTING)

    # 重置顶点颜色并设置纹理环境模式
    # 骨骼蒙皮着色器的 vertex attribute 3 会污染 OpenGL 当前顶点颜色，
    # 导致固定管线渲染时纹理颜色乘以接近零的颜色值变为不可见
    glColor4f(1.0, 1.0, 1.0, 1.0)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)

    # 启用纹理和混合
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 绘制全屏四边形
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex2f(width, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex2f(width, height)
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, height)
    glEnd()

    # 恢复状态
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
        # 计算骨骼末端位置（用于可视化）
        _m = glm.mat4(1.0)
        _m = glm.translate(_m, bone.pos)
        _m = glm.rotate(_m, glm.radians(-bone.toward.x), glm.vec3(0, 1, 0))
        _m = glm.rotate(_m, glm.radians(bone.toward.y), glm.vec3(1, 0, 0))
        _m = glm.rotate(_m, glm.radians(bone.toward.z), glm.vec3(0, 0, 1))
        _ep = _m * glm.vec4(0, 0, bone.length, 1.0)
        end_pos = (_ep.x, _ep.y, _ep.z)
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


def _store_mtl_material(width, height, R, G, B, A, emission, bump_texture, double_side, max_light_count, surface):
    """
    将材质数据存储为数据字典，用于data_only模式
    :param width:           纹理宽度
    :param height:          纹理高度
    :param R:               红色通道值
    :param G:               绿色通道值
    :param B:               蓝色通道值
    :param A:               透明度通道值
    :param emission:        自发光数据
    :param bump_texture:    法线贴图数据
    :param double_side:     是否启用双面渲染
    :param max_light_count: 最大光源数量
    :param surface:         表面着色器类型
    :return: 材质数据字典
    """
    return {
        "base_color": {"width": width, "height": height, "R": R, "G": G, "B": B, "A": A},
        "emission": emission,
        "normal": bump_texture,
        "double_side": double_side,
        "max_light_count": max_light_count,
        "surface": surface,
    }


def open_mtl(mtl: str,
             double_side: bool = True,
             roll_funk=None,
             encoding: str = "utf-8",
             max_light_count: int = 8,
             surface = soup3D.shader.AutoSP,
             data_only: bool = False) -> "dict | Data":
    """
    根据mtl文件生成多个着色器
    :param mtl:             *.mtl纹理文件路径
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)
    :param max_light_count: 这些着色器出现时会同时出现的最多的光源数量，大了会导致性能问题
    :param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side, max_light_count等
                            参数
    :param data_only:       是否只创建模型数据结构，当为True时，则返回着色器相关的数据，而不是着色器本身。当需要用一个文件创建多组独立的着色
                            器时，则将该值设为True。
    :return: 所有生成出的表面着色器，当data_only为True时返回Data对象
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
                    if data_only:
                        mtl_dict[now_mtl] = _store_mtl_material(
                            width, height, R, G, B, A, emission, bump_texture,
                            double_side, max_light_count, surface)
                    else:
                        mtl_dict[now_mtl] = surface(
                            base_color=soup3D.shader.MixChannel((width, height), R, G, B, A),
                            emission=emission,
                            normal=bump_texture if bump_texture else (0.5, 0.5, 1),
                            double_side=double_side,
                            max_light_count=max_light_count
                        )

                    R, G, B, A = 1.0, 1.0, 1.0, 1.0
                    width, height = 1, 1
                    emission = 0, 0, 0
                    bump_texture = None
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
                try:
                    img = imageio.imread(tex_path)
                    height, width = img.shape[:2]
                except:
                    width, height = 1, 1
                if data_only:
                    R = ("channel", tex_path, 0)
                    G = ("channel", tex_path, 1)
                    B = ("channel", tex_path, 2)
                else:
                    texture = soup3D.shader.Texture(tex_path)
                    R = soup3D.shader.Channel(texture, 0)
                    G = soup3D.shader.Channel(texture, 1)
                    B = soup3D.shader.Channel(texture, 2)
            if args[0] == "map_d":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                if data_only:
                    A = ("channel", tex_path, 3)
                else:
                    texture = soup3D.shader.Texture(tex_path)
                    A = soup3D.shader.Channel(texture, 3)
            if args[0] == "map_Ke":
                base_dir = os.path.dirname(mtl)
                tex_path = (os.path.join(base_dir, args[1]))
                if data_only:
                    emission = ("texture", tex_path)
                else:
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
                        arg_name = None
                        continue
                if data_only:
                    bump_texture = ("texture", tex_path)
                else:
                    bump_texture = soup3D.shader.Texture(tex_path)

    # 添加最后一个材质
    if now_mtl is not None:
        if data_only:
            mtl_dict[now_mtl] = _store_mtl_material(
                width, height, R, G, B, A, emission, bump_texture,
                double_side, max_light_count, surface)
        else:
            mtl_dict[now_mtl] = surface(
                base_color=soup3D.shader.MixChannel((width, height), R, G, B, A),
                emission=emission,
                normal=bump_texture if bump_texture else (0.5, 0.5, 1),
                double_side=double_side,
                max_light_count=max_light_count
            )

    if data_only:
        return Data("mtl", mtl_dict)
    return mtl_dict


def open_obj(obj: str,
             mtl: "str | dict | Data | None" = None,
             double_side: bool = True,
             roll_funk=None,
             encoding: str = "utf-8",
             max_light_count: int = 8,
             data_only: bool = False) -> "Model | Data":
    """
    从obj文件导入模型
    :param obj:             *.obj模型文件路径
    :param mtl:             *.mtl纹理文件路径、已加载的材质字典或Data对象
    :param double_side:     是否启用双面渲染
    :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数
    :param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)
    :param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题
    :param data_only:       是否只创建模型数据结构，当为True时，则返回模型相关的数据，而不是模型本身。当需要用一个文件创建多个独立的模型时，
                            则将该值设为True。
    :return: 生成出来的模型数据(Model类)，当data_only为True时返回Data对象
    """
    # 处理mtl文件
    mtl_dict = {}

    # 如果mtl是字符串路径，则调用load_mtl加载
    if isinstance(mtl, str):
        mtl_dict = open_mtl(mtl, double_side, roll_funk, encoding, max_light_count, data_only=data_only)
    elif isinstance(mtl, Data):
        # 如果传入的是Data对象，根据data_only决定是否构建着色器
        if data_only:
            mtl_dict = mtl
        else:
            mtl_dict = mtl.make()
    elif isinstance(mtl, dict):
        # 如果已经是字典，则直接使用
        mtl_dict = mtl

    # 创建默认材质（如果未提供MTL或材质未定义时使用），data_only模式下不创建着色器对象
    default_material = None
    if not data_only:
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
    current_material_name = None

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
                    mtl_dict = open_mtl(mtl_path, double_side, roll_funk, encoding, max_light_count, data_only=data_only)

        # 处理材质使用
        elif prefix == 'usemtl':
            # 切换当前使用的材质
            if data:
                material_name = data[0]
                current_material_name = material_name
                if not data_only:
                    # 如果材质在库中未定义，使用默认材质
                    if isinstance(mtl_dict, dict):
                        current_material = mtl_dict.get(material_name, default_material)
                    else:
                        current_material = default_material

        # 处理面定义
        elif prefix == 'f':
            if len(data) < 3:
                continue  # 至少需要3个顶点构成面

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
            triangles = []
            for i in range(1, len(base_indexes) - 1):
                triangles.extend([
                    base_indexes[0],
                    base_indexes[i],
                    base_indexes[i + 1]
                ])

            if data_only:
                # data_only模式：按材质名称分组
                mat_key = current_material_name
                if mat_key not in faces_by_material:
                    faces_by_material[mat_key] = {'vertices': []}
                faces_by_material[mat_key]['vertices'].extend(triangles)
            else:
                # 普通模式：按材质对象id分组
                material_id = id(current_material) if current_material else id(default_material)
                if material_id not in faces_by_material:
                    faces_by_material[material_id] = {
                        'material': current_material if current_material else default_material,
                        'vertices': []
                    }
                faces_by_material[material_id]['vertices'].extend(triangles)

    if data_only:
        # 获取材质数据
        if isinstance(mtl_dict, Data):
            mtl_data = mtl_dict._data
        elif isinstance(mtl_dict, dict):
            mtl_data = mtl_dict
        else:
            mtl_data = {}

        face_groups = []
        for mat_name, face_data in faces_by_material.items():
            if face_data['vertices']:
                face_groups.append({
                    "material_name": mat_name,
                    "vertices": face_data['vertices'],
                })

        obj_data = {
            "face_groups": face_groups,
            "mtl_data": mtl_data,
            "default_material": _store_mtl_material(
                1, 1, 1.0, 1.0, 1.0, 1.0, (0, 0, 0), None,
                double_side, max_light_count, soup3D.shader.AutoSP),
            "double_side": double_side,
            "max_light_count": max_light_count,
        }
        return Data("obj", obj_data)

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


def _gltf_load_materials(gltf_data: dict, base_dir: str, double_side: bool, max_light_count: int, surface, data_only: bool = False) -> dict:
    """
    加载GLTF材质，返回材质索引到着色器的映射
    :param gltf_data:      GLTF JSON数据
    :param base_dir:       GLTF文件所在目录
    :param double_side:    是否启用双面渲染
    :param max_light_count: 最大光源数量
    :param surface:        表面着色器类型
    :param data_only:      是否只存储材质数据而不创建着色器对象
    :return: 材质字典 {材质索引: 着色器对象或材质数据字典}
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
        base_color_data = ("solid", 1, 1, 0.8, 0.8, 0.8, 1.0)
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
                    has_alpha = fmt == "RGBA"
                    img_bytes = img_array.tobytes()
                    if data_only:
                        base_color_data = ("textured", img_bytes, w, h, fmt, has_alpha)
                    else:
                        tex = soup3D.shader.Texture(img_bytes, width=w, height=h, format=fmt)
                        r_ch = soup3D.shader.Channel(tex, 0)
                        g_ch = soup3D.shader.Channel(tex, 1)
                        b_ch = soup3D.shader.Channel(tex, 2)
                        a_ch = soup3D.shader.Channel(tex, 3) if has_alpha else 1.0
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
                    img_bytes = img_array.tobytes()
                    if data_only:
                        emission = ("image", img_bytes, w, h, fmt)
                    else:
                        tex = soup3D.shader.Texture(img_bytes, width=w, height=h, format=fmt)
                        emission = tex

        if data_only:
            materials_dict[mat_idx] = {
                "base_color": base_color_data,
                "emission": emission,
                "normal": (0.5, 0.5, 1),
                "double_side": mat_double_side,
                "max_light_count": max_light_count,
                "surface": surface,
            }
        else:
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


def _gltf_compute_world_recursive(idx, nodes, parent_transform, world_transforms):
    """
    递归计算单个节点的世界变换矩阵
    :param idx:              节点索引
    :param nodes:            GLTF节点列表
    :param parent_transform: 父节点世界变换矩阵
    :param world_transforms: 世界变换矩阵列表（就地修改）
    :return: None
    """
    local = _gltf_build_node_transform(nodes[idx])
    world = parent_transform * local
    world_transforms[idx] = world
    for child_idx in nodes[idx].get("children", []):
        _gltf_compute_world_recursive(child_idx, nodes, world, world_transforms)


def _gltf_compute_world_transforms(nodes: list) -> list:
    """
    计算所有节点的世界变换矩阵
    :param nodes: GLTF节点列表
    :return: 世界变换矩阵列表
    """
    world_transforms = [None] * len(nodes)
    root_nodes = []
    has_parent = set()
    for i, node in enumerate(nodes):
        for child_idx in node.get("children", []):
            has_parent.add(child_idx)
    for i in range(len(nodes)):
        if i not in has_parent:
            root_nodes.append(i)

    for root_idx in root_nodes:
        _gltf_compute_world_recursive(root_idx, nodes, glm.mat4(1.0), world_transforms)

    return world_transforms


def _gltf_build_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, skeleton):
    """
    递归构建骨骼节点
    :param joint_idx:        关节索引
    :param nodes:            GLTF节点列表
    :param world_transforms: 世界变换矩阵列表
    :param joint_names:      关节名称映射
    :param children_map:     关节子节点映射
    :param skeleton:         骨架对象（就地添加骨骼）
    :return: 骨骼对象
    """
    name = joint_names[joint_idx]
    world_mat = world_transforms[joint_idx]
    pos = glm.vec3(world_mat[3])
    rot_mat = glm.mat3(world_mat)

    # 从旋转矩阵提取骨骼方向（Blender骨骼在GLTF中沿局部+Y轴延伸）
    raw_dir = rot_mat * glm.vec3(0, 1, 0)
    if glm.length(raw_dir) < 1e-6:
        direction = glm.vec3(0, 1, 0)
    else:
        direction = glm.normalize(raw_dir)

    # 从文件数据计算骨骼长度（骨骼根到最近子关节的距离）
    child_joints = children_map.get(joint_idx, [])
    if child_joints:
        child_pos = glm.vec3(world_transforms[child_joints[0]][3])
        length = glm.length(child_pos - pos)
        if length < 1e-6:
            length = 1.0
    else:
        length = 1.0

    # 将方向向量转换为Bone类的(yaw, pitch, roll)约定
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
        child_bone = _gltf_build_bone_recursive(
            child_idx, nodes, world_transforms, joint_names, children_map, skeleton
        )
        bone.add_child(child_bone)

    skeleton.add_bone(name, bone)
    return bone


def _gltf_store_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, bones_data):
    """
    递归存储骨骼数据为字典格式，用于data_only模式
    :param joint_idx:        关节索引
    :param nodes:            GLTF节点列表
    :param world_transforms: 世界变换矩阵列表
    :param joint_names:      关节名称映射
    :param children_map:     关节子节点映射
    :param bones_data:       骨骼数据字典（就地修改）
    :return: 骨骼名称
    """
    name = joint_names[joint_idx]
    world_mat = world_transforms[joint_idx]
    pos = glm.vec3(world_mat[3])
    rot_mat = glm.mat3(world_mat)

    raw_dir = rot_mat * glm.vec3(0, 1, 0)
    if glm.length(raw_dir) < 1e-6:
        direction = glm.vec3(0, 1, 0)
    else:
        direction = glm.normalize(raw_dir)

    child_joints = children_map.get(joint_idx, [])
    if child_joints:
        child_pos = glm.vec3(world_transforms[child_joints[0]][3])
        length = glm.length(child_pos - pos)
        if length < 1e-6:
            length = 1.0
    else:
        length = 1.0

    dx, dy, dz = direction.x, direction.y, direction.z
    h = math.sqrt(dx * dx + dz * dz)
    if h > 1e-6:
        yaw = math.degrees(math.atan2(-dx, dz))
        pitch = math.degrees(math.atan2(-dy, h))
    else:
        yaw = 0.0
        pitch = -90.0 if dy > 0 else 90.0

    child_names = []
    for child_idx in child_joints:
        child_name = _gltf_store_bone_recursive(
            child_idx, nodes, world_transforms, joint_names, children_map, bones_data
        )
        child_names.append(child_name)

    bones_data[name] = {
        "pos": (pos.x, pos.y, pos.z),
        "length": length,
        "toward": (yaw, pitch, 0.0),
        "children": child_names,
    }
    return name


def _gltf_store_skeleton(gltf_data: dict, world_transforms: list) -> dict:
    """
    从GLTF数据存储骨架数据为字典格式
    :param gltf_data:        GLTF JSON数据
    :param world_transforms: 节点世界变换矩阵列表
    :return: 骨架数据字典 {"bones": {name: info}, "root_bones": [name]}
    """
    nodes = gltf_data["nodes"]
    skins = gltf_data.get("skins", [])

    bones_data = {}
    root_bones = []

    if not skins:
        return {"bones": bones_data, "root_bones": root_bones}

    skin_info = skins[0]
    joints = skin_info["joints"]
    joint_names = {}
    for joint_idx in joints:
        joint_names[joint_idx] = nodes[joint_idx].get("name", f"bone_{joint_idx}")

    children_map = {}
    for joint_idx in joints:
        children_map[joint_idx] = []
        for child_idx in nodes[joint_idx].get("children", []):
            if child_idx in joint_names:
                children_map[joint_idx].append(child_idx)

    root_joints = []
    for joint_idx in joints:
        is_root = True
        for other_idx in joints:
            if joint_idx in nodes[other_idx].get("children", []):
                is_root = False
                break
        if is_root:
            root_joints.append(joint_idx)

    for root_idx in root_joints:
        root_name = _gltf_store_bone_recursive(
            root_idx, nodes, world_transforms, joint_names, children_map, bones_data
        )
        root_bones.append(root_name)

    return {"bones": bones_data, "root_bones": root_bones}


def _gltf_build_skeleton(gltf_data: dict, world_transforms: list) -> soup3D.skeleton.Skeleton:
    """
    从GLTF数据构建骨架
    :param gltf_data:        GLTF JSON数据
    :param world_transforms: 节点世界变换矩阵列表
    :return: Skeleton对象
    """
    nodes = gltf_data["nodes"]
    skeleton = soup3D.skeleton.Skeleton()

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
    root_joints = []
    for joint_idx in joints:
        is_root = True
        for other_idx in joints:
            if joint_idx in nodes[other_idx].get("children", []):
                is_root = False
                break
        if is_root:
            root_joints.append(joint_idx)

    for root_idx in root_joints:
        _gltf_build_bone_recursive(root_idx, nodes, world_transforms, joint_names, children_map, skeleton)

    return skeleton


def open_gltf(
        gltf: str,
        double_side: bool = True,
        max_light_count: int = 8,
        surface = soup3D.shader.AutoSP,
        skin = soup3D.shader.BoneBinderSP,
        data_only: bool = False,
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
    :param data_only:       是否只创建模型和骨骼的数据结构，当为True时，则返回模型相关的数据，而不是模型和骨骼本身。当需要用一个文件创建多个
                            独立的模型时，则将该值设为True。
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
    materials_dict = _gltf_load_materials(gltf_data, base_dir, double_side, max_light_count, surface, data_only=data_only)

    # 检查是否有蒙皮数据
    skins_data = gltf_data.get("skins", [])
    has_skin = len(skins_data) > 0

    # 构建骨架或存储骨架数据
    skeleton = None
    skeleton_data = None
    if data_only:
        skeleton_data = _gltf_store_skeleton(gltf_data, world_transforms)
    else:
        skeleton = _gltf_build_skeleton(gltf_data, world_transforms)

    # 读取蒙皮的逆绑定矩阵和关节映射
    # JOINTS_0的值是skin.joints数组的索引，需要映射到骨骼名称
    joint_name_map = {}
    if has_skin:
        skin_info = skins_data[0]
        joints = skin_info["joints"]
        for arr_idx, node_idx in enumerate(joints):
            joint_name_map[arr_idx] = nodes[node_idx].get("name", f"bone_{node_idx}")

    # 创建默认材质（data_only模式下不创建着色器对象）
    default_surface = None
    if not data_only:
        default_surface = surface(
            base_color=soup3D.shader.MixChannel((1, 1), 0.8, 0.8, 0.8, 1.0),
            emission=(0, 0, 0),
            normal=(0.5, 0.5, 1),
            double_side=double_side,
            max_light_count=max_light_count
        )

    # 处理所有网格
    all_faces = []
    primitives_data = []
    meshes = gltf_data.get("meshes", [])

    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            attributes = primitive.get("attributes", {})

            # 读取顶点数据
            positions = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("POSITION", -1)) if "POSITION" in attributes else []
            prim_normals = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("NORMAL", -1)) if "NORMAL" in attributes else []
            texcoords = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("TEXCOORD_0", -1)) if "TEXCOORD_0" in attributes else []
            joints_data = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("JOINTS_0", -1)) if "JOINTS_0" in attributes else []
            weights_data = _gltf_read_accessor(gltf_data, buffers_data, attributes.get("WEIGHTS_0", -1)) if "WEIGHTS_0" in attributes else []

            # 读取索引数据
            indices = []
            if "indices" in primitive:
                indices = _gltf_read_accessor(gltf_data, buffers_data, primitive["indices"])

            # 获取材质
            mat_idx = primitive.get("material", -1)
            prim_surface = default_surface
            if not data_only:
                if mat_idx >= 0 and mat_idx in materials_dict:
                    prim_surface = materials_dict[mat_idx]

            # 构建顶点列表
            vertices = []
            prim_has_skin = has_skin and bool(joints_data) and bool(weights_data)
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
                nrm = prim_normals[idx] if idx < len(prim_normals) else (0, 0, 1)

                if prim_has_skin:
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

            if data_only:
                primitives_data.append({
                    "vertices": vertices,
                    "has_skin": prim_has_skin,
                    "material_idx": mat_idx,
                })
            else:
                # 根据是否有骨骼选择着色器类型
                if prim_has_skin:
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

    if data_only:
        gltf_stored = {
            "primitives": primitives_data,
            "materials": materials_dict,
            "skeleton_data": skeleton_data,
            "double_side": double_side,
            "max_light_count": max_light_count,
            "surface": surface,
            "skin": skin,
            "default_surface_class": surface,
        }
        return Data("gltf", gltf_stored)

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