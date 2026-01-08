#!/usr/bin/env python3
"""
测试覆盖率测量脚本
运行测试并生成覆盖率报告，提取覆盖率百分比
"""

import json
import subprocess
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("📊 开始测量测试覆盖率...")
    
    # 检查pytest是否可用
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ pytest已安装: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest未安装，请先安装: pip install pytest pytest-cov")
        sys.exit(1)
    
    # 检查coverage是否可用
    try:
        subprocess.run(
            [sys.executable, "-c", "import coverage"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ coverage未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"], check=True)
    
    # 运行测试并生成覆盖率报告
    print("🧪 运行测试并测量覆盖率...")
    try:
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                "--cov=src/medcrux",
                "--cov-report=term-missing",
                "--cov-report=json:coverage.json",
                "--cov-report=html:htmlcov",
                "-v"
            ],
            cwd=project_root,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ 测试运行失败: {e}")
        sys.exit(1)
    
    # 从JSON报告中提取覆盖率百分比
    coverage_json_path = project_root / "coverage.json"
    if coverage_json_path.exists():
        with open(coverage_json_path) as f:
            data = json.load(f)
        
        coverage_percent = data['totals']['percent_covered']
        print("")
        print(f"✅ 测试覆盖率: {coverage_percent:.1f}%")
        print(f"📄 详细报告: {project_root / 'htmlcov' / 'index.html'}")
        print(f"📊 JSON报告: {coverage_json_path}")
        print("")
        print(f"请将覆盖率数据更新到 Dashboard: {coverage_percent:.1f}%")
        
        return coverage_percent
    else:
        print("❌ 未能生成覆盖率报告")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()

