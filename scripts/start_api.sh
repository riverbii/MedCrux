#!/bin/bash
# 启动MedCrux API服务

echo "🚀 启动MedCrux API服务..."
echo ""

# 检查Python版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "📌 Python版本: $PYTHON_VERSION"

# 检查依赖是否安装
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "❌ 错误: 依赖未安装"
    echo ""
    echo "请先安装依赖："
    echo "  uv sync"
    echo "  或"
    echo "  pip install -e ."
    echo ""
    exit 1
fi

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  警告: DEEPSEEK_API_KEY未设置，AI分析功能将不可用"
    echo "   请设置: export DEEPSEEK_API_KEY='sk-your-api-key-here'"
    echo ""
fi

# 检查模块导入
if ! python3 -c "import sys; sys.path.insert(0, 'src'); import medcrux.api.main" 2>/dev/null; then
    echo "❌ 错误: 模块导入失败"
    echo "   请检查依赖是否已正确安装"
    exit 1
fi

echo "✅ 依赖检查通过"
echo ""

# 启动服务
uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
