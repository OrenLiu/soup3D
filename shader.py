"""
处理soup3D中的着色系统
"""
import PIL.Image


class Texture:
    def __init__(self, pil_pic: PIL.Image.Image):
        """
        贴图，基于pillow处理图像
        提取通道时：
        通道0: 红色通道
        通道1: 绿色通道
        通道2: 蓝色通道
        通道3: 透明度(如无该通道，则统一返回1)
        :param pil_pic: pillow图像
        """
        self.pil_pic = pil_pic

        self.hash = None
        self.update()

    def update(self):
        self.change_hash()

    def change_hash(self):
        """
        更改着色单元哈希值
        :return: None
        """
        self.hash = self.get_hash()

    def get_hash(self):
        """
        获取新着色单元哈希值
        :return: 新着色单元哈希值
        """
        return hash_shader(self.pil_pic.tobytes())

    def reset(self, pil_pic: PIL.Image.Image | None = None):
        """
        重设类成员，并重置着色单元哈希值
        参数同__init__，无需更改的参数可填写None
        """
        if pil_pic is not None:
            self.pil_pic = pil_pic

        self.change_hash()


class Channel:
    def __init__(self, texture: Texture, channelID: int):
        """
        提取贴图中的单个通道
        :param texture:   提取通道的贴图
        :param channelID: 通道编号
        """
        self.texture = texture
        self.channelID = channelID

        self.band_cache = None  # 添加通道图像缓存

        self.hash = None
        self.update()

    def get_pil_band(self, size=None):
        """获取通道的PIL图像，可指定尺寸"""
        img = self.texture.pil_pic
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        bands = img.split()
        band = bands[self.channelID]

        if size is not None and size != band.size:
            band = band.resize(size, PIL.Image.BILINEAR)

        return band

    def update(self):
        self.change_hash()

    def change_hash(self):
        """
        更改着色单元哈希值
        :return: None
        """
        self.hash = self.get_hash()

    def get_hash(self):
        """
        获取新着色单元哈希值
        :return: 新着色单元哈希值
        """
        return hash_shader(self.texture, self.channelID)

    def reset(self,
              texture: Texture | None = None,
              channelID: int | None = None):
        """
        重设类成员，并重置着色单元哈希值
        参数同__init__，无需更改的参数可填写None
        """
        if texture is not None:
            if not isinstance(texture, Texture):
                raise TypeError(f"Texture requires Texture, got {type(texture)}")
            self.texture = texture
        if channelID is not None:
            if not isinstance(channelID, int):
                raise TypeError(f"channelID requires int, got {type(channelID)}")
            self.channelID = channelID

        self.change_hash()


