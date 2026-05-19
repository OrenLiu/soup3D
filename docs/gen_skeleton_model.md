# gen_skeleton_model   
   
[返回上级](./__init__.md)   
   
**签名**: `gen_skeleton_model(_skeleton, bone_color, size)`   
   
生成骨架模型，在屏幕中用线条叠加渲染骨架，用于调试。警告：该操作比较占用性能，只建议在调试时使用。   
:param _skeleton: 骨架对象或骨骼字典   
:param bone_color:  骨骼颜色字典，键为骨骼名称，值为颜色元组   
:param size:        骨骼模型的大小，默认0.01   
:return: 模型(Model类)   
   
