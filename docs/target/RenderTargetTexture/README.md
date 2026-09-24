# RenderTargetTexture   
   
[返回上级](../README.md)   
   
渲染目标附属纹理的包装对象（颜色/深度），实现 gen_gl_texture(texture_unit) 与   
get_texture_id() 协议，可直接传入 ShaderProgram.uniform_tex 作为贴图采样。   
浮点颜色附着（rgba16f/rgba32f）同样以纹理形式被采样，无需特殊处理。   
   
## 方法   
   
- [__init__(self, texture_id, width, height)](__init__.md): `函数`   
- [gen_gl_texture(self, texture_unit)](gen_gl_texture.md): `函数`   
- [get_texture_id(self)](get_texture_id.md): `函数`   
   
