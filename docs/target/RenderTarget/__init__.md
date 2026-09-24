# RenderTarget.__init__   
   
[返回上级](./README.md)   
   
**签名**: `__init__(self, width, height, color, depth)`   
   
创建渲染目标（要求 GL 上下文已就绪，即在 soup3D.init() 之后创建）   
:param width:  宽（像素，正整数）   
:param height: 高（像素，正整数）   
:param color:  颜色附着格式："rgba8" / "rgba16f" / "rgba32f"   
:param depth:  深度附着：False / "renderbuffer" / "texture"   
:raises TypeError: 参数类型错误   
:raises ValueError: 参数值超出约定   
:raises RuntimeError: FBO 不完整（附状态码与原因提示）   
:return: RenderTarget   
   
