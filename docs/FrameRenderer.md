# FrameRenderer

[返回上级](./__init__.md)

帧级渲染器协议（Protocol）。实现 `on_frame` 方法的对象即视为实现该协议，通过 `update(render=渲染器对象)` 传入后接管一帧的完整画面输出（含清屏）。

## 协议要点

- 引擎在 on_frame 前后保存/恢复自身依赖的 GL 状态（BLEND、深度测试、清屏色、viewport、FBO 绑定，glPushAttrib(GL_ALL_ATTRIB_BITS) + FBO 单独保存）。
- **矩阵栈与着色器程序绑定不在恢复范围内**——渲染器内部切 program 时必须在结束时恢复（或保证下一使用者自行 use），矩阵修改同理。
- 自定义帧不会自动消费 render_queue / EAU：单帧模型与更新回调的处置权在渲染器，可在 on_frame 内调用 `soup3D.update()` 复用默认渲染主体。
- 渲染器可访问的数据：相机（`soup3D.camera.X/Y/Z`、`QUAT`、`proj_fov`）、场景（`stable_shapes` / `render_queue` 中的模型，Model.face_groups 按表面分组的面数据，材质 Kd=surface.base_color，Ke=surface.emission）。

## 协议方法

**签名**: `on_frame() -> None`

接管本帧全部画面输出，包括清屏。

## 示例

```python
class MyRenderer:
    def on_frame(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # 自定义管线（可调用 soup3D.update() 复用默认渲染主体）
        ...
soup3D.update(render=MyRenderer())
```
