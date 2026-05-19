# Texture.__init__   
   
[返回上级](./Texture.md)   
   
**签名**: `__init__(self, image_data, width, height, format)`   
   
贴图，直接使用二进制图像数据或文件路径   
提取通道时：   
通道 0: 红色通道   
通道 1: 绿色通道   
通道 2: 蓝色通道   
通道 3: 透明度 (如无该通道，则统一返回 1)   
:param image_data: 二进制图像数据或文件路径字符串   
:param width: 图像宽度（当 image_data 为二进制数据时需要提供）   
:param height: 图像高度（当 image_data 为二进制数据时需要提供）   
:param format: 图像格式，可以是 'RGBA', 'RGB', 'L' (灰度) 等   
   
