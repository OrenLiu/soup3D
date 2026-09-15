# RenderTarget.to_pixels

[返回上级](./RenderTarget.md)

**签名**: `to_pixels() -> numpy.ndarray`

回读颜色附着像素，供测试与截图。

- 返回 `(height, width, 4)` 的 numpy 数组，rgba8 目标为 uint8，rgba16f/rgba32f 为 float32
- **顶原点行序**：数组第 0 行为图像顶行，与 Texture.from_array / present 的方向一致
- 回读期间临时切 READ_FRAMEBUFFER 到本目标并恢复，不改变其他状态

## 示例

```python
with soup3D.RenderTarget(64, 64, "rgba8") as rt:
    soup3D.update(target=rt)
    px = rt.to_pixels()
    print(px.shape)   # (64, 64, 4)
```
