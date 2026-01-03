#!/bin/bash
# 启动MedCrux UI服务（使用uv运行）

echo "🌐 启动MedCrux UI界面（使用uv）..."
echo ""
echo "⚠️  请确保API服务已启动 (http://127.0.0.1:8000)"
echo ""

# 检查uv是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: uv未安装"
    echo ""
    echo "请先安装uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo ""
    exit 1
fi

# 检查依赖是否已同步
if [ ! -f "uv.lock" ]; then
    echo "⚠️  警告: uv.lock文件不存在，正在同步依赖..."
    uv sync
fi

echo "✅ 使用uv运行UI服务..."
echo ""

# 使用uv run启动Streamlit（uv会自动管理Python版本和依赖）
uv run streamlit run src/medcrux/ui/app.py
