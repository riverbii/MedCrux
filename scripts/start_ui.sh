#!/bin/bash
# 启动MedCrux UI服务

echo "🌐 启动MedCrux UI界面..."
echo ""
echo "⚠️  请确保API服务已启动 (http://127.0.0.1:8000)"
echo ""

# 启动Streamlit
streamlit run src/medcrux/ui/app.py
