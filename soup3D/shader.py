"""
处理soup3D中的着色系统
"""
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import numpy as np
from pyglm import glm
import math
import inspect
import weakref
import traceback
import sys
import imageio.v2 as imageio

import soup3D.name
import soup3D.skeleton
import soup3D.target


set_mat_queue = weakref.WeakValueDictionary()

light_queue = {}


# uniform 上传函数走 PyOpenGL raw 层（ctypes 直调 + argtypes，无包装层
# 的每调用 Python 对象分配——包装层 _cast/转换器是 GC 升代大户，见
# gc-stutter 诊断；raw 层语义一致，仅无 glGetError 检查，引擎已有独立检查）
from OpenGL.raw.GL.VERSION.GL_2_0 import (
    glUniform1f as _glUniform1f, glUniform2f as _glUniform2f,
    glUniform3f as _glUniform3f, glUniform4f as _glUniform4f,
    glUniform1i as _glUniform1i, glUniform2i as _glUniform2i,
    glUniform3i as _glUniform3i, glUniform4i as _glUniform4i,
    glUniform1fv as _glUniform1fv, glUniform2fv as _glUniform2fv,
    glUniform3fv as _glUniform3fv, glUniform4fv as _glUniform4fv,
    glUniform1iv as _glUniform1iv, glUniform2iv as _glUniform2iv,
    glUniform3iv as _glUniform3iv, glUniform4iv as _glUniform4iv,
    glUniformMatrix2fv as _glUniformMatrix2fv,
    glUniformMatrix3fv as _glUniformMatrix3fv,
    glUniformMatrix4fv as _glUniformMatrix4fv,
)

type_map = {
    soup3D.name.FLOAT_VEC1: _glUniform1f,
    soup3D.name.FLOAT_VEC2: _glUniform2f,
    soup3D.name.FLOAT_VEC3: _glUniform3f,
    soup3D.name.FLOAT_VEC4: _glUniform4f,
    soup3D.name.INT_VEC1: _glUniform1i,
    soup3D.name.INT_VEC2: _glUniform2i,
    soup3D.name.INT_VEC3: _glUniform3i,
    soup3D.name.INT_VEC4: _glUniform4i,
    soup3D.name.ARRAY_FLOAT_VEC1: _glUniform1fv,
    soup3D.name.ARRAY_FLOAT_VEC2: _glUniform2fv,
    soup3D.name.ARRAY_FLOAT_VEC3: _glUniform3fv,
    soup3D.name.ARRAY_FLOAT_VEC4: _glUniform4fv,
    soup3D.name.ARRAY_INT_VEC1: _glUniform1iv,
    soup3D.name.ARRAY_INT_VEC2: _glUniform2iv,
    soup3D.name.ARRAY_INT_VEC3: _glUniform3iv,
    soup3D.name.ARRAY_INT_VEC4: _glUniform4iv,
    soup3D.name.ARRAY_MATRIX_VEC2: _glUniformMatrix2fv,
    soup3D.name.ARRAY_MATRIX_VEC3: _glUniformMatrix3fv,
    soup3D.name.ARRAY_MATRIX_VEC4: _glUniformMatrix4fv,

    soup3D.name.BYTE: GL_BYTE,
    soup3D.name.BYTE_US: GL_UNSIGNED_BYTE,
    soup3D.name.SHORT: GL_SHORT,
    soup3D.name.SHORT_US: GL_UNSIGNED_SHORT,
    soup3D.name.INT: GL_INT,
    soup3D.name.INT_US: GL_UNSIGNED_INT,
    soup3D.name.FLOAT_H: GL_HALF_FLOAT,
    soup3D.name.FLOAT: GL_FLOAT,
    soup3D.name.FLOAT_D: GL_DOUBLE,
    soup3D.name.FIXED: GL_FIXED
}

# 整型 GL 类型 → numpy dtype 映射（整型属性指针路径 glVertexAttribIPointer 使用）。
# rend_cached 共享本表；rend 保持其函数内局部映射不动（上游代码原样）
_INT_TYPE_MAP = {
    GL_BYTE: np.int8, GL_UNSIGNED_BYTE: np.uint8,
    GL_SHORT: np.int16, GL_UNSIGNED_SHORT: np.uint16,
    GL_INT: np.int32, GL_UNSIGNED_INT: np.uint32,
}

# rend_cached 单个 surface 实例的缓存槽上限。正常静态场景每 surface 的不同顶点
# 列表数 = 共享它的 Face 数，远小于该值；超出则 FIFO 淘汰最旧槽（被淘汰的顶点
# 列表下次调用时重建缓冲，性能退化但结果正确），防止逐帧换新列表的调用方式
# 让缓存无限增长
_REND_CACHE_MAX_SLOTS = 256


class Texture:
    def __init__(self, image_data: bytes | str, width: int = None, height: int = None, format: str = 'RGBA'):
        """
        贴图，直接使用二进制图像数据或文件路径
        提取通道时：
        通道 0: 红色通道
        通道 1: 绿色通道
        通道 2: 蓝色通道
        通道 3: 透明度 (如无该通道，则统一返回 1)
        :param image_data: 二进制图像数据或文件路径字符串
        :param width: 图像宽度（当 image_data 为二进制数据时需要提供）
        :param height: 图像高度（当 image_data 为二进制数据时需要提供）
        :param format: 图像格式，可以是 'RGBA', 'RGB', 'L' (灰度) 等
        """
        if not isinstance(image_data, (str, bytes)):
            raise TypeError("image_data must be a string path or bytes")
        if width is not None and not isinstance(width, int):
            raise TypeError("width must be an int or None")
        if height is not None and not isinstance(height, int):
            raise TypeError("height must be an int or None")
        if not isinstance(format, str):
            raise TypeError("format must be a string")

        self.width = width
        self.height = height
        self.format = format
        self.texture_id = None
        
        # 如果传入的是文件路径，读取文件
        if isinstance(image_data, str):
            self.image_path = image_data
            self.image_data = None  # 延迟加载
        else:
            self.image_path = None
            self.image_data = image_data
            if width is None or height is None:
                raise ValueError("When providing binary data, width and height must be specified")
            # 数据长度与格式不符会使 glTexImage2D 越界读取，必须快速失败
            bytes_per_pixel = {"RGBA": 4, "RGB": 3, "L": 1, "A": 1}
            if self.format in bytes_per_pixel:
                expected = width * height * bytes_per_pixel[self.format]
                if len(image_data) != expected:
                    raise ValueError(
                        "image_data length " + str(len(image_data))
                        + " does not match format " + self.format
                        + " at " + str(width) + "x" + str(height)
                        + " (expected " + str(expected) + ")"
                    )

    def gen_gl_texture(self, texture_unit: int = 0):
        """
        生成 OpenGL 纹理
        :param texture_unit: 纹理单元编号（0 表示 GL_TEXTURE0，1 表示 GL_TEXTURE1 等）
        :return: None
        """
        if not isinstance(texture_unit, int):
            raise TypeError("texture_unit must be an int")
        # 已创建过纹理则仅重新绑定到目标单元（uniform_tex 每次注册都会调用本方法，重复创建会泄漏并使旧 id 失效）
        if self.texture_id is not None:
            glActiveTexture(GL_TEXTURE0 + texture_unit)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            return self.texture_id


        # 激活指定纹理单元
        glActiveTexture(GL_TEXTURE0 + texture_unit)

        # 加载图像数据（如果还未加载）
        if self.image_path and self.image_data is None:
            self._load_image()

        # 确定图像模式和对应的 OpenGL 格式
        format_map = {
            'RGBA': (GL_RGBA, GL_RGBA),
            'RGB': (GL_RGB, GL_RGB),
            'L': (GL_RED, GL_RED),  # 灰度图使用 RED 通道
            'A': (GL_ALPHA, GL_ALPHA)
        }
        
        internal_format, data_format = format_map.get(self.format, (GL_RGBA, GL_RGBA))
        
        # 获取图像尺寸
        width, height = self.width, self.height

        # 创建或绑定纹理
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # 设置纹理参数
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

        # 上传纹理数据
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, data_format, GL_UNSIGNED_BYTE, self.image_data)

        # 生成 mipmap（提高纹理在远距离的渲染质量）
        glGenerateMipmap(GL_TEXTURE_2D)

        self.texture_id = texture_id
        return texture_id
    
    @classmethod
    def from_array(cls, arr, color=None):
        """
        从 numpy 数组创建数据纹理，立即创建 GL 纹理对象（需 GL 上下文就绪，如 soup3D.init() 之后调用）
        数组第 0 行为图像顶行（上传前内部垂直翻转，与 to_pixels/present 的顶原点一致）
        :param arr: (h, w, 4)/(h, w, 3)/(h, w) 的 uint8 或 float32 数组
        :param color: 内部格式。None 时按 dtype/shape 推断：uint8 → rgba8/rgb8/l8，float32 → rgba32f/rgb32f/r32f；
                      显式指定可覆盖，如浮点数据指定 rgba16f。格式须与通道数匹配：rgba*=4 通道、rgb*=3 通道、l8/r32f=1 通道
        :return: Texture 实例
        """
        if not isinstance(arr, np.ndarray):
            raise TypeError("arr must be a numpy array")
        if color is not None and not isinstance(color, str):
            raise TypeError("color must be a string or None")
        if arr.ndim not in (2, 3):
            raise ValueError("arr must be 2D (h, w) or 3D (h, w, 3 or 4 channels)")
        channels = 1 if arr.ndim == 2 else arr.shape[2]
        if channels not in (1, 3, 4):
            raise ValueError("arr must have 1, 3 or 4 channels")
        if arr.dtype == np.uint8:
            suffix = "8"
        elif arr.dtype == np.float32:
            suffix = "32f"
        else:
            raise ValueError("arr.dtype must be uint8 or float32; float64 must be cast to float32 first")
        if color is None:
            if channels == 4:
                color = "rgba" + suffix
            elif channels == 3:
                color = "rgb" + suffix
            else:
                color = ("l" if suffix == "8" else "r") + suffix
        else:
            if color.startswith("rgba"):
                need = 4
            elif color.startswith("rgb"):
                need = 3
            else:
                need = 1
            if need != channels:
                raise ValueError("color=" + color + " needs " + str(need) + " channels but arr has " + str(channels))
        u8 = GL_UNSIGNED_BYTE
        fmt_map = {
            "rgba8": (GL_RGBA8, GL_RGBA, u8),
            "rgb8": (GL_RGB8, GL_RGB, u8),
            "l8": (GL_R8, GL_RED, u8),
            "rgba16f": (GL_RGBA16F, GL_RGBA, GL_FLOAT),
            "rgba32f": (GL_RGBA32F, GL_RGBA, GL_FLOAT),
            "rgb32f": (GL_RGB32F, GL_RGB, GL_FLOAT),
            "r32f": (GL_R32F, GL_RED, GL_FLOAT),
        }
        if color not in fmt_map:
            raise ValueError("color must be one of: " + ", ".join(sorted(fmt_map)) + " (got " + str(color) + ")")
        internal_format, data_format, gl_type = fmt_map[color]
        arr_c = np.ascontiguousarray(arr)
        # GL 上传以底行为第 0 行：上传前垂直翻转，使「第 0 行 = 顶行」语义成立
        arr_c = np.ascontiguousarray(arr_c[::-1])
        tex = cls.__new__(cls)
        tex.width = int(arr_c.shape[1])
        tex.height = int(arr_c.shape[0])
        tex.format = color
        tex.texture_id = glGenTextures(1)
        prev_align = glGetIntegerv(GL_UNPACK_ALIGNMENT)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, tex.texture_id)
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, tex.width, tex.height, 0, data_format, gl_type, arr_c)
        glPixelStorei(GL_UNPACK_ALIGNMENT, int(prev_align))
        # 数据纹理采样参数：NEAREST + CLAMP_TO_EDGE，无 mipmap（数据纹理不做插值与越界重复）
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        return tex
    def _load_image(self):
        """
        从文件路径加载图像数据
        这里需要根据实际情况实现图像加载逻辑
        如果需要支持多种格式，可以集成 stb_image 或其他轻量级图像加载库
        """
        if not self.image_path:
            return

        img = imageio.imread(self.image_path)
        self.height, self.width = img.shape[:2]

        if len(img.shape) == 2:  # 灰度图
            self.format = 'L'
            self.image_data = img.tobytes()
        elif img.shape[2] == 3:  # RGB
            self.format = 'RGB'
            self.image_data = img.tobytes()
        elif img.shape[2] == 4:  # RGBA
            self.format = 'RGBA'
            self.image_data = img.tobytes()

    def get_texture_id(self):
        """
        获取纹理 id，若无纹理 id，则创建纹理 id。
        :return: 纹理 id
        """
        if self.texture_id is None:
            self.gen_gl_texture()
        return self.texture_id

    def __del__(self):
        # GL 上下文可能在对象销毁前已释放（解释器关闭期），删除失败时静默
        try:
            if self.texture_id is not None:
                glDeleteTextures([self.texture_id])
            self.texture_id = None
        except Exception:
            pass


