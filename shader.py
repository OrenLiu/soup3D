"""
处理soup3D中的着色系统
"""
import PIL.Image
import numpy as np
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram


class Texture:
    def __init__(self, pil_pic: PIL.Image.Image):
        """
        贴图，基于pillow处理图像
        提取通道时：
        通道0: 红色通道
        通道1: 绿色通道
        通道2: 蓝色通道
        通道3: 透明度(如无该通道，则统一返回1)
        :param pil_pic: pillow图像
        """
        if not isinstance(pil_pic, PIL.Image.Image):
            raise TypeError(f"pil_pic should be PIL.Image.Image not {type(pil_pic)}")

        self.pil_pic = pil_pic

        self.hash = None
        self.update()

    def update(self):
        ...


class Channel:
    def __init__(self, texture: "Texture | MixChannel", channelID: int):
        """
        提取贴图中的单个通道
        :param texture:   提取通道的贴图
        :param channelID: 通道编号
        """
        if not isinstance(texture, Texture | MixChannel):
            raise TypeError(f"texture should be Texture | MixChannel not {type(texture)}")

        if not isinstance(channelID, int):
            raise TypeError(f"channelID should be int not {type(channelID)}")

        self.texture = texture
        self.channelID = channelID

        self.pil_band = None

        self.hash = None
        self.update()

    def get_pil_band(self) -> PIL.Image:
        """
        获取单通道pil图像
        :return:
        """
        img = self.texture.pil_pic
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        bands = img.split()
        self.pil_band = bands[self.channelID]

        return self.pil_band

    def update(self) -> None:
        self.get_pil_band()


class MixChannel:
    def __init__(self,
                 resize: tuple[int, int],
                 R: int | float | Channel,
                 G: int | float | Channel,
                 B: int | float | Channel,
                 A: int | float | Channel = 1.0):
        """
        混合通道成为一个贴图
        混合通道贴图(MixChannel)可通过类似贴图(Texture)的方式提取通道
        :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像
        :param R: 红色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param G: 绿色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param B: 蓝色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param A: 透明度通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        """
        if not isinstance(resize, tuple):
            raise TypeError(f"resize should be tuple[int not {type(resize)}")

        if not isinstance(R, int | float | Channel):
            raise TypeError(f"R should be int | float | Channel not {type(R)}")

        if not isinstance(G, int | float | Channel):
            raise TypeError(f"G should be int | float | Channel not {type(G)}")

        if not isinstance(B, int | float | Channel):
            raise TypeError(f"B should be int | float | Channel not {type(B)}")

        if not isinstance(A, int | float | Channel):
            raise TypeError(f"A should be int | float | Channel not {type(A)}")

        self.resize = resize
        self.R = R
        self.G = G
        self.B = B
        self.A = A

        self.pil_pic = None  # 缓存混合通道后的图像，以便父着色单元提取

        self.hash = None
        self.update()

    def update(self) -> None:
        """
        更新所有缓存项
        :return: None
        """
        # 创建目标尺寸的空图像（RGBA模式）
        result = PIL.Image.new('RGBA', self.resize)

        # 处理每个通道：R, G, B, A
        bands = {}
        for channel_name in ['R', 'G', 'B', 'A']:
            source = getattr(self, channel_name)

            if isinstance(source, (float, int)):  # 浮点常数
                # 创建纯色通道图像（值为0-255的整数）
                value = max(0, min(255, int(source * 255)))
                band = PIL.Image.new('L', self.resize, value)
                bands[channel_name] = band

            elif isinstance(source, Channel):  # Channel对象
                texture_img = source.texture.pil_pic

                # 转换为RGBA确保有四个通道
                if texture_img.mode != 'RGBA':
                    texture_img = texture_img.convert('RGBA')

                # 分离RGBA通道
                r_band, g_band, b_band, a_band = texture_img.split()
                all_bands = {'R': r_band, 'G': g_band, 'B': b_band, 'A': a_band}

                # 选择所需通道并调整尺寸
                selected = all_bands.get(
                    ['R', 'G', 'B', 'A'][source.channelID],
                    PIL.Image.new('L', texture_img.size, 255)  # 默认全白（1.0）
                )
                bands[channel_name] = selected.resize(self.resize, PIL.Image.BILINEAR)

        # 合并所有通道（缺失通道用灰色占位）
        final_bands = []
        for ch in ['R', 'G', 'B', 'A']:
            final_bands.append(bands.get(ch, PIL.Image.new('L', self.resize, 128)))

        # 合并为最终RGBA图像
        self.pil_pic = PIL.Image.merge('RGBA', final_bands)


