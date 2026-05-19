# ShaderProgram.uniform   
   
[返回上级](./ShaderProgram.md)   
   
**签名**: `uniform(self, v_name, v_type)`   
   
在下一帧向着色器传递数据   
:param v_name: 在着色器内该数据对应的变量名   
:param v_type: 指定数据类型   
:param value:  其他填入glUniform方法的参数，当传入值为单独数据时(如v_name=soup3D.INT_VEC1),需在此项填写传入的数据，如果需传   
               入数组(如v_name=soup3D.ARRAY_INT_VEC1)，则需要在此项填入(数组长度, 数组)，如果为矩阵，则需填入   
               (矩阵数量, 是否转置矩阵, 传入的矩阵)   
:return: 是否成功添加uniform   
   
