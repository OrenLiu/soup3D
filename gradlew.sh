#!/bin/bash

# soup3D PyPI发布准备脚本

echo "开始准备soup3D包发布到PyPI..."

# 清理旧的构建产物
echo "清理旧的构建产物..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info/

# 编辑配置文件
${EDITOR:-nano} setup.py

# 运行测试（如果有的话）
# python -m pytest

# 构建源码分发和wheel分发
echo "构建包..."
python -m build

# 检查构建的包
echo "检查构建的包..."
twine check dist/*

echo "准备完成！使用 'twine upload dist/*' 命令上传到PyPI"
echo "或者使用 'twine upload --repository testpypi dist/*' 上传到TestPyPI进行测试"