# make_surface   
   
[返回上级](./README.md)   
   
**签名**: `make_surface(cls, params)`   
   
按照色器类可接收的参数过滤后实例化表面着色器。模型文件加载器(open_obj/open_mtl/open_gltf)通过该函数   
动态适配任意表面着色器类：类需要什么参数就传什么参数，不强制要求任何特定参数；当类声明了接收   
**kwargs时全量传入；当类缺少可供给的必填参数时抛出带说明的TypeError   
:param cls:     表面着色器类或工厂函数   
:param params:  标准材质参数字典，键为SURFACE_MATERIAL_PARAMS中的参数名   
:return:        表面着色器实例   
   
