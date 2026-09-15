# render_target

[返回上级](./README.md)

处理 soup3D 中的渲染目标（RenderTarget/FBO）。渲染到纹理的帧缓冲抽象：场景可先渲进独立尺寸的离屏目标（含 rgba16f/rgba32f 浮点颜色），再经 uniform_tex 采样或 present() 显示，供后处理、屏幕空间反射、光线追踪累积等需要中间结果在多个渲染通道间流动的效果使用。

## 模块成员

- [RenderTarget](./RenderTarget.md): 渲染目标（FBO + 颜色纹理 [+ 深度附着]）
- [RenderTargetTexture](./RenderTargetTexture.md): 渲染目标附属纹理包装（颜色/深度附着），可直接传入 uniform_tex 采样
- `_ensure_present_program`：内部函数，惰性创建共享 present 直通着色器程序（不在公共 API 内）

## 渲染到纹理的最小示例

```python
import soup3D
import soup3D.render_target

soup3D.init(width=800, height=600)
rt = soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer")
with rt:
    soup3D.update(target=rt)
pixels = rt.to_pixels()          # (600, 800, 4) float32，顶原点行序
rt.present()                     # 或把结果直通显示到窗口
soup3D.update()
```

浮点颜色附着（rgba16f/rgba32f）需要 GL 上下文支持浮点渲染目标（桌面 GL 3.3 均支持）。
