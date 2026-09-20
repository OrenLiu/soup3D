# ShaderProgram.get_uniform_loc

[返回上级](./ShaderProgram.md)

**签名**: `get_uniform_loc(self, v_name: str) -> int`

查询 uniform 变量的位置（glGetUniformLocation 的公开封装）。
优先读位置缓存，未命中才查询并写入缓存；不存在的变量返回 -1。

## 参数

- `v_name`：uniform 变量名

## 返回

位置整数；不存在为 -1。
