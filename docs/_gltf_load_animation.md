# _gltf_load_animation   
   
[返回上级](./__init__.md)   
   
**签名**: `_gltf_load_animation(gltf_data, buffers_data, world_transforms)`   
   
加载GLTF动画数据，转换为可用于make_pose的格式   
:param gltf_data:        GLTF JSON数据   
:param buffers_data:     已加载的缓冲区数据列表   
:param world_transforms: 节点世界变换矩阵列表   
:return: 动画帧列表，每帧为{bone_name: (x, y, z, length, yaw, pitch, roll)}   
   
