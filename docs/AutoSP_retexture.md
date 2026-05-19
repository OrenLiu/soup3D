# AutoSP.retexture   
   
[返回上级](./AutoSP.md)   
   
**签名**: `retexture(self, base_color, normal, emission)`   
   
重新向着色器上传纹理，填写None则保持原纹理不变   
:param base_color: 主要颜色   
:param normal:     自定义法线或法线贴图   
:param emission:   自发光度，   
                   当该参数为数字时，0.0为不发光，1.0为完全发光；   
                   当该参数为灰度图时，黑色为不发光，白色为完全发光   
:return: None   
   
