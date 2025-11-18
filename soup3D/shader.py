"""
处理soup3D中的着色系统
"""
from OpenGL.GL import *
from OpenGL.GL.shaders import compileShader, compileProgram
import PIL.Image
import numpy as np
from pyglm import glm
import math
import weakref

import soup3D.name


EAU = []
set_mat_queue = weakref.WeakValueDictionary()


type_map = {
    soup3D.name.FLOAT_VEC1: glUniform1f,
    soup3D.name.FLOAT_VEC2: glUniform2f,
    soup3D.name.FLOAT_VEC3: glUniform3f,
    soup3D.name.FLOAT_VEC4: glUniform4f,
    soup3D.name.INT_VEC1: glUniform1i,
    soup3D.name.INT_VEC2: glUniform2i,
    soup3D.name.INT_VEC3: glUniform3i,
    soup3D.name.INT_VEC4: glUniform4i,
    soup3D.name.ARRAY_FLOAT_VEC1: glUniform1fv,
    soup3D.name.ARRAY_FLOAT_VEC2: glUniform2fv,
    soup3D.name.ARRAY_FLOAT_VEC3: glUniform3fv,
    soup3D.name.ARRAY_FLOAT_VEC4: glUniform4fv,
    soup3D.name.ARRAY_INT_VEC1: glUniform1iv,
    soup3D.name.ARRAY_INT_VEC2: glUniform2iv,
    soup3D.name.ARRAY_INT_VEC3: glUniform3iv,
    soup3D.name.ARRAY_INT_VEC4: glUniform4iv,
    soup3D.name.ARRAY_MATRIX_VEC2: glUniformMatrix2fv,
    soup3D.name.ARRAY_MATRIX_VEC3: glUniformMatrix3fv,
    soup3D.name.ARRAY_MATRIX_VEC4: glUniformMatrix4fv,

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
        self.pil_pic = pil_pic
        self.texture_id = None

    def gen_gl_texture(self, texture_unit: int = 0):
        """
        生成OpenGL纹理
        :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）
        :return: None
        """

        # 激活指定纹理单元
        glActiveTexture(GL_TEXTURE0 + texture_unit)

        # 确定图像模式并转换为RGBA格式
        mode = self.pil_pic.mode
        if mode == '1':  # 黑白图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'L':  # 灰度图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'RGB':  # RGB图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'RGBA':  # RGBA图像
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        else:
            # 其他格式转换为RGBA
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)

        # 获取图像尺寸
        width, height = self.pil_pic.size

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

        # 生成mipmap（提高纹理在远距离的渲染质量）
        glGenerateMipmap(GL_TEXTURE_2D)

        self.texture_id = texture_id
        return texture_id

    def get_texture_id(self):
        """
        获取纹理id，若无纹理id，则创建纹理id。
        :return: 纹理id
        """

        if self.texture_id is None:
            self.gen_gl_texture()
        return self.texture_id

    def __del__(self):
        if self.texture_id is not None:
            glDeleteTextures([self.texture_id])
            self.texture_id = None


class Channel:
    def __init__(self, texture: "Img", channelID: int):
        """
        提取贴图中的单个通道
        :param texture:   提取通道的贴图
        :param channelID: 通道编号
        """
        self.texture = texture
        self.channelID = channelID

        self.pil_band = None

        self._get_pil_band()

    def _get_pil_band(self) -> PIL.Image:
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

    def __del__(self):
        if self.pil_band is not None:
            self.pil_band.close()
            self.pil_band = None


