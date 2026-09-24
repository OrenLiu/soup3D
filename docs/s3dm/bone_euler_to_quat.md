# bone_euler_to_quat   
   
[返回上级](./README.md)   
   
**签名**: `bone_euler_to_quat(yaw, pitch, roll)`   
   
欧拉角转四元数（Bone 历史耦合约定）   
与 Bone 蒙皮矩阵历史行为一致：R = Ry(-yaw)·Rx(pitch)·Rz(roll-yaw)。   
:param yaw:   绕y轴偏航角   
:param pitch: 绕x轴俯仰角   
:param roll:  绕z轴横滚角   
:return: glm.quat   
   
