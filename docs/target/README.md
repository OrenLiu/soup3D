# target

[返回上级](../README.md)

调用：`soup3D.target`（常用入口：顶层别名 `soup3D.RenderTarget`）

处理soup3D中的渲染目标（RenderTarget/FBO）
渲染到纹理的帧缓冲抽象：场景可先渲进独立尺寸的离屏目标（含 rgba16f/rgba32f 浮点颜色），
再经 uniform_tex 采样或 present() 显示，供后处理、屏幕空间反射、光线追踪累积等
需要中间结果在多个渲染通道间流动的效果使用。

## 术语速查

- **FBO**（帧缓冲对象，Framebuffer Object）：OpenGL 中"往哪画"的开关。绑定一个 FBO 后，画面写入它附着的纹理而不是屏幕。
- **附着**（attachment）：挂在 FBO 上的纹理/缓冲。本模块每个渲染目标固定有 1 个颜色附着，可选 1 个深度附着。
- **渲染到纹理**（Render To Texture）：先把 3D 场景画成一张"图片"（纹理），后续通道再把这张图片当作素材加工。

## 类

- [RenderTargetTexture](RenderTargetTexture/README.md): 渲染目标附属纹理的包装，可传入 `ShaderProgram.uniform_tex` 当贴图采样。
- [RenderTarget](RenderTarget/README.md): 渲染目标本体，建议配合 `with` 语句或 `soup3D.update(target=...)` 使用。

## 典型工作流

```
soup3D.update(target=rt_a)                # 第 1 通道：场景渲进 rt_a（不上屏）
sp.uniform_tex("sceneTex", rt_a.color, 0) # 第 2 通道：把 rt_a 的颜色当贴图
with rt_b:                                # 后处理结果渲进 rt_b
    sp.rend(GL_TRIANGLES, [...])
rt_b.present()                            # 显示到窗口（或 rt_b.to_pixels() 回读）
```

## 最小示例：离屏渲染一帧并取出像素

```python
import soup3D

# 在 soup3D.init(...) 之后创建（GL 上下文就绪后才能创建）
rt = soup3D.RenderTarget(800, 600, "rgba8", "renderbuffer")

soup3D.update(target=rt)          # 本帧场景渲进 rt，窗口不显示
pixels = rt.to_pixels()           # (600, 800, 4) uint8 数组，行序为顶原点，可直接存图
```

## 最小示例：后处理链

```python
import OpenGL.GL as gl
import soup3D
import soup3D.shader

# 1) 场景渲进 rt_a
rt_a = soup3D.RenderTarget(800, 600, "rgba8", "renderbuffer")
soup3D.update(target=rt_a)

# 2) 用自定义着色器对 rt_a 的颜色做灰度处理，结果写进 rt_b
sp = soup3D.shader.ShaderProgram(GRAY_VS, GRAY_FS, vbo_type="float")
sp.uniform_tex("sceneTex", rt_a.color, 0)   # RenderTargetTexture 可直接当贴图
rt_b = soup3D.RenderTarget(800, 600, "rgba8")
with rt_b:                                   # bind + rend + unbind 一气呵成
    sp.rend(gl.GL_TRIANGLES, [fullscreen_triangle])

# 3) 把 rt_b 直通显示到窗口（之后记得 pygame.display.flip() 真正上屏）
rt_b.present()
```
