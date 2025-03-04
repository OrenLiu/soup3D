"""
命名空间
"""

# shape_type
LINE_B = "line_b"          # 不相连线段
LINE_S = "line_s"          # 连续线段
LINE_L = "line_l"          # 头尾相连的连续线段
TRIANGLE_B = "triangle_b"  # 不相连三角形
TRIANGLE_S = "triangle_s"  # 相连三角形
TRIANGLE_L = "triangle_l"  # 头尾相连的连续三角形

# light_type
POINT = "point"         # 点光源
DIRECT = "direct"  # 方向光源

# wrap
REPEAT = "repeat"      # 超出边缘后重复
MIRRORED = "mirrored"  # 超出边缘后镜像
EDGE = "edge"          # 超出边缘后延伸边缘颜色
BORDER = "border"      # 超出边缘后

# event
ON_CLOSE = "on_close"        # 窗口关闭事件
KEY_DOWN = "key_down"        # 键盘按下事件
KEY_UP = "key_up"            # 键盘松开事件
MOUSE_DOWN = "mouse_down"    # 鼠标按下事件
MOUSE_UP = "mouse_up"        # 鼠标松开事件
MOUSE_MOVE = "mouse_move"    # 鼠标移动事件
MOUSE_WHEEL = "mouse_wheel"  # 鼠标滚轮事件
