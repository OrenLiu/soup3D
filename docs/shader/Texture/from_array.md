# Texture.from_array   
   
[返回上级](./README.md)   
   
**签名**: `from_array(cls, arr, color)`   
   
从 numpy 数组创建数据纹理，立即创建 GL 纹理对象（需 GL 上下文就绪，如 soup3D.init() 之后调用）   
数组第 0 行为图像顶行（上传前内部垂直翻转，与 to_pixels/present 的顶原点一致）   
:param arr: (h, w, 4)/(h, w, 3)/(h, w) 的 uint8 或 float32 数组   
:param color: 内部格式。None 时按 dtype/shape 推断：uint8 → rgba8/rgb8/l8，float32 → rgba32f/rgb32f/r32f；   
              显式指定可覆盖，如浮点数据指定 rgba16f。格式须与通道数匹配：rgba*=4 通道、rgb*=3 通道、l8/r32f=1 通道   
:return: Texture 实例   
   
