# AutoSP.is_dirty   


[返回上级](./README.md)   


**签名**: `is_dirty(self)`   


查询表面着色器是否有待更新内容：模型/视图/投影矩阵或光照有变化，或底层 ShaderProgram 有未下发的 uniform 变更时为 True。引擎每帧渲染前据此决定是否调用 update()。   
   
:return: bool，是否需要更新   
