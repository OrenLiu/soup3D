# open_obj   
   
[返回上级](./__init__.md)   
   
**签名**: `open_obj(obj, mtl, double_side, roll_funk, encoding, max_light_count)`   
   
从obj文件导入模型   
:param obj:             *.obj模型文件路径   
:param mtl:             *.mtl纹理文件路径或已加载的材质字典   
:param double_side:     是否启用双面渲染   
:param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数   
:param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)   
:param max_light_count: 该模型出现时会同时出现的最多的光源数量，大了会导致性能问题   
:return: 生成出来的模型数据(Model类)   
   
