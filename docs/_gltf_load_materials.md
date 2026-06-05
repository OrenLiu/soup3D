# _gltf_load_materials   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_load_materials(gltf_data, base_dir, double_side, max_light_count, surface, data_only)`   
   
加载GLTF材质，返回材质索引到着色器的映射   
:param gltf_data:      GLTF JSON数据   
:param base_dir:       GLTF文件所在目录   
:param double_side:    是否启用双面渲染   
:param max_light_count: 最大光源数量   
:param surface:        表面着色器类型   
:param data_only:      是否只存储材质数据而不创建着色器对象   
:return: 材质字典 {材质索引: 着色器对象或材质数据字典}   
   
