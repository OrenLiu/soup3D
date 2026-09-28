# Model.show

[返回上级](./README.md)

**签名**: `show(self)`

固定每帧渲染该模型（加入 stable_shapes 持久队列，直到 hide() 才停止渲染）。

## 示例

```python
face = soup3D.Face("triangle_b", surface, vertices)
model = soup3D.Model(0, 0, 0, face)
model.show()      # 之后每帧 update() 都会渲染它
...
model.hide()      # 不再显示（从持久队列移除）
```

- `:return`: None
