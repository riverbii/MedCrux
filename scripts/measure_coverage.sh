#!/bin/bash
# 测试覆盖率测量脚本

set -e

echo "📊 开始测量测试覆盖率..."

# 检查是否安装了pytest-cov
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest未安装，请先安装: pip install pytest pytest-cov"
    exit 1
fi

if ! python3 -c "import coverage" > /dev/null 2>&1; then
    echo "❌ coverage未安装，正在安装..."
    pip install pytest-cov
fi

# 运行测试并生成覆盖率报告
echo "🧪 运行测试并测量覆盖率..."
python3 -m pytest \
    --cov=src/medcrux \
    --cov-report=term-missing \
    --cov-report=json:coverage.json \
    --cov-report=html:htmlcov \
    -v

# 从JSON报告中提取覆盖率百分比
if [ -f coverage.json ]; then
    COVERAGE=$(python3 -c "import json; data = json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")
    echo ""
    echo "✅ 测试覆盖率: ${COVERAGE}%"
    echo "📄 详细报告: htmlcov/index.html"
    echo "📊 JSON报告: coverage.json"
    echo ""
    echo "请将覆盖率数据更新到 Dashboard: ${COVERAGE}%"
else
    echo "❌ 未能生成覆盖率报告"
    exit 1
fi

