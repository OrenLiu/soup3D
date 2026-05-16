from pyglm import glm
import math


class Bone:
    def __init__(self, init_pos, init_length, init_toward):
        """
        单个骨骼节点
        :param init_pos:    骨骼根初始位置，使用特定着色器的网格会基于该点结合权重进行环绕、缩放和位移。需填写：(x, y, z)
        :param init_length: 骨骼初始长度，用于参照缩放比例。
        :param init_toward: 骨骼初始方向，用于参照旋转方向。需填写：(yaw, pitch, roll)
        """
        self.init_pos = glm.vec3(*init_pos)
        self.init_length = init_length
        self.init_toward = glm.vec3(*init_toward)

        # 当前变换
        self.pos = glm.vec3(*init_pos)
        self.length = init_length
        self.toward = glm.vec3(*init_toward)

        # 层级结构
        self.children = []

        # 缓存
        self._matrix_dirty = True
        self._world_matrix = glm.mat4(1.0)
        self._inverse_bind_matrix = glm.mat4(1.0)

    def add_child(self, child):
        """
        添加子骨骼，当该骨骼发生位移、缩放、旋转等行为时，父骨骼会自动更改子骨骼位置。需要注意的是，无论该骨骼发生的行为是位移、缩放还是旋转，子
        骨骼都只会发生位移，不会继承其他动作。
        :param child: 需要添加为子骨骼的骨骼。
        :return: None
        """
        self.children.append(child)

    def move(self, x, y, z):
        """
        移动骨骼，特定着色器会根据该位置结合权重改变顶点位置，同时移动子骨骼到(子骨骼初始位置+(父骨骼实际位置-父骨骼初始位置))。
        :param x: x轴偏移量
        :param y: y轴偏移量
        :param z: z轴偏移量
        :return: None
        """
        self.pos = glm.vec3(x, y, z)
        ...

    def resize(self, length):
        """
        缩放骨骼，特定着色器会根据该长度结合权重改变顶点位置，同时缩放子骨骼长度。
        :param length: 新长度
        :return: None
        """
        self.length = length
        ...

    def turn(self, yaw, pitch, roll):
        """
        旋转骨骼，特定着色器会根据该方向结合权重改变顶点位置，同时移动子骨骼位置。
        :param yaw:   偏移角度
        :param pitch: 俯仰角度
        :param roll:  横滚角度
        :return: None
        """
        self.toward = glm.vec3(yaw, pitch, roll)
        ...

    def get_bone_matrix(self):
        """
        获取骨骼的变换矩阵（用于着色器）
        :return: 4x4变换矩阵
        """
        self._update_matrix()
        return self._world_matrix

    def get_inverse_bind_matrix(self):
        """
        获取骨骼的逆绑定矩阵（用于蒙皮绑定）
        :return: 4x4逆绑定矩阵
        """
        self._update_matrix()
        return self._inverse_bind_matrix

    def _update_matrix(self):
        """更新骨骼变换矩阵"""
        if not self._matrix_dirty:
            return

        # 构建初始姿态矩阵
        bind_matrix = glm.mat4(1.0)
        bind_matrix = glm.translate(bind_matrix, self.init_pos)
        bind_matrix = glm.rotate(bind_matrix, glm.radians(-self.init_toward.x), glm.vec3(0.0, 1.0, 0.0))
        bind_matrix = glm.rotate(bind_matrix, glm.radians(self.init_toward.y), glm.vec3(1.0, 0.0, 0.0))
        bind_matrix = glm.rotate(bind_matrix, glm.radians(self.init_toward.z), glm.vec3(0.0, 0.0, 1.0))

        # 构建当前姿态矩阵
        current_matrix = glm.mat4(1.0)
        current_matrix = glm.translate(current_matrix, self.pos)
        current_matrix = glm.rotate(current_matrix, glm.radians(-self.toward.x), glm.vec3(0.0, 1.0, 0.0))
        current_matrix = glm.rotate(current_matrix, glm.radians(self.toward.y), glm.vec3(1.0, 0.0, 0.0))
        current_matrix = glm.rotate(current_matrix, glm.radians(self.toward.z), glm.vec3(0.0, 0.0, 1.0))

        # 逆绑定矩阵
        self._inverse_bind_matrix = glm.inverse(bind_matrix)

        # 世界矩阵 = 当前姿态 * 逆初始姿态
        # 当初始姿态与当前姿态相同时，结果为单位矩阵，顶点不会发生位移
        self._world_matrix = current_matrix * self._inverse_bind_matrix

        self._matrix_dirty = False

    def _mark_dirty(self):
        """标记矩阵需要更新"""
        self._matrix_dirty = True
        # 递归标记所有子骨骼为dirty
        for child in self.children:
            child._mark_dirty()

    def reset(self):
        """
        重置骨骼到初始姿态。不建议单个骨骼重置，可能会导致骨骼断层。
        :return: None
        """
        self.pos = glm.vec3(self.init_pos)
        self.toward = glm.vec3(self.init_toward)
        self.length = self.init_length
        ...


class Skeleton:
    def __init__(self):
        """
        骨架，包含多个骨骼的字典容器
        """
        self.bones = {}
        self._bone_index_map = {}
        self._max_bones = 0

    def add_bone(self, name: str, bone: Bone):
        """
        添加骨骼到骨架
        :param name: 骨骼名称
        :param bone: 骨骼对象
        :return: None
        """
        self.bones[name] = bone
        self._bone_index_map[name] = len(self._bone_index_map)
        self._max_bones = max(self._max_bones, len(self._bone_index_map))

    def get_bone(self, name: str) -> Bone:
        """
        获取指定名称的骨骼
        :param name: 骨骼名称
        :return: 骨骼对象
        """
        return self.bones.get(name)

    def get_bone_index(self, name: str) -> int:
        """
        获取骨骼在骨架中的索引
        :param name: 骨骼名称
        :return: 骨骼索引
        """
        return self._bone_index_map.get(name, -1)

    def get_bone_matrices(self) -> list:
        """
        获取所有骨骼的变换矩阵（用于着色器）
        :return: 骨骼矩阵列表
        """
        matrices = []
        for i in range(self._max_bones):
            matrices.append(glm.mat4(1.0))

        for name, bone in self.bones.items():
            idx = self._bone_index_map[name]
            if idx < len(matrices):
                matrices[idx] = bone.get_bone_matrix()

        return matrices

    def get_max_bones(self) -> int:
        """
        获取骨架中的骨骼数量
        :return: 骨骼数量
        """
        return self._max_bones

    def reset_all(self):
        """
        重置所有骨骼到初始姿态
        :return: None
        """
        for bone in self.bones.values():
            bone.reset()