class MixChannel:
    def __init__(self,
                 resize: tuple[int, int],
                 R: "int | float | GrayImg",
                 G: "int | float | GrayImg",
                 B: "int | float | GrayImg",
                 A: "int | float | GrayImg" = 1.0):
        """
        混合通道成为一个贴图
        混合通道贴图(MixChannel)可通过类似贴图(Texture)的方式提取通道
        :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像
        :param R: 红色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param G: 绿色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param B: 蓝色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param A: 透明度通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        """
        self.resize = resize
        self.R = R
        self.G = G
        self.B = B
        self.A = A

        self.pil_pic = None  # 缓存混合通道后的图像，以便父着色单元提取

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

            elif isinstance(source, GrayImg):  # Channel对象
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
        self.texture_id = None

    def gen_gl_texture(self, texture_unit: int = 0):
        """
        生成OpenGL纹理
        :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）
        :return: None
        """
        # 激活指定纹理单元
        glActiveTexture(GL_TEXTURE0 + texture_unit)

        # 确定图像模式并转换为RGBA格式
        mode = self.pil_pic.mode
        if mode == '1':  # 黑白图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'L':  # 灰度图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'RGB':  # RGB图像
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        elif mode == 'RGBA':  # RGBA图像
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)
        else:
            # 其他格式转换为RGBA
            self.pil_pic = self.pil_pic.convert('RGBA')
            data = self.pil_pic.tobytes('raw', 'RGBA', 0, -1)

        # 获取图像尺寸
        width, height = self.pil_pic.size

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

        # 生成mipmap（提高纹理在远距离的渲染质量）
        glGenerateMipmap(GL_TEXTURE_2D)

        self.texture_id = texture_id
        return texture_id

    def get_texture_id(self):
        """
        获取纹理id，若无纹理id，则创建纹理id。
        :return: 纹理id
        """
        if self.texture_id is None:
            self.gen_gl_texture()
        return self.texture_id

    def __del__(self):
        if self.texture_id is not None:
            glDeleteTextures([self.texture_id])
            self.texture_id = None

        if self.pil_pic is not None:
            self.pil_pic.close()
            self.pil_pic = None


