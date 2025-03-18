# ​**soup3D**

## camera:

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
  


- rotated(Xa, Ya, Xb, Yb, degree): `函数`

  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
  


## event:

事件处理方法库，可添加如鼠标、键盘等事件的处理方式



- bind(event, funk): `函数`

  事件绑定函数   
  :param event: 事件名称   
  :param funk:  绑定的函数，每个事件只能绑定一个函数，函数   
                需要有1个参数   
  :return: None   
  


- check_event(events): `函数`



## img:



- Texture: `类型`

  - __init__(self, img, width, height, img_type, wrap_x, wrap_y, linear): `函数`

    材质纹理贴图，当图形需要贴图时，在Shape的texture   
    赋值该类型   
       
    :param img:    贴图的二进制数据   
    :param width:  贴图的宽度（像素）   
    :param height: 贴图的高度（像素）   
    :param img_type: 图像模式，可为"rgb"或"rgba"   
    :param wrap_x: x轴环绕方式，当取色坐标超出图片范   
                   围时的取色方案，可为：   
                   "repeat" -> 重复图像   
                   "mirrored" -> 镜像图像   
                   "edge" -> 延生边缘像素   
                   "border" -> 纯色图像   
    :param wrap_y: y轴环绕方式（参数同wrap_x）   
    :param linear: 是否使用抗锯齿，True使用   
                   GL_LINEAR插值，False使用   
                   GL_NEAREST   
    


## light:

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
    
  - color(self, r, g, b): `函数`

    更改光线颜色   
    :param r: 红色   
    :param g: 绿色   
    :param b: 蓝色   
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
    
  - color(self, r, g, b): `函数`

    更改光线颜色   
    :param r: 红色   
    :param g: 绿色   
    :param b: 蓝色   
    :return: None   
    


- init(): `函数`

  初始化光源，启用全局光照   
  :return: None   
  


- rotated(Xa, Ya, Xb, Yb, degree): `函数`

  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
  


## name:

命名空间



## ui:

soup3D的ui子库，用于绘制2D图形，可绘制HUD叠加显示、GUI用户界面等。



- Shape: `类型`

  - __init__(self, shape_type): `函数`

    图形，可以批量生成线段、三角形   
    :param shape_type: 绘制方式，可以填写这些内容：   
                       "line_b": 不相连线段   
                       "line_s": 连续线段   
                       "line_l": 头尾相连的连续线段   
                       "triangle_b": 不相连三角形   
                       "triangle_s": 相连三角形   
                       "triangle_l": 头尾相连的连续三角形   
    :param args:       图形中所有的端点，每个参数的格式为：   
                       (x, y, r, g, b)   
                       或   
                       (x, y, texture_x, texture_y)   
    :param texture:    使用的纹理对象，默认为None   
    
  - resize(self, width, height): `函数`

    改变图形大小或宽高的比例   
    :param width:  宽度(沿X轴)拉伸多少倍   
    :param height: 高度(沿Y轴)拉伸多少倍   
    :return: 新Shape实例   
    
  - turn(self, angle): `函数`

    旋转图形   
    :param angle: 图形旋转角度（度）   
    :return: 新Shape实例   
    
  - _setup_projection(self): `函数`

    设置正交投影   
    
  - _restore_projection(self): `函数`

    恢复投影矩阵   
    
  - paint(self, x, y): `函数`

    在单帧渲染该图形   
    :param x: 坐标x增值   
    :param y: 坐标y增值   
    


- Group: `类型`

  - __init__(self): `函数`

    图形组   
    :param arg:    组中所有的图形   
    :param origin: 图形组在屏幕中的位置   
    
  - goto(self, x, y): `函数`

    设置绝对位置   
    
  - move(self, x, y): `函数`

    相对移动   
    
  - resize(self, width, height): `函数`

    整体缩放   
    
  - turn(self, angle): `函数`

    整体旋转   
    
  - display(self): `函数`

    单帧显示   
    


## __init__:

这是一个基于OpenGL和pygame开发的3D引擎，易于新手学习，可
用于3D游戏开发、数据可视化、3D图形的绘制等开发。