class Channel:
    def __init__(self, texture: "Img", channelID: int):
        """
        提取贴图中的单个通道
        :param texture:   提取通道的贴图
        :param channelID: 通道编号
        """
        if not isinstance(texture, (Texture, MixChannel)):
            raise TypeError("texture must be a Texture or MixChannel instance")
        if not isinstance(channelID, int):
            raise TypeError("channelID must be an int")

        self.texture = texture
        self.channelID = channelID


class MixChannel:
    def __init__(self,
                 resize: tuple[int, int],
                 R: "int | float | GrayImg",
                 G: "int | float | GrayImg",
                 B: "int | float | GrayImg",
                 A: "int | float | GrayImg" = 1.0):
        """
        混合通道成为一个贴图
        混合通道贴图 (MixChannel) 可通过类似贴图 (Texture) 的方式提取通道
        :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像
        :param R: 红色通道，可直接通过 0.0~1.0 的小数定义通道亮度，也可以引入 Channel 通道实现引入贴图通道
        :param G: 绿色通道，可直接通过 0.0~1.0 的小数定义通道亮度，也可以引入 Channel 通道实现引入贴图通道
        :param B: 蓝色通道，可直接通过 0.0~1.0 的小数定义通道亮度，也可以引入 Channel 通道实现引入贴图通道
        :param A: 透明度通道，可直接通过 0.0~1.0 的小数定义通道亮度，也可以引入 Channel 通道实现引入贴图通道
        """
        if not isinstance(resize, (list, tuple)) or len(resize) != 2:
            raise TypeError("resize must be a list or tuple of 2 integers")
        for r in resize:
            if not isinstance(r, int):
                raise TypeError("resize elements must be int")
        if not isinstance(R, (int, float, Channel)):
            raise TypeError("R must be an int, float, or Channel instance")
        if not isinstance(G, (int, float, Channel)):
            raise TypeError("G must be an int, float, or Channel instance")
        if not isinstance(B, (int, float, Channel)):
            raise TypeError("B must be an int, float, or Channel instance")
        if not isinstance(A, (int, float, Channel)):
            raise TypeError("A must be an int, float, or Channel instance")

        self.resize = resize
        self.R = R
        self.G = G
        self.B = B
        self.A = A
        self.texture_id = None

    def gen_gl_texture(self, texture_unit: int = 0):
        """
        生成 OpenGL 纹理
        :param texture_unit: 纹理单元编号（0 表示 GL_TEXTURE0，1 表示 GL_TEXTURE1 等）
        :return: None
        """
        if not isinstance(texture_unit, int):
            raise TypeError("texture_unit must be an int")

        # 激活指定纹理单元
        glActiveTexture(GL_TEXTURE0 + texture_unit)

        # 生成混合通道的二进制数据
        width, height = self.resize
        total_pixels = width * height
        
        # 初始化四个通道的数组
        r_data = np.zeros(total_pixels, dtype=np.uint8)
        g_data = np.zeros(total_pixels, dtype=np.uint8)
        b_data = np.zeros(total_pixels, dtype=np.uint8)
        a_data = np.full(total_pixels, 255, dtype=np.uint8)  # 默认不透明
        
        # 处理每个通道
        for i, (channel_name, source) in enumerate([('R', self.R), ('G', self.G), 
                                                      ('B', self.B), ('A', self.A)]):
            if isinstance(source, (float, int)):  # 浮点常数
                value = max(0, min(255, int(source * 255)))
                if channel_name == 'R':
                    r_data.fill(value)
                elif channel_name == 'G':
                    g_data.fill(value)
                elif channel_name == 'B':
                    b_data.fill(value)
                elif channel_name == 'A':
                    a_data.fill(value)
                    
            elif isinstance(source, Channel):  # Channel 对象
                # 从源纹理获取数据
                src_texture = source.texture
                if src_texture.image_path and src_texture.image_data is None:
                    src_texture._load_image()
                
                src_width = src_texture.width
                src_height = src_texture.height
                src_format = src_texture.format
                src_data = src_texture.image_data
                
                # 根据源格式解析数据
                if src_format == 'RGBA':
                    channels_per_pixel = 4
                elif src_format == 'RGB':
                    channels_per_pixel = 3
                elif src_format == 'L':
                    channels_per_pixel = 1
                else:
                    channels_per_pixel = 4
                
                # 提取指定通道
                src_channel_idx = source.channelID
                if src_channel_idx < channels_per_pixel:
                    channel_bytes = src_data[src_channel_idx::channels_per_pixel]
                    channel_array = np.frombuffer(channel_bytes, dtype=np.uint8)
                else:
                    channel_array = np.full(src_width * src_height, 255, dtype=np.uint8)
                
                # 调整尺寸（简单的最近邻插值）
                if (src_width, src_height) != self.resize:
                    channel_array = self._resize_channel(channel_array, 
                                                         (src_width, src_height), 
                                                         self.resize)
                
                # 填充到对应通道
                if channel_name == 'R':
                    r_data[:len(channel_array)] = channel_array
                elif channel_name == 'G':
                    g_data[:len(channel_array)] = channel_array
                elif channel_name == 'B':
                    b_data[:len(channel_array)] = channel_array
                elif channel_name == 'A':
                    a_data[:len(channel_array)] = channel_array
        
        # 合并为 RGBA 数据
        rgba_data = np.zeros((total_pixels, 4), dtype=np.uint8)
        rgba_data[:, 0] = r_data
        rgba_data[:, 1] = g_data
        rgba_data[:, 2] = b_data
        rgba_data[:, 3] = a_data
        
        data = rgba_data.tobytes()

        # 创建或绑定纹理
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)

        # 设置纹理参数
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)

        # 上传纹理数据
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)

        # 生成 mipmap
        glGenerateMipmap(GL_TEXTURE_2D)

        self.texture_id = texture_id
        return texture_id
    
    def _resize_channel(self, channel_array: np.ndarray, 
                        src_size: tuple[int, int], 
                        dst_size: tuple[int, int]) -> np.ndarray:
        """
        调整通道尺寸（最近邻插值）
        :param channel_array: 一维通道数组
        :param src_size: 原始尺寸 (width, height)
        :param dst_size: 目标尺寸 (width, height)
        :return: 调整后的通道数组
        """
        src_w, src_h = src_size
        dst_w, dst_h = dst_size
        
        # 重塑为 2D
        channel_2d = channel_array.reshape((src_h, src_w))
        
        # 创建目标数组
        result = np.zeros((dst_h, dst_w), dtype=np.uint8)
        
        # 计算缩放比例
        scale_x = src_w / dst_w
        scale_y = src_h / dst_h
        
        # 最近邻插值
        for y in range(dst_h):
            for x in range(dst_w):
                src_x = int(min(x * scale_x, src_w - 1))
                src_y = int(min(y * scale_y, src_h - 1))
                result[y, x] = channel_2d[src_y, src_x]
        
        return result.flatten()

    def get_texture_id(self):
        """
        获取纹理 id，若无纹理 id，则创建纹理 id。
        :return: 纹理 id
        """
        if self.texture_id is None:
            self.gen_gl_texture()
        return self.texture_id

    def __del__(self):
        # GL 上下文可能在对象销毁前已释放（解释器关闭期），删除失败时静默
        try:
            if self.texture_id is not None:
                glDeleteTextures([self.texture_id])
            self.texture_id = None
        except Exception:
            pass


