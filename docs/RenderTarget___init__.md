# RenderTarget.__init__

[返回上级](./RenderTarget.md)

**签名**: `__init__(width, height, color="rgba8", depth=False)`

创建渲染目标（要求 GL 上下文已就绪，即在 soup3D.init() 之后创建）。构造时完成 FBO 组装、完整性检查与清零，构造成功即保证可渲染：
- 颜色纹理：LINEAR 过滤 + CLAMP_TO_EDGE，构造后立即清零（保存/恢复清屏色与深度写掩码，不污染引擎全局清屏色）
- 深度附着（可选）：GL_DEPTH_COMPONENT24；"renderbuffer"（只作深度测试用）或 "texture"（可通过 rt.depth 采样）
- FBO 完整性检查失败抛 RuntimeError（附状态码与原因提示），失败时先恢复原 FBO 绑定再抛出

:param width:  宽（像素，正整数）
:param height: 高（像素，正整数）
:param color:  颜色附着格式："rgba8" / "rgba16f" / "rgba32f"
:param depth:  深度附着：False / "renderbuffer" / "texture"
:raises TypeError: 参数类型错误
:raises ValueError: 参数值超出约定
:raises RuntimeError: FBO 不完整（附状态码与原因提示）
:return: RenderTarget

## 示例

```python
soup3D.init(width=800, height=600)
rt = soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer")
with rt:
    soup3D.update(target=rt)
pixels = rt.to_pixels()          # (600, 800, 4) float32，顶原点行序
```
