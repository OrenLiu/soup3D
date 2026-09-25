# ShaderProgram.is_dirty   


[返回上级](./README.md)   


**签名**: `is_dirty(self)`   


查询是否有未下发的 uniform 变更：uniform()/uniform_tex() 只把变更入队，update() 时才真正执行 glUniform；存在入队未下发的变更时返回 True。   
   
:return: bool，是否有未下发的变更   
