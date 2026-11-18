# shader 模块性能优化记录  

[返回上级](./README.md)   

本文汇总 2026 年 11 月针对 `soup3D/shader.py` 的一轮性能优化修改。该轮修改由
另一个项目的 AI 为优化其自身项目（静态大场景逐帧渲染）的性能而作出，均属
引擎内部实现优化：`rend()` 与既有 API 的调用行为保持不变，现有项目无需改动。

修改共四项，另新增两个公开方法 `rend_cached`：  

| # | 修改 | 位置 | 目的 |
|---|------|------|------|
| 1 | 新增缓存式渲染 `rend_cached` | `ShaderProgram` / `AutoSP` | 静态模型逐帧渲染不再重复「拆分顶点 → 创建 VAO/VBO → 上传 → 绘制 → 删除」 |
| 2 | 矩阵持久 value_ptr + setter 原地拷贝 | `AutoSP` | 消除每帧 `glm.value_ptr()` 的 ctypes 指针包装分配 |
| 3 | uniform 上传函数切换 PyOpenGL raw 层 | 模块级 `type_map` | 绕过包装层每次调用的 Python 对象分配，降低 GC 压力 |
| 4 | `uniform_loc` 字典容量复用 | `ShaderProgram.update()` | `clear()` 保留 entry 表容量，避免每帧重建字典 |

## 1. 缓存式渲染 rend_cached

`rend()` 每帧的完整流程是：拆分顶点 → 新建 VAO/VBO → 上传顶点数据 → 绘制 →
删除缓冲。对顶点数据不变的静态模型（如地图），除绘制外的全部步骤都是重复开销。
`rend_cached` 把缓冲与拆分结果缓存在实例上，仅首次调用付出创建、上传与拆分成本：

- [ShaderProgram.rend_cached](ShaderProgram/rend_cached.md)：首次调用创建 VAO/VBO
  并以 `GL_STATIC_DRAW` 上传顶点数据（顶点装配状态记录进 VAO），之后每帧只做
  「绑定 VAO → 绘制」。缓存的 VAO/VBO 在 `__del__` 中随程序资源一并删除。
  绘制后将活动纹理单元归位 `GL_TEXTURE0`，避免遗留单元影响下游渲染方
  （如 pyimgui 的字体纹理绑定）。
- [AutoSP.rend_cached](AutoSP/rend_cached.md)：顶点拆分结果按入参列表对象的 id
  缓存，传入同一对象时跳过纯 Python 逐顶点拆分，直接以缓存结果调用
  `ShaderProgram.rend_cached`。

注意：`rend_cached` 是供外部逐帧直调的独立入口，引擎主流程（Model / Face /
update）仍走 `rend()`，行为不变。骨骼绑定表面 `BoneBinderSP` 的顶点格式与
AutoSP 不同（含骨骼权重字典），勿对其调用 `rend_cached`。

## 2. 矩阵持久 value_ptr 与 setter 原地拷贝

AutoSP 在构造时对 model / view / projection 三个矩阵各取一次 `glm.value_ptr()`
并长期持有（`_model_ptr` / `_view_ptr` / `_proj_ptr`），`use()` 上传矩阵时直接
复用持久指针，不再每帧重新包装。

为此三个 setter（`set_model_mat` / `set_view_mat` / `set_projection_mat`）改为
把传入矩阵的数值原地拷贝进内部矩阵对象，而不再替换内部矩阵的引用，内部矩阵
对象从此恒定，持久指针始终有效。

**行为变化**：调用方设置矩阵后再原地修改原 `mat` 对象不会生效，须重新调用
setter。按惯例每帧重新调用 setter 的用法不受影响。

## 3. uniform 上传函数切换 PyOpenGL raw 层

模块级 `type_map` 中 19 个 uniform 上传函数由 `OpenGL.GL` 包装层函数换成
`OpenGL.raw.GL` 层函数（ctypes 直调 + argtypes）。raw 层语义一致，仅省去包装层
每次调用的 `_cast`、转换器对象分配（它们是 GC 升代的主要来源），代价是 raw 层
不做 `glGetError` 检查，引擎已有独立的错误检查路径。引擎经 `type_map` 上传
uniform 的路径为 `ShaderProgram.update()`，该路径即切换至 raw 层函数。

另新增模块级 `_INT_TYPE_MAP`（整型 GL 类型 → numpy dtype），供 `rend_cached`
的整型属性指针路径（`glVertexAttribIPointer`）使用；`rend()` 保持其函数内局部
映射不变。

## 4. uniform_loc 字典容量复用

`ShaderProgram.update()` 末尾由 `self.uniform_loc = {}`（丢弃旧字典、按当前
容量新建）改为 `self.uniform_loc.clear()`。CPython 的 dict 在 `clear()` 后保留
entry 表容量，同键重新插入不再触发分配，消除每帧每 surface 一次的字典重建
（GC 升代大户）。

## 契约与注意事项汇总

1. `rend_cached` 契约「静态数据」：顶点数据仅首次上传生效；AutoSP 侧以入参   
   列表对象的 id 判定是否重拆，修改顶点数据须传入新的列表对象，原地改动   
   不会被感知。缓存按顶点列表对象 id 分槽（上限 256 槽，满则 FIFO 淘汰）   
   支持多个 Face 共享一个 surface 的静态模型。   
   引擎已将该路径接入 `Model.fixed()`：固定渲染模型的显示列表改按 rend_cached
   命中命令编译（预热后列表内只录制「绑定缓存 VAO + 绘制」，逐帧 glCallList
   重放零上传）；调用 paint/hide/goto/turn/turn_quat/size 后优化自动失效。
   见 [Model.fixed](../__init__/Model/fixed.md)。
2. 矩阵 setter 不再保存外部矩阵引用（见第 2 节行为变化）。
3. raw 层 uniform 上传不再经包装层做 `glGetError` 检查。
4. `BoneBinderSP` 不适用 `rend_cached`。
5. 缓存（VAO/VBO、拆分结果）生命周期与实例对齐，随垃圾回收在 `__del__` 中
   释放，无需显式清理。
