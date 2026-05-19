# Bone.move   
   
[返回上级](./Bone.md)   
   
**签名**: `move(self, x, y, z)`   
   
移动骨骼，特定着色器会根据该位置结合权重改变顶点位置，同时移动子骨骼到(子骨骼初始位置+(父骨骼实际位置-父骨骼初始位置))。   
:param x: x轴偏移量   
:param y: y轴偏移量   
:param z: z轴偏移量   
:return: None   
   
