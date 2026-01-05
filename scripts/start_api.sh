#!/bin/bash
# 启动MedCrux API服务（使用uv运行）

# 获取脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT" || { echo "❌ 无法切换到项目根目录"; exit 1; }

echo "🚀 启动MedCrux API服务（使用uv）..."
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

# 检查依赖是否已同步并安装包
if [ ! -f "uv.lock" ] || [ ! -d ".venv" ]; then
    echo "⚠️  警告: 依赖未同步，正在同步依赖..."
    uv sync
fi

# 确保包已安装（可编辑模式）
echo "📦 安装/更新包（可编辑模式）..."
uv pip install -e . 2>&1 | grep -v "already satisfied" || true

# 检查环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "⚠️  警告: DEEPSEEK_API_KEY未设置，AI分析功能将不可用"
    echo "   请设置: export DEEPSEEK_API_KEY='sk-your-api-key-here'"
    echo ""
fi

echo "✅ 使用uv运行服务..."
echo ""

# 使用uv run启动服务（uv会自动管理Python版本和依赖）
# 设置PYTHONPATH确保能找到medcrux模块
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
uv run uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
