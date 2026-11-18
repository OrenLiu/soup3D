# Model.gen_dis_list   
   
[返回上级](./README.md)   
   
**签名**: `gen_dis_list(self)`   
   
创建显示列表，该操作开销较大，不建议实时使用。固定渲染模式（fixed_mode 为 True）下，
编译前先预热触发 rend_cached 的缓冲创建/上传，列表内只录制「绑定缓存 VAO + 绘制」命令，逐帧重放零上传。   
:return: None   
   
