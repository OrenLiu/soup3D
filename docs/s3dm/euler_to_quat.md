# euler_to_quat   
   
[返回上级](./README.md)   
   
**签名**: `euler_to_quat(yaw, pitch, roll)`   
   
欧拉角转四元数（统一约定）   
与引擎历史行为一致：R = Ry(-yaw)·Rx(pitch)·Rz(roll)，角度单位为度。   
:param yaw:   绕y轴偏航角   
:param pitch: 绕x轴俯仰角   
:param roll:  绕z轴横滚角   
:return: glm.quat，分量为 (w, x, y, z)   
   
