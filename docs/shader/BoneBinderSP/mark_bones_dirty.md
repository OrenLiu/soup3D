# BoneBinderSP.mark_bones_dirty   


[返回上级](./README.md)   


**签名**: `mark_bones_dirty(self)`   


标记骨骼矩阵需要更新：下一帧 update() 时把最新骨骼矩阵写入 UBO。骨骼 move/turn 等操作后由 Bone 内部自动调用，外部一般无需手动调用。   
   
:return: None   
