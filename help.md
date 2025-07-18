# **soup3D** 
   
## __init__:   
调用：soup3D   
这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可   
用于3D游戏开发、数据可视化、3D图形的绘制等开发。   
   
- Face: `类型`   
  - __init__(self, shape_type, surface, vertex): `函数`   
    表面，可用于创建模型(Model类)的线段和多边形   
    :param shape_type: 绘制方式，可以填写这些内容：   
                       "line_b": 不相连线段   
                       "line_s": 连续线段   
                       "line_l": 头尾相连的连续线段   
                       "triangle_b": 不相连三角形   
                       "triangle_s": 相连三角形   
                       "triangle_l": 头尾相连的连续三角形   
    :param surface:    表面使用的BSDF着色器   
    :param vertex:     表面中所有的端点，格式为：   
                       [(x, y, z, u, v), ...]   
   
   
- Model: `类型`   
  - __init__(self, x, y, z): `函数`   
    模型，由多个面(Face类)组成，建议将场景中的面组合成尽量少的模型   
    :param x:    模型原点对应x坐标   
    :param y:    模型原点对应y坐标   
    :param z:    模型原点对应z坐标   
    :param face: 面   
   
  - paint(self): `函数`   
    在单帧绘制该模型   
    :return: None   
   
  - _generate_display_list(self): `函数`   
    生成OpenGL显示列表，应用材质属性   
   
  - show(self): `函数`   
    固定每帧渲染该模型   
    :return: None   
   
  - hide(self): `函数`   
    取消固定渲染   
    :return: None   
   
  - goto(self, x, y, z): `函数`   
    传送模型   
    :param x: 新x坐标   
    :param y: 新y坐标   
    :param z: 新z坐标   
    :return:   
   
  - deep_del(self): `函数`   
    深度清理模型，清理该模型本身及所有该模型用到的元素。在确定不再使用该模型时可使用该方法释放内存。   
    :return: None   
   
   
- _get_channel_value(channel): `函数`   
  从Channel对象或浮点数获取通道值   
   
   
- init(width, height, fov, bg_color, far): `函数`   
  初始化3D引擎   
  :param width:    视网膜宽度   
  :param height:   视网膜高度   
  :param fov:      视野   
  :param bg_color: 背景颜色   
  :param far:      最远渲染距离   
  :return: None   
   
   
- resize(width, height): `函数`   
  重新定义窗口尺寸   
  :param width:  窗口宽度   
  :param height: 窗口高度   
  :return: None   
   
   
- set_title(title): `函数`   
  设置窗口标题   
  :param title: 窗口标题   
  :return: None   
   
   
- set_ico(path): `函数`   
  设置窗口图标   
  :param path: 图标所在位置   
  :return: None   
   
   
- background_color(r, g, b): `函数`   
  设定背景颜色   
  :param r: 红色(0.0-1.0)   
  :param g: 绿色(0.0-1.0)   
  :param b: 蓝色(0.0-1.0)   
  :return: None   
   
   
- _paint_ui(shape, x, y): `函数`   
  在单帧渲染该图形   
   
   
- update(): `函数`   
  更新画布，包括处理渲染队列   
   
   
- open_obj(obj, mtl): `函数`   
  从obj文件导入模型   
  :param obj: *.obj模型文件路径   
  :param mtl: *.mtl纹理文件路径   
  :return: 生成出来的模型数据(Model类)   
   
   
- _rotated(Xa, Ya, Xb, Yb, degree): `函数`   
  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
   
   
   
## ui:   
调用：soup3D.ui   
soup3D的ui子库，用于绘制2D图形，可绘制HUD叠加显示、GUI用户界面等。   
   
- Shape: `类型`   
  - __init__(self, shape_type, texture, vertex): `函数`   
    图形，可以批量生成线段、三角形   
    :param shape_type: 绘制方式，可以填写这些内容：   
                       "line_b": 不相连线段   
                       "line_s": 连续线段   
                       "line_l": 头尾相连的连续线段   
                       "triangle_b": 不相连三角形   
                       "triangle_s": 相连三角形   
                       "triangle_l": 头尾相连的连续三角形   
    :param texture:    使用的纹理对象，默认为None   
    :param vertex:     图形中所有的端点，每个参数的格式为：(x, y, u, v)   
   
  - _setup_projection(self): `函数`   
    设置正交投影   
   
  - _restore_projection(self): `函数`   
    恢复投影矩阵   
   
  - paint(self, x, y): `函数`   
    在单帧渲染该图形   
   
   
- Group: `类型`   
  - __init__(self): `函数`   
    图形组   
    :param arg:    组中所有的图形   
    :param origin: 图形组在屏幕中的位置   
   
  - goto(self, x, y): `函数`   
    设置绝对位置   
   
  - move(self, x, y): `函数`   
    相对移动   
   
  - display(self): `函数`   
    单帧显示   
   
   
- _pil_to_texture(pil_img, texture_id, texture_unit): `函数`   
  将PIL图像转换为OpenGL纹理   
  :param pil_img: PIL图像对象   
  :param texture_id: 已有纹理ID（如None则创建新纹理）   
  :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）   
  :return: 纹理ID   
   
   
   
## event:   
调用：soup3D.event   
事件处理方法库，可添加如鼠标、键盘等事件的处理方式   
   
- bind(event, funk): `函数`   
  事件绑定函数   
  :param event: 事件名称   
  :param funk:  绑定的函数，每个事件只能绑定一个函数，函数   
                需要有1个参数   
  :return: None   
   
   
