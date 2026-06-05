# Data.__init__   
   
[返回上级](./Data.md)   
   
**签名**: `__init__(self, data_type, data)`   
   
数据结构，可通过该类创建的对象生成模型、着色器、骨骼等元素。该类通常通过文件加载器(如open_obj)创建对象。   
:param data_type: 数据类型标识，"obj"表示obj模型数据，"mtl"表示材质数据，"gltf"表示gltf模型数据   
:param data:      存储的原始数据   
   
