# update   
   
[返回上级](./README.md)   
   
**签名**: `update(render, target)`   
   
更新画布。   
:param render: 帧级渲染器（实现 FrameRenderer 协议：有 on_frame 方法即可）。   
               传入后本帧全部画面输出（含清屏）交给该渲染器接管，   
               引擎仅在其前后保存/恢复自身依赖的 GL 状态；   
               None 时使用引擎内置默认渲染器，与修改前行为逐像素一致   
:param target: 渲染目标（RenderTarget 实例）。传入后本帧默认渲染管线原样渲进该目标，   
               viewport 跟随目标尺寸，不显示到窗口；与 render 同时传入抛 ValueError；None 时渲到窗口与修改前逐像素一致   
:return: None   
   
