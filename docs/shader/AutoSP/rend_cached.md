# AutoSP.rend_cached   
   
[返回上级](./README.md)   
   
**签名**: `rend_cached(self, mode, vertex)`   
   
缓存式渲染：顶点拆分逻辑与 rend(mode, vertex) 一致，但拆分结果缓存在自身，   
后续帧传入同一顶点列表对象（按 id 判定）时跳过纯 Python 逐顶点拆分，   
直接以缓存结果调用 ShaderProgram.rend_cached 绘制。   
   
设计说明：静态模型逐帧渲染的拆分缓存。rend() 每帧把 (x, y, z, u, v, ...)   
顶点列表重新拆分为位置/纹理坐标/法线三列表，对数万顶点的静态地图是   
每帧重复的纯 Python 开销；本方法只在顶点列表对象变化（id 不同）时重拆一次，   
并复用着色器程序侧缓存的 VAO/VBO（见 ShaderProgram.rend_cached）。   
   
契约：以入参 vertex 的对象 id 变化判定重拆——修改顶点数据须传入新的   
列表对象，原地改动不会被感知；顶点数据本身也视为静态（不再重新上传）。   
支持同一实例的多个不同静态顶点列表（如多个 Face 共享 surface）：按源顶点   
列表对象 id 分槽缓存拆分结果，上限 256 槽，满则 FIFO 淘汰（被淘汰的列表   
下次调用时重拆，性能退化但内容正确）。拆分缓存随实例被垃圾回收自然释放，   
无需显式清理。仅适用于 AutoSP 的顶点格式（骨骼绑定的 BoneBinderSP 顶点   
格式不同，勿对其调用）。   
   
:param mode:   绘制方式   
:param vertex: 表面中所有的顶点   
:return: None   
   
