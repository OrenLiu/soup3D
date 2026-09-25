# Texture.__del__   


[返回上级](./README.md)   


**签名**: `__del__(self)`   


删除纹理的 GL 纹理对象，释放显存。GL 上下文可能在对象销毁前已释放（如解释器关闭期），删除失败时静默。   
   
:return: None   
