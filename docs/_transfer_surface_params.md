# _transfer_surface_params

[返回上级](./__init__.md)

**签名**: `_transfer_surface_params(src_surface, dst_surface_class, **extra)`

把已有表面着色器实例上的标准材质参数转移到目标着色器类的新实例，蒙皮转换的统一入口。按SURFACE_MATERIAL_PARAMS名单从vars()提取交集并附加extra后交由make_surface构造，源实例缺失某参数时跳过
:param src_surface:       源着色器实例
:param dst_surface_class: 目标着色器类
:param extra:             额外参数(如蒙皮的skeleton)
:return: 目标类的新实例
