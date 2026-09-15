# RenderTargetTexture

[返回上级](./render_target.md)

渲染目标附属纹理的包装对象（颜色/深度附着），实现 `gen_gl_texture(texture_unit)` 与 `get_texture_id()` 协议，可直接传入 ShaderProgram.uniform_tex 作为贴图采样。浮点附着（rgba16f/rgba32f）同样以纹理形式被采样，无需特殊处理。

## 成员变量

- `texture_id` / `width` / `height`

## 方法

- [__init__(texture_id, width, height)](./RenderTargetTexture___init__.md)
- [gen_gl_texture(texture_unit)](./RenderTargetTexture_gen_gl_texture.md)：把已有纹理绑定到指定纹理单元（只绑定，不重新创建）
- [get_texture_id()](./RenderTargetTexture_get_texture_id.md)：获取纹理句柄
