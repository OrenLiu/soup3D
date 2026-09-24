# get_surface_params   
   
[返回上级](./README.md)   
   
**签名**: `get_surface_params(cls)`   
   
内省表面着色器类(或工厂函数)可接收的构造参数名集合   
:param cls: 表面着色器类或工厂函数   
:return: 可接收的参数名集合；当形参含**kwargs或无法内省(如C扩展)时返回None，表示可接收任意参数   
   
