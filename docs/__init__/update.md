# update

[返回上级](./README.md)

**签名**: `update(render, target)`

更新画布（每帧调用）。三种调用形态：

```python
soup3D.update()                   # 1) 默认：渲到窗口
soup3D.update(render=my_renderer) # 2) 本帧画面输出交给自定义渲染器（实现 FrameRenderer 协议）
soup3D.update(target=rt)          # 3) 本帧渲进离屏渲染目标，不上屏
```

## 用 target= 做离屏渲染

```python
rt = soup3D.RenderTarget(800, 600, "rgba8", "renderbuffer")
soup3D.update(target=rt)        # 本帧场景原样渲进 rt（viewport 跟随目标尺寸）
pixels = rt.to_pixels()         # 取出像素做测试/后处理
```

## 用 render= 接管一帧

```python
def my_render(self):
    # 接管本帧全部画面输出（含清屏），可完全自定义绘制
    glClearColor(...)
    glClear(...)
    ...

soup3D.update(render=my_render)
```

## 注意

- `render` 与 `target` 同时传入抛 `ValueError`（互斥）。
- 传 None（即不传参）时与修改前行为逐像素一致。

- `:param render`: 帧级渲染器。
  传入后本帧全部画面输出（含清屏）交给该渲染器接管，
  引擎仅在其前后保存/恢复自身依赖的 GL 状态；
  None 时使用引擎内置默认渲染器
- `:param target`: 渲染目标（RenderTarget 实例）。传入后本帧默认渲染管线原样渲进该目标，
  viewport 跟随目标尺寸，不显示到窗口；与 render 同时传入抛 ValueError；None 时渲到窗口与修改前逐像素一致
- `:return`: None
