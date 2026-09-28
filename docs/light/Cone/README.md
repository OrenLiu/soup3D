# Cone

[返回上级](../README.md)

锥形光线，类似灯泡/手电筒光线，位置 + 朝向 + 锥角决定照明范围。

```python
lamp = soup3D.light.Cone(
    place=(0, 4, -4),      # 光源位置 (x, y, z)
    toward=(0, -90, 0),    # 朝向：欧拉角 (yaw, pitch, roll) 或四元数 (w, x, y, z)
    color=(1, 1, 1),       # 颜色，取值 0~1
    attenuation=0.05,      # 线性衰减率，越大光衰减越快
    angle=90,              # 锥角（角度制），180 = 全方向（灯泡）
    )
lamp.turn_on()             # 创建后默认关闭，必须 turn_on() 才照明
```

## 方法

- [__init__(self, place, toward, color, attenuation, angle)](__init__.md): `函数`
- [goto(self, x, y, z)](goto.md): `函数`
- [turn(self, yaw, pitch, roll)](turn.md): `函数`
- [turn_quat(self, quat)](turn_quat.md): `函数`
- [dye(self, r, g, b)](dye.md): `函数`
- [turn_off(self)](turn_off.md): `函数`
- [turn_on(self)](turn_on.md): `函数`
- [destroy(self)](destroy.md): `函数`
