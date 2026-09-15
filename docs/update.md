# update

[返回上级](./__init__.md)

**签名**: `update(render=None, target=None)`

更新画布。

- `render=None, target=None`：默认渲染管线（清屏+EAU 回调+固定/单帧模型+UI），与修改前 update() 逐像素一致
- `target=<RenderTarget>`：本帧默认管线原样渲进该目标，viewport 跟随目标尺寸，不显示到窗口
- `render=<FrameRenderer>`:本帧全部画面输出（含清屏）交给渲染器接管；引擎仅在其前后保存/恢复自身依赖的 GL 状态（BLEND、深度测试、清屏色、viewport、FBO 绑定）。**矩阵栈与着色器程序绑定不在恢复范围内**——渲染器内部切了 program/矩阵的，结束时必须自行恢复
- render 与 target 同时传抛 ValueError
- 自定义帧不会自动消费 render_queue / EAU（处置权在渲染器，可在 on_frame 内调 soup3D.update() 复用默认渲染主体）

:param render: 帧级渲染器（实现 FrameRenderer 协议：有 on_frame 方法即可）；None 时使用引擎内置默认渲染器
:param target: RenderTarget 实例；None 时渲到窗口
:raises ValueError: render 与 target 同时传入
:return: None
