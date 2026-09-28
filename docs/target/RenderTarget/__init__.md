# RenderTarget.__init__

[返回上级](./README.md)

**签名**: `__init__(self, width, height, color, depth)`

创建渲染目标（要求 GL 上下文就绪，即在 `soup3D.init()` 之后创建）。
构造完成后即可绑定绘制；构造时会自动清零（首次 `to_pixels()` 不会读到未初始化内存）。

```python
import soup3D

# 最常用：离屏渲染 + 深度测试，适合后处理中转、截图
rt = soup3D.RenderTarget(800, 600, "rgba8", "renderbuffer")

# HDR 累积（光线追踪、泛光素材）：颜色可超 1.0，回读得到 float32
rt_hdr = soup3D.RenderTarget(800, 600, "rgba16f")

# 需要在后续通道里采样深度（SSR、深度雾、光线步进）时
rt_depth = soup3D.RenderTarget(800, 600, "rgba8", "texture")
print(rt_depth.depth)   # RenderTargetTexture，可传给 uniform_tex 采样；其他模式为 None
```

- `:param width`:  宽（像素，正整数）
- `:param height`: 高（像素，正整数）
- `:param color`:  颜色附着格式："rgba8" / "rgba16f" / "rgba32f"（选型见类 README 的表格）
- `:param depth`:  深度附着：False / "renderbuffer" / "texture"（False 适合纯颜色后处理通道；"renderbuffer" 适合需要深度测试的 3D 场景；"texture" 需要采样深度时用）
- `:raises TypeError`: 参数类型错误
- `:raises ValueError`: 参数值超出约定（尺寸非正整数、格式名不合法等）
- `:raises RuntimeError`: FBO 不完整（附状态码与原因提示）；浮点格式需要显卡支持浮点渲染目标
- `:return`: RenderTarget
