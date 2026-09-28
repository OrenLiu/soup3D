# frame_render

[返回上级](./README.md)

**签名**: `frame_render()`

每帧渲染入口，由 `soup3D.update()` 每帧自动调用，一般无需手动调用。
单帧执行顺序：清空画布 → 光源脏则重传光源 uniform → 执行 EAU 更新队列并清空 → 渲染 stable_shapes 持久模型 → 渲染 render_queue 单帧 model.paint() 的模型 → 清空单帧队列 → 渲染 ui 单帧队列 → 渲染全屏叠加图像 → 清空 ui 队列
