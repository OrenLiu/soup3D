# light   
   
[返回上级](../README.md)   
   
调用：soup3D.light   
光源处理方法库：可向场景添加任意数量的 Cone（点光源/聚光灯）与 Direct（方向光源），   
每个表面着色器按 max_light_count（AutoSP 默认 8）取用其中先加入的若干个。   
光源的增减、移动、染色都会使相关着色器进入脏状态，在下一帧统一更新 uniform。   
   
## 类   
   
- [Cone](Cone/README.md): `类型`   
- [Direct](Direct/README.md): `类型`   
   
## 函数   
   
- [ambient(R, G, B)](ambient.md): `函数`   
- [set_surface_light()](set_surface_light.md): `函数`   
