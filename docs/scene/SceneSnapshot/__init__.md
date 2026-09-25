# SceneSnapshot.__init__   


[返回上级](./README.md)   


**签名**: `__init__(self, ...)`   
   
场景快照数据对象构造方法。快照由 scene_snapshot() 创建并返回，一般无需手动构造。   
成员（model_ids / triangles / material_kd 等）均为 numpy 数组，公开可读；不要直接修改成员，需要新数据时重新调用 scene_snapshot()。完整成员表见 [README](./README.md)。   
   
:return: None   
