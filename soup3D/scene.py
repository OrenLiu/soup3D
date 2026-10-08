"""
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
"""
import numpy as np
from pyglm import glm

import soup3D

__all__ = ["SceneSnapshot", "scene_snapshot"]


class SceneSnapshot:
    """场景快照数据对象。成员均为 numpy 数组（float32/int32/bool），
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
    """

    def __init__(self, model_ids, model_mats, model_skinned, model_skeletons,
                 triangles, normals, tri_model, tri_material, triangle_uvs,
                 material_kd, material_ke, material_flat, material_textures,
                 ambient, direct_dirs, direct_colors,
                 cone_positions, cone_directions, cone_colors, cone_attenuations,
                 cone_angles, camera_pos, camera_forward, camera_right, camera_up,
                 camera_fov, view_mat):
        self.model_ids = list(model_ids)
        self.model_count = len(self.model_ids)
        self.model_mats = model_mats
        self.model_skinned = model_skinned
        self.model_skeletons = model_skeletons
        self.triangle_count = int(triangles.shape[0])
        self.triangles = triangles
        self.triangle_uvs = triangle_uvs
        self.normals = normals
        self.tri_model = tri_model
        self.tri_material = tri_material
        self.material_count = int(material_kd.shape[0])
        self.material_kd = material_kd
        self.material_ke = material_ke
        self.material_flat = material_flat
        self.material_textures = list(material_textures)
        self.ambient = ambient
        self.direct_count = int(direct_dirs.shape[0])
        self.direct_dirs = direct_dirs
        self.direct_colors = direct_colors
        self.cone_count = int(cone_positions.shape[0])
        self.cone_positions = cone_positions
        self.cone_directions = cone_directions
        self.cone_colors = cone_colors
        self.cone_attenuations = cone_attenuations
        self.cone_angles = cone_angles
        self.camera_pos = camera_pos
        self.camera_forward = camera_forward
        self.camera_right = camera_right
        self.camera_up = camera_up
        self.camera_fov = float(camera_fov)
        self.view_mat = view_mat

