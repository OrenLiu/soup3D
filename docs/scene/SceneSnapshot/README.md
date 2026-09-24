# SceneSnapshot   
   
[返回上级](../README.md)   
   
场景快照数据对象。成员均为 numpy 数组（float32/int32/bool），   
公开可读；不要直接修改成员，需要新数据时重新调用 scene_snapshot()。   
   
模型与三角形（世界空间）：   
- model_count: 模型数 M   
- model_ids: list[int]，模型 id(model) 列表，跨帧识别与定位模型用   
- model_mats: (M,4,4)，各模型世界矩阵（get_model_mat 快照），   
  大场景增量更新：跨帧比较该矩阵，变化才重导出对应模型（tri_model 定位切片）   
- model_skinned: (M,) bool，模型是否含蒙皮表面   
- model_skeletons: list[(B,4,4) 或 None]，各模型首个蒙皮表面的骨骼矩阵表   
- triangle_count: 三角形总数 N   
- triangles: (N,3,3)，世界空间三角形顶点（局部顶点×模型矩阵，glm 同源变换）   
- normals: (N,3,3)，世界空间顶点法线（逆转置变换后归一化）   
- triangle_uvs: (N,3,2)，各三角形三顶点 UV（引擎顶点存储原值，OBJ 为 (u, -v)；缺失补 (0,0)）   
- tri_model: (N,) int32，每三角形所属模型号   
- tri_material: (N,) int32，每三角形材质号（材质表索引）   
材质（与 AutoSP 表面同源，纹理表面 flat=False）：   
- material_count: 材质数 Md   
- material_kd: (Md,4) 漫反射色 RGBA 原值；material_ke: (Md,3) 自发光 RGB 原值   
  （HDR 自发光保留原值不 clamp，如发光材质 (10,10,10)）   
- material_flat: (Md,) bool，Kd/Ke 是否为平面色（False=贴图表面）   
- material_textures: list，各材质 base_color 图像对象（Texture/MixChannel）   
光源（仅导出 on 状态光源）：   
- ambient: (3,) 环境光   
- direct_count / direct_dirs (K,3) / direct_colors (K,3)：   
  Direct 光的太阳来光方向与颜色（_calc_direction 原值）   
- cone_count / cone_positions (C,3) / cone_directions (C,3) / cone_colors (C,3)   
  / cone_attenuations (C,) / cone_angles (C,)：Cone 光参数   
  （cone_directions 为光锥轴指向场景的方向，即 _calc_direction）   
相机（与默认管线 view matrix 严格同源）：   
- camera_pos / camera_forward / camera_right / camera_up: (3,) 正交基   
- camera_fov: float，proj_fov（度）   
- view_mat: (4,4)，camera.get_view_mat() 同源快照   
   
## 方法   
   
- [__init__(self, model_ids, model_mats, model_skinned, model_skeletons, triangles, normals, tri_model, tri_material, triangle_uvs, material_kd, material_ke, material_flat, material_textures, ambient, direct_dirs, direct_colors, cone_positions, cone_directions, cone_colors, cone_attenuations, cone_angles, camera_pos, camera_forward, camera_right, camera_up, camera_fov, view_mat)](__init__.md): `函数`   
   
