"""
调用：soup3D.s3dm
数学工具库：旋转表示（四元数 w, x, y, z，pyglm 为 w-first）、平面旋转与向量运算。
供 engine 各模块收编散落的数学辅助函数，统一维护。
"""
from pyglm import glm
import math
from math import cos, sin, pi, sqrt

__all__ = [
    "euler_to_quat", "quat_to_euler",
    "bone_euler_to_quat", "bone_quat_to_euler",
    "parse_rotation",
    "rotated", "normalize", "cross", "quat_to_mat4",
]


def euler_to_quat(yaw, pitch, roll):
    """
    欧拉角转四元数（统一约定）
    与引擎历史行为一致：R = Ry(-yaw)·Rx(pitch)·Rz(roll)，角度单位为度。
    :param yaw:   绕y轴偏航角
    :param pitch: 绕x轴俯仰角
    :param roll:  绕z轴横滚角
    :return: glm.quat，分量为 (w, x, y, z)
    """
    if not isinstance(yaw, (int, float)):
        raise TypeError("yaw must be an int or float")
    if not isinstance(pitch, (int, float)):
        raise TypeError("pitch must be an int or float")
    if not isinstance(roll, (int, float)):
        raise TypeError("roll must be an int or float")

    qy = glm.angleAxis(glm.radians(-yaw), glm.vec3(0, 1, 0))
    qx = glm.angleAxis(glm.radians(pitch), glm.vec3(1, 0, 0))
    qz = glm.angleAxis(glm.radians(roll), glm.vec3(0, 0, 1))
    return qy * qx * qz


def quat_to_euler(q):
    """
    四元数转欧拉角（统一约定的逆变换）
    :param q: glm.quat 或 (w, x, y, z) 序列
    :return: (yaw, pitch, roll) 角度
    """
    if not isinstance(q, glm.quat):
        q = glm.quat(*q)
    w, x, y, z = q.w, q.x, q.y, q.z
    # R = Ry(-yaw) Rx(pitch) Rz(roll) 的 YXZ 提取
    siny = 2 * (w * y + x * z)
    cosy = 1 - 2 * (x * x + y * y)
    a = math.atan2(siny, cosy)
    sinp = 2 * (w * x - z * y)
    sinp = max(-1.0, min(1.0, sinp))
    b = math.asin(sinp)
    sinr = 2 * (w * z + x * y)
    cosr = 1 - 2 * (x * x + z * z)
    c = math.atan2(sinr, cosr)
    # 引擎约定中 Ry 用 -yaw，故 yaw = -a；pitch、roll 不变号
    return -math.degrees(a), math.degrees(b), math.degrees(c)


def bone_euler_to_quat(yaw, pitch, roll):
    """
    欧拉角转四元数（Bone 历史耦合约定）
    与 Bone 蒙皮矩阵历史行为一致：R = Ry(-yaw)·Rx(pitch)·Rz(roll-yaw)。
    :param yaw:   绕y轴偏航角
    :param pitch: 绕x轴俯仰角
    :param roll:  绕z轴横滚角
    :return: glm.quat
    """
    if not isinstance(yaw, (int, float)):
        raise TypeError("yaw must be an int or float")
    if not isinstance(pitch, (int, float)):
        raise TypeError("pitch must be an int or float")
    if not isinstance(roll, (int, float)):
        raise TypeError("roll must be an int or float")
    return euler_to_quat(yaw, pitch, roll - yaw)


def bone_quat_to_euler(q):
    """
    bone_euler_to_quat 的逆变换
    :param q: glm.quat 或 (w, x, y, z) 序列
    :return: (yaw, pitch, roll) 角度
    """
    yaw, pitch, roll = quat_to_euler(q)
    # Bone 约定中 R = Ry(-yaw) Rx(pitch) Rz(roll-yaw)，标准提取的 roll 项 = roll - yaw，
    # 故 bone 的 roll = 提取roll + yaw
    return yaw, pitch, roll + yaw


def parse_rotation(value):
    """
    解析旋转输入：长度检测，3 个数字为欧拉角(度)，4 个数字为四元数 (w, x, y, z)
    :param value: glm.quat，或包含 3 个(欧拉角) / 4 个(四元数)数字的 list/tuple
    :return: 归一化的 glm.quat
    """
    if isinstance(value, glm.quat):
        q = value
    elif isinstance(value, (list, tuple)) and len(value) == 3:
        return euler_to_quat(value[0], value[1], value[2])
    elif isinstance(value, (list, tuple)) and len(value) == 4:
        q = glm.quat(value[0], value[1], value[2], value[3])
    else:
        raise TypeError("rotation must be a glm.quat or a list/tuple of 3 or 4 numbers")
    q_len = glm.length(q)
    if q_len == 0:
        raise ValueError("quaternion must not be zero")
    return q / q_len


def rotated(Xa: int | float, Ya: int | float,
            Xb: int | float, Yb: int | float,
            degree: int | float) -> tuple[float, float]:
    """
    点A绕点B旋转特定角度后，点A的坐标
    :param Xa:     环绕点(点A)X坐标
    :param Ya:     环绕点(点A)Y坐标
    :param Xb:     被环绕点(点B)X坐标
    :param Yb:     被环绕点(点B)Y坐标
    :param degree: 旋转角度
    :return: 点A旋转后的X坐标, 点A旋转后的Y坐标
    """
    if not isinstance(Xa, (int, float)):
        raise TypeError("Xa must be an int or float")
    if not isinstance(Ya, (int, float)):
        raise TypeError("Ya must be an int or float")
    if not isinstance(Xb, (int, float)):
        raise TypeError("Xb must be an int or float")
    if not isinstance(Yb, (int, float)):
        raise TypeError("Yb must be an int or float")
    if not isinstance(degree, (int, float)):
        raise TypeError("degree must be an int or float")
    degree = degree * pi / 180
    outx = (Xa - Xb) * cos(degree) - (Ya - Yb) * sin(degree) + Xb
    outy = (Xa - Xb) * sin(degree) + (Ya - Yb) * cos(degree) + Yb
    return outx, outy


def normalize(v: list[float]) -> list[float]:
    """
    归一化三维向量
    :param v: 长度为 3 的数字列表
    :return: 归一化后的新列表
    """
    length = sqrt(sum(i * i for i in v))
    if length == 0:
        return [0.0, 0.0, 0.0]
    return [i / length for i in v]


def cross(a: list[float], b: list[float]) -> list[float]:
    """
    计算三维向量叉乘
    :param a: 长度为 3 的数字列表
    :param b: 长度为 3 的数字列表
    :return: 叉乘结果列表
    """
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def quat_to_mat4(qx, qy, qz, qw):
    """
    将四元数转换为4x4旋转矩阵
    :param qx: 四元数x分量
    :param qy: 四元数y分量
    :param qz: 四元数z分量
    :param qw: 四元数w分量
    :return: 4x4矩阵
    """
    mat = glm.mat4(1.0)
    mat[0][0] = 1 - 2 * (qy * qy + qz * qz)
    mat[0][1] = 2 * (qx * qy + qw * qz)
    mat[0][2] = 2 * (qx * qz - qw * qy)
    mat[1][0] = 2 * (qx * qy - qw * qz)
    mat[1][1] = 1 - 2 * (qx * qx + qz * qz)
    mat[1][2] = 2 * (qy * qz + qw * qx)
    mat[2][0] = 2 * (qx * qz + qw * qy)
    mat[2][1] = 2 * (qy * qz - qw * qx)
    mat[2][2] = 1 - 2 * (qx * qx + qy * qy)
    return mat
