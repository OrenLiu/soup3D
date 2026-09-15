# DefaultFrameRenderer

[返回上级](./__init__.md)

**签名**: `DefaultFrameRenderer()`

引擎内置默认渲染器：原 update() 的渲染主体（清屏+EAU 回调+固定/单帧模型渲染+UI 队列+全屏叠加图像）原样迁入，`update(render=None)` 时调用其 on_frame，与修改前的 update() 逐像素一致。

## 方法

**签名**: `on_frame() -> None`

执行默认渲染主体。引擎 update(render=None) 时调用，一般不直接调用。