class UniformBuffer:
    def __init__(self, size: int, usage: int = GL_DYNAMIC_DRAW):
        """
        Uniform Buffer Object，用于高效上传大量uniform数据
        
        :param size: UBO大小（字节）
        :param usage: 数据使用模式，可选：GL_STATIC_DRAW, GL_DYNAMIC_DRAW, GL_STREAM_DRAW
        """
        self.size = size
        self.usage = usage
        self.buffer_id = glGenBuffers(1)
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer_id)
        glBufferData(GL_UNIFORM_BUFFER, size, None, usage)
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    def bind(self, target: int = GL_UNIFORM_BUFFER) -> None:
        """
        绑定UBO到指定目标
        
        :param target: OpenGL绑定目标，默认GL_UNIFORM_BUFFER
        """
        glBindBuffer(target, self.buffer_id)

    def unbind(self, target: int = GL_UNIFORM_BUFFER) -> None:
        """
        解绑UBO
        
        :param target: OpenGL绑定目标，默认GL_UNIFORM_BUFFER
        """
        glBindBuffer(target, 0)

    def bind_base(self, binding_point: int) -> None:
        """
        将UBO绑定到指定绑定点
        
        :param binding_point: UBO绑定点编号（0-7或更高，取决于OpenGL实现）
        """
        glBindBufferBase(GL_UNIFORM_BUFFER, binding_point, self.buffer_id)

    def update(self, data: bytes | np.ndarray, offset: int = 0, size: int | None = None) -> None:
        """
        使用glBufferSubData更新UBO数据
        
        :param data: 要上传的数据，可以是bytes或numpy数组
        :param offset: 数据偏移量（字节）
        :param size: 数据大小（字节），为None时使用data的完整大小
        """
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer_id)
        
        if isinstance(data, np.ndarray):
            upload_data = data.tobytes()
        else:
            upload_data = data
        
        upload_size = size if size is not None else len(upload_data)
        glBufferSubData(GL_UNIFORM_BUFFER, offset, upload_size, upload_data)
        
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

    def __del__(self):
        """清理UBO资源"""
        if self.buffer_id is not None:
            glDeleteBuffers(1, [self.buffer_id])
            self.buffer_id = None


