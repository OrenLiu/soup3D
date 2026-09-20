# _build_gltf_normal

[返回上级](./__init__.md)

**签名**: `_build_gltf_normal(nd)`

从存储的gltf法线数据构建参数值，用于Data.make()内部调用。数据元组为普通元组或None时原样返回
:param nd: 存储的法线数据，数据元组为("normal_tex", bytes, w, h, fmt)时重建Texture，否则原样返回
:return: 法线参数值