def scene_snapshot(skinned: bool = False) -> 'SceneSnapshot':
    """导出引擎本帧场景快照。

    收集 stable_shapes 队列与 render_queue 中的全部模型（id 去重），连同
    开启状态的光源、相机状态，打包为 numpy 数组结构的只读快照对象。
    只读引擎 Python 侧状态、零 GL 调用，on_frame 内调用安全。

    :param skinned: True 时对蒙皮模型 CPU 预蒙皮，导出三角形为蒙皮后
        的局部顶点（再乘模型矩阵）；False 导出绑定姿态顶点。
        骨骼矩阵表两种模式下都导出，消费方可自行蒙皮。
    :return: SceneSnapshot 类实例
    """
    if not isinstance(skinned, bool):
        raise TypeError("skinned must be a bool")
    mat_table = {}
    mat_kd = []
    mat_ke = []
    mat_flat = []
    mat_tex = []
    tri_pts = []
    tri_nrm_rows = []
    tri_mats = []
    tri_uvs = []
    tri_models = []
    model_ids = []
    model_mats_list = []
    model_skinned = []
    skel_list = []
    seen = set()
    models = []
    for mdl in soup3D.stable_shapes.values():
        if id(mdl) not in seen:
            seen.add(id(mdl))
            models.append(mdl)
    for mdl in soup3D.render_queue:
        if id(mdl) not in seen:
            seen.add(id(mdl))
            models.append(mdl)
    for mdl in models:
        model_ids.append(id(mdl))
        model_mats_list.append(_mat4_to_numpy(mdl.get_model_mat()))
    for midx, mdl in enumerate(models):
        pts, nrm_rows, mats, uvs, skel = _extract_model(
            mdl, skinned, mat_table, mat_kd, mat_ke, mat_flat, mat_tex)
        tri_pts.extend(pts)
        tri_nrm_rows.extend(nrm_rows)
        tri_mats.extend(mats)
        tri_uvs.extend(uvs)
        tri_models.extend([midx] * len(pts))
        model_skinned.append(skel is not None)
        skel_list.append(skel)
    triangles = np.array(tri_pts, dtype=np.float32).reshape(-1, 3, 3)
    normals = np.array(tri_nrm_rows, dtype=np.float32).reshape(-1, 3, 3)
    tri_model_arr = np.array(tri_models, dtype=np.int32)
    tri_material_arr = np.array(tri_mats, dtype=np.int32)
    triangle_uvs_arr = np.array(tri_uvs, dtype=np.float32).reshape(-1, 3, 2)
    material_kd_arr = np.array(mat_kd, dtype=np.float32).reshape(-1, 4)
    material_ke_arr = np.array(mat_ke, dtype=np.float32).reshape(-1, 3)
    material_flat_arr = np.array(mat_flat, dtype=bool)
    mats_np = np.array(model_mats_list, dtype=np.float32).reshape(-1, 4, 4)
    skinned_arr = np.array(model_skinned, dtype=bool)
    d_dirs = []
    d_cols = []
    c_pos = []
    c_dir = []
    c_col = []
    c_att = []
    c_ang = []
    for lt in soup3D.light.light_queue.values():
        if not getattr(lt, "on", False):
            continue
        if isinstance(lt, soup3D.light.Direct):
            d_dirs.append(lt._calc_direction())
            d_cols.append(lt.color)
        elif isinstance(lt, soup3D.light.Cone):
            c_pos.append(lt.place)
            c_dir.append(lt._calc_direction())
            c_col.append(lt.color)
            c_att.append(lt.attenuation)
            c_ang.append(lt.angle)
    ambient_np = np.array(soup3D.light.ambient_val, dtype=np.float32)
    pos_v = glm.vec3(float(soup3D.camera.X), float(soup3D.camera.Y), float(soup3D.camera.Z))
    fwd = soup3D.camera.QUAT * glm.vec3(0, 0, -1)
    up0 = soup3D.camera.QUAT * glm.vec3(0, 1, 0)
    right = glm.normalize(glm.cross(fwd, up0))
    up = glm.cross(right, fwd)
    view_np = _mat4_to_numpy(soup3D.camera.get_view_mat())
    snap = SceneSnapshot(
        model_ids, mats_np, skinned_arr, skel_list,
        triangles, normals, tri_model_arr, tri_material_arr, triangle_uvs_arr,
        material_kd_arr, material_ke_arr, material_flat_arr, mat_tex,
        ambient_np,
        np.array(d_dirs, dtype=np.float32).reshape(-1, 3),
        np.array(d_cols, dtype=np.float32).reshape(-1, 3),
        np.array(c_pos, dtype=np.float32).reshape(-1, 3),
        np.array(c_dir, dtype=np.float32).reshape(-1, 3),
        np.array(c_col, dtype=np.float32).reshape(-1, 3),
        np.array(c_att, dtype=np.float32),
        np.array(c_ang, dtype=np.float32),
        _vec3_to_numpy(pos_v), _vec3_to_numpy(fwd),
        _vec3_to_numpy(right), _vec3_to_numpy(up),
        float(soup3D.proj_fov), view_np)
    return snap


def _mat4_to_numpy(m) -> np.ndarray:
    """glm 矩阵转 numpy (4,4) float32。glm 列主序：numpy[r][c] = glm[c][r]"""
    out = np.empty((4, 4), dtype=np.float32)
    for c in range(4):
        col = m[c]
        for r in range(4):
            out[r, c] = float(col[r])
    return out


def _vec3_to_numpy(v) -> np.ndarray:
    """glm 向量转 numpy (3,) float32"""
    return np.array((float(v.x), float(v.y), float(v.z)), dtype=np.float32)


def _surface_flat_color(surface) -> tuple:
    """提取表面的平面漫反射色 Kd=(R,G,B,A)。
    仅当 base_color 是全数值通道的 MixChannel 时可平面化；
    纹理表面返回 (1,1,1,1)，由 flat 标记区分。"""
    bc = getattr(surface, "base_color", None)
    if bc is not None and isinstance(bc, soup3D.shader.MixChannel) \
            and all(isinstance(c, (int, float)) for c in (bc.R, bc.G, bc.B, bc.A)):
        return (float(bc.R), float(bc.G), float(bc.B), float(bc.A)), True
    return (1.0, 1.0, 1.0, 1.0), False


