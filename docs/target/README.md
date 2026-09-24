# target   
   
[返回上级](../README.md)   
   
处理soup3D中的渲染目标（RenderTarget/FBO）   
渲染到纹理的帧缓冲抽象：场景可先渲进独立尺寸的离屏目标（含 rgba16f/rgba32f 浮点颜色），   
再经 uniform_tex 采样或 present() 显示，供后处理、屏幕空间反射、光线追踪累积等   
需要中间结果在多个渲染通道间流动的效果使用。   
   
## 类   
   
- [RenderTargetTexture](RenderTargetTexture/README.md): `类型`   
- [RenderTarget](RenderTarget/README.md): `类型`   
   
