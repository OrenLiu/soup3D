# scene   
   
[返回上级](../README.md)   
   
调用：soup3D.scene   
场景快照模块：把引擎本帧场景（模型/光源/相机/骨骼）导出为 numpy 友好   
的只读数据结构，供光追等外部渲染消费方零侵入消费引擎场景状态。   
   
设计约定：   
- on_frame 内调用安全：只读引擎 Python 侧状态，不做任何 GL 调用；   
- 世界空间顶点用 glm 逐顶点变换（与 get_model_mat() 同源同序），   
  数值与消费方手工路径逐位一致；   
- 材质 Kd/Ke 与 AutoSP 同源：读表面对象的 base_color/emission 原始值，   
  不经过 GL 纹理化（保留 HDR 自发光强度）；   
- 蒙皮模型：默认导出绑定姿态顶点；skinned=True 时引擎 CPU 预蒙皮，   
  消费方零蒙皮逻辑；骨骼矩阵表并行导出。   
   
## 类   
   
- [SceneSnapshot](SceneSnapshot/README.md): `类型`   
   
## 函数   
   
- [scene_snapshot(skinned)](scene_snapshot.md): `函数`   
   
