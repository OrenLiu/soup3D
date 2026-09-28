# Model.paint

[返回上级](./README.md)

**签名**: `paint(self)`

在单帧绘制该模型（加入 render_queue 单帧队列，只在下一帧渲染一次，之后自动移除，无需 hide）。

## show 与 paint 的区别

```python
scene = soup3D.Model(0, 0, 0, face)
scene.show()     # 每帧都渲染（场景、角色等长期对象）

spark = soup3D.Model(0, 0, 0, spark_face)
spark.paint()    # 只渲染一帧（粒子、火花等短命对象），下帧自动消失
```

- `:return`: show/paint 都返回 None
