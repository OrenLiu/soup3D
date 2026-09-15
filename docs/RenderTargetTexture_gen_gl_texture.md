# RenderTargetTexture.gen_gl_texture

[返回上级](./RenderTargetTexture.md)

**签名**: `gen_gl_texture(texture_unit)`

把已有纹理绑定到指定纹理单元（只绑定，不重新创建纹理）。

:param texture_unit: 纹理单元编号（int，非 bool）
:raises TypeError: texture_unit 类型错误
:return: None
