# Face.__init__   
   
[返回上级](./Face.md)   
   
**签名**: `__init__(self, shape_type, surface, vertex)`   
   
表面，可用于创建模型(Model类)的线段和多边形   
:param shape_type: 绘制方式，可以填写这些内容：   
                   "line_b": 不相连线段   
                   "line_s": 连续线段   
                   "line_l": 头尾相连的连续线段   
                   "triangle_b": 不相连三角形   
                   "triangle_s": 相连三角形   
                   "triangle_l": 头尾相连的连续三角形   
:param surface:    表面使用的着色器   
:param vertex:     表面中所有的顶点，格式由surface参数指定的着色器决定   
   
