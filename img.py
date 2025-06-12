"""
调用：soup3D
用于管理材质贴图
"""
from OpenGL.GL import *
import numpy
from PIL import Image


class Texture:
    def __init__(self, img, width, height, img_type="rgb", wrap_x="edge", wrap_y="edge", linear=False):
        """
        (该类已不再支持，为兼容老程序而保留，建议改用soup3D.shader.Texture类)
        材质纹理贴图，当图形需要贴图时，在Shape的texture
        赋值该类型

        :param img:      贴图的二进制数据
        :param width:    贴图的宽度（像素）
        :param height:   贴图的高度（像素）
        :param img_type: 图像模式，可为"rgb"或"rgba"
        :param wrap_x:   x轴环绕方式，当取色坐标超出图片范
                         围时的取色方案，可为：
                         "repeat" -> 重复图像
                         "mirrored" -> 镜像图像
                         "edge" -> 延生边缘像素
                         "border" -> 纯色图像
        :param wrap_y:   y轴环绕方式（参数同wrap_x）
        :param linear:   是否使用抗锯齿，True使用
                         GL_LINEAR插值，False使用
                         GL_NEAREST
        """
        ...


def pil_to_texture(pil_img: Image.Image, texture_id: int | None = None, texture_unit: int = 0) -> int:
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


type_group = Texture
