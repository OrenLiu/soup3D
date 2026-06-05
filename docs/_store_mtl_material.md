# _store_mtl_material   
   
[返回上级](./__init__.md)   
   
**签名**: `_store_mtl_material(width, height, R, G, B, A, emission, bump_texture, double_side, max_light_count, surface)`   
   
将材质数据存储为数据字典，用于data_only模式   
:param width:           纹理宽度   
:param height:          纹理高度   
:param R:               红色通道值   
:param G:               绿色通道值   
:param B:               蓝色通道值   
:param A:               透明度通道值   
:param emission:        自发光数据   
:param bump_texture:    法线贴图数据   
:param double_side:     是否启用双面渲染   
:param max_light_count: 最大光源数量   
:param surface:         表面着色器类型   
:return: 材质数据字典   
   