class ShaderProgram:
    def __init__(
            self, vertex: str, fragment: str,
            vbo_type: str | list[str] | tuple[str] = "float",
            depth_test: bool = True
        ):
        """
        代码着色器，作为表面着色器渲染时使用的顶点列表格式：
        [
            [  # vbo0
                (),  # vertex0
                (),  # vertex1
                (),  # vertex2
            ],
            [  # vbo1
                (),  # vertex0
                (),  # vertex1
                (),  # vertex2
            ]
            ...
        ]
        在着色器代码中，vbo的读取编号取决于vbo处于列表的位置，例如列表中第0个，也就是首个vbo，着色器代码中可以通过
        "layout (location = 0) in <type> <value_name>"这段代码读取。
        :param vertex:   顶点着色程序代码
        :param fragment: 片段着色程序代码
        :param vbo_type: 定义传入着色器程序的顶点列表(vbo)的数据类型。如每个定点列表数据类型相同，可通过填写一个字符串定义所有的定点列表的
                         数据类型；如果需要不同的数据类型，可通过填写一个列表来分别定义每个顶点列表的数据类型。在同一vbo下，所有vertex的
                         长度需一致，且长度范围在1-4个数据。
        """
        if not isinstance(vertex, str):
            raise TypeError("vertex must be a string")
        if not isinstance(fragment, str):
            raise TypeError("fragment must be a string")
        if not isinstance(vbo_type, (str, list, tuple)):
            raise TypeError("vbo_type must be a string, list, or tuple")
        if isinstance(vbo_type, (list, tuple)):
            for t in vbo_type:
                if not isinstance(t, str):
                    raise TypeError("vbo_type elements must be strings")

        if not isinstance(depth_test, bool):
            raise TypeError("depth_test must be a bool")
        self.depth_test = depth_test

        self.vertex = vertex
        self.fragment = fragment
        self.vbo_type = vbo_type

        self.vertex_shader = compileShader(self.vertex, GL_VERTEX_SHADER)
        self.fragment_shader = compileShader(self.fragment, GL_FRAGMENT_SHADER)

        self.shader = compileProgram(self.vertex_shader, self.fragment_shader)

        self.uniform_loc = {}
        self.uniform_val = {}
        self.uniform_type = {}
        # uniform 位置持久缓存。uniform_loc 会被 update() 末尾清空（它只是待上传队列），
        # 而 location 与着色器程序一一对应，必须单独缓存，避免每帧重复执行字符串查询
        self.uniform_loc_cache = {}

        self.texture_val = {}

        # 缓存式渲染（rend_cached）的多槽缓冲缓存：按传入顶点列表对象的 id 分槽，
        # 值为 (顶点列表, vao, vbo_ids, 顶点数)；缓存强引用保活顶点列表，使 id 不可能
        # 被回收复用，命中时以 is 校验对象同一性。槽位上限 _REND_CACHE_MAX_SLOTS，
        # 满则 FIFO 淘汰（GL 资源一并删除）。生命周期与实例对齐（__del__ 中随程序资源一并删除）
        self._rend_cache = {}

        self.dirty = False

    def use(self):
        """
        使用该着色器，会在应用时自动调用
        :return: None
        """
        glUseProgram(self.shader)

    def rend(self, mode, vertex):
        """
        创建该着色器的渲染流程
        :param mode:   绘制方式
        :param vertex: 表面中所有的顶点
        :return: None
        """
        if isinstance(self.vbo_type, str):
            types = [type_map[self.vbo_type] for i in vertex]
        else:
            if len(self.vbo_type) != len(vertex):
                raise TypeError(f"this ShaderProgram need {len(self.vbo_type)} vbo but {len(vertex)} were given")
            types = [type_map[i] for i in self.vbo_type]

        for i in self.texture_val:
            value = self.texture_val[i]
            texture, texture_unit = value
            glActiveTexture(GL_TEXTURE0 + texture_unit)
            glBindTexture(GL_TEXTURE_2D, texture.get_texture_id())

        if self.depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        num_buffers = len(vertex)
        vbo_ids = glGenBuffers(num_buffers)

        if num_buffers == 1:
            vbo_ids = [vbo_ids]  # 包装为列表

        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        _int_type_map = {
            GL_BYTE: np.int8, GL_UNSIGNED_BYTE: np.uint8,
            GL_SHORT: np.int16, GL_UNSIGNED_SHORT: np.uint16,
            GL_INT: np.int32, GL_UNSIGNED_INT: np.uint32,
        }

        for i, vert_group in enumerate(vertex):
            if not vert_group:  # 空顶点组跳过
                continue

            gl_type = types[i]
            if gl_type in _int_type_map:
                vbo_np = np.array(vert_group, dtype=_int_type_map[gl_type])
            else:
                vbo_np = np.array(vert_group, dtype=np.float32)

            glBindBuffer(GL_ARRAY_BUFFER, vbo_ids[i])
            glBufferData(GL_ARRAY_BUFFER, vbo_np.nbytes, vbo_np, GL_STATIC_DRAW)

            # 计算每个顶点的元素个数
            components = len(vert_group[0])
            if gl_type in _int_type_map:
                glVertexAttribIPointer(i, components, gl_type, 0, ctypes.c_void_p(0))
            else:
                glVertexAttribPointer(i, components, gl_type, GL_FALSE, 0, ctypes.c_void_p(0))
            glEnableVertexAttribArray(i)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(vao)

        # 使用第一个顶点组的长度作为顶点数量
        if vertex and vertex[0]:
            total_vertices = len(vertex[0])
        else:
            total_vertices = 0

        glDrawArrays(mode, 0, total_vertices)

        # 清理资源
        glBindVertexArray(0)
        glDeleteVertexArrays(1, [vao])
        glDeleteBuffers(num_buffers, vbo_ids)

    def rend_cached(self, mode, vertex):
        """
        缓存式渲染：与 rend(mode, vertex) 入参语义一致，但首次调用创建的 VAO/VBO
        缓存在自身，后续调用直接绑定缓存 VAO 绘制，不重复创建/上传/删除缓冲。

        设计说明：静态模型逐帧渲染的缓冲复用。rend() 每帧「新建 VAO/VBO → 上传 →
        绘制 → 删除」，对顶点数据不变的静态场景（如地图模型）是纯浪费；本方法将
        缓冲生命周期与着色器程序对齐，仅首次付出创建与上传成本，消除逐帧的
        缓冲创建/删除churn，绘制时顶点装配状态由 VAO 直接恢复。

        契约：顶点数据视为静态——同一顶点列表对象后续调用传入的数据须保持不变，
        本方法不再重新上传（仅首次数据生效）。支持同一实例的多个不同静态顶点列表
        （如多个 Face 共享 surface）：按顶点列表对象 id 分槽缓存，上限
        _REND_CACHE_MAX_SLOTS 槽，满则 FIFO 淘汰最旧槽（其 GL 资源一并删除；
        被淘汰的顶点列表下次调用时重建，性能退化但结果正确）。缓存的 VAO/VBO
        随实例被垃圾回收，在 __del__ 中随程序资源一并删除，无需显式清理。

        :param mode:   绘制方式
        :param vertex: 表面中所有的顶点
        :return: None
        """
        if isinstance(self.vbo_type, str):
            types = [type_map[self.vbo_type] for i in vertex]
        else:
            if len(self.vbo_type) != len(vertex):
                raise TypeError(f"this ShaderProgram need {len(self.vbo_type)} vbo but {len(vertex)} were given")
            types = [type_map[i] for i in self.vbo_type]

        for i in self.texture_val:
            value = self.texture_val[i]
            texture, texture_unit = value
            glActiveTexture(GL_TEXTURE0 + texture_unit)
            glBindTexture(GL_TEXTURE_2D, texture.get_texture_id())

        if self.depth_test:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

        # 按 id(顶点列表) 查缓存；命中时校验缓存保活的顶点列表与入参为同一对象
        cache_key = id(vertex)
        entry = self._rend_cache.get(cache_key)
        if entry is not None and entry[0] is not vertex:
            # id 槽被其他对象占用：删除旧槽资源并视为未命中
            self._drop_rend_cache_slot(cache_key)
            entry = None

        if entry is None:
            # 未命中：创建 VAO/VBO 并上传顶点数据；属性指针绑定记录进 VAO 状态，
            # 之后逐帧只需绑定该 VAO 即可恢复全部顶点装配状态
            num_buffers = len(vertex)
            vbo_ids = glGenBuffers(num_buffers)

            if num_buffers == 1:
                vbo_ids = [vbo_ids]  # 包装为列表

            vao = glGenVertexArrays(1)
            glBindVertexArray(vao)

            for i, vert_group in enumerate(vertex):
                if not vert_group:  # 空顶点组跳过
                    continue

                gl_type = types[i]
                if gl_type in _INT_TYPE_MAP:
                    vbo_np = np.array(vert_group, dtype=_INT_TYPE_MAP[gl_type])
                else:
                    vbo_np = np.array(vert_group, dtype=np.float32)

                glBindBuffer(GL_ARRAY_BUFFER, vbo_ids[i])
                glBufferData(GL_ARRAY_BUFFER, vbo_np.nbytes, vbo_np, GL_STATIC_DRAW)

                # 计算每个顶点的元素个数
                components = len(vert_group[0])
                if gl_type in _INT_TYPE_MAP:
                    glVertexAttribIPointer(i, components, gl_type, 0, ctypes.c_void_p(0))
                else:
                    glVertexAttribPointer(i, components, gl_type, GL_FALSE, 0, ctypes.c_void_p(0))
                glEnableVertexAttribArray(i)

            glBindBuffer(GL_ARRAY_BUFFER, 0)

            # 使用第一个顶点组的长度作为顶点数量（静态契约：数量随首帧数据固定）
            if vertex and vertex[0]:
                cache_count = len(vertex[0])
            else:
                cache_count = 0

            self._store_rend_cache_slot(cache_key, vertex, vao, vbo_ids, cache_count)
            draw_vao = vao
            draw_count = cache_count
        else:
            draw_vao = entry[1]
            draw_count = entry[3]

        glBindVertexArray(draw_vao)
        glDrawArrays(mode, 0, draw_count)
        glBindVertexArray(0)
        # 状态卫生：纹理绑定循环把活动纹理单元遗留在最后一个引擎纹理的单元上
        # （如 GL_TEXTURE3），不归位会令下游基于固定管线/默认单元的渲染方
        # （如 pyimgui 的字体绑定）落在错误单元上而整体不可见
        glActiveTexture(GL_TEXTURE0)

    def _drop_rend_cache_slot(self, key):
        """
        删除一个 rend_cached 缓存槽及其 VAO/VBO GL 资源
        :param key: 缓存键（id(顶点列表)）
        :return: None
        """
        entry = self._rend_cache.pop(key, None)
        if entry is None:
            return
        glDeleteVertexArrays(1, [entry[1]])
        glDeleteBuffers(len(entry[2]), entry[2])

    def _store_rend_cache_slot(self, key, vertex, vao, vbo_ids, count):
        """
        存入 rend_cached 缓存槽；槽满则 FIFO 淘汰最旧槽，其 GL 资源一并删除
        :param key:     缓存键（id(顶点列表)）
        :param vertex:  顶点列表（缓存强引用保活，防止 id 复用）
        :param vao:     新建的 VAO
        :param vbo_ids: 新建的 VBO id 列表
        :param count:   顶点数
        :return: None
        """
        if len(self._rend_cache) >= _REND_CACHE_MAX_SLOTS and key not in self._rend_cache:
            self._drop_rend_cache_slot(next(iter(self._rend_cache)))
        self._rend_cache[key] = (vertex, vao, vbo_ids, count)

    def unuse(self):
        """
        停用该着色器，会在结束应用时自动调用
        :return: None
        """
        glUseProgram(0)

    def uniform(self, v_name: str, v_type: str, *value) -> bool:
        """
        在下一帧向着色器传递数据
        :param v_name: 在着色器内该数据对应的变量名
        :param v_type: 指定数据类型
        :param value:  其他填入glUniform方法的参数，当传入值为单独数据时(如v_name=soup3D.INT_VEC1),需在此项填写传入的数据，如果需传
                       入数组(如v_name=soup3D.ARRAY_INT_VEC1)，则需要在此项填入(数组长度, 数组)，如果为矩阵，则需填入
                       (矩阵数量, 是否转置矩阵, 传入的矩阵)
        :return: 是否成功添加uniform
        """
        if not isinstance(v_name, str):
            raise TypeError("v_name must be a string")
        if not isinstance(v_type, str):
            raise TypeError("v_type must be a string")

        # 获取统一变量位置（优先读缓存，未命中才查询；-1 也缓存，避免重复查询不存在的变量）
        loc = self.uniform_loc_cache.get(v_name)
        if loc is None:
            loc = glGetUniformLocation(self.shader, v_name)
            self.uniform_loc_cache[v_name] = loc
        if loc == -1:
            return False
        self.uniform_loc[v_name] = loc
        self.uniform_val[v_name] = value
        self.uniform_type[v_name] = v_type

        self.dirty_update()
        return True

    def uniform_tex(self, v_name: str, texture: "Img", texture_unit: int = 0) -> bool:
        """
        在下一帧向着色器传递纹理
        :param v_name:       在着色器内该纹理对应的变量名
        :param texture:      贴图类（Texture / MixChannel / RenderTargetTexture，如 RenderTarget.color）
        :param texture_unit: 纹理单元编号
        :return: 是否成功添加文理
        """
        if not isinstance(v_name, str):
            raise TypeError("v_name must be a string")
        if not isinstance(texture, (Texture, MixChannel, soup3D.target.RenderTargetTexture)):
            raise TypeError("texture must be a Texture, MixChannel or RenderTargetTexture instance")
        if not isinstance(texture_unit, int):
            raise TypeError("texture_unit must be an int")

        # 获取统一变量位置（优先读缓存）
        prev_program = glGetIntegerv(GL_CURRENT_PROGRAM)
        loc = self.uniform_loc_cache.get(v_name)
        if loc is None:
            loc = glGetUniformLocation(self.shader, v_name)
            self.uniform_loc_cache[v_name] = loc
        if loc == -1:
            return False

        # 记录纹理信息
        self.uniform_loc[v_name] = loc
        self.texture_val[v_name] = (texture, texture_unit)
        self.uniform_type[v_name] = "texture"

        # 处理纹理类型的uniform
        texture.gen_gl_texture(texture_unit)

        self.dirty_update()

        return True

    def is_dirty(self):
        return self.dirty

    def dirty_update(self):
        """
        标记该着色器为需要更新
        :return: None
        """
        if not self.dirty:
            self.dirty = True

    def update(self):
        """
        更新着色器
        :return: None
        """
        prev_program = glGetIntegerv(GL_CURRENT_PROGRAM)
        if prev_program != self.shader:
            glUseProgram(self.shader)

        for key in self.uniform_loc:
            loc = self.uniform_loc.get(key, -1)
            if loc == -1:
                continue

            v_type = self.uniform_type[key]

            if v_type == "texture":
                value = self.texture_val[key]
                # 处理纹理类型的uniform
                texture, texture_unit = value
                glUniform1i(loc, texture_unit)
            else:
                value = self.uniform_val[key]
                # 处理其他类型的uniform
                if v_type in type_map:
                    type_map[v_type](loc, *value)

        # clear() 而非重建 dict：CPython dict clear 后保留 entry 表容量，
        # 同键重新插入不再分配（每帧 45 surface × 新 dict 是 GC 升代大户）
        self.uniform_loc.clear()
        self.dirty = False

    def has_uniform(self, v_name: str) -> bool:
        """
        查询着色器中是否存在指定 uniform（不存在返回 False）
        :param v_name: uniform 名称
        :return: bool，是否存在
        """
        return self.get_uniform_loc(v_name) != -1

    def get_uniform_loc(self, v_name: str) -> int:
        """
        查询 uniform 位置（location），不存在的 uniform 返回 -1
        :param v_name: uniform 名称
        :return: int，uniform 位置
        """
        # 优先读缓存（与 uniform() 的位置缓存同源），未命中才查询并写入缓存
        loc = self.uniform_loc_cache.get(v_name)
        if loc is None:
            loc = glGetUniformLocation(self.shader, v_name)
            self.uniform_loc_cache[v_name] = loc
        return int(loc)

    def __del__(self):
        """
        深度清理着色器，清理该着色器本身及所有该着色器用到的元素。在确定不再使用该着色器时可使用该方法释放内存。
        :return: None
        """
        # 删除顶点着色器
        if hasattr(self, 'vertex_shader') and self.vertex_shader:
            glDeleteShader(self.vertex_shader)
            self.vertex_shader = None

        # 删除片段着色器
        if hasattr(self, 'fragment_shader') and self.fragment_shader:
            glDeleteShader(self.fragment_shader)
            self.fragment_shader = None

        # 删除着色器程序
        if hasattr(self, 'shader') and self.shader:
            glDeleteProgram(self.shader)
            self.shader = None

        # 删除缓存式渲染（rend_cached）的多槽缓冲缓存；GL 上下文可能已释放，失败静默
        try:
            cache = getattr(self, '_rend_cache', None)
            if cache:
                for entry in cache.values():
                    glDeleteVertexArrays(1, [entry[1]])
                    glDeleteBuffers(len(entry[2]), entry[2])
                cache.clear()
        except Exception:
            pass

        # 清空相关字典
        if hasattr(self, 'uniform_loc'):
            self.uniform_loc.clear()
        if hasattr(self, 'uniform_val'):
            self.uniform_val.clear()
        if hasattr(self, 'uniform_type'):
            self.uniform_type.clear()
        if hasattr(self, 'texture_val'):
            self.texture_val.clear()


