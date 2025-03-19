这是一个基于`OpenGL`和`pygame`开发的3D引擎，易于新手学习，可  
用于3D游戏开发、数据可视化、3D图形的绘制等开发。

## 安装

如果您的`python`环境中包含`pip`，可使用如下代码进行安装：

```bash
pip install -i https://osoup.top/simple soup3D
```

使用该库还需要`OpenGL`和`pygame`，可使用如下代码安装：

```bash
pip install pygame
pip install pyopengl
```

## 小试牛刀

安装完成后，您可以试试这段代码：

```python
import soup3D
from soup3D.name import *
from math import *
from time import*


def stop(event):
    global running
    running = False


def rotated(Xa, Ya, Xb, Yb, degree):
    """
    点A绕点B旋转特定角度后，点A的坐标
    :param Xa:     环绕点(点A)X坐标
    :param Ya:     环绕点(点A)Y坐标
    :param Xb:     被环绕点(点B)X坐标
    :param Yb:     被环绕点(点B)Y坐标
    :param degree: 旋转角度
    :return: 点A旋转后的X坐标, 点A旋转后的Y坐标
    """
    degree = degree * pi / 180
    outx = (Xa - Xb) * cos(degree) - (Ya - Yb) * sin(degree) + Xb
    outy = (Xa - Xb) * sin(degree) + (Ya - Yb) * cos(degree) + Yb
    return outx, outy


running = True


if __name__ == '__main__':
    soup3D.init(bg_color=(0.5, 0.75, 1))       # 设置背景颜色
    soup3D.event.bind(ON_CLOSE, stop)          # 绑定关闭窗口事件

    soup3D.light.init()                                   # 初始化光照
    sun = soup3D.light.Direct((45, 45, 45), (1, 0.5, 0))  # 创建光照

    ground = soup3D.Group(  # 创建一个圆
        soup3D.Shape(TRIANGLE_L,
                     * [(rotated(0, 10, 0, 0, i)[1], rotated(0, 10, 0, 0, i)[0], 20, 0, 0.5, 1) for i in range(360)]
                     )
    )

    ground.display_stable()  # 固定显示圆

    fps = 0
    last = time()
    frame_time = time()
    while running:  # 主循环
        frame_time = time()

        now = time()
        sun.display()  # 应用光照

        soup3D.update()  # 更新并渲染整个场景
        fps += 1
        if time() - last > 1:
            print(fps)
            last = time()
            fps = 0


```

这段代码运行后，您可以看到一个圆形在窗口中

## 更多内容

该库还有很多的方法供您使用，更多内容可参阅[帮助文档](./help.md)
