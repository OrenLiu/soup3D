# RenderTarget.to_pixels

[返回上级](./README.md)

**签名**: `to_pixels(self)`

回读颜色附着像素（顶原点行序，左上角为 pixels[0][0]），供测试与截图。
rgba8 回读 uint8，rgba16f/rgba32f 回读 float32（值域不限于 0~1）。

## 示例：保存为 PNG 截图

```python
import imageio.v2 as imageio

pixels = rt.to_pixels()                       # (height, width, 4) numpy 数组
imageio.imwrite("screenshot.png", pixels[:, :, :3])   # 通常只取 RGB 三通道存图
```

## 示例：浮点目标回读 HDR 值

```python
rt = soup3D.RenderTarget(800, 600, "rgba32f", "renderbuffer")
soup3D.update(target=rt)
pixels = rt.to_pixels()        # float32，亮度可大于 1.0，适合后续数值分析
print(pixels.max())            # HDR 场景可 > 1.0
```

- `:return`: (height, width, 4) numpy 数组；rgba8 为 uint8，浮点格式为 float32
