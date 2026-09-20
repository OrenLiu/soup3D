# ShaderProgram.has_uniform

[返回上级](./ShaderProgram.md)

**签名**: `has_uniform(self, v_name: str) -> bool`

查询着色器中是否存在指定 uniform 变量。优先读位置缓存（与 uniform() 的
位置缓存同源），未命中才调用 glGetUniformLocation 并写入缓存。

## 参数

- `v_name`：uniform 变量名

## 返回

存在返回 True；不存在（位置为 -1）返回 False。

## 示例

```python
sp = soup3D.shader.ShaderProgram(vs, fs)
if sp.has_uniform("uTime"):
    sp.uniform("uTime", soup3D.FLOAT_VEC1, 1.0)
```
```
