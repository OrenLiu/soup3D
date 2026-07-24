# UniformBuffer.update   
   
[返回上级](./UniformBuffer.md)   
   
**签名**: `update(self, data, offset, size)`   
   
使用glBufferSubData更新UBO数据   
   
:param data: 要上传的数据，可以是bytes或numpy数组   
:param offset: 数据偏移量（字节）   
:param size: 数据大小（字节），为None时使用data的完整大小   
   
