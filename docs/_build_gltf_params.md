# _build_gltf_params

[返回上级](./__init__.md)

**签名**: `_build_gltf_params(mat_info)`

从存储的gltf材质数据构建表面着色器参数字典，用于Data.make()内部调用。依次重建base_color、emission、normal后返回
:param mat_info: 存储的材质数据字典，含params与surface
:return: 表面着色器参数字典
