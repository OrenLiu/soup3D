# SceneSnapshot

[返回上级](./scene.md)

场景快照数据容器（scene_snapshot() 的返回类型，纯数据类）。
所有数组字段只读使用；数据与引擎实际渲染管线逐位一致（glm f32）。

## 成员变量

模型与三角形：

- `model_ids` / `model_count`：模型数量与 id 列表（遍历序：stable_shapes 优先、render_queue 补充）
- `model_mats`：各模型世界矩阵 (model_count, 4, 4) float32
- `model_skinned`：各模型是否蒙皮 (model_count,) bool
- `model_skeletons`：各模型骨骼矩阵表（未绑骨骼为 None；蒙皮模型为 (bone_count, 4, 4) float32）
- `triangles`：世界空间三角形顶点 (triangle_count, 3, 3) float32
- `normals`：世界空间三角形法线 (triangle_count, 3, 3) float32
- `tri_model`：三角形所属模型下标 (triangle_count,) int32
- `tri_material`：三角形的材质下标 (triangle_count,) int32

材质：

- `material_count` / `material_kd`：材质数与漫反射色 (material_count, 4) float32
- `material_ke`：自发光色 (material_count, 3) float32（HDR 原值，不 clamp）
- `material_flat`：是否纯色材质 (material_count,) bool
- `material_textures`：各材质的贴图通道对象列表（无贴图为 None，仅对象引用不导出像素）

光源与相机：

- `ambient`：环境光颜色 (3,) float32
- `direct_count` / `direct_dirs` / `direct_colors`：方向光数量/方向/颜色
- `cone_count` / `cone_positions` / `cone_directions` / `cone_colors` / `cone_attenuations` / `cone_angles`：锥光参数
- `camera_pos` / `camera_forward` / `camera_right` / `camera_up`：相机基 (3,) float32
- `camera_fov`：垂直视场角（度，float）
- `view_mat`：引擎 view 矩阵 (4, 4) float32
