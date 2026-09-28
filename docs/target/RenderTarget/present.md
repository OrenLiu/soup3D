# RenderTarget.present

[返回上级](./README.md)

**签名**: `present(self)`

把颜色附着直通绘制到默认帧缓冲的当前 viewport 区域（支持缩放），不做任何色彩空间转换。
绘制走内置的直通着色器（内部自动创建并缓存），并保存/恢复 GL 状态，可安全穿插在渲染循环中调用。

## 示例：把离屏结果上屏

```python
soup3D.update(target=rt)     # 场景渲进 rt，窗口黑屏
rt.present()                 # rt 内容直通绘制到窗口后备缓冲
pygame.display.flip()        # 真正上屏（present 只画到后备缓冲）
```

## 示例：后处理链最后一步上屏

```python
soup3D.update(target=rt_a)                 # 1) 场景渲进 rt_a
sp.uniform_tex("sceneTex", rt_a.color, 0)  # 2) 后处理着色器采样 rt_a
with rt_b:
    sp.rend(GL_TRIANGLES, [tri])           #    结果写进 rt_b
rt_b.present()                             # 3) 显示后处理结果
pygame.display.flip()
```

## 注意

- 显示区域/缩放由当前 viewport 决定，先 `soup3D.resize(w, h)` 可控制显示尺寸。
- 不做色彩空间转换：浮点目标的 HDR 值会被直接截断到 0~1。
- 之后记得 `pygame.display.flip()` 才真正上屏。
