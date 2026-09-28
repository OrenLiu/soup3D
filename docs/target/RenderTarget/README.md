# RenderTarget

[返回上级](../README.md)

渲染目标（FBO + 颜色纹理 [+ 深度附着]），渲染到纹理的标准抽象。
可作为上下文管理器使用：

```python
with soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer") as rt:
    soup3D.update()            # FBO 已绑定到 rt，本帧渲进 rt；也可用 update(target=rt)
    pixels = rt.to_pixels()
```

## 两种使用方式

- **配合 `soup3D.update(target=rt)`**（推荐）：本帧默认渲染管线原样渲进目标，无需手动 bind/unbind（update 内部自动 bind/unbind）。
- **配合 `with` 语句**：用于自己控制绘制（如后处理通道、读深度），块内可调用任何 OpenGL 绘制（或 `ShaderProgram.rend`），退出时自动恢复 viewport 等状态。

## 颜色格式与深度模式怎么选

| 需求 | color | depth |
|------|-------|-------|
| 普通离屏渲染、后处理中转、截图 | `"rgba8"` | `"renderbuffer"`（场景含 3D 几何时） |
| HDR 累积（光线追踪、泛光素材）、亮度可超 1.0 | `"rgba16f"` / `"rgba32f"` | `"renderbuffer"` |
| 后续通道需要采样**深度**（SSR、深度雾、光线步进） | 按上两行选 | `"texture"` |

浮点格式的渲染需要显卡支持浮点渲染目标（桌面 OpenGL 3.3 一般都支持）。

## 方法

- [__init__(self, width, height, color, depth)](__init__.md): `函数`
- [bind(self)](bind.md): `函数`
- [unbind(self)](unbind.md): `函数`
- [__enter__(self)](__enter__.md): `函数`
- [__exit__(self, exc_type, exc_val, exc_tb)](__exit__.md): `函数`
- [to_pixels(self)](to_pixels.md): `函数`
- [present(self)](present.md): `函数`
- [__del__(self)](__del__.md): `函数`
