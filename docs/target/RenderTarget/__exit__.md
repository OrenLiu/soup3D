# RenderTarget.__exit__

[返回上级](./README.md)

**签名**: `__exit__(self, exc_type, exc_val, exc_tb)`

上下文管理器出口：调用 unbind() 恢复 bind() 保存的 viewport / FBO 绑定 / draw buffer 状态。
即使 with 块内抛异常也会恢复状态，异常照常向外抛出。

- `:param exc_type`: 异常类型（未发生异常时为 None）
- `:param exc_val`: 异常对象（未发生异常时为 None）
- `:param exc_tb`: 异常 traceback（未发生异常时为 None）
- `:return`: False，不吞异常，with 块内的异常照常抛出
