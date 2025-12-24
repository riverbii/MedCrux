import requests
import streamlit as st

# --- 配置 ---
# 这是我们刚才启动的 FastAPI 后端地址
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MedCrux Analysis", page_icon="🩺", layout="wide")

# --- 侧边栏 ---
with st.sidebar:
    st.title("MedCrux 🛡️")
    st.info("后端 API 状态监控")

    # 尝试连接后端进行健康检查
    try:
        health_res = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health_res.status_code == 200:
            st.success(f"🟢 系统在线 (v{health_res.json().get('version')})")
        else:
            st.error("🔴 服务异常")
    except requests.exceptions.ConnectionError:
        st.error("🔴 无法连接后端 (请检查 FastAPI 是否启动)")

# --- 主界面 ---
st.title("上传医学影像报告")

uploaded_file = st.file_uploader("上传报告 (JPG/PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.image(uploaded_file, caption="原始影像", use_container_width=True)

    with col2:
        st.subheader("智能分析")

        # 创建一个按钮来触发分析，避免重复请求
        if st.button("开始分析 🚀", type="primary"):
            with st.spinner("正在发送数据至 MedCrux 核心引擎..."):
                try:
                    # 1. 准备文件数据
                    # uploaded_file.getvalue() 获取二进制数据
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }

                    # 2. 发送 POST 请求给 FastAPI
                    response = requests.post(f"{API_BASE_URL}/analyze/upload", files=files)

                    # 3. 处理结果
                    if response.status_code == 200:
                        result = response.json()
                        ai_data = result.get("ai_result", {})

                        # OCR 原文折叠
                        with st.expander("📄 查看 OCR 识别原文", expanded=False):
                            st.text(result.get("ocr_text"))

                        # --- AI 核心分析区 ---
                        st.divider()

                        # 风险警报头
                        risk = ai_data.get("ai_risk_assessment", "Unknown")
                        alert = ai_data.get("inconsistency_alert", False)

                        if alert or risk == "High":
                            st.error(f"🚨 风险等级: {risk} (检测到潜在不一致)")
                        elif risk == "Medium":
                            st.warning(f"⚠️ 风险等级: {risk}")
                        else:
                            st.success(f"✅ 风险等级: {risk}")

                        # 左右分栏
                        c1, c2 = st.columns(2)

                        with c1:
                            st.markdown("#### 🔍 提取的事实")
                            for finding in ai_data.get("extracted_findings", []):
                                st.markdown(f"- {finding}")
                            st.markdown(f"**原报告结论**: {ai_data.get('original_conclusion')}")

                        with c2:
                            st.markdown("#### 💡 MedCrux 建议")
                            st.info(ai_data.get("advice"))

                    else:
                        st.error(f"分析失败: {response.status_code} - {response.text}")

                except Exception as e:
                    st.error(f"发生错误: {str(e)}")
