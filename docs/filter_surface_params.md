# filter_surface_params   
   
[返回上级](./shader.md)   
   
**签名**: `filter_surface_params(cls, params)`   
   
按目标着色器类可接收的参数名过滤参数字典，返回新字典。目标类含**kwargs形参或无法内省时返回全量拷贝；纯无参构造返回空字典   
:param cls:    表面着色器类或工厂函数   
:param params: 材质参数字典，键可包含SURFACE_MATERIAL_PARAMS中的任意子集   
:return: 过滤后的参数字典   
   