class MixChannel:
    def __init__(self,
                 resize: tuple[int, int],
                 R: float | Channel,
                 G: float | Channel,
                 B: float | Channel,
                 A: float | Channel = 1.0):
        """
        混合通道成为一个贴图
        混合通道贴图(MixChannel)可通过类似贴图(Texture)的方式提取通道
        :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像
        :param R: 红色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param G: 绿色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param B: 蓝色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        :param A: 透明度通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道
        """
        self.resize = resize
        self.R = R
        self.G = G
        self.B = B
        self.A = A

        self.pil_pic = None  # 缓存混合通道后的图像，以便父着色单元提取

        self.hash = None
        self.update()

    def update(self):
        """
        更新所有缓存项
        :return: None
        """
        # 创建目标尺寸的空图像（RGBA模式）
        result = PIL.Image.new('RGBA', self.resize)

        # 处理每个通道：R, G, B, A
        bands = {}
        for channel_name in ['R', 'G', 'B', 'A']:
            source = getattr(self, channel_name)

            if isinstance(source, (float, int)):  # 浮点常数
                # 创建纯色通道图像（值为0-255的整数）
                value = max(0, min(255, int(source * 255)))
                band = PIL.Image.new('L', self.resize, value)
                bands[channel_name] = band

            elif isinstance(source, Channel):  # Channel对象
                texture_img = source.texture.pil_pic

                # 转换为RGBA确保有四个通道
                if texture_img.mode != 'RGBA':
                    texture_img = texture_img.convert('RGBA')

                # 分离RGBA通道
                r_band, g_band, b_band, a_band = texture_img.split()
                all_bands = {'R': r_band, 'G': g_band, 'B': b_band, 'A': a_band}

                # 选择所需通道并调整尺寸
                selected = all_bands.get(
                    ['R', 'G', 'B', 'A'][source.channelID],
                    PIL.Image.new('L', texture_img.size, 255)  # 默认全白（1.0）
                )
                bands[channel_name] = selected.resize(self.resize, PIL.Image.BILINEAR)

        # 合并所有通道（缺失通道用灰色占位）
        final_bands = []
        for ch in ['R', 'G', 'B', 'A']:
            final_bands.append(bands.get(ch, PIL.Image.new('L', self.resize, 128)))

        # 合并为最终RGBA图像
        self.pil_pic = PIL.Image.merge('RGBA', final_bands)

        # 更新着色单元哈希值
        self.change_hash()

    def change_hash(self):
        """
        更改着色单元哈希值
        :return: None
        """
        self.hash = self.get_hash()

    def get_hash(self):
        """
        获取新着色单元哈希值
        :return: 新着色单元哈希值
        """
        return hash_shader(self.resize, self.R, self.G, self.B, self.A)

    def reset(self,
              resize: tuple[int, int] | None = None,
              R: float | Channel | None = None,
              G: float | Channel | None = None,
              B: float | Channel | None = None,
              A: float | Channel | None = None):
        """
        重设类成员，并重置着色单元哈希值
        参数同__init__，无需更改的参数可填写None
        """
        if resize is not None:
            if not (isinstance(resize, tuple) and len(resize) == 2 and
                    all(isinstance(i, int) for i in resize)):
                raise TypeError("resize requires tuple[int, int]")
            self.resize = resize

        def update_channel(name, value, attr):
            if value is None:
                return
            if not (isinstance(value, (float, Channel)) or
                    (isinstance(value, int) and value == 0)):  # 允许0作为float
                raise TypeError(f"{name} requires float or Channel, got {type(value)}")
            if isinstance(value, float) and not (0.0 <= value <= 1.0):
                raise ValueError(f"{name} must be between 0.0 and 1.0, got {value}")
            setattr(self, attr, value)

        update_channel("R", R, "R")
        update_channel("G", G, "G")
        update_channel("B", B, "B")
        update_channel("A", A, "A")

        self.change_hash()


class BSDF:
    def __init__(self,
                 base_color: Texture | MixChannel,
                 smoothness: float | Channel = 0.0,
                 normal: Texture | MixChannel = None,
                 emission: float | Channel = 0.0):
        """
        原理化双向散射分布函数
        :param base_color: 主要颜色
        :param smoothness: 光滑度
        :param normal:     法线贴图
        :param emission:   自发光度
        """
        self.base_color = base_color
        self.smoothness = smoothness
        self.normal = normal
        if self.normal is None:
            self.normal = MixChannel((1, 1), 0.5, 0.5, 1)
        self.emission = emission

        self.hash = None
        self.change_hash()

    def update(self):
        self.change_hash()

    def change_hash(self):
        """
        更改着色单元哈希值
        :return: None
        """
        self.hash = self.get_hash()

    def get_hash(self):
        """
        获取新着色单元哈希值
        :return: 新着色单元哈希值
        """
        return hash_shader(self.base_color, self.normal, self.emission)

    def reset(self,
              base_color: Texture | MixChannel | None,
              smoothness: float | Channel | None,
              normal: Texture | MixChannel | None,
              emission: float | Channel | None):
        if base_color is not None:
            self.base_color = base_color
        if smoothness is not None:
            self.smoothness = smoothness
        if normal is not None:
            self.normal = normal
        if emission is not None:
            self.emission = emission

        self.change_hash()


type_group = Texture | Channel | MixChannel | BSDF


