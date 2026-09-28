# RenderTarget.__enter__

[返回上级](./README.md)

**签名**: `__enter__(self)`

上下文管理器入口：调用 bind() 把渲染切换到本目标（保存并替换 viewport / FBO 绑定），并返回自身。

## 示例

```python
rt = soup3D.RenderTarget(512, 512, "rgba8", "renderbuffer")
with rt:                      # 进入时自动调用 bind()
    soup3D.update()           # 或任何绘制调用，画面写入 rt
# 离开时自动调用 unbind()，恢复正常渲染
```

- `:return`: RenderTarget，即目标自身
