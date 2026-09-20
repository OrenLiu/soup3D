# _surface_params_from_callable

[返回上级](./shader.md)

**签名**: `_surface_params_from_callable(target)`

内省一个可调用对象的形参，返回(可接收的参数名集合或None, 必填参数名元组)。集合为None表示形参含**kwargs或无法内省，即可接收任意关键字参数
:param target: 函数、方法等可调用对象
:return: (可接收参数集合或None, 必填参数名元组)
