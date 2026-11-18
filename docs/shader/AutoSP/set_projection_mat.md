# AutoSP.set_projection_mat   
   
[返回上级](./README.md)   
   
**签名**: `set_projection_mat(self, mat)`   
   
设置投影矩阵，在变换矩阵时自动调用   
:param mat: 投影矩阵   
:return: None   
   
   
**注意**（2026-11 性能优化）：本方法将 `mat` 的数值原地拷贝进内部恒定矩阵对象，不再保存外部矩阵的引用。设置后再原地改动原 `mat` 对象不会生效，须重新调用本方法。详见[性能优化记录](../performance_optimizations.md)。
