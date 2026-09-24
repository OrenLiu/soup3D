# s3dm   
   
[返回上级](../README.md)   
   
调用：soup3D.s3dm   
数学工具库：旋转表示（四元数 w, x, y, z，pyglm 为 w-first）、平面旋转与向量运算。   
供 engine 各模块收编散落的数学辅助函数，统一维护。   
   
## 函数   
   
- [euler_to_quat(yaw, pitch, roll)](euler_to_quat.md): `函数`   
- [quat_to_euler(q)](quat_to_euler.md): `函数`   
- [bone_euler_to_quat(yaw, pitch, roll)](bone_euler_to_quat.md): `函数`   
- [bone_quat_to_euler(q)](bone_quat_to_euler.md): `函数`   
- [parse_rotation(value)](parse_rotation.md): `函数`   
- [rotated(Xa, Ya, Xb, Yb, degree)](rotated.md): `函数`   
- [normalize(v)](normalize.md): `函数`   
- [cross(a, b)](cross.md): `函数`   
- [quat_to_mat4(qx, qy, qz, qw)](quat_to_mat4.md): `函数`   
   
