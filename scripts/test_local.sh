#!/bin/bash

# MedCrux v1.3.0 本地测试环境启动脚本

echo "🚀 启动MedCrux v1.3.0本地测试环境"
echo ""

# 检查环境
echo "📋 检查环境..."
python3 --version || { echo "❌ Python未安装"; exit 1; }
node --version || { echo "❌ Node.js未安装"; exit 1; }
npm --version || { echo "❌ npm未安装"; exit 1; }

# 获取脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT" || { echo "❌ 无法切换到项目根目录"; exit 1; }

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ] || [ ! -d "frontend" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查后端依赖
if [ ! -d ".venv" ] && ! command -v uv &> /dev/null; then
    echo "⚠️  警告: 未检测到虚拟环境，建议先运行 'uv sync' 或 'pip install -e .'"
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  警告: 前端依赖未安装，正在安装..."
    cd frontend
    npm install
    cd ..
fi

# 启动后端（后台运行）
echo ""
echo "🔧 启动后端API..."
"$SCRIPT_DIR/start_api.sh" > /tmp/medcrux_backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 5

# 检查后端是否启动
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ 后端API启动成功 (PID: $BACKEND_PID)"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ 后端API启动失败，请检查日志: /tmp/medcrux_backend.log"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# 启动前端
echo ""
echo "🌐 启动前端..."
cd frontend
npm run dev > /tmp/medcrux_frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# 等待前端启动
echo "⏳ 等待前端启动..."
sleep 5

echo ""
echo "✅ 测试环境启动完成！"
echo ""
echo "📍 前端地址: http://localhost:3000"
echo "📍 后端API: http://localhost:8000"
echo "📍 API文档: http://localhost:8000/docs"
echo ""
echo "📋 进程信息:"
echo "   - 后端PID: $BACKEND_PID"
echo "   - 前端PID: $FRONTEND_PID"
echo ""
echo "📝 日志文件:"
echo "   - 后端日志: /tmp/medcrux_backend.log"
echo "   - 前端日志: /tmp/medcrux_frontend.log"
echo ""
echo "📖 测试指南:"
echo "   - 完整测试: 查看 docs/dev/versions/v1.3.0/LOCAL_TESTING.md"
echo "   - 测试清单: 查看 docs/dev/versions/v1.3.0/TEST_CHECKLIST.md"
echo ""
echo "⚠️  按Ctrl+C停止所有服务"
echo ""

# 清理函数
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

# 捕获中断信号
trap cleanup INT TERM

# 等待用户中断
wait

