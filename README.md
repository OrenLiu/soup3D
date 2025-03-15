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


def move(event):
    global w, s, a, d, space, shift
    if event["unicode"] in list("wW"):
        w = True

    if event["unicode"] in list("sS"):
        s = True

    if event["unicode"] in list("aA"):
        a = True

    if event["unicode"] in list("dD"):
        d = True

    if event["scancode"] == 44:
        space = True

    if event["scancode"] == 225:
        shift = True


def unmove(event):
    global w, s, a, d, space, shift

    if event["unicode"] in list("wW"):
        w = False

    if event["unicode"] in list("sS"):
        s = False

    if event["unicode"] in list("aA"):
        a = False

    if event["unicode"] in list("dD"):
        d = False

    if event["scancode"] == 44:
        space = False

    if event["scancode"] == 225:
        shift = False


def mouse_down(event):
    global md
    md = True


def mouse_up(event):
    global md
    md = False


def turn(event):
    if md:
        Y = soup3D.camera.YAW+event['rel'][0]/2
        P = soup3D.camera.PITCH+event['rel'][1]/2
        if P > 90:
            P = 90
        if P < -90:
            P = -90
        soup3D.camera.turn(Y, P, 0)


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


md = False
w = False
s = False
a = False
d = False
space = False
shift = False
running = True


if __name__ == '__main__':
    soup3D.init(bg_color=(0.5, 0.75, 1))       # 设置背景颜色
    soup3D.event.bind(ON_CLOSE, stop)          # 绑定关闭窗口事件
    soup3D.event.bind(KEY_DOWN, move)          # 绑定键盘按下事件
    soup3D.event.bind(KEY_UP, unmove)          # 绑定键盘抬起事件
    soup3D.event.bind(MOUSE_DOWN, mouse_down)  # 绑定鼠标按下事件
    soup3D.event.bind(MOUSE_UP, mouse_up)      # 绑定鼠标抬起事件
    soup3D.event.bind(MOUSE_MOVE, turn)        # 绑定鼠标拖动事件

    soup3D.light.init()                                   # 初始化光照
    sun = soup3D.light.Direct((45, 45, 45), (1, 0.5, 0))  # 创建光照

    ground = soup3D.Group(  # 在地上创建一个圆
        soup3D.Shape(TRIANGLE_L,
                     * [(rotated(0, 10, 0, 0, i)[0], -10, rotated(0, 10, 0, 0, i)[1], 0, 0.5, 1) for i in range(360)]
                     )
    )

    ground.display_stable()  # 固定显示地上的圆

    fps = 0
    last = time()
    frame_time = time()
    while running:  # 主循环
        if any([w, s, a, d, space, shift]):  # 控制移动
            if w:
                x, z = 0, (time()-frame_time)*10
                x, z = rotated(x, z, 0, 0, soup3D.camera.YAW)
                soup3D.camera.goto(soup3D.camera.X + x,
                                   soup3D.camera.Y,
                                   soup3D.camera.Z + z)
            if s:
                x, z = 0, -(time()-frame_time)*10
                x, z = rotated(x, z, 0, 0, soup3D.camera.YAW)
                soup3D.camera.goto(soup3D.camera.X + x,
                                   soup3D.camera.Y,
                                   soup3D.camera.Z + z)
            if a:
                x, z = (time()-frame_time)*10, 0
                x, z = rotated(x, z, 0, 0, soup3D.camera.YAW)
                soup3D.camera.goto(soup3D.camera.X + x,
                                   soup3D.camera.Y,
                                   soup3D.camera.Z + z)
            if d:
                x, z = -(time()-frame_time)*10, 0
                x, z = rotated(x, z, 0, 0, soup3D.camera.YAW)
                soup3D.camera.goto(soup3D.camera.X + x,
                                   soup3D.camera.Y,
                                   soup3D.camera.Z + z)

            if space:
                soup3D.camera.goto(soup3D.camera.X,
                                   soup3D.camera.Y + (time()-frame_time)*10,
                                   soup3D.camera.Z)

            if shift:
                soup3D.camera.goto(soup3D.camera.X,
                                   soup3D.camera.Y - (time()-frame_time)*10,
                                   soup3D.camera.Z)
        frame_time = time()

        now = time()
        sun.display()

        soup3D.update()  # 更新并渲染整个场景
        fps += 1
        if time() - last > 1:
            print(fps)
            last = time()
            fps = 0


```

这段代码运行后，您可以通过鼠标拖动调整视角，向下看可以看到一个圆形，通过w、s、a、d键还可以移动相机位置
