# RenderTargetTexture.gen_gl_texture

[返回上级](./README.md)

**签名**: `gen_gl_texture(self, texture_unit)`

把已有纹理绑定到指定纹理单元（不重新创建纹理，只是绑定）。
`ShaderProgram.uniform_tex` 内部调用它把渲染目标的颜色/深度附着绑定到采样单元，
一般无需手动调用。

- `:param texture_unit`: 纹理单元编号
- `:return`: None
