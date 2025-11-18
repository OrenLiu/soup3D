# **help.md**    
   
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
   
  - gen_gl_texture(self, texture_unit): `函数`   
    生成OpenGL纹理   
    :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）   
    :return: None   
   
  - get_texture_id(self): `函数`   
    获取纹理id，若无纹理id，则创建纹理id。   
    :return: 纹理id   
   
  - __del__(self): `函数`   
   
- Channel: `类型`   
  - __init__(self, texture, channelID): `函数`   
    提取贴图中的单个通道   
    :param texture:   提取通道的贴图   
    :param channelID: 通道编号   
   
  - _get_pil_band(self): `函数`   
    获取单通道pil图像   
    :return:   
   
  - __del__(self): `函数`   
   
- MixChannel: `类型`   
  - __init__(self, resize, R, G, B, A): `函数`   
    混合通道成为一个贴图   
    混合通道贴图(MixChannel)可通过类似贴图(Texture)的方式提取通道   
    :param resize: 重新定义图像尺寸，不同的通道可能来自不同尺寸的贴图，为实现合并，需将所有通道转换为同一尺寸的图像   
    :param R: 红色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param G: 绿色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param B: 蓝色通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
    :param A: 透明度通道，可直接通过0.0~1.0的小数定义通道亮度，也可以引入Channel通道实现引入贴图通道   
   
  - gen_gl_texture(self, texture_unit): `函数`   
    生成OpenGL纹理   
    :param texture_unit: 纹理单元编号（0表示GL_TEXTURE0，1表示GL_TEXTURE1等）   
    :return: None   
   
  - get_texture_id(self): `函数`   
    获取纹理id，若无纹理id，则创建纹理id。   
    :return: 纹理id   
   
  - __del__(self): `函数`   
   
- ShaderProgram: `类型`   
  - __init__(self, vertex, fragment, vbo_type): `函数`   
    代码着色器，作为表面着色器渲染时使用的顶点列表格式：   
    [   
        [  # vbo0   
            (),  # vertex0   
            (),  # vertex1   
            (),  # vertex2   
        ],   
        [  # vbo1   
            (),  # vertex0   
            (),  # vertex1   
            (),  # vertex2   
        ]   
        ...   
    ]   
    在着色器代码中，vbo的读取编号取决于vbo处于列表的位置，例如列表中第0个，也就是首个vbo，着色器代码中可以通过   
    “layout (location = 0) in <type> <value_name>”这段代码读取。   
    :param vertex:   顶点着色程序代码   
    :param fragment: 片段着色程序代码   
    :param vbo_type: 定义传入着色器程序的顶点列表(vbo)的数据类型。如每个定点列表数据类型相同，可通过填写一个字符串定义所有的定点列表的   
                     数据类型；如果需要不同的数据类型，可通过填写一个列表来分别定义每个顶点列表的数据类型。在同一vbo下，所有vertex的   
                     长度需一致，且长度范围在1-4个数据。   
   
  - use(self): `函数`   
    使用该着色器，会在应用时自动调用   
    :return: None   
   
  - rend(self, mode, vertex): `函数`   
    创建该着色器的渲染流程   
    :param mode:   绘制方式   
    :param vertex: 表面中所有的顶点   
    :return: None   
   
  - unuse(self): `函数`   
    停用该着色器，会在结束应用时自动调用   
    :return: None   
   
  - uniform(self, v_name, v_type): `函数`   
    在下一帧向着色器传递数据   
    :param v_name: 在着色器内该数据对应的变量名   
    :param v_type: 指定数据类型   
    :param value:  其他填入glUniform方法的参数，当传入值为单独数据时(如v_name=soup3D.INT_VEC1),需在此项填写传入的数据，如果需传   
                   入数组(如v_name=soup3D.ARRAY_INT_VEC1)，则需要在此项填入(数组长度, 数组)，如果为矩阵，则需填入   
                   (矩阵数量, 是否转置矩阵, 传入的矩阵)   
    :return: None   
   
  - uniform_tex(self, v_name, texture, texture_unit): `函数`   
    在下一帧向着色器传递纹理   
    :param v_name:       在着色器内该纹理对应的变量名   
    :param texture:      贴图类   
    :param texture_unit: 纹理单元编号   
    :return: None   
   
  - dirty_update(self): `函数`   
    标记该着色器为需要更新   
    :return: None   
   
  - update(self): `函数`   
    更新着色器   
    :return: None   
   
  - __del__(self): `函数`   
    深度清理着色器，清理该着色器本身及所有该着色器用到的元素。在确定不再使用该着色器时可使用该方法释放内存。   
    :return: None   
   
   