def _surface_flat_emission(surface) -> tuple:
    """提取表面的平面自发光色 Ke=(r,g,b)。
    仅当 emission 是 3 元数值元组时可平面化（保留 HDR 原值不 clamp）；
    贴图自发光返回 (0,0,0)，由 flat 标记区分。"""
    em = getattr(surface, "emission", None)
    if em is not None and isinstance(em, (list, tuple)) and len(em) == 3 \
            and all(isinstance(c, (int, float)) for c in em):
        return (float(em[0]), float(em[1]), float(em[2])), True
    return (0.0, 0.0, 0.0), False


def _unfold_indices(count: int, shape_type: str) -> list:
    """把三角形族面顶点展开成三角形索引三元组列表。
    triangle_b: 每 3 顶点一三角形；triangle_s: 滑窗条带；triangle_l: 扇形。
    line_* 族返回空列表（快照仅导出三角形面）。"""
    if shape_type == soup3D.TRIANGLE_B:
        return [(i, i + 1, i + 2) for i in range(0, count - 2, 3)]
    if shape_type == soup3D.TRIANGLE_S:
        return [(i, i + 1, i + 2) for i in range(count - 2)]
    if shape_type == soup3D.TRIANGLE_L:
        return [(0, i, i + 1) for i in range(1, count - 1)]
    return []


def _face_vertex_arrays(verts, is_skin: bool) -> tuple:
    """从面顶点列表提取局部位置/法线/UV 数组。
    蒙皮面 (权重字典, x,y,z, u,v[,nx,ny,nz])：位置 [1:4]、法线 [6:9]、UV [4:6]；
    普通面 (x,y,z,u,v[,nx,ny,nz])：位置 [0:3]、法线 [5:8]、UV [3:5]。
    法线缺失时按 rend() 同语义回退 (0,0,1)，UV 缺失时回退 (0,0)。"""
    n = len(verts)
    pos = np.empty((n, 3), dtype=np.float32)
    nrm = np.empty((n, 3), dtype=np.float32)
    uv = np.zeros((n, 2), dtype=np.float32)
    for i, v in enumerate(verts):
        b = 1 if is_skin else 0
        pos[i] = (v[b], v[b + 1], v[b + 2])
        if len(v) >= b + 8:
            nrm[i] = (v[b + 5], v[b + 6], v[b + 7])
        else:
            nrm[i] = (0.0, 0.0, 1.0)
        if len(v) >= b + 5:
            uv[i] = (v[b + 3], v[b + 4])
    return pos, nrm, uv


def _skin_face(verts, skeleton, mats_np: np.ndarray) -> tuple:
    """CPU 蒙皮：镜像 BoneBinderSP.rend() 的权重语义（按权重排序取前 4 + 归一化）。
    位置 = Σ w·B·p（totalWeight<0.001 时恒等），法线 = 逆转置(Σ w·B₃)·n。
    :param mats_np: 骨骼矩阵堆叠 (B,4,4) float32
    :return: (位置 (n,3), 法线 (n,3), UV (n,2))，均为局部系未归一化法线，UV 直通不参与蒙皮"""
    n = len(verts)
    ids = np.zeros((n, 4), dtype=np.int32)
    ws = np.zeros((n, 4), dtype=np.float32)
    P = np.empty((n, 3), dtype=np.float32)
    N = np.empty((n, 3), dtype=np.float32)
    U = np.zeros((n, 2), dtype=np.float32)
    for i, v in enumerate(verts):
        d = v[0] if isinstance(v[0], dict) else {}
        pairs = []
        for bname, w in d.items():
            bi = skeleton.get_bone_index(bname)
            if bi >= 0:
                pairs.append((float(w), bi))
        pairs.sort(reverse=True)
        top = pairs[:4]
        total = 0.0
        for k in range(len(top)):
            total += top[k][0]
        for k in range(len(top)):
            ids[i, k] = top[k][1]
            ws[i, k] = top[k][0] / total if total > 0 else 0.0
        P[i] = (v[1], v[2], v[3])
        if len(v) >= 9:
            N[i] = (v[6], v[7], v[8])
        else:
            N[i] = (0.0, 0.0, 1.0)
        if len(v) >= 6:
            U[i] = (v[4], v[5])
    ph = np.concatenate([P, np.ones((n, 1), dtype=np.float32)], axis=1)
    pos = np.zeros((n, 3), dtype=np.float32)
    skin3 = np.zeros((n, 3, 3), dtype=np.float32)
    for k in range(4):
        A = mats_np[ids[:, k]]          # (n,4,4) 按顶点取各自骨骼矩阵
        t = np.einsum('nij,nj->ni', A, ph)
        pos += ws[:, k:k + 1] * t[:, :3]
        skin3 += ws[:, k, None, None] * A[:, :3, :3]
    # totalWeight<0.001 的顶点按恒等蒙皮处理（与着色器一致）
    degenerate = (np.abs(skin3).sum(axis=(1, 2)) < 1e-8)
    if degenerate.any():
        skin3[degenerate] = np.eye(3, dtype=np.float32)
    try:
        nit = np.linalg.inv(skin3).transpose(0, 2, 1)
    except np.linalg.LinAlgError:
        nit = np.empty_like(skin3)
        for i in range(n):
            try:
                nit[i] = np.linalg.inv(skin3[i]).T
            except np.linalg.LinAlgError:
                nit[i] = np.eye(3, dtype=np.float32)
    nrm = np.einsum('nij,nj->ni', nit, N)
    return pos, nrm, U


