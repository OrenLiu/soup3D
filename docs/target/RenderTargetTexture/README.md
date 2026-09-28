# RenderTargetTexture

[返回上级](../README.md)

渲染目标附属纹理的包装对象（颜色/深度），通过 `RenderTarget.color` / `RenderTarget.depth` 访问，
实现 `gen_gl_texture(texture_unit)` 与 `get_texture_id()` 协议，可直接传入
`ShaderProgram.uniform_tex` 作为贴图采样。浮点颜色附着（rgba16f/rgba32f）同样以纹理形式被采样，无需特殊处理。

## 示例：后处理着色器采样场景颜色

```python
sp.uniform_tex("sceneTex", rt.color, 0)   # 第 0 号纹理单元
```

## 示例：采样场景深度（depth="texture" 时才有值）

```python
rt = soup3D.RenderTarget(800, 600, "rgba8", "texture")
sp.uniform_tex("depthTex", rt.depth, 1)   # 片段着色器里 texture(depthTex, uv).r 即深度
```

一般无需手动构造/调用本类方法——`uniform_tex` 内部会调用 `gen_gl_texture` 绑定纹理，
`get_texture_id` 供需要原生句柄的场合（如跨模块传递）。

## 方法

- [__init__(self, texture_id, width, height)](__init__.md): `函数`
- [gen_gl_texture(self, texture_unit)](gen_gl_texture.md): `函数`
- [get_texture_id(self)](get_texture_id.md): `函数`
