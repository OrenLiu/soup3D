# _mtl_params

[返回上级](./__init__.md)

**签名**: `_mtl_params(width, height, R, G, B, A, emission, bump_texture, double_side, max_light_count, ior, roughness, metallic, data_only)`

根据MTL解析状态构建材质参数字典，data_only为True时产出可存储的数据形式(base_color为数据字典，否则为MixChannel对象)。文件未提供的可选参数(ior、roughness、metallic)不会出现在字典中
:param width:           纹理宽度
:param height:          纹理高度
:param R:               红色通道值
:param G:               绿色通道值
:param B:               蓝色通道值
:param A:               透明度值
:param emission:        自发光参数
:param bump_texture:    法线贴图参数，为空时使用默认法线
:param double_side:     是否启用双面渲染
:param max_light_count: 最大光源数量
:param ior:             MTL的Ni关键字值(折射率)，文件未提供时为None
:param roughness:       MTL的Pr关键字值(粗糙度)，文件未提供时为None
:param metallic:        MTL的Pm关键字值(金属度)，文件未提供时为None
:param data_only:       是否为数据存储模式
:return: 材质参数字典
