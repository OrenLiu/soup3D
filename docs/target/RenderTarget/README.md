# RenderTarget   
   
[返回上级](../README.md)   
   
渲染目标（FBO + 颜色纹理 [ + 深度附着 ]），渲染到纹理的标准抽象。   
可作为上下文管理器使用：   
```python
with soup3D.RenderTarget(800, 600, "rgba16f", "renderbuffer") as rt:   
    soup3D.update(target=rt)   
    pixels = rt.to_pixels()   
```
   
## 方法   
   
- [__init__(self, width, height, color, depth)](__init__.md): `函数`   
- [bind(self)](bind.md): `函数`   
- [unbind(self)](unbind.md): `函数`   
- [__enter__(self)](__enter__.md): `函数`   
- [__exit__(self, exc_type, exc_val, exc_tb)](__exit__.md): `函数`   
- [to_pixels(self)](to_pixels.md): `函数`   
- [present(self)](present.md): `函数`   
- [__del__(self)](__del__.md): `函数`   
   
