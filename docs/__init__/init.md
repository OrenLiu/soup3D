# init

[返回上级](./README.md)

**签名**: `init(width, height, fov, bg_color, near, far)`

初始化3D引擎（创建 GL 状态、渲染队列与默认相机）。
必须在 `pygame.display.set_mode(..., OPENGL)` 之后调用，之后才能创建模型、光源或渲染目标。

## 最小完整示例

```python
import pygame
import soup3D

pygame.init()
pygame.display.set_mode((800, 600), pygame.DOUBLEBUF | pygame.OPENGL)
soup3D.init(800, 600, 45, (0.2, 0.2, 0.25), 0.1, 1024)

# 之后：创建 Face/Model 并 show()，循环里调用 soup3D.update()

while True:
    soup3D.update()
    pygame.display.flip()
```

- `:param width`:    窗口宽度
- `:param height`:   窗口高度
- `:param fov`:      视野（角度制，如 45）
- `:param bg_color`: 背景颜色 (r, g, b)，取值 0~1
- `:param near`:     最近渲染距离
- `:param far`:      最远渲染距离
- `:return`: None
