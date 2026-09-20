# scene_snapshot()

[返回上级](./scene.md)

**签名**: `scene_snapshot(skinned: bool = False) -> SceneSnapshot`

导出当前帧的场景快照。一次调用返回本帧完整场景描述：模型三角形（世界空间）、
材质表、光源、相机与蒙皮骨骼矩阵表，全部为 numpy 数组。全程零 GL 调用，
在 on_frame（帧级渲染器协议）内调用安全。

## 参数

- `skinned`：是否对蒙皮模型做 CPU 预变换。True 时快照三角形已是蒙皮后的世界顶点，
  消费方零蒙皮逻辑；False 时蒙皮模型导出 bind pose 顶点与骨骼矩阵表，由消费方自行蒙皮。
  非 bool 传参抛 TypeError。

## 返回

[SceneSnapshot](./SceneSnapshot.md) 实例。三角形按模型遍历序展开
（stable_shapes 优先、render_queue 补充，同 id 去重），材质按表面首次出现编号。

## 示例

```python
import soup3D
import soup3D.scene

snap = soup3D.scene_snapshot()
print(snap.model_count, snap.triangle_count)
print(snap.triangles.shape)        # (triangle_count, 3, 3) 世界空间顶点
print(snap.direct_dirs)            # (N, 3) 方向光方向
print(snap.camera_pos, snap.camera_forward, snap.camera_fov)
```
