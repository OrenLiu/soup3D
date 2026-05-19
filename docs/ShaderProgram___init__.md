# ShaderProgram.__init__   
   
[返回上级](./ShaderProgram.md)   
   
**签名**: `__init__(self, vertex, fragment, vbo_type)`   
   
代码着色器，作为表面着色器渲染时使用的顶点列表格式：   
[   
    [  # vbo0   
        (),  # vertex0   
        (),  # vertex1   
        (),  # vertex2   
    ],   
    [  # vbo1   
        (),  # vertex0   
        (),  # vertex1   
        (),  # vertex2   
    ]   
    ...   
]   
在着色器代码中，vbo的读取编号取决于vbo处于列表的位置，例如列表中第0个，也就是首个vbo，着色器代码中可以通过   
“layout (location = 0) in <type> <value_name>”这段代码读取。   
:param vertex:   顶点着色程序代码   
:param fragment: 片段着色程序代码   
:param vbo_type: 定义传入着色器程序的顶点列表(vbo)的数据类型。如每个定点列表数据类型相同，可通过填写一个字符串定义所有的定点列表的   
                 数据类型；如果需要不同的数据类型，可通过填写一个列表来分别定义每个顶点列表的数据类型。在同一vbo下，所有vertex的   
                 长度需一致，且长度范围在1-4个数据。   
   
