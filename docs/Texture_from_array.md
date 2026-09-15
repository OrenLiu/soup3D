# Texture.from_array

[返回上级](./Texture.md)

**签名**: `from_array(arr, color=None)`（classmethod）

从 numpy 数组创建数据纹理，立即创建 GL 纹理对象（要求 GL 上下文就绪，即在 soup3D.init() 之后调用）。

## 参数与推断规则

- `arr`：2D (h, w) 或 3D (h, w, c) 的 uint8/float32 数组。**shape[0] 是高度、shape[1] 是宽度**（numpy 图像惯例，数组第 0 行为图像顶行，与 RenderTarget.to_pixels / present 方向一致）
- dtype 推断：uint8 → 8bit 格式；float32 → 32f 格式；其他 dtype 抛 ValueError（float64 需先 astype(np.float32)）
- `color=None` 时按通道数推断：4 通道 → rgba*，3 通道 → rgb*，1 通道 → uint8 为 l8 / float32 为 r32f
- `color` 显式指定（如浮点数据指定 rgba16f）时与通道数不匹配抛 ValueError
- 采样参数固定为 NEAREST + CLAMP_TO_EDGE、无 mipmap（数据纹理不做插值与越界重复）
- 上传前临时设 GL_UNPACK_ALIGNMENT=1 并恢复；数组非连续内存自动 ascontiguousarray
- uniform_tex 每帧重绑走 gen_gl_texture 的幂等分支（已创建过则只绑定，防纹理泄漏）

## 示例

```python
soup3D.init(width=800, height=600)
# 一维数据表：宽 N 高 1 的 rgba32f（texelFetch ivec2(i, 0) 读取）
table = np.zeros((1, 256, 4), dtype=np.float32)
tex = soup3D.shader.Texture.from_array(table)
```
