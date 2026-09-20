# get_surface_params   
   
[返回目标](./shader.md)   
   
**签名**: `get_surface_params(cls)`   
   
内省表面着色器类(或工厂函数)的构造签名，返回该类可接收的材质参数名集合。当形参含**kwargs或无法内省时返回None(表示可接收任意参数)；纯无参构造返回空集   
:param cls: 表面着色器类或工厂函数   
:return: 可接收的参数名集合(frozenset)或None   
   
