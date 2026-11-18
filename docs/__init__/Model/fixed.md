# Model.fixed   

[返回上级](./README.md)   

**签名**: `fixed(self)`   

将模型设为固定渲染模式。当模型长期不改变、固定在场景中时（如地图模型），调用本方法后模型的显示列表改按缓存渲染命令编译：编译前先预热触发 rend_cached 的缓冲创建/上传，列表内只录制「绑定缓存 VAO + 绘制」命令，逐帧 glCallList 重放零上传、零 Python 分派。   

表面着色器须支持 rend_cached（ShaderProgram / AutoSP 支持；骨骼绑定的 BoneBinderSP 顶点格式不同，不支持）。不支持时本方法静默不优化，模型照常渲染，成员 fixed_mode 记录实际是否生效，重新调用本方法可再次启用。   

性能说明：常规显示列表路径本身即由驱动在编译期完成一次缓冲创建与上传（重放不再上传），因此已 show() 的场景中本优化的帧数收益依驱动而定（实测环境两者持平）；直接逐帧调用 rend_cached（不经显示列表）的场景收益显著。   

契约与失效：顶点数据与表面视为静态；调用 paint、hide、goto、turn、turn_quat、size 后优化自动失效，模型退回常规显示列表路径（需要时会重建显示列表），重新调用 fixed() 可再次启用。   

## 示例

```python
model = soup3D.Model(0, 0, 0, face)
model.show()
model.fixed()    # 显示列表改按缓存渲染命令编译（成员 fixed_mode 变为 True）
```

- `:return`: None
