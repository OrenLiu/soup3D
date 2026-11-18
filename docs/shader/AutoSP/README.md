# AutoSP

[返回上级](../README.md)   

标准的可被模型文件加载器使用的着色器管理类。可通过继承该类开发自定义着色器管理类。

## 方法

- [__init__(self, base_color, normal, emission, double_side, max_light_count, shader_program)](__init__.md): `函数`   
- [retexture(self, base_color, normal, emission)](retexture.md): `函数`   
- [create_shader_program(self)](create_shader_program.md): `函数`   
- [set_model_mat(self, mat)](set_model_mat.md): `函数`   
- [set_view_mat(self, mat)](set_view_mat.md): `函数`   
- [set_projection_mat(self, mat)](set_projection_mat.md): `函数`   
- [set_light(self)](set_light.md): `函数`   
- [use(self)](use.md): `函数`   
- [rend(self, mode, vertex)](rend.md): `函数`   
- [rend_cached(self, mode, vertex)](rend_cached.md): `函数`   
- [unuse(self)](unuse.md): `函数`   
- [is_dirty(self)](is_dirty.md): `函数`   
- [update(self)](update.md): `函数`   
- [__del__(self)](__del__.md): `函数`   
