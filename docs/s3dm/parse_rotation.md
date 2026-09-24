# parse_rotation   
   
[返回上级](./README.md)   
   
**签名**: `parse_rotation(value)`   
   
解析旋转输入：长度检测，3 个数字为欧拉角(度)，4 个数字为四元数 (w, x, y, z)   
:param value: glm.quat，或包含 3 个(欧拉角) / 4 个(四元数)数字的 list/tuple   
:return: 归一化的 glm.quat   
   
