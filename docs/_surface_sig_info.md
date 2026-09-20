# _surface_sig_info

[返回上级](./shader.md)

**签名**: `_surface_sig_info(cls)`

获取表面着色器类的签名信息(带缓存)，返回(可接收的参数名集合或None, 必填参数名元组)。类未定义__init__或使用object.__init__时视为无参构造，工厂函数直接内省
:param cls: 表面着色器类或工厂函数
:return: (可接收参数集合或None, 必填参数名元组)
