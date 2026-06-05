# _gltf_store_bone_recursive   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_store_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, bones_data)`   
   
递归存储骨骼数据为字典格式，用于data_only模式   
:param joint_idx:        关节索引   
:param nodes:            GLTF节点列表   
:param world_transforms: 世界变换矩阵列表   
:param joint_names:      关节名称映射   
:param children_map:     关节子节点映射   
:param bones_data:       骨骼数据字典（就地修改）   
:return: 骨骼名称   
   
