# _gltf_store_skeleton   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_store_skeleton(gltf_data, world_transforms)`   
   
从GLTF数据存储骨架数据为字典格式   
:param gltf_data:        GLTF JSON数据   
:param world_transforms: 节点世界变换矩阵列表   
:return: 骨架数据字典 {"bones": {name: info}, "root_bones": [name]}   
   