class AutoSP:
    def __init__(self,
                 base_color: "Img",
                 normal: "list | tuple | Img" = (0.5, 0.5, 1),
                 emission: "list | tuple | Img" = (0, 0, 0),
                 double_side: bool = True,
                 max_light_count: int = 8,
                 shader_program: ShaderProgram | None = None):
        """
        根据用户提供的参数自动生成ShaderProgram类，并在需要时自动调用ShaderProgram的类成员，作为表面着色器渲染时使用的顶点列表格式：
        [
            (x, y, z, u, v) | (x, y, z, u, v, nx, ny, nz),
            ...
        ]
        其中：
        x, y, z: 顶点3维坐标

        u, v: 顶点对应的贴图uv坐标位置

        nx, ny, nz: 顶点法线偏移，默认为0

        :param base_color:      主要颜色
        :param normal:          自定义法线或法线贴图
        :param emission:        自发光度，
                                当该参数为数字时，0.0为不发光，1.0为完全发光；
                                当该参数为灰度图时，黑色为不发光，白色为完全发光
        :param double_side:     是否启用双面渲染
        :param max_light_count: 该着色器使用时会同时出现的最多的光源数量
        :param shader_program:  被AutoSP管理的着色器程序，若为None，则生成着色器程序。该参数为内部调用参数，可以但不建议直接使用该参数。
        """
        if not isinstance(base_color, (Texture, MixChannel)):
            raise TypeError("base_color must be a Texture or MixChannel instance")
        if not isinstance(normal, (list, tuple, Texture, MixChannel)):
            raise TypeError("normal must be a list, tuple, Texture, or MixChannel instance")
        if isinstance(normal, (list, tuple)) and len(normal) != 3:
            raise TypeError("normal tuple/list must have 3 elements")
        if not isinstance(emission, (list, tuple, Texture, MixChannel)):
            raise TypeError("emission must be a list, tuple, Texture, or MixChannel instance")
        if isinstance(emission, (list, tuple)) and len(emission) != 3:
            raise TypeError("emission tuple/list must have 3 elements")
        if not isinstance(double_side, bool):
            raise TypeError("double_side must be a bool")
        if not isinstance(max_light_count, int):
            raise TypeError("max_light_count must be an int")
        if shader_program is not None and not isinstance(shader_program, ShaderProgram):
            raise TypeError("shader_program must be a ShaderProgram instance or None")

        self.base_color = base_color
        self.normal = normal
        self.emission = emission
        self.double_side = double_side
        self.max_light_count = max_light_count

        # 生成着色器程序
        self.shader_program = shader_program
        if shader_program is None:
            self.shader_program = self.create_shader_program()

        # 存储矩阵
        self.model_mat = glm.mat4(1.0)
        self.view_mat = glm.mat4(1.0)
        self.projection_mat = glm.mat4(1.0)
        # 持久 value_ptr：矩阵对象此后恒定（setter 改为原地拷贝，不替换引用），
        # 指针数据随矩阵原地写自动同步；消除每帧 glm.value_ptr() 的 ctypes
        # 指针包装分配（GC 升代大户，见 gc-stutter 诊断）
        self._model_ptr = glm.value_ptr(self.model_mat)
        self._view_ptr = glm.value_ptr(self.view_mat)
        self._proj_ptr = glm.value_ptr(self.projection_mat)

        # 缓存式渲染（rend_cached）的多槽拆分缓存：按源顶点列表对象 id 分槽，
        # 值为 (源顶点列表, 拆分结果)；缓存强引用保活源顶点列表，使 id 不可能被
        # 回收复用，命中时以 is 校验对象同一性。槽位上限 _REND_CACHE_MAX_SLOTS，
        # 满则 FIFO 淘汰（纯 Python 数据，无 GL 资源需删除）
        self._split_cache = {}

        # 注册到矩阵更新队列
        set_mat_queue[id(self)] = self

        soup3D.light.dirty = True

        self.dirty = True

        self.model_dirty = True
        self.view_dirty = True
        self.projection_dirty = True

        self.light_dirty = True

    def retexture(self,
                  base_color: "None | Img" = None,
                  normal: "None | list | tuple | Img" = None,
                  emission: "None | list | tuple | Img" = None):
        """
        重新向着色器上传纹理，填写None则保持原纹理不变
        :param base_color: 主要颜色
        :param normal:     自定义法线或法线贴图
        :param emission:   自发光度，
                           当该参数为数字时，0.0为不发光，1.0为完全发光；
                           当该参数为灰度图时，黑色为不发光，白色为完全发光
        :return: None
        """
        if base_color is not None and not isinstance(base_color, (Texture, MixChannel)):
            raise TypeError("base_color must be a Texture or MixChannel instance or None")
        if normal is not None and not isinstance(normal, (list, tuple, Texture, MixChannel)):
            raise TypeError("normal must be a list, tuple, Texture, MixChannel instance, or None")
        if isinstance(normal, (list, tuple)) and len(normal) != 3:
            raise TypeError("normal tuple/list must have 3 elements")
        if emission is not None and not isinstance(emission, (list, tuple, Texture, MixChannel)):
            raise TypeError("emission must be a list, tuple, Texture, MixChannel instance, or None")
        if isinstance(emission, (list, tuple)) and len(emission) != 3:
            raise TypeError("emission tuple/list must have 3 elements")

        # 更新基础颜色纹理
        if base_color is not None:
            self.base_color = base_color
            self.shader_program.uniform_tex("baseColor", self.base_color, 0)

        # 更新法线贴图
        if normal is not None:
                
            self.normal = normal
            if isinstance(self.normal, (list, tuple)):
                # 如果是元组或列表，创建混合通道纹理
                normal_texture = MixChannel((1, 1), *self.normal)
                self.shader_program.uniform_tex("normal", normal_texture, 1)
            else:
                # 如果是纹理对象，直接使用
                self.shader_program.uniform_tex("normal", self.normal, 1)

        # 更新自发光贴图
        if emission is not None:
            self.emission = emission
            if isinstance(self.emission, (list, tuple)):
                # 如果是元组或列表，创建混合通道纹理
                emission_texture = MixChannel((1, 1), *self.emission)
                self.shader_program.uniform_tex("emission", emission_texture, 3)
            else:
                # 如果是纹理对象，直接使用
                self.shader_program.uniform_tex("emission", self.emission, 3)

    def create_shader_program(self) -> ShaderProgram:
        """根据参数创建着色器程序"""
        vertex_shader = """
        #version 330 core
        layout(location = 0) in vec3 VertPos;
        layout(location = 1) in vec2 VertUV;
        layout(location = 2) in vec3 VertNormal;
        
        out vec2 TexCoord;
        out vec3 FragPos;
        out vec3 Normal;
        
        uniform mat4 model;       // 模型矩阵
        uniform mat4 view;        // 相机矩阵
        uniform mat4 projection;  // 透视矩阵
        
        void main()
        {
            FragPos = vec3(model * vec4(VertPos, 1.0));
            mat3 normalMatrix = transpose(inverse(mat3(model)));
            Normal = normalMatrix * VertNormal;
        
            gl_Position = projection * view * vec4(FragPos, 1.0);
            TexCoord = vec2(VertUV.x, 1-VertUV.y);
        }
        
        
        """

        fragment_shader = """
        #version 330 core
        in vec2 TexCoord;
        in vec3 FragPos;
        in vec3 Normal;
        out vec4 FragColor;
        
        // 材质属性
        uniform sampler2D baseColor;
        uniform sampler2D normal;
        uniform sampler2D emission;
        
        // 光照属性
        struct Light {
            vec3 position;
            vec3 direction;
            vec3 color;
            float attenuation;
            float angle;
            float cosAngle;
            int type;
        };
        
        uniform Light lights[%i];
        uniform int lightCount;
        uniform vec3 ambient;
        
        void main()
        {
            vec3 SideNormal = Normal;
            %s
        
            // 基础颜色
            vec4 base = texture(baseColor, TexCoord);
        
            // 法线处理
            vec4 norm_tex = texture(normal, TexCoord);
            vec3 norm = normalize(SideNormal) + vec3(norm_tex.rg*2-1, norm_tex.b-1);
        
            // 自发光
            vec4 emi = texture(emission, TexCoord);
        
            // 漫反射贡献
            vec3 diffuse = vec3(0.0);
        
            // 遍历所有光源
            for (int i = 0; i < lightCount; i++) {
                vec3 lightDir;
                float attenuation = 1.0;
                float spotFactor = 1.0;
        
                if (lights[i].type == 0) {
                    lightDir = normalize(lights[i].position - FragPos);
        
                    // 计算衰减
                    float distance = length(lights[i].position - FragPos);
                    attenuation = 1.0 / (1.0 + lights[i].attenuation * distance);
        
                    // 计算聚光灯效果
                    vec3 spotDir = normalize(-lights[i].direction);
                    float cosTheta = dot(lightDir, spotDir);
        
                    // 检查是否在聚光灯锥角内
                    if (cosTheta > lights[i].cosAngle) {
                        // 计算聚光灯衰减（边缘平滑过渡）
                        float epsilon = lights[i].cosAngle - lights[i].cosAngle * 0.9;
                        spotFactor = clamp((cosTheta - lights[i].cosAngle) / epsilon, 0.0, 1.0);
                    } else {
                        spotFactor = 0.0;
                    }
                    attenuation *= spotFactor;
                } else { // 方向光
                    lightDir = normalize(lights[i].direction);
                }
        
                // 漫反射计算
                float diff = max(dot(norm, lightDir), 0.0);
                diffuse += lights[i].color * diff * attenuation;
            }
        
            // 最终颜色 = (环境光 + 漫反射) * 基础颜色 + 自发光
            vec3 result = (ambient + diffuse) * base.rgb + base.rgb * emi.rgb;
            FragColor = vec4(result, base.a);
        }
        """

        if self.double_side:
            fragment_shader = fragment_shader % (
                self.max_light_count,
                """
                if (!gl_FrontFacing) {
                    SideNormal = -Normal;
                }
                """
            )
        else:
            fragment_shader = fragment_shader % (
                self.max_light_count,
                """
                if (!gl_FrontFacing) {
                    discard;
                }
                """
            )

        # 创建着色器程序
        shader_program = ShaderProgram(
            vertex_shader,
            fragment_shader,
            vbo_type=[soup3D.FLOAT, soup3D.FLOAT, soup3D.FLOAT]  # 位置、纹理坐标、法线
        )

        # 设置基础颜色纹理
        shader_program.uniform_tex("baseColor", self.base_color, 0)

        # 设置法线
        if isinstance(self.normal, (list | tuple)):
            normal_texture = MixChannel((1, 1), *self.normal)
            shader_program.uniform_tex("normal",
                                       normal_texture,
                                       1)
        else:
            shader_program.uniform_tex("normal",
                                       self.normal,
                                       1)

        # 设置自发光
        if isinstance(self.emission, (list | tuple)):
            emission_texture = MixChannel((1, 1), *self.emission)
            shader_program.uniform_tex("emission",
                                       emission_texture,
                                       3)
        else:
            shader_program.uniform_tex("emission",
                                       self.emission,
                                       3)

        return shader_program

    def set_model_mat(self, mat: glm.mat4):
        """
        设置模型矩阵，在变换矩阵时自动调用
        :param mat: 模型矩阵
        :return: None
        """
        if not isinstance(mat, glm.mat4):
            raise TypeError("mat must be a glm.mat4")
        # 原地拷贝而非替换引用：矩阵对象恒定，持久 value_ptr 指针保持有效；
        # pyglm 支持整行 vec4 赋值且 C 端按值拷贝（已验证）
        for i in range(4):
            self.model_mat[i] = mat[i]
        self.dirty = True
        self.model_dirty = True

    def set_view_mat(self, mat: glm.mat4):
        """
        设置投影矩阵，在变换矩阵时自动调用
        :param mat: 投影矩阵
        :return: None
        """
        if not isinstance(mat, glm.mat4):
            raise TypeError("mat must be a glm.mat4")
        # 原地拷贝（同 set_model_mat：矩阵对象恒定，持久指针保持有效）
        for i in range(4):
            self.view_mat[i] = mat[i]
        self.dirty = True
        self.view_dirty = True

    def set_projection_mat(self, mat: glm.mat4):
        """
        设置视图矩阵，在变换矩阵时自动调用
        :param mat: 视图矩阵
        :return: None
        """
        if not isinstance(mat, glm.mat4):
            raise TypeError("mat must be a glm.mat4")
        # 原地拷贝（同 set_model_mat：矩阵对象恒定，持久指针有效）
        for i in range(4):
            self.projection_mat[i] = mat[i]
        self.dirty = True
        self.projection_dirty = True

    def set_light(self):
        """
        设置光照，在添加、减少光照时自动调用
        :param light_queue: 光照列队
        :return: None
        """
        self.dirty = True
        self.light_dirty = True

    def use(self):
        """
        使用该着色器，会在应用时自动调用
        :return: None
        """
        self.shader_program.use()

    def rend(self, mode, vertex):
        """
        创建该着色器的渲染流程
        :param mode:   绘制方式
        :param vertex: 表面中所有的顶点
        :return: None
        """
        # 计算面法线（使用前三个顶点）
        normal = [0.0, 0.0, 1.0]  # 默认法线
        if len(vertex) >= 3:
            v0 = vertex[0]
            v1 = vertex[1]
            v2 = vertex[2]

            # 确保顶点有足够的数据
            if len(v0) >= 3 and len(v1) >= 3 and len(v2) >= 3:
                # 计算两个向量
                u = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]]
                v = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]]

                # 叉积得到法线
                normal = [
                    u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]
                ]

                # 归一化
                length = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5
                if length > 0:
                    normal = [n / length for n in normal]

        # 将顶点数据拆分为位置、纹理坐标和法线
        positions = []
        tex_coords = []
        normals = []  # 法线数据

        for v in vertex:
            # 位置数据
            if len(v) >= 3:
                positions.append(v[0:3])
            else:
                positions.append((0.0, 0.0, 0.0))

            # 纹理坐标
            if len(v) >= 5:
                tex_coords.append((v[3], 1.0 - v[4]))  # 翻转纹理坐标的Y轴
            else:
                tex_coords.append((0.0, 0.0))
            # 法线数据 - 使用计算的面法线
            if len(v) >= 8:
                normals.append(v[5:8])
            else:
                normals.append(normal)

        # 确保所有数据长度一致
        min_len = min(len(positions), len(tex_coords), len(normals))
        positions = positions[:min_len]
        tex_coords = tex_coords[:min_len]
        normals = normals[:min_len]

        # 渲染
        self.shader_program.rend(mode, [positions, tex_coords, normals])

    def rend_cached(self, mode, vertex):
        """
        缓存式渲染：顶点拆分逻辑与 rend(mode, vertex) 一致，但拆分结果缓存在自身，
        后续帧传入同一顶点列表对象（按 id 判定）时跳过纯 Python 逐顶点拆分，
        直接以缓存结果调用 ShaderProgram.rend_cached 绘制。

        设计说明：静态模型逐帧渲染的拆分缓存。rend() 每帧把 (x, y, z, u, v, ...)
        顶点列表重新拆分为位置/纹理坐标/法线三列表，对数万顶点的静态地图是
        每帧重复的纯 Python 开销；本方法只在顶点列表对象变化（id 不同）时重拆一次，
        并复用着色器程序侧缓存的 VAO/VBO（见 ShaderProgram.rend_cached）。

        契约：以入参 vertex 的对象 id 变化判定重拆——修改顶点数据须传入新的
        列表对象，原地改动不会被感知；顶点数据本身也视为静态（不再重新上传）。
        支持同一实例的多个不同静态顶点列表（如多个 Face 共享 surface）：按源
        顶点列表对象 id 分槽缓存拆分结果，上限 _REND_CACHE_MAX_SLOTS 槽，满则
        FIFO 淘汰（被淘汰的列表下次调用时重拆，性能退化但内容正确）。拆分缓存
        随实例被垃圾回收自然释放，无需显式清理。仅适用于 AutoSP 的顶点格式
        （骨骼绑定的 BoneBinderSP 顶点格式不同，勿对其调用）。

        :param mode:   绘制方式
        :param vertex: 表面中所有的顶点
        :return: None
        """
        # 按 id(源顶点列表) 查拆分缓存；命中时校验缓存保活的源顶点列表与入参为同一对象
        cache_key = id(vertex)
        entry = self._split_cache.get(cache_key)
        if entry is not None and entry[0] is not vertex:
            # id 槽被其他对象占用：淘汰旧槽
            del self._split_cache[cache_key]
            entry = None

        if entry is None:
            # 未命中：拆分顶点（计算面法线，按位置/纹理坐标/法线分列）
            # 计算面法线（使用前三个顶点）
            normal = [0.0, 0.0, 1.0]  # 默认法线
            if len(vertex) >= 3:
                v0 = vertex[0]
                v1 = vertex[1]
                v2 = vertex[2]

                # 确保顶点有足够的数据
                if len(v0) >= 3 and len(v1) >= 3 and len(v2) >= 3:
                    # 计算两个向量
                    u = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]]
                    v = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]]

                    # 叉积得到法线
                    normal = [
                        u[1] * v[2] - u[2] * v[1],
                        u[2] * v[0] - u[0] * v[2],
                        u[0] * v[1] - u[1] * v[0]
                    ]

                    # 归一化
                    length = (normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2) ** 0.5
                    if length > 0:
                        normal = [n / length for n in normal]

            # 将顶点数据拆分为位置、纹理坐标和法线
            positions = []
            tex_coords = []
            normals = []  # 法线数据

            for v in vertex:
                # 位置数据
                if len(v) >= 3:
                    positions.append(v[0:3])
                else:
                    positions.append((0.0, 0.0, 0.0))

                # 纹理坐标
                if len(v) >= 5:
                    tex_coords.append((v[3], 1.0 - v[4]))  # 翻转纹理坐标的Y轴
                else:
                    tex_coords.append((0.0, 0.0))
                # 法线数据 - 使用计算的面法线
                if len(v) >= 8:
                    normals.append(v[5:8])
                else:
                    normals.append(normal)

            # 确保所有数据长度一致
            min_len = min(len(positions), len(tex_coords), len(normals))
            positions = positions[:min_len]
            tex_coords = tex_coords[:min_len]
            normals = normals[:min_len]

            split = [positions, tex_coords, normals]
            self._store_split_cache_slot(cache_key, vertex, split)
        else:
            split = entry[1]

        # 渲染
        self.shader_program.rend_cached(mode, split)

    def _store_split_cache_slot(self, key, vertex, split):
        """
        存入拆分缓存槽；槽满则 FIFO 淘汰最旧槽（纯 Python 数据，无 GL 资源需删除）
        :param key:   缓存键（id(源顶点列表)）
        :param vertex: 源顶点列表（缓存强引用保活，防止 id 复用）
        :param split: 拆分结果
        :return: None
        """
        if len(self._split_cache) >= _REND_CACHE_MAX_SLOTS and key not in self._split_cache:
            del self._split_cache[next(iter(self._split_cache))]
        self._split_cache[key] = (vertex, split)

    def unuse(self):
        """
        停用该着色器，会在结束应用时自动调用
        :return: None
        """
        self.shader_program.unuse()

    def is_dirty(self):
        return self.shader_program.dirty or self.dirty

    def update(self):
        if self.dirty:
            if self.model_dirty:
                self.shader_program.uniform(
                    "model",
                    soup3D.ARRAY_MATRIX_VEC4,
                    1,
                    GL_FALSE,
                    self._model_ptr
                )
                self.model_dirty = False
            if self.view_dirty:
                self.shader_program.uniform(
                    "view",
                    soup3D.ARRAY_MATRIX_VEC4,
                    1,
                    GL_FALSE,
                    self._view_ptr
                )
                self.view_dirty = False
            if self.projection_dirty:
                self.shader_program.uniform(
                    "projection",
                    soup3D.ARRAY_MATRIX_VEC4,
                    1,
                    GL_FALSE,
                    self._proj_ptr
                )
                self.projection_dirty = False
            if self.light_dirty:
                # 环境光直接读 light 模块的缓存(ambient() 写入),不再逐 surface 做 glGetFloatv 读回
                ambient = soup3D.light.ambient_val
                self.shader_program.uniform("ambient", soup3D.FLOAT_VEC3, *ambient)

                # 收集有效光源
                light_count = 0
                for light_id, light in light_queue.items():
                    if light.on and light_count < self.max_light_count:
                        if isinstance(light, soup3D.light.Cone):
                            # 点光源（聚光灯）
                            direction = light._calc_direction()
                            # 计算锥角的余弦值
                            cos_angle = math.cos(math.radians(light.angle / 2))

                            self.shader_program.uniform(f"lights[{light_count}].position", soup3D.FLOAT_VEC3,
                                                        *light.place)
                            self.shader_program.uniform(f"lights[{light_count}].direction", soup3D.FLOAT_VEC3,
                                                        *direction)
                            self.shader_program.uniform(f"lights[{light_count}].color", soup3D.FLOAT_VEC3, *light.color)
                            self.shader_program.uniform(f"lights[{light_count}].attenuation", soup3D.FLOAT_VEC1,
                                                        light.attenuation)
                            self.shader_program.uniform(f"lights[{light_count}].cosAngle", soup3D.FLOAT_VEC1, cos_angle)
                            self.shader_program.uniform(f"lights[{light_count}].type", soup3D.INT_VEC1, 0)
                            light_count += 1
                        elif isinstance(light, soup3D.light.Direct):
                            # 方向光
                            direction = light._calc_direction()
                            self.shader_program.uniform(f"lights[{light_count}].position", soup3D.FLOAT_VEC3, 0, 0, 0)
                            self.shader_program.uniform(f"lights[{light_count}].direction", soup3D.FLOAT_VEC3,
                                                        *direction)
                            self.shader_program.uniform(f"lights[{light_count}].color", soup3D.FLOAT_VEC3, *light.color)
                            self.shader_program.uniform(f"lights[{light_count}].attenuation", soup3D.FLOAT_VEC1, 0.0)
                            self.shader_program.uniform(f"lights[{light_count}].cosAngle", soup3D.FLOAT_VEC1, 0.0)
                            self.shader_program.uniform(f"lights[{light_count}].type", soup3D.INT_VEC1, 1)
                            light_count += 1

                # 设置光源数量
                self.shader_program.uniform("lightCount", soup3D.INT_VEC1, light_count)

                # 填充剩余光源槽位
                for i in range(light_count, self.max_light_count):
                    self.shader_program.uniform(f"lights[{i}].color", soup3D.FLOAT_VEC3, 0.0, 0.0, 0.0)

                self.light_dirty = False
        if self.shader_program.is_dirty():
            self.shader_program.update()
        self.dirty = False

    def __del__(self):
        """
        深度清理着色器，清理该着色器本身及所有该着色器用到的元素。在确定不再使用该着色器时可使用该方法释放内存。
        :return: None
        """
        # 从全局队列中移除
        if id(self) in set_mat_queue:
            del set_mat_queue[id(self)]

        # 清理材质相关资源
        if self.base_color:
            self.base_color = None

        if self.normal and not isinstance(self.normal, (list, tuple)):
            self.normal = None

        if self.emission and not isinstance(self.emission, (list, tuple)):
            self.emission = None

        if self.shader_program:
            self.shader_program = None

        # 清理矩阵
        self.model_mat = None
        self.view_mat = None
        self.projection_mat = None


