"""
处理soup3D中的渲染目标（RenderTarget/FBO）
渲染到纹理的帧缓冲抽象：场景可先渲进独立尺寸的离屏目标（含 rgba16f/rgba32f 浮点颜色），
再经 uniform_tex 采样或 present() 显示，供后处理、屏幕空间反射、光线追踪累积等
需要中间结果在多个渲染通道间流动的效果使用。
"""
from OpenGL.GL import *
import numpy as np

# 颜色格式映射：名称 -> (内部格式, 数据上传/回读类型, 回读 numpy dtype)
_COLOR_FORMATS = {
    "rgba8": (GL_RGBA8, GL_UNSIGNED_BYTE, np.uint8),
    "rgba16f": (GL_RGBA16F, GL_FLOAT, np.float32),
    "rgba32f": (GL_RGBA32F, GL_FLOAT, np.float32),
}

# present() 用的直通着色器：全屏三角形（gl_VertexID，无需顶点缓冲）
_PRESENT_VS = """#version 330 core
out vec2 UV;
void main() {
    vec2 pos = vec2(float((gl_VertexID << 1) & 2), float(gl_VertexID & 2));
    UV = pos;
    gl_Position = vec4(pos * 2.0 - 1.0, 0.0, 1.0);
}
"""

_PRESENT_FS = """#version 330 core
in vec2 UV;
out vec4 FragColor;
uniform sampler2D targetTex;
void main() {
    // 直通采样：不做任何色彩空间转换
    FragColor = texture(targetTex, UV);
}
"""

# 惰性创建的共享 present 着色器程序（模块级缓存；需在 GL 上下文就绪后创建）
_present_program = None


def _gl_scalar(value) -> int:
    """把 PyOpenGL 标量查询结果归一化为 int（不同绑定可能返回数组、numpy 标量或 int）"""
    try:
        return int(value[0])
    except (TypeError, IndexError):
        return int(value)


def _check_shader_compile(shader, kind):
    """检查着色器编译状态，失败抛异常"""
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(kind + " shader compile failed: " + str(glGetShaderInfoLog(shader)))


def _check_program_link(program):
    """检查着色器程序链接状态，失败抛异常"""
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError("shader program link failed: " + str(glGetProgramInfoLog(program)))


def _ensure_present_program() -> int:
    """
    惰性创建共享 present 着色器程序（重复调用只创建一次）
    :return: 程序句柄
    """
    global _present_program
    if _present_program is not None:
        return _present_program
    vs = glCreateShader(GL_VERTEX_SHADER)
    glShaderSource(vs, _PRESENT_VS)
    glCompileShader(vs)
    _check_shader_compile(vs, "vertex")
    fs = glCreateShader(GL_FRAGMENT_SHADER)
    glShaderSource(fs, _PRESENT_FS)
    glCompileShader(fs)
    _check_shader_compile(fs, "fragment")
    _present_program = int(glCreateProgram())
    glAttachShader(_present_program, vs)
    glAttachShader(_present_program, fs)
    glLinkProgram(_present_program)
    _check_program_link(_present_program)
    glDeleteShader(vs)
    glDeleteShader(fs)
    return _present_program


class RenderTargetTexture:
    """
    渲染目标附属纹理的包装对象（颜色/深度），实现 gen_gl_texture(texture_unit) 与
    get_texture_id() 协议，可直接传入 ShaderProgram.uniform_tex 作为贴图采样。
    浮点颜色附着（rgba16f/rgba32f）同样以纹理形式被采样，无需特殊处理。
    """

    def __init__(self, texture_id, width: int, height: int):
        """
        :param texture_id: GL 纹理句柄
        :param width:      纹理宽度
        :param height:     纹理高度
        :return: None
        """
        self.texture_id = texture_id
        self.width = width
        self.height = height

    def gen_gl_texture(self, texture_unit: int = 0):
        """
        把已有纹理绑定到指定纹理单元（不重新创建纹理，只是绑定）
        :param texture_unit: 纹理单元编号
        :return: None
        """
        if not isinstance(texture_unit, int) or isinstance(texture_unit, bool):
            raise TypeError("texture_unit must be an int")
        glActiveTexture(GL_TEXTURE0 + texture_unit)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)

    def get_texture_id(self):
        """
        获取纹理句柄
        :return: GL 资源句柄
        """
        return self.texture_id


