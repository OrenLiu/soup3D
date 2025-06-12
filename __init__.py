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

import soup3D.shader
import soup3D.img
import soup3D.event
import soup3D.camera
import soup3D.light
import soup3D.ui
from soup3D.name import *

render_queue = []  # 全局渲染队列
stable_shapes = {}

_current_fov = 45
_current_far = 1024


class Face:
    def __init__(self,
                 shape_type: str,
                 surface: soup3D.shader.BSDF,
                 vertex: list | tuple):
        """
        表面，可用于创建线段、多边形
        :param shape_type: 绘制方式，可以填写这些内容：
                           "line_b": 不相连线段
                           "line_s": 连续线段
                           "line_l": 头尾相连的连续线段
                           "triangle_b": 不相连三角形
                           "triangle_s": 相连三角形
                           "triangle_l": 头尾相连的连续三角形
        :param surface:    表面使用的BSDF着色器
        :param vertex:     图形中所有的端点，格式为：
                           [(x, y, z, u, v), ...]
        """
        # 1. 初始化类成员
        self.shape_type = shape_type
        self.surface = surface
        self.vertex = vertex

        # 设置OpenGL绘制模式
        self.mode_map = {
            "line_b": GL_LINES,
            "line_s": GL_LINE_STRIP,
            "line_l": GL_LINE_LOOP,
            "triangle_b": GL_TRIANGLES,
            "triangle_s": GL_TRIANGLE_STRIP,
            "triangle_l": GL_TRIANGLE_FAN
        }

        if shape_type not in self.mode_map:
            raise ValueError(f"不支持的shape_type: {shape_type}")

        self.mode = self.mode_map[shape_type]

        # 计算渲染优先级（基于base_color的透明度）
        self.render_priority = False
        # 检查base_color是否是Texture或MixChannel
        if isinstance(self.surface.base_color, soup3D.shader.Texture):
            # 假设Texture可能包含透明像素
            self.render_priority = True
        elif isinstance(self.surface.base_color, soup3D.shader.MixChannel):
            # 检查MixChannel的A通道
            if isinstance(self.surface.base_color.A, (float, int)):
                # 如果A通道是浮点数且小于1.0
                if self.surface.base_color.A < 1.0:
                    self.render_priority = True
            else:
                # 如果A通道是Channel对象（可能包含透明像素）
                self.render_priority = True

        # 2. 创建OpenGL渲染列表
        self.list_id = glGenLists(1)
        self._generate_display_list()

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

    def _generate_display_list(self):
        """生成OpenGL显示列表，应用材质属性"""
        # 处理透明度
        self.smoothness_tex_id = None
        self.emission_tex_id = None

        # 获取顶点纹理尺寸（使用第一个顶点的UV坐标）
        tex_size = (64, 64)  # 默认纹理尺寸
        if self.vertex and len(self.vertex[0]) >= 5:
            # 假设所有顶点使用相同的纹理尺寸
            tex_size = (int(max(v[3] for v in self.vertex) * 64),
                        int(max(v[4] for v in self.vertex) * 64))

        # 材质贴图（分配到纹理单元0）
        self.texture_id = None
        if isinstance(self.surface.base_color, soup3D.shader.Texture):
            pil_img = self.surface.base_color.pil_pic
            self.texture_id = soup3D.img.pil_to_texture(pil_img, texture_unit=0)
        elif isinstance(self.surface.base_color, soup3D.shader.MixChannel):
            pil_img = self.surface.base_color.pil_pic
            self.texture_id = soup3D.img.pil_to_texture(pil_img, texture_unit=0)

        # 法线贴图（分配到纹理单元1）
        self.normal_map_id = None
        if isinstance(self.surface.normal, soup3D.shader.Texture):
            pil_img = self.surface.normal.pil_pic
            self.normal_map_id = soup3D.img.pil_to_texture(pil_img, texture_unit=1)
        elif isinstance(self.surface.normal, soup3D.shader.MixChannel):
            pil_img = self.surface.normal.pil_pic
            self.normal_map_id = soup3D.img.pil_to_texture(pil_img, texture_unit=1)

        # 处理光滑度纹理
        if isinstance(self.surface.smoothness, soup3D.shader.Channel):
            band_img = self.surface.smoothness.get_pil_band(tex_size)
            # 创建灰度图像
            smooth_img = Image.new("L", band_img.size)
            smooth_img.putdata(band_img.getdata())
            self.smoothness_tex_id = soup3D.img.pil_to_texture(smooth_img, texture_unit=3)

        # 处理自发光纹理
        if isinstance(self.surface.emission, soup3D.shader.Channel):
            band_img = self.surface.emission.get_pil_band(tex_size)
            # 创建灰度图像
            emission_img = Image.new("L", band_img.size)
            emission_img.putdata(band_img.getdata())
            self.emission_tex_id = soup3D.img.pil_to_texture(emission_img, texture_unit=4)

        # 创建显示列表
        glNewList(self.list_id, GL_COMPILE)

        # 启用必要的OpenGL功能
        glEnable(GL_DEPTH_TEST)

        # 设置材质属性
        if self.texture_id:
            # 使用纹理时不设置颜色
            glColor4f(1.0, 1.0, 1.0, 1.0)
        else:
            # 如果没有纹理，使用基色
            if isinstance(self.surface.base_color, tuple):
                base_color = self.surface.base_color
            else:
                base_color = (1.0, 1.0, 1.0)  # 默认白色
            glColor4f(base_color[0], base_color[1], base_color[2], 1.0)

        # 检查是否需要透明度 (基于base_color是否可能有透明)
        use_alpha = self.render_priority

        # 启用混合
        if use_alpha:
            # 保存当前混合模式
            glPushAttrib(GL_COLOR_BUFFER_BIT | GL_ENABLE_BIT)

            # 启用并设置正确的混合函数
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # 使用预乘Alpha混合以获得更好的结果
            glBlendEquation(GL_FUNC_ADD)
            glBlendFuncSeparate(
                GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA,
                GL_ONE, GL_ONE_MINUS_SRC_ALPHA
            )
        else:
            glDisable(GL_BLEND)

        # 开启纹理
        if self.texture_id or self.normal_map_id or self.smoothness_tex_id or self.emission_tex_id:
            glEnable(GL_TEXTURE_2D)

        # 激活并绑定材质贴图（纹理单元0）
        if self.texture_id:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        # 激活并绑定法线贴图（纹理单元1）
        if self.normal_map_id:
            glActiveTexture(GL_TEXTURE1)
            glBindTexture(GL_TEXTURE_2D, self.normal_map_id)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE)
            glTexEnvi(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_DOT3_RGB)

        # 激活并绑定光滑度贴图（纹理单元3）
        if self.smoothness_tex_id:
            glActiveTexture(GL_TEXTURE3)
            glBindTexture(GL_TEXTURE_2D, self.smoothness_tex_id)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        # 激活并绑定自发光贴图（纹理单元4）
        if self.emission_tex_id:
            glActiveTexture(GL_TEXTURE4)
            glBindTexture(GL_TEXTURE_2D, self.emission_tex_id)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        # 光滑度处理
        if self.surface.smoothness != 0.0 and not self.smoothness_tex_id:
            smoothness = max(0.0, min(1.0, float(self.surface.smoothness)))
            glMaterialf(GL_FRONT, GL_SHININESS, 128 * smoothness)
            glMaterialfv(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))

        # 自发光处理
        if self.surface.emission != 0.0 and not self.emission_tex_id:
            emission = max(0.0, min(1.0, float(self.surface.emission)))
            glMaterialfv(GL_FRONT, GL_EMISSION, (emission, emission, emission, 1.0))

        # 绘制几何图形
        glBegin(self.mode)
        for v in self.vertex:
            if len(v) == 5:
                # 设置纹理坐标
                if self.texture_id:
                    glMultiTexCoord2f(GL_TEXTURE0, v[3], v[4])  # base_color纹理
                if self.normal_map_id:
                    glMultiTexCoord2f(GL_TEXTURE1, v[3], v[4])  # 法线纹理
                if self.smoothness_tex_id:
                    glMultiTexCoord2f(GL_TEXTURE3, v[3], v[4])  # 光滑度纹理
                if self.emission_tex_id:
                    glMultiTexCoord2f(GL_TEXTURE4, v[3], v[4])  # 自发光纹理
                glVertex3f(v[0], v[1], v[2])
            else:
                # 没有纹理坐标的情况
                glVertex3f(v[0], v[1], v[2])
        glEnd()

        # 清理OpenGL状态
        if self.texture_id or self.normal_map_id or self.smoothness_tex_id or self.emission_tex_id:
            glDisable(GL_TEXTURE_2D)
            glActiveTexture(GL_TEXTURE0)

        # 恢复光照属性
        if self.surface.smoothness != 0.0 and not self.smoothness_tex_id:
            glMaterialfv(GL_FRONT, GL_SPECULAR, (0.0, 0.0, 0.0, 1.0))

        if self.surface.emission != 0.0 and not self.emission_tex_id:
            glMaterialfv(GL_FRONT, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

        if use_alpha:
            # 恢复之前的混合状态
            glPopAttrib()

        glEndList()

    def paint(self, x, y, z):
        """
        将渲染任务添加到渲染队列
        :param x: 坐标x增值
        :param y: 坐标y增值
        :param z: 坐标z增值
        :return: None
        """
        # 计算物体位置相对于相机的位置（用于深度排序）
        cam_pos = soup3D.camera.X, soup3D.camera.Y, soup3D.camera.Z
        obj_pos = (x, y, z)
        distance = sqrt((x - cam_pos[0]) ** 2 +
                        (y - cam_pos[1]) ** 2 +
                        (z - cam_pos[2]) ** 2)

        # 添加到全局渲染队列
        render_queue.append((distance, self.render_priority, self, obj_pos))

    def destroy(self):
        """
        释放与该图形相关的所有资源
        :return: None
        """
        # 删除显示列表
        glDeleteLists(self.list_id, 1)

        # 删除纹理
        textures = [
            self.texture_id,
            self.normal_map_id,
            self.smoothness_tex_id,
            self.emission_tex_id
        ]

        for tex_id in textures:
            if tex_id:
                glDeleteTextures([tex_id])


class Model:
    def __init__(self, x: int | float, y: int | float, z: int | float, *face: Face):
        """
        模型，由多个面(Face)组成，
        :param x:    模型原点对应x坐标
        :param y:    模型原点对应y坐标
        :param z:    模型原点对应z坐标
        :param face: 面
        """
        self.x, self.y, self.z = x, y, z
        self.faces = list(face)


def _get_channel_value(channel):
    """从Channel对象或浮点数获取通道值"""
    if isinstance(channel, soup3D.shader.Channel):
        # 对于纹理通道，我们不再使用平均值，而是使用纹理
        return 0.5  # 返回中间值，实际值将由纹理提供
    elif isinstance(channel, float) or isinstance(channel, int):
        return float(channel)
    return 1.0


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
    更新画布，包括处理渲染队列
    """
    global render_queue

    # 处理事件
    soup3D.event.check_event(pygame.event.get())

    # 清空画布
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # 设置相机
    soup3D.camera.update()

    # 对渲染队列排序：首先按渲染优先级（透明物体最后渲染），然后按距离（从远到近）
    render_queue.sort(key=lambda item: (item[1], -item[0]), reverse=False)

    # 渲染所有物体
    for distance, priority, face, position in render_queue:
        # 获取位置
        x, y, z = position

        # 实际渲染
        glPushMatrix()
        glTranslatef(x, y, z)
        glCallList(face.list_id)
        glPopMatrix()

    # 清空渲染队列
    render_queue = []

    # 刷新显示
    pygame.display.flip()


def open_obj(obj, mtl=None):
    ...


def _rotated(Xa, Ya, Xb, Yb, degree):
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
