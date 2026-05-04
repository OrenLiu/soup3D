class Bone:
    def __init__(self, init_pos, init_length, init_toward):
        """
        单个骨骼节点
        :param init_pos:    骨骼根初始位置，整个骨骼将会绕该点旋转，绑定该骨骼的蒙皮会结合权重绕该点旋转。需填写：(x, y, z)
        :param init_length: 骨骼初始长度，这会决定子骨骼与父骨骼之间的距离。
        :param init_toward: 骨骼初始方向，这会决定子骨骼在父骨骼的什么方向。需填写：(yaw, pitch, roll)
        """
        self.init_pos = init_pos
        self.init_length = init_length
        self.init_toward = init_toward

        self.x = 0
        self.y = 0
        self.z = 0

        self.length = 0

        self.yaw = 0
        self.pitch = 0
        self.roll = 0

        self.children = []
        ...

    def add_child(self, init_length, init_toward):
        """
        添加子骨骼，该方法将根据父骨骼的初始位置、长度和方向自动计算子骨骼的初始位置。当父骨骼发生改变时，父骨骼将自动向子骨骼传递旋转角度和旋转
        后子骨骼的位置。
        :param init_length: 子骨骼初始长度，这会决定子骨骼与子骨骼的子骨骼之间的距离。
        :param init_toward: 子骨骼初始方向，这会决定子骨骼的子骨骼在子骨骼的什么方向。需填写：(yaw, pitch, roll)
        :return: 子骨骼对象(Bone类)
        """
        ...

    def move(self, x, y, z):
        """
        移动骨骼，特定着色器会根据该位置结合权重改变顶点位置，同时移动子骨骼位置。
        :param x: x轴偏移量
        :param y: y轴偏移量
        :param z: z轴偏移量
        :return: None
        """
        self.x = x
        self.y = y
        self.z = z
        ...

    def turn(self, yaw, pitch, roll):
        """
        旋转骨骼，特定着色器会根据该方向结合权重改变顶点位置，同时移动子骨骼位置。
        :param yaw:   偏移角度
        :param pitch: 俯仰角度
        :param roll:  横滚角度
        :return: None
        """
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
        ...
