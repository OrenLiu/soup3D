# BoneBinderSP.update   


[返回上级](./README.md)   


**签名**: `update(self)`   


蒙皮着色器的每帧刷新：骨骼脏时先把最新骨骼矩阵写入 UBO，再把 UBO 绑定到着色器绑定点，最后走 AutoSP.update() 下发矩阵/光照等 uniform。引擎每帧渲染前自动调用，一般无需手动调用。   
   
:return: None   
