from pyglm import glm
import math


class Bone:
    def __init__(self, init_pos, init_length, init_toward):
        """
        单个骨骼节点
        :param init_pos:    骨骼根初始位置，整个骨骼将会绕该点旋转，绑定该骨骼的蒙皮会结合权重绕该点旋转。需填写：(x, y, z)
        :param init_length: 骨骼初始长度，这会决定子骨骼与父骨骼之间的距离。
        :param init_toward: 骨骼初始方向，这会决定子骨骼在父骨骼的什么方向。需填写：(yaw, pitch, roll)
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

    def add_child(self, init_length, init_toward):
        """
        添加子骨骼，该方法将根据父骨骼的初始位置、长度和方向自动计算子骨骼的初始位置。当父骨骼发生改变时，父骨骼将自动向子骨骼传递旋转角度和旋转
        后子骨骼的位置。
        :param init_length: 子骨骼初始长度，这会决定子骨骼与子骨骼的子骨骼之间的距离。
        :param init_toward: 子骨骼初始方向，这会决定子骨骼的子骨骼在子骨骼的什么方向。需填写：(yaw, pitch, roll)
        :return: 子骨骼对象(Bone类)
        """
        # 计算子骨骼的初始位置（在父骨骼末端）
        child_init_pos = self._get_init_end_position()
        # 计算子骨骼的偏移位置（在父骨骼末端）
        child_real_pos = self._get_end_position()

        # 创建子骨骼
        child = Bone(child_init_pos, init_length, init_toward)

        # 移动子骨骼到偏移位置
        child.move(
            child_real_pos[0],
            child_real_pos[1],
            child_real_pos[2]
        )

        self.children.append(child)
        return child

    def move(self, x, y, z):
        """
        移动骨骼，特定着色器会根据该位置结合权重改变顶点位置，同时移动子骨骼位置。
        :param x: x轴偏移量
        :param y: y轴偏移量
        :param z: z轴偏移量
        :return: None
        """
        self.pos = glm.vec3(x, y, z)

        child_real_pos = self._get_end_position()

        # 更新子骨骼位置
        for child in self.children:
            child.move(*child_real_pos)

        self._mark_dirty()

    def turn(self, yaw, pitch, roll):
        """
        旋转骨骼，特定着色器会根据该方向结合权重改变顶点位置，同时移动子骨骼位置。
        :param yaw:   偏移角度
        :param pitch: 俯仰角度
        :param roll:  横滚角度
        :return: None
        """
        self.toward = glm.vec3(yaw, pitch, roll)

        child_real_pos = self._get_end_position()

        # 更新子骨骼位置
        for child in self.children:
            child.move(*child_real_pos)

        self._mark_dirty()

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

    def _get_init_end_position(self):
        """
        获取骨骼初始末端位置
        :return: (x, y, z)
        """
        # 构建初始变换矩阵
        matrix = glm.mat4(1.0)
        matrix = glm.translate(matrix, self.init_pos)

        # 应用初始方向旋转
        matrix = glm.rotate(matrix, glm.radians(-self.init_toward.x), glm.vec3(0.0, 1.0, 0.0))
        matrix = glm.rotate(matrix, glm.radians(self.init_toward.y), glm.vec3(1.0, 0.0, 0.0))
        matrix = glm.rotate(matrix, glm.radians(self.init_toward.z), glm.vec3(0.0, 0.0, 1.0))

        # 沿Z轴延伸骨骼长度
        end_point = glm.vec4(0.0, 0.0, self.init_length, 1.0)
        end_pos = matrix * end_point

        return end_pos.x, end_pos.y, end_pos.z

    def _get_end_position(self):
        """
        获取骨骼末端位置
        :return: (x, y, z)
        """
        # 构建初始变换矩阵
        matrix = glm.mat4(1.0)
        matrix = glm.translate(matrix, self.pos)

        # 应用初始方向旋转
        matrix = glm.rotate(matrix, glm.radians(-self.toward.x), glm.vec3(0.0, 1.0, 0.0))
        matrix = glm.rotate(matrix, glm.radians(self.toward.y), glm.vec3(1.0, 0.0, 0.0))
        matrix = glm.rotate(matrix, glm.radians(self.toward.z), glm.vec3(0.0, 0.0, 1.0))

        # 沿Z轴延伸骨骼长度
        end_point = glm.vec4(0.0, 0.0, self.length, 1.0)
        end_pos = matrix * end_point

        return end_pos.x, end_pos.y, end_pos.z

    def _update_matrix(self):
        """更新骨骼变换矩阵"""
        if not self._matrix_dirty:
            return

        # 构建局部变换矩阵
        local_matrix = glm.mat4(1.0)

        # 移动
        local_matrix = glm.translate(
            local_matrix,
            glm.vec3(
                self.pos.x-self.init_pos.x,
                self.pos.y-self.init_pos.y,
                self.pos.z-self.init_pos.z
            )
        )

        # 旋转
        local_matrix = glm.rotate(
            local_matrix, glm.radians(-self.toward.x-self.init_toward.x), glm.vec3(0.0, 1.0, 0.0)
        )
        local_matrix = glm.rotate(
            local_matrix, glm.radians(self.toward.y-self.init_toward.y), glm.vec3(1.0, 0.0, 0.0)
        )
        local_matrix = glm.rotate(
            local_matrix, glm.radians(self.toward.z-self.init_toward.z), glm.vec3(0.0, 0.0, 1.0)
        )

        # 缩放长度
        scale = self.length / self.init_length if self.init_length > 0 else 1.0
        local_matrix = glm.scale(local_matrix, glm.vec3(1.0, 1.0, scale))

        # 构建初始变换矩阵
        init_matrix = glm.mat4(1.0)
        init_matrix = glm.translate(init_matrix, self.init_pos)
        init_matrix = glm.rotate(init_matrix, glm.radians(-self.init_toward.x), glm.vec3(0.0, 1.0, 0.0))
        init_matrix = glm.rotate(init_matrix, glm.radians(self.init_toward.y), glm.vec3(1.0, 0.0, 0.0))
        init_matrix = glm.rotate(init_matrix, glm.radians(self.init_toward.z), glm.vec3(0.0, 0.0, 1.0))

        # 计算世界变换矩阵
        self._world_matrix = init_matrix * local_matrix

        # 计算逆绑定矩阵（初始姿态的逆矩阵）
        self._inverse_bind_matrix = glm.inverse(init_matrix)

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

        self._mark_dirty()


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
