# Bone.__init__   
   
[返回上级](./Bone.md)   
   
**签名**: `__init__(self, init_pos, init_length, init_toward)`   
   
单个骨骼节点   
:param init_pos:    骨骼根初始位置，使用特定着色器的网格会基于该点结合权重进行环绕、缩放和位移。需填写：(x, y, z)   
:param init_length: 骨骼初始长度，用于参照缩放比例。   
:param init_toward: 骨骼初始方向，用于参照旋转方向。需填写：(yaw, pitch, roll)   
   
