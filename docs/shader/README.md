# shader   
   
[返回上级](../README.md)   
   
处理soup3D中的着色系统   
模块内类分层：底层 ShaderProgram（GLSL 程序封装）← AutoSP（表面着色器，按纹理描述自动生成 GLSL）← BoneBinderSP（骨骼蒙皮扩展）。   
   
## 类   
   
- [Texture](Texture/README.md): `类型`   
- [Channel](Channel/README.md): `类型`   
- [MixChannel](MixChannel/README.md): `类型`   
- [UniformBuffer](UniformBuffer/README.md): `类型`   
- [ShaderProgram](ShaderProgram/README.md): `类型`   
- [AutoSP](AutoSP/README.md): `类型`   
- [BoneBinderSP](BoneBinderSP/README.md): `类型`   
   
## 函数   
   
- [get_surface_params](get_surface_params.md): `函数`   
- [filter_surface_params](filter_surface_params.md): `函数`   
- [make_surface](make_surface.md): `函数`   
   
## 类型别名   
   
shader.py 末尾定义了三个类型别名（联合类型，非基类），供类型标注使用：   
   
- Img = Texture | MixChannel：可作为贴图使用的图像对象   
- GrayImg = Channel：可作为灰度通道使用的对象   
- Surface = ShaderProgram | AutoSP：「表面着色器」的统一类型标注；BoneBinderSP 继承 AutoSP，同样满足 Surface。   
  Face 的 surface 参数、make_surface() 的返回值等处均以 Surface 为类型标注   
   
## SURFACE_MATERIAL_PARAMS（标准材质参数契约）   
   
模型文件加载器（open_obj / open_mtl / open_gltf）与自定义表面着色器类的适配契约：   
加载器会尽量提供 SURFACE_MATERIAL_PARAMS 中的参数（键名即参数名），   
表面着色器类按需声明接收其中的任意子集，make_surface() 按类签名过滤后实例化。   
详见 [make_surface](make_surface.md)。   
   
- 参数名：base_color, normal, emission, double_side, max_light_count, roughness, metallic, ior, transmission, shininess, illum

## 最小示例：纯色三角形模型

```python
import soup3D
import soup3D.shader

# MixChannel 描述纯色，AutoSP 按它自动生成着色器
sp = soup3D.shader.AutoSP(soup3D.shader.MixChannel((1, 1), 0.9, 0.2, 0.2))
face = soup3D.Face("triangle_b", sp, [
    (-1, -1, -3, 0, 0),
    (1, -1, -3, 0, 0),
    (0, 1, -3, 0, 0),
])
model = soup3D.Model(0, 0, 0, face)
model.show()
```   