def shader2mermaid(shader: type_group, visited=None, level=0):
    """
    将着色单元的层级关系以mermaid的方式进行展示
    :param shader: 需要展示其以及其所有子着色单元层级关系的着色单元
    :param visited: 已访问节点的字典，防止无限循环
    :param level: 当前节点的递归层级
    :return: mermaid代码
    """
    if visited is None:
        visited = {}

    # 生成唯一节点ID
    node_id = id(shader)

    # 初始化输出
    mermaid_lines = []

    # 检查是否已访问过该节点
    if node_id in visited:
        return mermaid_lines
    visited[node_id] = True

    # 确定节点描述文本 - 使用更具描述性的标签
    if isinstance(shader, Texture):
        node_label = "[\"Texture\"]"
    elif isinstance(shader, Channel):
        channel_names = {0: "R", 1: "G", 2: "B", 3: "A"}
        node_label = f"[\"Channel {channel_names.get(shader.channelID, '?')}\"]"
    elif isinstance(shader, MixChannel):
        node_label = "[\"MixChannel\"]"
    elif isinstance(shader, BSDF):
        node_label = "[\"BSDF\"]"
    else:
        return mermaid_lines

    # 添加当前节点
    mermaid_lines.append(f"    node_{node_id}{node_label}")

    # 递归处理子节点并添加关系
    if isinstance(shader, Channel):
        # Channel -> Texture
        child_lines = shader2mermaid(shader.texture, visited, level + 1)
        mermaid_lines.extend(child_lines)
        mermaid_lines.append(f"    node_{id(shader.texture)} -->|\"texture\"| node_{node_id}")

    elif isinstance(shader, MixChannel):
        # 处理MixChannel的子通道
        for i, channel in enumerate(['R', 'G', 'B', 'A']):
            value = getattr(shader, channel)

            # 处理常量值
            if isinstance(value, (int, float)):
                const_id = f"{node_id}_{channel}"
                mermaid_lines.append(f"    const_{const_id}[\"Const: {value}\"]")
                mermaid_lines.append(f"    const_{const_id} -->|\"{channel}\"| node_{node_id}")
            # 处理Channel对象
            elif isinstance(value, Channel):
                child_lines = shader2mermaid(value, visited, level + 1)
                mermaid_lines.extend(child_lines)
                mermaid_lines.append(f"    node_{id(value)} -->|\"{channel}\"| node_{node_id}")

    elif isinstance(shader, BSDF):
        # 处理BSDF的子属性
        for prop, value in [
            ('base_color', shader.base_color),
            ('smoothness', shader.smoothness),
            ('normal', shader.normal),
            ('emission', shader.emission)
        ]:
            # 处理常量值
            if isinstance(value, (int, float)):
                const_id = f"{node_id}_{prop}"
                mermaid_lines.append(f"    const_{const_id}[\"Const: {value}\"]")
                mermaid_lines.append(f"    const_{const_id} -->|\"{prop}\"| node_{node_id}")
            # 处理着色单元
            elif isinstance(value, type_group):
                child_lines = shader2mermaid(value, visited, level + 1)
                mermaid_lines.extend(child_lines)
                mermaid_lines.append(f"    node_{id(value)} -->|\"{prop}\"| node_{node_id}")

    # 添加流程图声明
    if level == 0:  # 仅在根节点添加
        codes = ""
        for line in ["flowchart TD"] + mermaid_lines:
            codes += line+"\n"
        return codes
    return mermaid_lines


def hash_shader(*args):
    str_join_hash = ""
    for arg in args:
        if isinstance(arg, type_group):
            str_join_hash += f"{arg.get_hash()},"
        else:
            str_join_hash += f"{arg},"
    return hash(str_join_hash)


def soft_update(shader: type_group):
    """
    软更新着色树，通过比对哈希值判断是否需要更新着色单元
    :return: None
    """
    need_update = False

    if shader.hash != shader.get_hash():
        need_update = True

    if type(shader) is Texture:
        return need_update
    if type(shader) is Channel:
        need_update = need_update or soft_update(shader.texture)
        return need_update
    if type(shader) is MixChannel:
        if type(shader.R) is Channel:
            need_update = need_update or soft_update(shader.R)
        if type(shader.G) is Channel:
            need_update = need_update or soft_update(shader.G)
        if type(shader.B) is Channel:
            need_update = need_update or soft_update(shader.B)
        if type(shader.A) is Channel:
            need_update = need_update or soft_update(shader.A)
        return need_update
    if type(shader) is BSDF:
        if type(shader.base_color) in (Texture, Channel):
            need_update = need_update or soft_update(shader.base_color)
        if type(shader.smoothness) is Channel:
            need_update = need_update or soft_update(shader.smoothness)
        if type(shader.normal) in (Texture, Channel):
            need_update = need_update or soft_update(shader.normal)
        if type(shader.emission) is Channel:
            need_update = need_update or soft_update(shader.emission)
        return need_update

    if need_update:
        shader.update()


if __name__ == '__main__':
    ...
