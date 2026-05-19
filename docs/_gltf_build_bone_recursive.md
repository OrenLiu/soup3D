# _gltf_build_bone_recursive   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_build_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, skeleton)`   
   
递归构建骨骼节点   
:param joint_idx:        关节索引   
:param nodes:            GLTF节点列表   
:param world_transforms: 世界变换矩阵列表   
:param joint_names:      关节名称映射   
:param children_map:     关节子节点映射   
:param skeleton:         骨架对象（就地添加骨骼）   
:return: 骨骼对象   
   
