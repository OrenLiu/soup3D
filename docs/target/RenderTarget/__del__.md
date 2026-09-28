# RenderTarget.__del__

[返回上级](./README.md)

**签名**: `__del__(self)`

清理渲染目标的全部 GL 资源（FBO、颜色纹理、深度 renderbuffer / 深度纹理）。
GL 上下文可能在对象销毁前已释放（如解释器关闭期），删除失败时静默。

## 示例：手动提前释放

```python
rt = soup3D.RenderTarget(800, 600, "rgba8", "renderbuffer")
...  # 使用
del rt          # 引用计数归零时触发 __del__，立即释放 GL 资源
```

- `:return`: None
