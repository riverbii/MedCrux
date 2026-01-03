#!/bin/bash
# 启动MedCrux API服务

echo "🚀 启动MedCrux API服务..."
echo ""

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  警告: DEEPSEEK_API_KEY未设置，AI分析功能将不可用"
    echo "   请设置: export DEEPSEEK_API_KEY='sk-your-api-key-here'"
    echo ""
fi

# 启动服务
uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
