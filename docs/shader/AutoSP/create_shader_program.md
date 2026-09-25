# AutoSP.create_shader_program   


[返回上级](./README.md)   


**签名**: `create_shader_program(self)`   


根据 base_color / normal / emission 配置生成顶点、片元着色器并编译链接为 AutoSP 内部管理的 ShaderProgram。   
顶点格式：`(x, y, z, u, v)` 或 `(x, y, z, u, v, nx, ny, nz)`。   
由 __init__ 与 retexture() 内部调用，一般无需手动调用。   
   
:return: ShaderProgram   
