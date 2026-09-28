# Direct

[返回上级](../README.md)

方向光线，类似太阳光：只有方向没有位置，场景中所有物体同一方向受光。

```python
sun = soup3D.light.Direct(
    toward=(30, -60, 0),   # 朝向：欧拉角 (yaw, pitch, roll) 或四元数 (w, x, y, z)
    color=(0.4, 0.4, 0.5), # 颜色，取值 0~1
    )
sun.turn_on()              # 创建后默认关闭，必须 turn_on() 才照明
```

## 方法

- [__init__(self, toward, color)](__init__.md): `函数`
- [turn(self, yaw, pitch, roll)](turn.md): `函数`
- [turn_quat(self, quat)](turn_quat.md): `函数`
- [dye(self, r, g, b)](dye.md): `函数`
- [turn_off(self)](turn_off.md): `函数`
- [turn_on(self)](turn_on.md): `函数`
- [destroy(self)](destroy.md): `函数`
