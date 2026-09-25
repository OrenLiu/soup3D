# RenderTarget.__enter__   


[返回上级](./README.md)   


**签名**: `__enter__(self)`   


上下文管理器入口：调用 bind() 把渲染切换到本目标（保存并替换 viewport / FBO 绑定），并返回自身，配合 with 语句使用。   
   
:return: RenderTarget，即目标自身   
