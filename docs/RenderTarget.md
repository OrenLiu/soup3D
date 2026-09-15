# RenderTarget

[返回上级](./render_target.md)

渲染目标（FBO + 颜色纹理 [+ 深度附着]），渲染到纹理的标准抽象。场景先渲进独立尺寸的离屏目标，再经 uniform_tex 采样或 present() 显示。

支持 `with` 语句自动解绑：

```python
with soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer") as rt:
    soup3D.update(target=rt)
    pixels = rt.to_pixels()
```

## 成员变量

- `width` / `height`：目标尺寸（只读使用）
- `color`：颜色附着（[RenderTargetTexture](./RenderTargetTexture.md)），可直接传入 `ShaderProgram.uniform_tex` 作为贴图采样
- `depth`：深度附着（仅 depth="texture" 时非 None，同样可采样）

## 方法

- [\_\_init\_\_(width, height, color, depth)](./RenderTarget___init__.md)
- [bind()](./RenderTarget_bind.md) / [unbind()](./RenderTarget_unbind.md)：手动管理绑定，保存/恢复 viewport、FBO 绑定与 draw/read buffer 状态；不修改深度测试等绘制状态
- [to_pixels()](./RenderTarget_to_pixels.md)：回读颜色附着像素（顶原点行序）
- [present()](./RenderTarget_present.md)：把颜色附着直通显示到默认帧缓冲当前 viewport 区域（支持缩放）
