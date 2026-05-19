# _gltf_compute_world_recursive   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_compute_world_recursive(idx, nodes, parent_transform, world_transforms)`   
   
递归计算单个节点的世界变换矩阵   
:param idx:              节点索引   
:param nodes:            GLTF节点列表   
:param parent_transform: 父节点世界变换矩阵   
:param world_transforms: 世界变换矩阵列表（就地修改）   
:return: None   
   
