# RenderTarget.bind / unbind

[返回上级](./RenderTarget.md)

**签名**: `bind()` / `unbind()`

手动管理渲染目标绑定（推荐直接用 `with` 语句，自动解绑）。bind 保存当前状态并切换到本目标；unbind 恢复 bind 保存的状态。重复 bind（已绑定时）或未绑定时 unbind 抛 RuntimeError。

**保存/恢复范围**：viewport（跟随目标尺寸）、FBO 绑定（draw + read）、draw buffer 与 read buffer 配置。

**不在保存/恢复范围内**：深度测试、混色、着色器程序绑定、矩阵栈等绘制状态——调用方按需自行管理。例如自定义渲染器里建议在光栅化 pass 前 `glDisable(GL_BLEND)`，结束时恢复。

## 示例

```python
rt.bind()
try:
    soup3D.update(target=rt)   # 或自定义 GL 绘制
finally:
    rt.unbind()
```
