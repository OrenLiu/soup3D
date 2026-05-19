# Shape.__init__   
   
[返回上级](./Shape.md)   
   
**签名**: `__init__(self, shape_type, texture, vertex)`   
   
(已停止支持，建议使用full_display作为平替)   
图形，可以批量生成线段、三角形   
:param shape_type: 绘制方式，可以填写这些内容：   
                   "line_b": 不相连线段   
                   "line_s": 连续线段   
                   "line_l": 头尾相连的连续线段   
                   "triangle_b": 不相连三角形   
                   "triangle_s": 相连三角形   
                   "triangle_l": 头尾相连的连续三角形   
:param texture:    使用的纹理对象，默认为None   
:param vertex:     图形中所有的端点，每个参数的格式为：(x, y, u, v)   
   
