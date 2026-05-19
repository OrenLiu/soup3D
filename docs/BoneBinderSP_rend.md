# BoneBinderSP.rend   
   
[返回上级](./BoneBinderSP.md)   
   
**签名**: `rend(self, mode, vertex)`   
   
创建该着色器的渲染流程   
:param mode:   绘制方式   
:param vertex: 表面中所有的顶点，格式：   
               [   
                   ({name: weight, ...}, x, y, z, u, v) | ({name: weight, ...}, weight, x, y, z, u, v, nx, ny, nz),   
                   ...   
               ]   
:return: None   
   