def _register_material(surface, mat_table: dict, mat_kd: list, mat_ke: list,
                       mat_flat: list, mat_tex: list) -> int:
    """按表面实例登记材质（首次出现顺序编号），返回材质号。"""
    key = id(surface)
    if key in mat_table:
        return mat_table[key]
    mi = len(mat_kd)
    mat_table[key] = mi
    kd, flat_c = _surface_flat_color(surface)
    ke, flat_e = _surface_flat_emission(surface)
    mat_kd.append(kd)
    mat_ke.append(ke)
    mat_flat.append(flat_c and flat_e)
    mat_tex.append(getattr(surface, "base_color", None))
    return mi


def _extract_model(model, skinned_mode: bool, mat_table: dict, mat_kd: list,
                   mat_ke: list, mat_flat: list, mat_tex: list) -> tuple:
    """导出单个模型的三角形与骨骼。
    :return: (tri_pts list[(3,3)元组], tri_nrm list[(3,)×3], tri_mats list[int],
              tri_uvs list[((2,)×3)元组], 骨骼矩阵 (B,4,4) 或 None)"""
    m_glm = model.get_model_mat()
    m_np = _mat4_to_numpy(m_glm)
    m3 = m_np[:3, :3]
    nit = np.linalg.inv(m3).T
    tri_pts = []
    tri_nrm_rows = []
    tri_mats = []
    tri_uvs = []
    skel_mats = None
    for face in model.faces:
        surface = face.surface
        idx = _unfold_indices(len(face.vertex), face.shape_type)
        if not idx:
            continue  # line 族面跳过
        mi = _register_material(surface, mat_table, mat_kd, mat_ke, mat_flat, mat_tex)
        is_skin = hasattr(surface, "skeleton")
        if is_skin and skel_mats is None:
            mats = surface.skeleton.get_bone_matrices()
            skel_mats = np.stack([_mat4_to_numpy(bm) for bm in mats]) if mats else None
        if is_skin and skinned_mode and skel_mats is not None:
            pos, nrm, uv = _skin_face(face.vertex, surface.skeleton, skel_mats)
        else:
            pos, nrm, uv = _face_vertex_arrays(face.vertex, is_skin)
        for (a, b, c) in idx:
            pts = []
            nm = []
            for k in (a, b, c):
                w = m_glm * glm.vec4(float(pos[k, 0]), float(pos[k, 1]), float(pos[k, 2]), 1.0)
                pts.append((w.x, w.y, w.z))
                tn = nit @ nrm[k]
                ln = float(np.linalg.norm(tn))
                if ln > 1e-9:
                    tn = tn / ln
                nm.append(tn)
            tri_pts.append((pts[0], pts[1], pts[2]))
            tri_nrm_rows.extend(nm)
            tri_mats.append(mi)
            tri_uvs.append((uv[a], uv[b], uv[c]))
    return tri_pts, tri_nrm_rows, tri_mats, tri_uvs, skel_mats
