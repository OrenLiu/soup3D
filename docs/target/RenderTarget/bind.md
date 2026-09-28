# RenderTarget.bind

[返回上级](./README.md)

**签名**: `bind(self)`

绑定渲染目标：保存当前 viewport / FBO 绑定 / draw buffer 状态并切换到本目标，
viewport 跟随目标尺寸；不修改深度测试等 `soup3D.update` 依赖的绘制状态。

## 示例：手动 bind/unbind（不熟悉 OpenGL 状态机时建议用 with 语句）

```python
rt = soup3D.RenderTarget(512, 512, "rgba8", "renderbuffer")
rt.bind()
try:
    # 从这里开始，所有绘制写入 rt 而不是屏幕
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    my_draw_calls()                # 任何 OpenGL 绘制或 sp.rend(...)
finally:
    rt.unbind()                    # 必须恢复，否则后续画面会渲进 rt
```

## 注意事项

- bind 保存/恢复的是 **viewport / FBO 绑定 / draw buffer** 硬件状态，深度测试开关等绘制状态不受影响。
- 同一目标重复 bind 会抛 `RuntimeError`（防 bind/unbind 错配）。
- `soup3D.update(target=rt)` 内部自动完成 bind → 渲染 → unbind，此时无需手动调用本方法。
