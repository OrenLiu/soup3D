# full_display

[返回上级](./README.md)

**签名**: `full_display(img)`

从下一帧开始全屏覆盖一张图像，可覆盖如 UI、标题画面、过场图等。
重复调用会替换当前覆盖图；配合 `soup3D.ui.clean_display()` 取消覆盖。

## 示例

```python
import soup3D.ui

# 从图片文件创建贴图并全屏覆盖（如标题画面）
tex = soup3D.shader.Texture("title.png")
soup3D.ui.full_display(tex)
...
soup3D.ui.clean_display()   # 取消覆盖，恢复 3D 场景显示
```

- `:param img`: 需要全屏显示的图像（Texture 或 MixChannel 实例）
- `:return`: None
