# RenderTarget.bind   
   
[返回上级](./README.md)   
   
**签名**: `bind(self)`   
   
绑定渲染目标：保存当前 viewport / FBO 绑定 / draw buffer 状态并切换到本目标，   
viewport 跟随目标尺寸；不修改深度测试等绘制状态。   
   