class BoneBinderSP(AutoSP):
    def __init__(self,
                 base_color: "Img",
                 normal: "list | tuple | Img" = (0.5, 0.5, 1),
                 emission: "list | tuple | Img" = (0, 0, 0),
                 double_side: bool = True,
                 max_light_count: int = 8,
                 shader_program: ShaderProgram | None = None,
                 skeleton: soup3D.skeleton.Skeleton | dict = None):
        """
        骨骼绑定着色器，作为表面着色器渲染时使用的顶点列表格式：
        [
            ({name: weight, ...}, x, y, z, u, v) | ({name: weight, ...}, weight, x, y, z, u, v, nx, ny, nz),
            ...
        ]
        其中：

        name: 骨头字典中骨头对应的名称

        weight: 该骨头对应在该顶点上的权重

        未定义权重的名称对应的骨骼权重默认为0

        x, y, z: 顶点3维坐标

        u, v: 顶点对应的贴图uv坐标位置

        nx, ny, nz: 顶点法线偏移，默认为0

        :param base_color:      主要颜色
        :param normal:          自定义法线或法线贴图
        :param emission:        自发光度，
                                当该参数为数字时，0.0为不发光，1.0为完全发光；
                                当该参数为灰度图时，黑色为不发光，白色为完全发光
        :param double_side:     是否启用双面渲染
        :param max_light_count: 该着色器使用时会同时出现的最多的光源数量
        :param shader_program:  被AutoSP管理的着色器程序，若为None，则生成着色器程序。该参数为内部调用参数，可以但不建议直接使用该参数。
        :param skeleton:        一个Skeleton对象或包含多个骨头的字典，格式：{name: bone, name: bone, ...}
        """
        if skeleton is not None and not isinstance(skeleton, (soup3D.skeleton.Skeleton, dict)):
            raise TypeError("skeleton must be a Skeleton instance, dict, or None")

        # 如果skeleton为None，创建一个空的Skeleton对象
        if skeleton is None:
            self.skeleton = soup3D.skeleton.Skeleton()
        else:
            self.skeleton = skeleton

        self.max_bones = len(self.skeleton.bones) if self.skeleton else 0  # 最大骨骼数量
        self.bones_dirty = True  # 骨骼矩阵更新标记
        self.bone_binding_point = 1  # UBO绑定点编号

        super().__init__(base_color, normal, emission, double_side, max_light_count, shader_program)

        # 创建骨骼矩阵UBO
        self.bone_ubo = self._create_bone_ubo()

        # 将自身注册到所有骨骼的着色器通知列表
        skeleton_obj = self._get_skeleton_obj()
        for bone in skeleton_obj.bones.values():
            bone._bound_shaders[id(self)] = self

    def create_shader_program(self):
        """根据参数创建着色器程序"""
        vertex_shader = """
        #version 330 core
        #define MAX_BONES %d

        layout(location = 0) in vec3 VertPos;
        layout(location = 1) in vec2 VertUV;
        layout(location = 2) in vec3 VertNormal;
        layout(location = 3) in uvec4 BoneIDs;
        layout(location = 4) in vec4 BoneWeights;

        out vec2 TexCoord;
        out vec3 FragPos;
        out vec3 Normal;

        uniform mat4 model;       // 模型矩阵
        uniform mat4 view;        // 相机矩阵
        uniform mat4 projection;  // 透视矩阵

        layout(std140) uniform BoneBlock {
            mat4 boneMatrices[MAX_BONES];
        };

        void main()
        {
            // 计算骨骼蒙皮变换矩阵
            mat4 skinMatrix = mat4(0.0);
            float totalWeight = 0.0;
            for (int i = 0; i < 4; i++) {
                skinMatrix += BoneWeights[i] * boneMatrices[int(BoneIDs[i])];
                totalWeight += BoneWeights[i];
            }

            // 无骨骼绑定时使用单位矩阵，避免顶点被移动到原点
            if (totalWeight < 0.001) {
                skinMatrix = mat4(1.0);
            }

            // 应用蒙皮变换
            vec4 skinnedPos = skinMatrix * vec4(VertPos, 1.0);
            FragPos = vec3(model * skinnedPos);

            // 法线变换
            mat3 skinNormalMatrix = transpose(inverse(mat3(model * skinMatrix)));
            Normal = skinNormalMatrix * VertNormal;

            gl_Position = projection * view * vec4(FragPos, 1.0);
            TexCoord = vec2(VertUV.x, 1.0 - VertUV.y);
        }
        """

        fragment_shader = """
        #version 330 core
        in vec2 TexCoord;
        in vec3 FragPos;
        in vec3 Normal;
        out vec4 FragColor;

        // 材质属性
        uniform sampler2D baseColor;
        uniform sampler2D normal;
        uniform sampler2D emission;

        // 光照属性
        struct Light {
            vec3 position;
            vec3 direction;
            vec3 color;
            float attenuation;
            float angle;
            float cosAngle;
            int type;
        };

        uniform Light lights[8];
        uniform int lightCount;
        uniform vec3 ambient;

        void main()
        {
            vec3 SideNormal = Normal;
            %s

            // 基础颜色
            vec4 base = texture(baseColor, TexCoord);
            
            if (base.a < 0.5) {
                discard;
            }

            // 法线处理
            vec4 norm_tex = texture(normal, TexCoord);
            vec3 norm = normalize(SideNormal) + vec3(norm_tex.rg*2-1, norm_tex.b-1);

            // 自发光
            vec4 emi = texture(emission, TexCoord);

            // 漫反射贡献
            vec3 diffuse = vec3(0.0);

            // 遍历所有光源
            for (int i = 0; i < lightCount; i++) {
                vec3 lightDir;
                float attenuation = 1.0;
                float spotFactor = 1.0;

                if (lights[i].type == 0) {
                    lightDir = normalize(lights[i].position - FragPos);

                    // 计算衰减
                    float distance = length(lights[i].position - FragPos);
                    attenuation = 1.0 / (1.0 + lights[i].attenuation * distance);

                    // 计算聚光灯效果
                    vec3 spotDir = normalize(-lights[i].direction);
                    float cosTheta = dot(lightDir, spotDir);

                    // 检查是否在聚光灯锥角内
                    if (cosTheta > lights[i].cosAngle) {
                        // 计算聚光灯衰减（边缘平滑过渡）
                        float epsilon = lights[i].cosAngle - lights[i].cosAngle * 0.9;
                        spotFactor = clamp((cosTheta - lights[i].cosAngle) / epsilon, 0.0, 1.0);
                    } else {
                        spotFactor = 0.0;
                    }
                    attenuation *= spotFactor;
                } else { // 方向光
                    lightDir = normalize(lights[i].direction);
                }

                // 漫反射计算
                float diff = max(dot(norm, lightDir), 0.0);
                diffuse += lights[i].color * diff * attenuation;
            }

            // 最终颜色 = (环境光 + 漫反射) * 基础颜色 + 自发光
            vec3 result = (ambient + diffuse) * base.rgb + base.rgb * emi.rgb;
            FragColor = vec4(result, base.a);
        }
        """

        vertex_shader = vertex_shader % self.max_bones

        if self.double_side:
            fragment_shader = fragment_shader % (
                """
                if (!gl_FrontFacing) {
                    SideNormal = -Normal;
                }
                """
            )
        else:
            fragment_shader = fragment_shader % (
                """
                if (!gl_FrontFacing) {
                    discard;
                }
                """
            )

        # 创建着色器程序
        shader_program = ShaderProgram(
            vertex_shader,
            fragment_shader,
            vbo_type=[soup3D.FLOAT, soup3D.FLOAT, soup3D.FLOAT, soup3D.INT_US, soup3D.FLOAT]
        )

        # 绑定UBO块到着色器
        bone_block_index = glGetUniformBlockIndex(shader_program.shader, b"BoneBlock")
        if bone_block_index != GL_INVALID_INDEX:
            glUniformBlockBinding(shader_program.shader, bone_block_index, self.bone_binding_point)

        # 设置基础颜色纹理
        shader_program.uniform_tex("baseColor", self.base_color, 0)

        # 设置法线
        if isinstance(self.normal, (list | tuple)):
            normal_texture = MixChannel((1, 1), *self.normal)
            shader_program.uniform_tex("normal", normal_texture, 1)
        else:
            shader_program.uniform_tex("normal", self.normal, 1)

        # 设置自发光
        if isinstance(self.emission, (list | tuple)):
            emission_texture = MixChannel((1, 1), *self.emission)
            shader_program.uniform_tex("emission", emission_texture, 3)
        else:
            shader_program.uniform_tex("emission", self.emission, 3)

        return shader_program

    def rend(self, mode, vertex):
        """
        创建该着色器的渲染流程
        :param mode:   绘制方式
        :param vertex: 表面中所有的顶点，格式：
                       [
                           ({name: weight, ...}, x, y, z, u, v) | ({name: weight, ...}, weight, x, y, z, u, v, nx, ny, nz),
                           ...
                       ]
        :return: None
        """
        # 获取骨架信息
        skeleton_obj = self._get_skeleton_obj()

        # 准备顶点数据
        positions = []
        tex_coords = []
        normals = []
        bone_ids = []
        bone_weights = []

        for v in vertex:
            # 解析骨骼权重
            bone_weights_dict = v[0] if isinstance(v[0], dict) else {}

            # 提取骨骼ID和权重
            bone_id_list = []
            weight_list = []

            for bone_name, weight in bone_weights_dict.items():
                bone_idx = skeleton_obj.get_bone_index(bone_name)
                if bone_idx >= 0:
                    bone_id_list.append(bone_idx)
                    weight_list.append(weight)

            # 规范化为4个骨骼权重（最多支持4个骨骼影响一个顶点）
            while len(bone_id_list) < 4:
                bone_id_list.append(0)
                weight_list.append(0.0)

            # 按权重排序，取前4个
            sorted_pairs = sorted(zip(weight_list, bone_id_list), reverse=True)
            weight_list = [p[0] for p in sorted_pairs[:4]]
            bone_id_list = [p[1] for p in sorted_pairs[:4]]

            # 归一化权重
            total_weight = sum(weight_list[:4])
            if total_weight > 0:
                weight_list = [w / total_weight for w in weight_list[:4]]
            else:
                weight_list = [0.0, 0.0, 0.0, 0.0]

            bone_ids.append(bone_id_list[:4])
            bone_weights.append(weight_list[:4])

            # 解析位置
            if len(v) >= 4:
                positions.append(v[1:4])
            else:
                positions.append((0.0, 0.0, 0.0))

            # 解析纹理坐标
            if len(v) >= 6:
                tex_coords.append((v[4], 1.0 - v[5]))
            else:
                tex_coords.append((0.0, 0.0))

            # 解析法线
            if len(v) >= 9:
                normals.append(v[6:9])
            else:
                normals.append((0.0, 0.0, 1.0))

        # 渲染
        self.shader_program.rend(mode, [positions, tex_coords, normals, bone_ids, bone_weights])

    def update(self):
        """更新着色器"""
        if self.dirty:
            if self.bones_dirty:
                self._update_bone_matrices()
                self.bones_dirty = False

        # 绑定UBO到着色器绑定点，确保渲染时使用正确的骨骼数据
        if hasattr(self, 'bone_ubo') and self.bone_ubo is not None:
            self.bone_ubo.bind_base(self.bone_binding_point)

        super().update()

    def set_skeleton(self, skeleton: soup3D.skeleton.Skeleton | dict):
        """
        设置骨架
        :param skeleton: Skeleton对象或骨骼字典
        :return: None
        """
        if not isinstance(skeleton, (soup3D.skeleton.Skeleton, dict)):
            raise TypeError("skeleton must be a Skeleton instance or dict")

        old_skeleton_obj = self._get_skeleton_obj()
        
        for bone in old_skeleton_obj.bones.values():
            if id(self) in bone._bound_shaders:
                del bone._bound_shaders[id(self)]
        
        self.skeleton = skeleton
        
        skeleton_obj = self._get_skeleton_obj()
        new_max_bones = skeleton_obj.get_max_bones()
        
        for bone in skeleton_obj.bones.values():
            bone._bound_shaders[id(self)] = self
        
        if new_max_bones != self.max_bones:
            self.max_bones = new_max_bones
            self.bone_ubo = self._create_bone_ubo()
            self.shader_program = self.create_shader_program()
        
        self.bones_dirty = True
        self.dirty = True

    def mark_bones_dirty(self):
        """标记骨骼需要更新"""
        self.bones_dirty = True
        self.dirty = True

    def _get_skeleton_obj(self) -> soup3D.skeleton.Skeleton:
        """获取Skeleton对象"""
        if isinstance(self.skeleton, soup3D.skeleton.Skeleton):
            return self.skeleton
        elif isinstance(self.skeleton, dict):
            # 如果是字典，转换为Skeleton对象
            skel = soup3D.skeleton.Skeleton()
            for name, bone in self.skeleton.items():
                skel.add_bone(name, bone)
            return skel
        else:
            # 返回空骨架
            return soup3D.skeleton.Skeleton()

    def _create_bone_ubo(self) -> UniformBuffer:
        """创建骨骼矩阵UBO
        
        :return: UniformBuffer实例
        """
        bytes_per_matrix = 16 * 4
        ubo_size = self.max_bones * bytes_per_matrix
        return UniformBuffer(ubo_size, GL_DYNAMIC_DRAW)

    def _update_bone_matrices(self):
        """更新骨骼矩阵到UBO"""
        skeleton_obj = self._get_skeleton_obj()

        bone_matrices = skeleton_obj.get_bone_matrices()
        
        total_size = self.max_bones * 16
        bone_data = np.zeros(total_size, dtype=np.float32)
        
        for i, mat in enumerate(bone_matrices):
            if i >= self.max_bones:
                break
            mat_array = np.ctypeslib.as_array(glm.value_ptr(mat), shape=(16,)).copy()
            bone_data[i*16:(i+1)*16] = mat_array
        
        for i in range(len(bone_matrices), self.max_bones):
            identity_offset = i * 16
            bone_data[identity_offset] = 1.0
            bone_data[identity_offset + 5] = 1.0
            bone_data[identity_offset + 10] = 1.0
            bone_data[identity_offset + 15] = 1.0

        self.bone_ubo.update(bone_data)

    def __del__(self):
        """清理骨骼绑定着色器资源"""
        if hasattr(self, 'bone_ubo') and self.bone_ubo is not None:
            self.bone_ubo = None
        
        super().__del__()


