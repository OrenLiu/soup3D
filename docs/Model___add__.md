# Model.__add__   
   
[返回上级](./Model.md)   
   
**签名**: `__add__(self, other)`   
   
将多个模型组合成一个模型，当使用“model1 + model2”时，model2将会被组合到model1。需要注意的是，模型组合后，模型中其他模型的部分将与模   
型2共享资源，所以模型组合后，不建议继续使用参与计算的模型，建议使用返回值进行操作，比如“model3 = model1 + model2”,则建议抛弃model1   
和model2，使用model3执行后续操作。当模型因为不可抗因素需要分开倒入时，可以用该方法进行合并。   
:param other: 组合到该模型的模型   
:return: 修改后的本模型   
   
