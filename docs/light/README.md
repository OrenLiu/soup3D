# light

[返回上级](../README.md)

调用：`soup3D.light`
光源处理方法库：可向场景添加任意数量的 Cone（点光源/聚光灯）与 Direct（方向光），
每个表面着色器按 max_light_count（AutoSP 默认 8）取用其中先加入的若干个。
光源的增减、移动、染色都会使相关着色器进入脏状态，在下一帧统一更新 uniform。

## 示例：一盏太阳光 + 一盏手电筒

```python
import soup3D
import soup3D.light

# 方向光（类似太阳）：toward 是欧拉角 (yaw, pitch, roll) 或四元数 (w, x, y, z)
sun = soup3D.light.Direct((30, -60, 0), (0.4, 0.4, 0.5))
sun.turn_on()    # 重要：光源创建后默认关闭，必须 turn_on()

# 点光源/聚光灯：place 位置、toward 朝向、color 颜色、attenuation 衰减率、angle 锥角
flash = soup3D.light.Cone((0, 0, 3), (0, 0, 0), (1, 1, 1), 0.05, 90)
flash.turn_on()

soup3D.light.ambient(0.2, 0.2, 0.2)   # 环境光，避免背光面全黑
```

## 类

- [Cone](Cone/README.md): `类型`
- [Direct](Direct/README.md): `类型`

## 函数

- [ambient(R, G, B)](ambient.md): `函数`
- [set_surface_light()](set_surface_light.md): `函数`
