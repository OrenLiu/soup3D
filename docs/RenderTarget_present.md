# RenderTarget.present

[返回上级](./RenderTarget.md)

**签名**: `present()`

把颜色附着直通绘制到默认帧缓冲的当前 viewport 区域（支持缩放），不做任何色彩空间转换。使用引擎内置的共享直通着色器（惰性创建、全局复用），全屏三角形 + texture() 采样。

present 保存并恢复的状态：viewport、FBO 绑定、深度测试与混色开关、着色器程序、活动纹理单元与单元 0 的绑定。**矩阵栈不在保存/恢复范围内**。

## 示例

```python
rt = soup3D.RenderTarget(960, 540, "rgba16f")
with rt:
    soup3D.update(target=rt)
rt.present()   # 直通显示到窗口
soup3D.update()
```