- Shape: `类型`

  - __init__(self, shape_type): `函数`

    图形，可以批量生成线段、三角形   
    :param shape_type: 绘制方式，可以填写这些内容：   
                       "line_b": 不相连线段   
                       "line_s": 连续线段   
                       "line_l": 头尾相连的连续线段   
                       "triangle_b": 不相连三角形   
                       "triangle_s": 相连三角形   
                       "triangle_l": 头尾相连的连续三角形   
    :param args:       图形中所有的端点，每个参数的格式为：   
                       (x, y, z, r, g, b)   
                       或   
                       (x, y, z, texture_x, texture_y)   
    :param texture:    使用的纹理对象，默认为None   
    :param generate_normals: 是否自动生成法线，仅适用于三角形类型   
    
  - calculate_normals(self): `函数`

    自动计算三角形面的法线（仅支持triangle_b类型）   
    :return: None   
    
  - resize(self, width, height, length, generate_normals): `函数`

    改变物体大小或长宽高的比例   
    :param width:            宽度(沿X轴)拉伸多少倍   
    :param height:           高度(沿Y轴)拉伸多少倍   
    :param length:           长度(沿Z轴)拉伸多少倍   
    :param generate_normals: 是否计算发线   
    :return: None   
    
  - turn(self, yaw, pitch, roll, generate_normals): `函数`

    旋转物体   
    :param yaw:   图形旋转偏移角   
    :param pitch: 图形旋转俯仰角   
    :param roll:  图形旋转横滚角   
    :return: None   
    
  - paint(self, x, y, z): `函数`

    在单帧渲染该图形，当图形需要频繁切换形态、位置等参数时使用。   
    :param x: 坐标x增值   
    :param y: 坐标y增值   
    :param z: 坐标z增值   
    :return: None   
    
  - stable(self, x, y, z): `函数`

    每帧固定渲染该图形，可以用于渲染固定场景，可提升性能。   
    :param x: 坐标x增值   
    :param y: 坐标y增值   
    :param z: 坐标z增值   
    :return: None   
    
  - unstable(self): `函数`

    取消stable的渲染   
    :return: None   
    


- Group: `类型`

  - __init__(self): `函数`

    图形组，图形组中的所有图形的坐标都以组的原点为原点   
    :param args:   组中所有的图形   
    :param origin: 图形组在世界坐标的位置   
    
  - goto(self, x, y, z): `函数`

    以世界坐标更改图形组位置   
    :param x: 图形组x坐标   
    :param y: 图形组y坐标   
    :param z: 图形组z坐标   
    :return: None   
    
  - move(self, x, y, z): `函数`

    以相对坐标更改图形组位置   
    :param x: x增加多少   
    :param y: y增加多少   
    :param z: z增加多少   
    :return: None   
    
  - resize(self, width, height, length, generate_normals): `函数`

    改变物体大小或长宽高的比例   
    :param width:            宽度(沿X轴)拉伸多少倍   
    :param height:           高度(沿Y轴)拉伸多少倍   
    :param length:           长度(沿Z轴)拉伸多少倍   
    :param generate_normals: 是否计算发线   
    :return: None   
    
  - turn(self, yaw, pitch, roll, generate_normals): `函数`

    旋转物体   
    :param yaw:   图形旋转偏移角   
    :param pitch: 图形旋转俯仰角   
    :param roll:  图形旋转横滚角   
    :return:   
    
  - display(self): `函数`

    单帧显示图形组   
    :return: None   
    
  - display_stable(self): `函数`

    每帧显示图形组   
    :return: None   
    
  - hide(self): `函数`

    隐藏图形组，相当于撤销display_stable操作   
    :return: None   
    


- init(width, height, fov, bg_color, far): `函数`

  初始化3D引擎   
  :param width:    视网膜宽度   
  :param height:   视网膜高度   
  :param fov:      视野   
  :param bg_color: 背景颜色   
  :param far:      最远渲染距离   
  :return: None   
  


- background_color(r, g, b): `函数`

  设定背景颜色   
  :param r: 红色(0.0-1.0)   
  :param g: 绿色(0.0-1.0)   
  :param b: 蓝色(0.0-1.0)   
  :return:   
  


- update(): `函数`

  更新画布   
  


- open_obj(obj, mtl): `函数`

  打开一个obj模型文件和mtl纹理文件，并生成图形组(Group类)   
  :param obj: 模型文件位置   
  :param mtl: 纹理文件位置   
  :return: 图形组(Group类)   
  


- rotated(Xa, Ya, Xb, Yb, degree): `函数`

  点A绕点B旋转特定角度后，点A的坐标   
  :param Xa:     环绕点(点A)X坐标   
  :param Ya:     环绕点(点A)Y坐标   
  :param Xb:     被环绕点(点B)X坐标   
  :param Yb:     被环绕点(点B)Y坐标   
  :param degree: 旋转角度   
  :return: 点A旋转后的X坐标, 点A旋转后的Y坐标   
  

