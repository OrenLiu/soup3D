# open_mtl   
   
[返回上级](./__init__.md)   
   
**签名**: `open_mtl(mtl, double_side, roll_funk, encoding, max_light_count, surface)`   
   
根据mtl文件生成多个着色器   
:param mtl:             *.mtl纹理文件路径   
:param double_side:     是否启用双面渲染   
:param roll_funk:       每当读取一行时调用一次，方法需有，且仅有1个参数，用于接收已读取的行数   
:param encoding:        读取文本文件时使用的字符集(建议在建模软件里把所有元素命名为英文，这样就不用管这个参数了)   
:param max_light_count: 这些着色器出现时会同时出现的最多的光源数量，大了会导致性能问题   
:param surface:         模型使用的表面着色器类型，着色器需要有base_color, emission, normal, double_side, max_light_count等   
                        参数   
:return: 所有生成出的表面着色器   
   
