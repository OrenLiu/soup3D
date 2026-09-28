# ShaderProgram.uniform_tex   
   
[返回上级](./README.md)   
   
**签名**: `uniform_tex(self, v_name, texture, texture_unit)`   
   
在下一帧向着色器传递纹理
:param v_name:       在着色器内该纹理对应的变量名
:param texture:      贴图类（Texture / MixChannel / RenderTargetTexture，如 RenderTarget.color）
:param texture_unit: 纹理单元编号
:return: 是否成功添加纹理

## 示例：普通贴图

```python
sp.uniform_tex("base_color", soup3D.shader.Texture("wood.png"), 0)
```

## 示例：采样渲染目标（与 target 模块联动）

```python
# rt 是 RenderTarget；rt.color 是 RenderTargetTexture，直接当贴图传
sp.uniform_tex("sceneTex", rt.color, 0)
# depth="texture" 创建的目标还可采样深度：
sp.uniform_tex("depthTex", rt.depth, 1)
```
   