class RenderTarget:
    """
    渲染目标（FBO + 颜色纹理 [ + 深度附着 ]），渲染到纹理的标准抽象。
    可作为上下文管理器使用：
        with soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer") as rt:
            soup3D.update(target=rt)
            pixels = rt.to_pixels()
    """

    def __init__(self, width, height, color="rgba8", depth=False):
        """
        创建渲染目标（要求 GL 上下文已就绪，即在 soup3D.init() 之后创建）
        :param width:  宽（像素，正整数）
        :param height: 高（像素，正整数）
        :param color:  颜色附着格式："rgba8" / "rgba16f" / "rgba32f"
        :param depth:  深度附着：False / "renderbuffer" / "texture"
        :raises TypeError: 参数类型错误
        :raises ValueError: 参数值超出约定
        :raises RuntimeError: FBO 不完整（附状态码与原因提示）
        :return: RenderTarget
        """
        # --- 参数校验 ---
        if not isinstance(width, int) or isinstance(width, bool):
            raise TypeError("width must be an int")
        if not isinstance(height, int) or isinstance(height, bool):
            raise TypeError("height must be an int")
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if color not in _COLOR_FORMATS:
            raise ValueError("color must be one of: " + ", ".join(sorted(_COLOR_FORMATS)))
        if depth not in (False, "renderbuffer", "texture"):
            raise ValueError('depth must be False, "renderbuffer" or "texture"')

        self.width = width
        self.height = height
        self._format = color
        self._depth_mode = depth
        self._bound = False
        self._saved_state = None

        internal_format, upload_type, read_dtype = _COLOR_FORMATS[color]

        # 颜色纹理
        self._color_tex = int(glGenTextures(1))
        glBindTexture(GL_TEXTURE_2D, self._color_tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, GL_RGBA, upload_type, None)

        # 颜色附着包装（实现 gen_gl_texture/get_texture_id 协议，供 uniform_tex 采样）
        self.color = RenderTargetTexture(self._color_tex, width, height)

        # 深度附着（可选）
        self._depth_rb = None
        self._depth_tex = None
        self.depth = None
        if depth == "renderbuffer":
            self._depth_rb = int(glGenRenderbuffers(1))
            glBindRenderbuffer(GL_RENDERBUFFER, self._depth_rb)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, width, height)
        elif depth == "texture":
            self._depth_tex = int(glGenTextures(1))
            glBindTexture(GL_TEXTURE_2D, self._depth_tex)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width, height, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_INT, None)
            self.depth = RenderTargetTexture(self._depth_tex, width, height)

        # FBO 组装与完整性检查
        self._fbo = int(glGenFramebuffers(1))
        prev_fbo = _gl_scalar(glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING))
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self._color_tex, 0)
        if self._depth_rb is not None:
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, self._depth_rb)
        elif self._depth_tex is not None:
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self._depth_tex, 0)
        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            # 恢复原绑定后再抛出，不遗留绑定状态
            glBindFramebuffer(GL_FRAMEBUFFER, prev_fbo)
            raise RuntimeError("RenderTarget FBO incomplete: status=0x%X (color=%s, depth=%s). "
                               "Float color formats (rgba16f/rgba32f) need float render target support"
                               % (status, color, depth))
        # 构造后立即清零（避免读到未初始化纹理内存；保存/恢复清屏色与深度写掩码，不污染引擎全局状态）
        prev_clear = glGetFloatv(GL_COLOR_CLEAR_VALUE)
        prev_mask = glGetBooleanv(GL_DEPTH_WRITEMASK)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDepthMask(GL_TRUE)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glDepthMask(prev_mask)
        glClearColor(*prev_clear)
        glBindFramebuffer(GL_FRAMEBUFFER, prev_fbo)

    def bind(self):
        """
        绑定渲染目标：保存当前 viewport / FBO 绑定 / draw buffer 状态并切换到本目标，
        viewport 跟随目标尺寸；不修改深度测试等绘制状态。
        """
        if self._bound:
            raise RuntimeError("RenderTarget is already bound")
        self._saved_state = (
            tuple(int(v) for v in glGetIntegerv(GL_VIEWPORT)),
            _gl_scalar(glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING)),
            _gl_scalar(glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING)),
            _gl_scalar(glGetIntegerv(GL_DRAW_BUFFER)),
            _gl_scalar(glGetIntegerv(GL_READ_BUFFER)),
        )
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glViewport(0, 0, self.width, self.height)
        self._bound = True

    def unbind(self):
        """
        解绑渲染目标：恢复 bind 保存的 viewport / FBO 绑定 / draw buffer 状态
        """
        if not self._bound:
            raise RuntimeError("RenderTarget is not bound")
        viewport, draw_fbo, read_fbo, draw_buf, read_buf = self._saved_state
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, draw_fbo)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, read_fbo)
        glDrawBuffer(draw_buf)
        glReadBuffer(read_buf)
        glViewport(viewport[0], viewport[1], viewport[2], viewport[3])
        self._bound = False
        self._saved_state = None

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unbind()
        return False

    def to_pixels(self):
        """
        回读颜色附着像素（顶原点行序），供测试与截图
        :return: (height, width, 4) numpy 数组；rgba8 为 uint8，浮点格式为 float32
        """
        _, read_type, read_dtype = _COLOR_FORMATS[self._format]
        prev_read_fbo = _gl_scalar(glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING))
        glBindFramebuffer(GL_READ_FRAMEBUFFER, self._fbo)
        raw = glReadPixels(0, 0, self.width, self.height, GL_RGBA, read_type)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, prev_read_fbo)
        arr = np.frombuffer(raw, dtype=read_dtype).reshape(self.height, self.width, 4)[::-1].copy()
        return arr

    def present(self):
        """
        把颜色附着直通绘制到默认帧缓冲的当前 viewport 区域（支持缩放），
        不做任何色彩空间转换。
        """
        prog = _ensure_present_program()
        # 保存状态
        prev_viewport = tuple(int(v) for v in glGetIntegerv(GL_VIEWPORT))
        prev_draw_fbo = _gl_scalar(glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING))
        prev_read_fbo = _gl_scalar(glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING))
        prev_depth = glIsEnabled(GL_DEPTH_TEST)
        prev_blend = glIsEnabled(GL_BLEND)
        prev_program = _gl_scalar(glGetIntegerv(GL_CURRENT_PROGRAM))
        prev_active_tex = _gl_scalar(glGetIntegerv(GL_ACTIVE_TEXTURE))
        prev_unit0_tex = _gl_scalar(glGetIntegerv(GL_TEXTURE_BINDING_2D))
        # 切换到默认帧缓冲，直通绘制全屏三角形
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glUseProgram(prog)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._color_tex)
        glUniform1i(glGetUniformLocation(prog, "targetTex"), 0)
        glDrawArrays(GL_TRIANGLES, 0, 3)
        # 恢复状态
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, prev_unit0_tex)
        glActiveTexture(prev_active_tex)
        glUseProgram(prev_program)
        if prev_depth:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)
        if prev_blend:
            glEnable(GL_BLEND)
        else:
            glDisable(GL_BLEND)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, prev_draw_fbo)
        glBindFramebuffer(GL_READ_FRAMEBUFFER, prev_read_fbo)
        glViewport(prev_viewport[0], prev_viewport[1], prev_viewport[2], prev_viewport[3])

    def __del__(self):
        # GL 上下文可能在对象销毁前已释放，删除失败时静默处理（参照 Texture.__del__）
        try:
            if self._fbo is not None:
                glDeleteFramebuffers([self._fbo])
            if self._depth_rb is not None:
                glDeleteRenderbuffers([self._depth_rb])
            if self._color_tex is not None:
                glDeleteTextures([self._color_tex])
            if self._depth_tex is not None:
                glDeleteTextures([self._depth_tex])
        except Exception:
            pass
