# scene

[返回上级](./README.md)

场景快照模块：把当前帧的完整场景状态（模型三角形、材质、光源、相机、蒙皮骨骼矩阵）
一次性导出为 numpy 数组集合，供外部渲染消费方（如光线追踪器）零侵入读取。
快照导出全程零 GL 调用，可在 on_frame 等任意时刻安全调用；世界空间数据
（三角形/法线/光源/相机）与引擎实际渲染使用的 glm f32 管线逐位一致。

## 模块成员

- [scene_snapshot()](./scene_snapshot.md): 导出当前帧场景快照（模块级主入口，已挂到 `soup3D.scene_snapshot`）
- [SceneSnapshot](./SceneSnapshot.md): 快照数据容器（纯数据类，字段全部为 numpy 数组或标量）