class FPL:
    def __init__(self,
                 base_color: Texture | MixChannel,
                 emission: float | int = 0.0):
        """
        Fixed pipeline固定管线式着色器
        :param base_color: 主要颜色
        :param emission:   自发光度
        """
        if not isinstance(base_color, Texture | MixChannel):
            raise TypeError(f"base_color should be Texture | MixChannel not {type(base_color)}")

        if not isinstance(emission, float | int):
            raise TypeError(f"emission should be float | int not {type(emission)}")

        self.base_color = base_color
        self.emission = emission

        self.base_color_id = None

        self.hash = None
        self.update()

    def rend(self, mode, vertex):
        # 材质贴图
        texture_id = self.base_color_id

        # 启用必要的OpenGL功能
        glEnable(GL_DEPTH_TEST)

        # 设置材质属性
        glColor4f(1.0, 1.0, 1.0, 1.0)

        # 开启纹理
        if texture_id:
            glEnable(GL_TEXTURE_2D)

        # 激活并绑定材质贴图（纹理单元0）
        if texture_id:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, texture_id)
            glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

        # 自发光处理
        if self.emission != 0.0:
            emission = max(0.0, min(1.0, float(self.emission)))
            glMaterialfv(GL_FRONT, GL_EMISSION, (emission, emission, emission, 1.0))

        # 绘制几何图形
        glBegin(mode)
        # 3. 计算平面法线方向
        if len(vertex) >= 3:
            v0 = vertex[0]
            v1 = vertex[1]
            v2 = vertex[2]

            # 计算两个向量
            u = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            v = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

            # 叉乘得到法线
            normal = (
                u[1] * v[2] - u[2] * v[1],
                u[2] * v[0] - u[0] * v[2],
                u[0] * v[1] - u[1] * v[0]
            )
        else:
            normal = (0, 0, 1)  # 默认Z轴正向
        glNormal3f(normal[0], normal[1], normal[2])
        for v in vertex:
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

        if self.emission != 0.0:
            glMaterialfv(GL_FRONT, GL_EMISSION, (0.0, 0.0, 0.0, 1.0))

    def update(self) -> None:
        # 处理基础色材质
        pil_img = self.base_color.pil_pic
        self.base_color_id = _pil_to_texture(pil_img, texture_unit=0)


type_group = Texture | Channel | MixChannel | FPL


class ShaderProgram:
    def __init__(self, vertex: str, fragment: str):
        """
        着色程序
        :param vertex:   顶点着色程序
        :param fragment: 片段着色程序
        """
        self.vertex = vertex
        self.fragment = fragment

        self.vertex_shader = compileShader(self.vertex, GL_VERTEX_SHADER)
        self.fragment_shader = compileShader(self.fragment, GL_FRAGMENT_SHADER)


def _pil_to_texture(pil_img: PIL.Image.Image, texture_id: int | None = None, texture_unit: int = 0) -> int:
    """
    将PIL图像转换为OpenGL纹理
    :param pil_img: PIL图像对象
    :param texture_id: 已有纹理ID（如None则创建新纹理）
    :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）
    :return: 纹理ID
    """
    # 激活指定纹理单元
    glActiveTexture(GL_TEXTURE0 + texture_unit)

    # 确定图像模式并转换为RGBA格式
    mode = pil_img.mode
    if mode == '1':  # 黑白图像
        pil_img = pil_img.convert('RGBA')
        data = pil_img.tobytes('raw', 'RGBA', 0, -1)
    elif mode == 'L':  # 灰度图像
        pil_img = pil_img.convert('RGBA')
        data = pil_img.tobytes('raw', 'RGBA', 0, -1)
    elif mode == 'RGB':  # RGB图像
        pil_img = pil_img.convert('RGBA')
        data = pil_img.tobytes('raw', 'RGBA', 0, -1)
    elif mode == 'RGBA':  # RGBA图像
        data = pil_img.tobytes('raw', 'RGBA', 0, -1)
    else:
        # 其他格式转换为RGBA
        pil_img = pil_img.convert('RGBA')
        data = pil_img.tobytes('raw', 'RGBA', 0, -1)

    # 获取图像尺寸
    width, height = pil_img.size

    # 创建或绑定纹理
    if texture_id is None:
        texture_id = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texture_id)

    # 设置纹理参数
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

    # 上传纹理数据
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

    # 生成mipmap（提高纹理在远距离的渲染质量）
    glGenerateMipmap(GL_TEXTURE_2D)

    return texture_id


if __name__ == '__main__':
    ...
