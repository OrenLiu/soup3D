# AutoSP.update   


[返回上级](./README.md)   


**签名**: `update(self)`   


把脏标记对应的待更新内容批量下发给底层 ShaderProgram：模型/视图/投影矩阵、环境光与光源 uniform（脏才重传，避开每帧重复上传），最后调用其 update() 真正执行 glUniform。引擎每帧渲染前自动调用，一般无需手动调用。   
   
:return: None   
