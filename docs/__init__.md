# __init__   
   
[返回上级](./README.md)   
   
调用：soup3D   
这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可   
用于3D游戏开发、数据可视化、3D图形的绘制等开发。   
   
## 类   
   
- [Face](Face.md): `类型`   
- [Model](Model.md): `类型`   
- [Data](Data.md): `类型`   
   
## 函数   
   
- [_build_channel_value(val)](_build_channel_value.md): `函数`   
- [_build_base_color(bc_data)](_build_base_color.md): `函数`   
- [_build_surface_arg(val)](_build_surface_arg.md): `函数`   
- [_make_mtl_data(data)](_make_mtl_data.md): `函数`   
- [_make_obj_data(data)](_make_obj_data.md): `函数`   
- [_make_gltf_skeleton(data)](_make_gltf_skeleton.md): `函数`   
- [_build_gltf_base_color(bc_data)](_build_gltf_base_color.md): `函数`   
- [_build_gltf_emission(emi_data)](_build_gltf_emission.md): `函数`   
- [_make_gltf_data(data)](_make_gltf_data.md): `函数`   
- [init(width, height, fov, bg_color, near, far)](init.md): `函数`   
- [resize(width, height)](resize.md): `函数`   
- [background_color(r, g, b)](background_color.md): `函数`   
- [_paint_ui(shape, x, y)](_paint_ui.md): `函数`   
- [_render_fullscreen_image(img)](_render_fullscreen_image.md): `函数`   
- [update()](update.md): `函数`   
- [gen_skeleton_model(_skeleton, bone_color, size)](gen_skeleton_model.md): `函数`   
- [_store_mtl_material(width, height, R, G, B, A, emission, bump_texture, double_side, max_light_count, surface)](_store_mtl_material.md): `函数`   
- [open_mtl(mtl, double_side, roll_funk, encoding, max_light_count, surface, data_only)](open_mtl.md): `函数`   
- [open_obj(obj, mtl, double_side, roll_funk, encoding, max_light_count, data_only)](open_obj.md): `函数`   
- [_gltf_component_size(component_type)](_gltf_component_size.md): `函数`   
- [_gltf_component_count(accessor_type)](_gltf_component_count.md): `函数`   
- [_gltf_read_accessor(gltf_data, buffers_data, accessor_idx)](_gltf_read_accessor.md): `函数`   
- [_gltf_load_buffers(gltf_data, base_dir)](_gltf_load_buffers.md): `函数`   
- [_gltf_load_materials(gltf_data, base_dir, double_side, max_light_count, surface, data_only)](_gltf_load_materials.md): `函数`   
- [_quat_to_euler(qx, qy, qz, qw)](_quat_to_euler.md): `函数`   
- [_quat_to_mat4(qx, qy, qz, qw)](_quat_to_mat4.md): `函数`   
- [_gltf_build_node_transform(node)](_gltf_build_node_transform.md): `函数`   
- [_gltf_compute_world_recursive(idx, nodes, parent_transform, world_transforms)](_gltf_compute_world_recursive.md): `函数`   
- [_gltf_compute_world_transforms(nodes)](_gltf_compute_world_transforms.md): `函数`   
- [_gltf_build_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, skeleton)](_gltf_build_bone_recursive.md): `函数`   
- [_gltf_store_bone_recursive(joint_idx, nodes, world_transforms, joint_names, children_map, bones_data)](_gltf_store_bone_recursive.md): `函数`   
- [_gltf_store_skeleton(gltf_data, world_transforms)](_gltf_store_skeleton.md): `函数`   
- [_gltf_build_skeleton(gltf_data, world_transforms)](_gltf_build_skeleton.md): `函数`   
- [open_gltf(gltf, double_side, max_light_count, surface, skin, data_only)](open_gltf.md): `函数`   
- [get_projection_mat()](get_projection_mat.md): `函数`   
- [smart_split(line)](smart_split.md): `函数`   
   
