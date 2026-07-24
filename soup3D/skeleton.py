from pyglm import glm
import math
import weakref


class Bone:
    def __init__(self, init_pos, init_length, init_toward):
        """
        单个骨骼节点
        :param init_pos:    骨骼根初始位置，使用特定着色器的网格会基于该点结合权重进行环绕、缩放和位移。需填写：(x, y, z)
        :param init_length: 骨骼初始长度，用于参照缩放比例。
        :param init_toward: 骨骼初始方向，用于参照旋转方向。需填写：(yaw, pitch, roll)
        """
        if not isinstance(init_pos, (list, tuple)) or len(init_pos) != 3:
            raise TypeError("init_pos must be a list or tuple of 3 numbers")
        for p in init_pos:
            if not isinstance(p, (int, float)):
                raise TypeError("init_pos elements must be int or float")
        if not isinstance(init_length, (int, float)):
            raise TypeError("init_length must be an int or float")
        if not isinstance(init_toward, (list, tuple)) or len(init_toward) != 3:
            raise TypeError("init_toward must be a list or tuple of 3 numbers")
        for t in init_toward:
            if not isinstance(t, (int, float)):
                raise TypeError("init_toward elements must be int or float")

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

        # 关联的着色器（弱引用，防止循环引用导致内存泄漏）
        self._bound_shaders = weakref.WeakValueDictionary()

    def add_child(self, child):
        """
        添加子骨骼，当该骨骼发生位移、缩放、旋转等行为时，父骨骼会自动更改子骨骼位置。需要注意的是，无论该骨骼发生的行为是位移、缩放还是旋转，子
        骨骼都只会发生位移，不会继承其他动作。
        :param child: 需要添加为子骨骼的骨骼。
        :return: None
        """
        if not isinstance(child, Bone):
            raise TypeError("child must be a Bone instance")

        self.children.append(child)

    def move(self, x, y, z):
        """
        移动骨骼，特定着色器会根据该位置结合权重改变顶点位置，同时移动子骨骼到(子骨骼初始位置+(父骨骼实际位置-父骨骼初始位置))。
        :param x: x轴偏移量
        :param y: y轴偏移量
        :param z: z轴偏移量
        :return: None
        """
        if not isinstance(x, (int, float)):
            raise TypeError("x must be an int or float")
        if not isinstance(y, (int, float)):
            raise TypeError("y must be an int or float")
        if not isinstance(z, (int, float)):
            raise TypeError("z must be an int or float")

        self.pos = glm.vec3(x, y, z)
        # 子骨骼移动到: 子骨骼初始位置 + (父骨骼实际位置 - 父骨骼初始位置)
        offset = self.pos - self.init_pos
        for child in self.children:
            child.move(*(child.init_pos + offset))
        self._mark_dirty()

    def resize(self, length):
        """
        缩放骨骼，特定着色器会根据该长度结合权重改变顶点位置，同时缩放子骨骼长度。
        :param length: 新长度
        :return: None
        """
        if not isinstance(length, (int, float)):
            raise TypeError("length must be an int or float")

        scale = length / self.init_length
        self.length = length
        # 子骨骼到该骨骼的距离随缩放改变
        for child in self.children:
            new_pos = self.pos + (child.init_pos - self.init_pos) * scale
            child.move(*new_pos)
        self._mark_dirty()

    def turn(self, yaw, pitch, roll):
        """
        旋转骨骼，特定着色器会根据该方向结合权重改变顶点位置，同时移动子骨骼位置。
        :param yaw:   偏移角度
        :param pitch: 俯仰角度
        :param roll:  横滚角度
        :return: None
        """
        if not isinstance(yaw, (int, float)):
            raise TypeError("yaw must be an int or float")
        if not isinstance(pitch, (int, float)):
            raise TypeError("pitch must be an int or float")
        if not isinstance(roll, (int, float)):
            raise TypeError("roll must be an int or float")

        self.toward = glm.vec3(yaw, pitch, roll)
        # 构建当前旋转矩阵（相对于初始旋转的增量）
        init_rot = self._build_rotation_matrix(self.init_toward)
        cur_rot = self._build_rotation_matrix(self.toward)
        delta_rot = cur_rot * glm.inverse(init_rot)
        # 子骨骼根绕该骨骼旋转
        for child in self.children:
            offset = child.init_pos - self.init_pos
            rotated = delta_rot * glm.vec4(offset, 1.0)
            child.move(*(self.pos + glm.vec3(rotated)))
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

    def _build_rotation_matrix(self, toward):
        """根据朝向构建旋转矩阵"""
        m = glm.mat4(1.0)
        m = glm.rotate(m, glm.radians(-toward.x), glm.vec3(0.0, 1.0, 0.0))
        m = glm.rotate(m, glm.radians(toward.y), glm.vec3(1.0, 0.0, 0.0))
        m = glm.rotate(m, glm.radians(toward.z-toward.x), glm.vec3(0.0, 0.0, 1.0))
        return m

    def _update_matrix(self):
        """更新骨骼变换矩阵"""
        if not self._matrix_dirty:
            return

        # 缩放因子
        scale = self.length / self.init_length

        # 初始姿态矩阵: 位移 * 旋转 * 缩放（glTF规范要求包含所有变换）
        bind_matrix = glm.translate(glm.mat4(1.0), self.init_pos)
        bind_matrix = bind_matrix * self._build_rotation_matrix(self.init_toward)
        bind_matrix = glm.scale(bind_matrix, glm.vec3(1.0))

        # 当前姿态矩阵: 位移 * 旋转 * 缩放
        current_matrix = glm.translate(glm.mat4(1.0), self.pos)
        current_matrix = current_matrix * self._build_rotation_matrix(self.toward)
        current_matrix = glm.scale(current_matrix, glm.vec3(scale))

        # 逆绑定矩阵（glTF的inverseBindMatrix是绑定姿态世界矩阵的逆）
        self._inverse_bind_matrix = glm.inverse(bind_matrix)

        # 蒙皮矩阵 = 当前姿态世界矩阵 * 逆绑定矩阵
        # 当初始姿态与当前姿态相同时，结果为单位矩阵，顶点不会发生位移
        self._world_matrix = current_matrix * self._inverse_bind_matrix

        self._matrix_dirty = False

    def _mark_dirty(self):
        """标记矩阵需要更新"""
        self._matrix_dirty = True
        # 递归标记所有子骨骼为dirty
        for child in self.children:
            child._mark_dirty()
        # 通知所有关联的着色器骨骼已变化
        for shader in self._bound_shaders.values():
            shader.mark_bones_dirty()

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
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        if not isinstance(bone, Bone):
            raise TypeError("bone must be a Bone instance")

        self.bones[name] = bone
        self._bone_index_map[name] = len(self._bone_index_map)
        self._max_bones = max(self._max_bones, len(self._bone_index_map))

    def get_bone(self, name: str) -> Bone:
        """
        获取指定名称的骨骼
        :param name: 骨骼名称
        :return: 骨骼对象
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        return self.bones.get(name)

    def get_bone_index(self, name: str) -> int:
        """
        获取骨骼在骨架中的索引
        :param name: 骨骼名称
        :return: 骨骼索引
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string")
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

    def make_pose(self, pose_data: dict):
        """
        根据数据调整每个骨骼的姿态
        :param pose_data: 姿态数据
        :return: None
        """
        for bone_name in pose_data:
            bone = self.get_bone(bone_name)
            bone.pos = glm.vec3(*pose_data[bone_name][:3])
            bone.length = pose_data[bone_name][3]
            bone.toward = glm.vec3(*pose_data[bone_name][4:])
            bone._mark_dirty()

    def reset_all(self):
        """
        重置所有骨骼到初始姿态
        :return: None
        """
        for bone in self.bones.values():
            bone.reset()
