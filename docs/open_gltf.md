# open_gltf   
   
[返回上级](./__init__.md)   
   
**签名**: `open_gltf(gltf, double_side, max_light_count, surface, skin)`   
   
从gltf文件导入模型和骨骼   
:param gltf:            gltf模型文件路径   
:param double_side:     是否启用双面渲染   
:param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题   
:param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side,max_light_count等参   
                        数   
:param skin:            模型使用的蒙皮着色器类型，着色器需要有skeleton, base_color, emission, normal, double_side,   
                        max_light_count等参数   
:return: (模型数据(Model类), 骨架数据(Skeleton类))   
   
