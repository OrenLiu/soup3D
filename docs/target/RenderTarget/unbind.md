# RenderTarget.unbind

[返回上级](./README.md)

**签名**: `unbind(self)`

解绑渲染目标：恢复 bind() 保存的 viewport / FBO 绑定 / draw buffer 状态。
与 bind() 必须成对使用，未 bind 时调用会抛 `RuntimeError`。

## 示例

```python
rt = soup3D.RenderTarget(512, 512, "rgba8", "renderbuffer")
rt.bind()
try:
    my_draw_calls()      # 绘制写入 rt
finally:
    rt.unbind()          # 恢复原 viewport / FBO 绑定；之后绘制重新写入屏幕
```

## 注意事项

- 推荐优先用 `with` 语句（自动调用 __enter__/__exit__ 即 bind/unbind），可避免忘记 unbind：
  `with rt: ...`
- 多个渲染目标依次使用时，bind/unbind 可嵌套，恢复顺序与 bind 顺序相反（栈式恢复）。
