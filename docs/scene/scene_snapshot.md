# scene_snapshot   
   
[返回上级](./README.md)   
   
**签名**: `scene_snapshot(skinned)`   
   
导出引擎本帧场景快照。   
   
收集 stable_shapes 队列与 render_queue 中的全部模型（id 去重），连同   
开启状态的光源、相机状态，打包为 numpy 数组结构的只读快照对象。   
只读引擎 Python 侧状态、零 GL 调用，on_frame 内调用安全。   
   
:param skinned: True 时对蒙皮模型 CPU 预蒙皮，导出三角形为蒙皮后   
    的局部顶点（再乘模型矩阵）；False 导出绑定姿态顶点。   
    骨骼矩阵表两种模式下都导出，消费方可自行蒙皮。   
:return: SceneSnapshot 类实例   
   