- check_event(events): `函数`   
   
## name:   
调用：soup3D   
命名空间   
   
   
## light:   
调用：soup3D.light   
光源处理方法库，可在soup3D空间中添加7个光源   
   
- Cone: `类型`   
  - __init__(self, place, toward, color, attenuation, angle): `函数`   
    锥形光线，类似灯泡光线   
    :param place:        光源位置(x, y, z)   
    :param toward:       光源朝向(yaw, pitch, roll)   
    :param color:        光源颜色(red, green, blue)   
    :param attenuation:  线性衰减率   
    :param angle:        锥形光线锥角   
   
  - display(self): `函数`   
    更新光源参数到OpenGL   
   
  - _calc_direction(self): `函数`   
    根据欧拉角计算方向向量   
   
  - goto(self, x, y, z): `函数`   
    更改光源位置   
    :param x: 光源x坐标   
    :param y: 光源y坐标   
    :param z: 光源z坐标   
    :return: None   
   
  - turn(self, yaw, pitch, roll): `函数`   
    更改光线朝向   
    :param yaw:   光线偏移角度   
    :param pitch: 光线府仰角度   
    :param roll:  光线横滚角度   
    :return: None   
   
  - dye(self, r, g, b): `函数`   
    更改光线颜色   
    :param r: 红色   
    :param g: 绿色   
    :param b: 蓝色   
    :return: None   
   
  - turn_off(self): `函数`   
    熄灭光源   
    :return: None   
   
  - turn_on(self): `函数`   
    点亮光源   
    :return: None   
   
  - destroy(self): `函数`   
    摧毁光源，并归还光源编号   
    :return: None   
   
   
- Direct: `类型`   
  - __init__(self, toward, color): `函数`   
    方向光线，类似太阳光线   
    :param toward: 光源朝向(yaw, pitch, roll)   
    :param color:  光源颜色(red, green, blue)   
   
  - display(self): `函数`   
    更新方向光源参数   
   
  - _calc_direction(self): `函数`   
    计算逆向方向向量   
   
  - turn(self, yaw, pitch, roll): `函数`   
    更改光线朝向   
    :param yaw:   光线偏移角度   
    :param pitch: 光线府仰角度   
    :param roll:  光线横滚角度   
    :return: None   
   
  - dye(self, r, g, b): `函数`   
    更改光线颜色   
    :param r: 红色   
    :param g: 绿色   
    :param b: 蓝色   
    :return: None   
   
  - turn_off(self): `函数`   
    熄灭光源   
    :return: None   
   
  - turn_on(self): `函数`   
    点亮光源   
    :return: None   
   
  - destroy(self): `函数`   
    摧毁光源，并归还光源编号   
    :return: None   
   
   
- init(ambientR, ambientG, ambientB): `函数`   
  初始化光源，启用全局光照   
  :param ambientR: 红环境光亮度   
  :param ambientG: 绿环境光亮度   
  :param ambientB: 蓝环境光亮度   
  :return:   
   
   
   
## camera:   
调用：soup3D.camera   
相机方法库，可在soup3D空间内移动相机位置   
   
- goto(x, y, z): `函数`   
  移动相机位置   
  :param x: 相机x坐标位置   
  :param y: 相机y坐标位置   
  :param z: 相机z坐标位置   
  :return: None   
   
   
- turn(yaw, pitch, roll): `函数`   
  旋转相机   
  :param yaw:   相机旋转偏移角   
  :param pitch: 相机旋转俯仰角   
  :param roll:  相机旋转横滚角   
  :return:   
   
   
- update(): `函数`   
  更新相机   
  :return: None   
   
   
   
## shader:   
处理soup3D中的着色系统   
   
- Texture: `类型`   
  - __init__(self, pil_pic): `函数`   
    贴图，基于pillow处理图像   
    提取通道时：   
    通道0: 红色通道   
    通道1: 绿色通道   
    通道2: 蓝色通道   
    通道3: 透明度(如无该通道，则统一返回1)   
    :param pil_pic: pillow图像   
   
  - update(self): `函数`   
   
- Channel: `类型`   
  - __init__(self, texture, channelID): `函数`   
    提取贴图中的单个通道   
    :param texture:   提取通道的贴图   
    :param channelID: 通道编号   
   
  - get_pil_band(self): `函数`   
    获取单通道pil图像   
    :return:   
   
  - update(self): `函数`   
   
- MixChannel: `类型`   
  - __init__(self, resize, R, G, B, A): `函数`   
    混合通道成为一个贴图   
    混合通道贴图(MixChannel)可通过类似贴图(Texture)的方式提取通道   
    :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像   
    :param R: 红色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param G: 绿色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param B: 蓝色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param A: 透明度通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
   
  - update(self): `函数`   
    更新所有缓存项   
    :return: None   
   
   
- FPL: `类型`   
  - __init__(self, base_color, emission): `函数`   
    Fixed pipeline固定管线式贴图   
    :param base_color: 主要颜色   
    :param emission:   自发光度   
   
  - update(self): `函数`   
   
- ShaderProgram: `类型`   
  - __init__(self, vertex, fragment): `函数`   
    着色程序   
    :param vertex:   顶点着色程序   
    :param fragment: 片段着色程序   
   
   
- _pil_to_texture(pil_img, texture_id, texture_unit): `函数`   
  将PIL图像转换为OpenGL纹理   
  :param pil_img: PIL图像对象   
  :param texture_id: 已有纹理ID（如None则创建新纹理）   
  :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）   
  :return: 纹理ID   
   
   
   
