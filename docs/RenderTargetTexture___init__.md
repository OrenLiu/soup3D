# RenderTargetTexture.__init__

[返回上级](./RenderTargetTexture.md)

**签名**: `__init__(texture_id, width, height)`

把 GL 纹理句柄包装为渲染目标附属纹理对象。

:param texture_id: GL 纹理句柄
:param width:      纹理宽度
:param height:     纹理高度
:return: RenderTargetTexture

成员 texture_id/width/height 公开可读，外部不应直接改写。