- AutoSP: `类型`   
  - __init__(self, base_color, normal, emission, double_side, max_light_count): `函数`   
    更具用户提供的参数自动生成ShaderProgram类，并在需要时自动调用ShaderProgram的类成员，作为表面着色器渲染时使用的顶点列表格式：   
    [   
        (x, y, z, u, v) | (x, y, z, u, v, nx, ny, nz),   
        ...   
    ]   
    其中：   
    x, y, z: 顶点3维坐标   
       
    u, v: 顶点对应的贴图uv坐标位置   
       
    nx, ny, nz: 顶点法线偏移，默认为0   
       
    :param base_color:      主要颜色   
    :param normal:          自定义法线或法线贴图   
    :param emission:        自发光度，   
                            当该参数为数字时，0.0为不发光，1.0为完全发光；   
                            当该参数为灰度图时，黑色为不发光，白色为完全发光   
    :param double_side:     是否启用双面渲染   
    :param max_light_count: 该着色器使用时会同时出现的最多的光源数量   
   
  - retexture(self, base_color, normal, emission): `函数`   
    重新向着色器上传纹理，填写None则保持原纹理不变   
    :param base_color: 主要颜色   
    :param normal:     自定义法线或法线贴图   
    :param emission:   自发光度，   
                       当该参数为数字时，0.0为不发光，1.0为完全发光；   
                       当该参数为灰度图时，黑色为不发光，白色为完全发光   
    :return: None   
   
  - create_shader_program(self): `函数`   
    根据参数创建着色器程序   
   
  - set_model_mat(self, mat): `函数`   
    设置模型矩阵，在变换矩阵时自动调用   
    :param mat: 模型矩阵   
    :return: None   
   
  - set_view_mat(self, mat): `函数`   
    设置投影矩阵，在变换矩阵时自动调用   
    :param mat: 投影矩阵   
    :return: None   
   
  - set_projection_mat(self, mat): `函数`   
    设置视图矩阵，在变换矩阵时自动调用   
    :param mat: 视图矩阵   
    :return: None   
   
  - set_light(self, light_queue): `函数`   
    设置光照，在添加、减少光照时自动调用   
    :param light_queue: 光照列队   
    :return: None   
   
  - use(self): `函数`   
    使用该着色器，会在应用时自动调用   
    :return: None   
   
  - rend(self, mode, vertex): `函数`   
    创建该着色器的渲染流程   
    :param mode:   绘制方式   
    :param vertex: 表面中所有的顶点   
    :return: None   
   
  - unuse(self): `函数`   
    停用该着色器，会在结束应用时自动调用   
    :return: None   
   
  - __del__(self): `函数`   
    深度清理着色器，清理该着色器本身及所有该着色器用到的元素。在确定不再使用该着色器时可使用该方法释放内存。   
    :return: None   
   
   
   
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
   
   
   
## name:   
调用：soup3D   
   
   
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
    :param surface:    表面使用的着色器   
    :param vertex:     表面中所有的顶点，格式由surface参数指定的着色器决定   
   
   
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
    :return: None   
   
  - turn(self, yaw, pitch, roll): `函数`   
    旋转模型   
    :param yaw:   偏移角度，绕世界z轴旋转   
    :param pitch: 俯仰角度，绕模型x轴旋转   
    :param roll:  横滚角度，绕模型y轴旋转   
    :return: None   
   
  - size(self, width, height, length): `函数`   
    模型尺寸缩放   
    :param width:  模型宽度倍数，沿模型x轴缩放的倍数   
    :param height: 模型高度倍数，沿模型y轴缩放的倍数   
    :param length: 模型长度倍数，沿模型z轴缩放的倍数   
    :return: None   
   
  - get_model_mat(self): `函数`   
    获取模型矩阵，可用于代码着色器   
    :return: 模型变换矩阵   
   
  - __del__(self): `函数`   
    深度清理模型，清理该模型本身及所有该模型用到的元素。在确定不再使用该模型时可使用该方法释放内存。   
    :return: None   
   
   
- init(width, height, fov, bg_color, near, far): `函数`   
  初始化3D引擎   
  :param width:    视网膜宽度   
  :param height:   视网膜高度   
  :param fov:      视野   
  :param bg_color: 背景颜色   
  :param near:     最近渲染距离   
  :param far:      最远渲染距离   
  :return: None   
   
   
- resize(width, height): `函数`   
  重新定义窗口尺寸   
  :param width:  窗口宽度   
  :param height: 窗口高度   
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
  更新画布   
   
   
- open_mtl(mtl, double_side, roll_funk, encoding, max_light_count, surface): `函数`   
  根据mtl文件生成多个着色器   
  :param mtl:             *.mtl纹理文件路径   
  :param double_side:     是否启用双面渲染   
  :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数   
  :param encoding:        读取mtl文件时使用的字符集   
  :param max_light_count: 这些着色器出现时会同时出现的最多的光源数量   
  :param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side, max_light_count等   
                          参数   
  :return: 所有生成出的表面着色器   
   
   
- open_obj(obj, mtl, double_side, roll_funk, encoding, max_light_count): `函数`   
  从obj文件导入模型   
  :param obj:             *.obj模型文件路径   
  :param mtl:             *.mtl纹理文件路径或已加载的材质字典   
  :param double_side:     是否启用双面渲染   
  :param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数   
  :param encoding:        读取obj或mtl文件时使用的字符集   
  :param max_light_count: 该模型出现时会同时出现的最多的光源数量   
  :return: 生成出来的模型数据(Model类)   
   
   
- get_projection_mat(): `函数`   
  获取透视矩阵，可用于代码着色器   
  :return: 矩阵   
   
   
- smart_split(line): `函数`   
  高效的字符串分割函数，用于替代shlex.split处理OBJ/MTL文件行解析   
  针对OBJ/MTL文件格式进行了优化，比shlex.split快得多   
  :param line: 要分割的行   
  :return: 分割后的字符串列表   
   
   
   
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
   
   
- ambient(R, G, B): `函数`   
  更改环境光亮度   
  :param R: 红色环境光   
  :param G: 绿色环境光   
  :param B: 蓝色环境光   
  :return: None   
   
   
- set_surface_light(): `函数`   
- rotated(Xa, Ya, Xb, Yb, degree): `函数`   
  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
   
   
   
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
   
   
- get_view_mat(): `函数`   
  获取相机矩阵，可用于代码着色器   
  :return: 矩阵   
   
   
- _rotated(Xa, Ya, Xb, Yb, degree): `函数`   
  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
   
   
   
