# RenderTarget.unbind   


[返回上级](./README.md)   


**签名**: `unbind(self)`   


解绑渲染目标：恢复 bind 保存的 viewport / FBO 绑定 / draw buffer 状态。与 bind() 必须成对使用，未 bind 时调用会抛 RuntimeError。   
   
:return: None   