# 标准材质参数名:模型文件加载器会尽量提供这些参数，表面着色器类按需声明接收其中的任意子集
SURFACE_MATERIAL_PARAMS = (
    "base_color", "normal", "emission", "double_side", "max_light_count",
    "roughness", "metallic", "ior", "transmission", "shininess", "illum",
)

# 表面着色器类的参数内省缓存，键为类或工厂函数，值为(可接收参数集合或None, 必填参数名元组)，
# 其中可接收参数集合为None表示形参含**kwargs或无法内省，可接收任意参数
_surface_sig_cache = {}


def filter_surface_params(cls, params: dict) -> dict:
    """
    从参数字典中筛选出目标表面着色器类可接收的参数
    :param cls:     表面着色器类或工厂函数
    :param params:  加载器提供的标准材质参数字典
    :return:        按类签名过滤后的参数字典
    """
    accepted = get_surface_params(cls)
    if accepted is None:
        # 类带**kwargs或无法内省时，全量传入
        return dict(params)
    return {k: v for k, v in params.items() if k in accepted}


def make_surface(cls, params: dict) -> "Surface":
    """
    按照色器类可接收的参数过滤后实例化表面着色器。模型文件加载器(open_obj/open_mtl/open_gltf)通过该函数
    动态适配任意表面着色器类：类需要什么参数就传什么参数，不强制要求任何特定参数；当类声明了接收
    **kwargs时全量传入；当类缺少可供给的必填参数时抛出带说明的TypeError
    :param cls:     表面着色器类或工厂函数
    :param params:  标准材质参数字典，键为SURFACE_MATERIAL_PARAMS中的参数名
    :return:        表面着色器实例
    """
    accepted, required = _surface_sig_info(cls)
    kwargs = filter_surface_params(cls, params)
    missing = [name for name in required if name not in kwargs]
    if missing:
        raise TypeError(
            "cannot create surface shader "
            + getattr(cls, "__name__", repr(cls))
            + ": required parameters missing: "
            + ", ".join(missing)
            + "; loader can provide: "
            + ", ".join(sorted(kwargs))
        )
    return cls(**kwargs)


