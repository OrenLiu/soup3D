# open_gltf   
   
[返回上级](./__init__.md)   
   
**签名**: `open_gltf(gltf, double_side, max_light_count, surface, skin, data_only)`   
   
从gltf文件导入模型和骨骼   
:param gltf:            gltf模型文件路径   
:param double_side:     是否启用双面渲染   
:param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题   
:param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side,max_light_count等参   
                        数   
:param skin:            模型使用的蒙皮着色器类型，着色器需要有skeleton, base_color, emission, normal, double_side,   
                        max_light_count等参数   
:param data_only:       是否只创建模型和骨骼的数据结构，当为True时，则返回模型相关的数据，而不是模型和骨骼本身。当需要用一个文件创建多个   
                        独立的模型时，则将该值设为True。   
:return: (模型数据(Model类), 骨架数据(Skeleton类))   
   
