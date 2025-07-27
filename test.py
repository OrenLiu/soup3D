import soup3D
import soup3D.event
import soup3D.shader
from name import ON_CLOSE, TRIANGLE_B


def stop(event):  # 用于绑定窗口关闭事件的函数，每个事件绑定的函数都需要有一个参数。
    global running
    running = False


running = True


if __name__ == '__main__':
    soup3D.init(bg_color=(0.5, 0.75, 1))       # 初始化窗口
    soup3D.event.bind(ON_CLOSE, stop)          # 绑定关闭窗口事件

    green = soup3D.shader.FPL(soup3D.shader.MixChannel((1, 1), 0, 1, 0))  # 创建绿色材质
    face = soup3D.Face(TRIANGLE_B, green, [                               # 创建面
        (0, 0, 0, 0, 0),  # (R, G, B, U, V)
        (100, 0, 0, 0, 0),
        (0, 100, 0, 0, 0)
    ])

    triangle = soup3D.Model(0, 0, -500, face)  # 将面加入模型
    triangle.show()                            # 显示模型
    while running:  # 主循环
        soup3D.update()  # 更新画面
