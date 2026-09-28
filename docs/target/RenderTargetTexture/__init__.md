# RenderTargetTexture.__init__

[返回上级](./README.md)

**签名**: `__init__(self, texture_id, width, height)`

一般无需手动构造本类：`RenderTarget.color` 与 `RenderTarget.depth`
（depth="texture" 时）就是现成的 RenderTargetTexture 实例。

- `:param texture_id`: GL 纹理句柄
- `:param width`:      纹理宽度
- `:param height`:     纹理高度
- `:return`: None
