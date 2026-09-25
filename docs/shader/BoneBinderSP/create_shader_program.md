# BoneBinderSP.create_shader_program   


[返回上级](./README.md)   


**签名**: `create_shader_program(self)`   


生成带骨骼蒙皮扩展的着色器程序：顶点着色器含 BoneIDs / BoneWeights 顶点属性，骨骼矩阵经 UniformBuffer（UBO）按 MAX_BONES 上传。   
由 __init__ 与 set_skeleton() 内部调用（骨架规模变化时会重建程序），一般无需手动调用。   
   
:return: ShaderProgram   
