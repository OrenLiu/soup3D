# _build_stored_surface

[返回纹理](./__init__.md)

**签名**: `_build_stored_surface(mat_info)`

从存储的mtl材质数据构建表面着色器，用于Data.make()内部调用。从数据字典重建base_color、emission、normal后交由shader.make_surface按目标类过滤构造
:param mat_info: 存储的材质数据字典，含params与surface
:return: 表面着色器实例
