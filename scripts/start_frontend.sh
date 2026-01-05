#!/bin/bash

# MedCrux Frontend 启动脚本

echo "🚀 启动 MedCrux Frontend (React + Vite)"
echo ""

# 检查是否在项目根目录
if [ ! -f "frontend/package.json" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 进入frontend目录
cd frontend || exit 1

# 检查node_modules是否存在
if [ ! -d "node_modules" ]; then
    echo "📦 首次运行，正在安装依赖..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 启动开发服务器
echo "✅ 启动开发服务器..."
echo "📍 前端地址: http://localhost:3000"
echo "📍 后端API: http://localhost:8000"
echo ""
echo "⚠️  请确保后端服务已启动 (./scripts/start_api.sh)"
echo ""

npm run dev


