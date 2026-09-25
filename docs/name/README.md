# name   


[返回上级](../README.md)   


调用：soup3D   
常量定义模块：集中定义引擎各处使用的字符串/数值常量，均可通过 `from soup3D import name` 后以 `name.XXX` 引用，也可直接书写等值字符串。   
所有常量按用途分组如下。   

## shape_type（绘制方式，传给 Face / ui.Shape 的 shape_type）   

- LINE_B = "line_b"：不相连线段   
- LINE_S = "line_s"：连续线段   
- LINE_L = "line_l"：头尾相连的连续线段   
- TRIANGLE_B = "triangle_b"：不相连三角形   
- TRIANGLE_S = "triangle_s"：相连三角形   
- TRIANGLE_L = "triangle_l"：头尾相连的连续三角形   

## vertex_type（OpenGL 数据类型，引擎内部类型映射表使用）   

- BYTE = "byte_s"：带符号 8 位整数   
- BYTE_US = "byte_u"：无符号 8 位整数   
- SHORT = "short_s"：带符号 16 位整数   
- SHORT_US = "short_u"：无符号 16 位整数   
- INT = "int_s"：带符号 32 位整数   
- INT_US = "int_u"：无符号 32 位整数   
- FLOAT_H = "float_h"：半精度浮点数   
- FLOAT = "float"：单精度浮点数   
- FLOAT_D = "double"：双精度浮点数   
- FIXED = "fixed"：定点数   

## uniform_type（传给 ShaderProgram.uniform 的 v_type）   

- FLOAT_VEC1~4 / INT_VEC1~4：标量与向量   
- ARRAY_FLOAT_VEC1~4 / ARRAY_INT_VEC1~4：数组类型   
- ARRAY_MATRIX_VEC2~4：矩阵数组类型（传矩阵给着色器）   

## bool（GL 常量 TRUE/FALSE）   

- TRUE / FALSE：GL_TRUE / GL_FALSE 数值常量   

## light_type（光源类型标识）   

- POINT = "point"：点光源（Cone）   
- DIRECT = "direct"：方向光源（Direct）   

## img_type（图像通道格式，传给 Texture 的 format）   

- RGB = "rgb"：红、绿、蓝三通道   
- RGBA = "rgba"：红、绿、蓝、不透明度四通道   

## wrap（纹理坐标越界处理，预留常量）   

- REPEAT = "repeat"：超出边缘后重复   
- MIRRORED = "mirrored"：超出边缘后镜像   
- EDGE = "edge"：超出边缘后延伸边缘颜色   

注：当前引擎纹理默认使用 repeat（Texture）或 edge（Texture.from_array 数据纹理），此组常量供自定义着色器类使用。   
- BORDER = "border"：超出边缘后填充边框色   

## resource（open_gltf 的 resources 参数取值）   

- MESH = "mesh"：网格   
- SKELETON = "skeleton"：骨架   
- ANIMATION = "animation"：动画   

## color（渲染目标颜色格式，传给 RenderTarget 的 color）   

- RGBA8 = "rgba8"：8 位精度 RGBA（uint8 回读）   
- RGBA16F / RGBA32F：半/全浮点格式（float32 回读，支持 HDR 自发光等中间结果）   
