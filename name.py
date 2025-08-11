"""
调用：soup3D
"""
from OpenGL.GL import *

# shape_type
LINE_B = "line_b"          # 不相连线段
LINE_S = "line_s"          # 连续线段
LINE_L = "line_l"          # 头尾相连的连续线段
TRIANGLE_B = "triangle_b"  # 不相连三角形
TRIANGLE_S = "triangle_s"  # 相连三角形
TRIANGLE_L = "triangle_l"  # 头尾相连的连续三角形

# vertex_type
BYTE = "byte_s"       # 带有符号的8位整数
BYTE_US = "byte_u"    # 不带符号的8位整数
SHORT = "short_s"     # 带有符号的16位整数
SHORT_US = "short_u"  # 不带符号的16位整数
INT = "int_s"         # 带有符号的32位整数
INT_US = "int_u"      # 不带符号的32位整数
FLOAT_H = "float_h"   # 半精度浮点数
FLOAT = "float"       # 单精度浮点数
FLOAT_D = "double"    # 双精度浮点数
FIXED = "fixed"       # 定点数

# uniform_type
FLOAT_VEC1 = "float_vec1"
FLOAT_VEC2 = "float_vec2"
FLOAT_VEC3 = "float_vec3"
FLOAT_VEC4 = "float_vec4"
INT_VEC1 = "int_vec1"
INT_VEC2 = "int_vec2"
INT_VEC3 = "int_vec3"
INT_VEC4 = "int_vec4"
ARRAY_FLOAT_VEC1 = "array(float_vec1)"
ARRAY_FLOAT_VEC2 = "array(float_vec2)"
ARRAY_FLOAT_VEC3 = "array(float_vec3)"
ARRAY_FLOAT_VEC4 = "array(float_vec4)"
ARRAY_INT_VEC1 = "array(int_vec1)"
ARRAY_INT_VEC2 = "array(int_vec2)"
ARRAY_INT_VEC3 = "array(int_vec3)"
ARRAY_INT_VEC4 = "array(int_vec4)"
ARRAY_MATRIX_VEC2 = "array(matrix_vec2)"
ARRAY_MATRIX_VEC3 = "array(matrix_vec3)"
ARRAY_MATRIX_VEC4 = "array(matrix_vec4)"

# bool
TRUE = GL_TRUE
FALSE = GL_FALSE

# light_type
POINT = "point"    # 点光源
DIRECT = "direct"  # 方向光源

# img_type
RGB = "rgb"    # 红、绿、蓝通道
RGBA = "rgba"  # 红、绿、蓝、不透明度通道

# wrap
REPEAT = "repeat"      # 超出边缘后重复
MIRRORED = "mirrored"  # 超出边缘后镜像
EDGE = "edge"          # 超出边缘后延伸边缘颜色
BORDER = "border"      # 超出边缘后
