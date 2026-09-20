# make_surface   
   
[返回上级](./shader.md)   
   
**签名**: `make_surface(cls, params)`   
   
按目标着色器类的构造签名过滤并构造表面着色器，是加载器动态适配的统一入口。参数中目标类不接收的项会被自动丢弃，缺失必填参数时抛出带说明的TypeError。当类含**kwargs形参或无法内省签名时，会全量传入所有参数   
:param cls:    表面着色器类或工厂函数   
:param params: 材质参数字典，键可包含SURFACE_MATERIAL_PARAMS中的任意子集   
:return: 表面着色器实例   
   
