# BoneBinderSP.__init__   
   
[返回上级](./BoneBinderSP.md)   
   
**签名**: `__init__(self, base_color, normal, emission, double_side, max_light_count, shader_program, skeleton)`   
   
骨骼绑定着色器，作为表面着色器渲染时使用的顶点列表格式：   
[   
    ({name: weight, ...}, x, y, z, u, v) | ({name: weight, ...}, weight, x, y, z, u, v, nx, ny, nz),   
    ...   
]   
其中：   
   
name: 骨头字典中骨头对应的名称   
   
weight: 该骨头对应在该顶点上的权重   
   
未定义权重的名称对应的骨骼权重默认为0   
   
x, y, z: 顶点3维坐标   
   
u, v: 顶点对应的贴图uv坐标位置   
   
nx, ny, nz: 顶点法线偏移，默认为0   
   
:param base_color:      主要颜色   
:param normal:          自定义法线或法线贴图   
:param emission:        自发光度，   
                        当该参数为数字时，0.0为不发光，1.0为完全发光；   
                        当该参数为灰度图时，黑色为不发光，白色为完全发光   
:param double_side:     是否启用双面渲染   
:param max_light_count: 该着色器使用时会同时出现的最多的光源数量   
:param shader_program:  被AutoSP管理的着色器程序，若为None，则生成着色器程序。该参数为内部调用参数，可以但不建议直接使用该参数。   
:param skeleton:        一个Skeleton对象或包含多个骨头的字典，格式：{name: bone, name: bone, ...}   
   