class ShaderProgram:
    def __init__(
            self, vertex: str, fragment: str,
            vbo_type: str | list[str] | tuple[str] = "float"
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
        “layout (location = 0) in <type> <value_name>”这段代码读取。
        :param vertex:   顶点着色程序代码
        :param fragment: 片段着色程序代码
        :param vbo_type: 定义传入着色器程序的顶点列表(vbo)的数据类型。如每个定点列表数据类型相同，可通过填写一个字符串定义所有的定点列表的
                         数据类型；如果需要不同的数据类型，可通过填写一个列表来分别定义每个顶点列表的数据类型。在同一vbo下，所有vertex的
                         长度需一致，且长度范围在1-4个数据。
        """
        self.vertex = vertex
        self.fragment = fragment
        self.vbo_type = vbo_type

        self.vertex_shader = compileShader(self.vertex, GL_VERTEX_SHADER)
        self.fragment_shader = compileShader(self.fragment, GL_FRAGMENT_SHADER)

        self.shader = compileProgram(self.vertex_shader, self.fragment_shader)

        self.uniform_loc = {}
        self.uniform_val = {}
        self.uniform_type = {}

        self.texture_val = {}

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

        glEnable(GL_DEPTH_TEST)

        num_buffers = len(vertex)
        vbo_ids = glGenBuffers(num_buffers)

        if num_buffers == 1:
            vbo_ids = [vbo_ids]  # 包装为列表

        vao = glGenVertexArrays(1)
        glBindVertexArray(vao)

        for i, vert_group in enumerate(vertex):
            if not vert_group:  # 空顶点组跳过
                continue

            vbo_np = np.array(vert_group, dtype=np.float32)

            glBindBuffer(GL_ARRAY_BUFFER, vbo_ids[i])
            glBufferData(GL_ARRAY_BUFFER, vbo_np.nbytes, vbo_np, GL_STATIC_DRAW)

            # 计算每个顶点的元素个数
            components = len(vert_group[0])
            glVertexAttribPointer(i, components, types[i], GL_FALSE, 0, ctypes.c_void_p(0))
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

    def unuse(self):
        """
        停用该着色器，会在结束应用时自动调用
        :return: None
        """
        glUseProgram(0)

    def uniform(self, v_name: str, v_type: str, *value):
        """
        在下一帧向着色器传递数据
        :param v_name: 在着色器内该数据对应的变量名
        :param v_type: 指定数据类型
        :param value:  其他填入glUniform方法的参数，当传入值为单独数据时(如v_name=soup3D.INT_VEC1),需在此项填写传入的数据，如果需传
                       入数组(如v_name=soup3D.ARRAY_INT_VEC1)，则需要在此项填入(数组长度, 数组)，如果为矩阵，则需填入
                       (矩阵数量, 是否转置矩阵, 传入的矩阵)
        :return: None
        """
        # 获取统一变量位置
        loc = glGetUniformLocation(self.shader, v_name)
        if loc == -1:
            print(f"Warning: Uniform '{v_name}' not found in shader")
            return
        self.uniform_loc[v_name] = loc
        self.uniform_val[v_name] = value
        self.uniform_type[v_name] = v_type

        self.dirty_update()

    def uniform_tex(self, v_name: str, texture: "Img", texture_unit: int = 0):
        """
        在下一帧向着色器传递纹理
        :param v_name:       在着色器内该纹理对应的变量名
        :param texture:      贴图类
        :param texture_unit: 纹理单元编号
        :return: None
        """
        # 获取统一变量位置
        prev_program = glGetIntegerv(GL_CURRENT_PROGRAM)
        loc = glGetUniformLocation(self.shader, v_name)
        if loc == -1:
            print(f"Warning: Uniform '{v_name}' not found in shader")
            return

        # 记录纹理信息
        self.uniform_loc[v_name] = loc
        self.texture_val[v_name] = (texture, texture_unit)
        self.uniform_type[v_name] = "texture"

        # 处理纹理类型的uniform
        texture.gen_gl_texture(texture_unit)

        self.dirty_update()

    def dirty_update(self):
        """
        标记该着色器为需要更新
        :return: None
        """
        if not self.dirty:
            self.dirty = True
            EAU.append((self.update,))

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

        self.uniform_loc = {}
        self.dirty = False

    def __del__(self):
        """
        深度清理着色器，清理该着色器本身及所有该着色器用到的元素。在确定不再使用该着色器时可使用该方法释放内存。
        :return: None
        """
        # 删除顶点着色器
        if self.vertex_shader:
            glDeleteShader(self.vertex_shader)
            self.vertex_shader = None

        # 删除片段着色器
        if self.fragment_shader:
            glDeleteShader(self.fragment_shader)
            self.fragment_shader = None

        # 删除着色器程序
        if self.shader:
            glDeleteProgram(self.shader)
            self.shader = None

        # 清空相关字典
        self.uniform_loc.clear()
        self.uniform_val.clear()
        self.uniform_type.clear()
        self.texture_val.clear()


class AutoSP:
    def __init__(self,
                 base_color: "Img",
                 normal: "list | tuple | Img" = (0.5, 0.5, 1),
                 emission: "list | tuple | Img" = (0, 0, 0),
                 double_side: bool = True,
                 max_light_count: int = 8,):
        """
        更具用户提供的参数自动生成ShaderProgram类，并在需要时自动调用ShaderProgram的类成员，作为表面着色器渲染时使用的顶点列表格式：
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
        """
        self.base_color = base_color
        self.normal = normal
        self.emission = emission
        self.double_side = double_side
        self.max_light_count = max_light_count

        # 生成着色器程序
        self.shader_program = self.create_shader_program()

        # 存储矩阵
        self.model_mat = glm.mat4(1.0)
        self.view_mat = glm.mat4(1.0)
        self.projection_mat = glm.mat4(1.0)

        # 注册到矩阵更新队列
        set_mat_queue[id(self)] = self

        soup3D.light.dirty = True

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
        self.model_mat = mat
        self.shader_program.uniform("model", soup3D.ARRAY_MATRIX_VEC4, 1, GL_FALSE, glm.value_ptr(self.model_mat))

    def set_view_mat(self, mat: glm.mat4):
        """
        设置投影矩阵，在变换矩阵时自动调用
        :param mat: 投影矩阵
        :return: None
        """
        self.view_mat = mat
        self.shader_program.uniform("view", soup3D.ARRAY_MATRIX_VEC4, 1, GL_FALSE, glm.value_ptr(self.view_mat))

    def set_projection_mat(self, mat: glm.mat4):
        """
        设置视图矩阵，在变换矩阵时自动调用
        :param mat: 视图矩阵
        :return: None
        """
        self.projection_mat = mat
        self.shader_program.uniform("projection", soup3D.ARRAY_MATRIX_VEC4, 1, GL_FALSE,
                                    glm.value_ptr(self.projection_mat))

    def set_light(self, light_queue):
        """
        设置光照，在添加、减少光照时自动调用
        :param light_queue: 光照列队
        :return: None
        """
        ambient = glGetFloatv(GL_LIGHT_MODEL_AMBIENT)[:3]
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

                    self.shader_program.uniform(f"lights[{light_count}].position", soup3D.FLOAT_VEC3, *light.place)
                    self.shader_program.uniform(f"lights[{light_count}].direction", soup3D.FLOAT_VEC3, *direction)
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
                    self.shader_program.uniform(f"lights[{light_count}].direction", soup3D.FLOAT_VEC3, *direction)
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

    def unuse(self):
        """
        停用该着色器，会在结束应用时自动调用
        :return: None
        """

        self.shader_program.unuse()

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


Img = Texture | MixChannel
GrayImg = Channel
Surface = ShaderProgram | AutoSP


if __name__ == '__main__':
    ...