def get_surface_params(cls) -> "frozenset[str] | None":
    """
    内省表面着色器类(或工厂函数)可接收的构造参数名集合
    :param cls: 表面着色器类或工厂函数
    :return: 可接收的参数名集合；当形参含**kwargs或无法内省(如C扩展)时返回None，表示可接收任意参数
    """
    return _surface_sig_info(cls)[0]


def _surface_params_from_callable(target) -> "frozenset | None":
    """
    内省一个可调用对象的形参，返回(可接收的参数名集合或None, 必填参数名元组)
    :param target: 函数、方法等可调用对象
    :return: 内省结果；可接收参数集合为None表示含**kwargs形参，可接收任意关键字参数
    """
    try:
        sig = inspect.signature(target)
    except (TypeError, ValueError):
        return None, ()
    accepts_all = False
    params = set()
    required = []
    for param in sig.parameters.values():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            accepts_all = True
        elif param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
            params.add(param.name)
            if param.default is inspect.Parameter.empty:
                required.append(param.name)
    if accepts_all:
        return None, ()
    return frozenset(params), tuple(required)


def _surface_sig_info(cls) -> tuple:
    """
    获取表面着色器类的签名内省结果，带缓存
    :param cls: 表面着色器类或工厂函数
    :return: (可接收的参数名集合或None, 必填参数名元组)
    """
    try:
        return _surface_sig_cache[cls]
    except KeyError:
        pass
    if inspect.isclass(cls):
        # 内省类本身而非__init__，inspect.signature会自动排除self并遵循__init__/__new__
        result = _surface_params_from_callable(cls)
    else:
        # 类以外的可调用对象(工厂函数)直接内省其形参
        result = _surface_params_from_callable(cls)
    _surface_sig_cache[cls] = result
    return result


Img = Texture | MixChannel
GrayImg = Channel
Surface = ShaderProgram | AutoSP


if __name__ == '__main__':
    ...
