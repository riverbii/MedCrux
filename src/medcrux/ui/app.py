import requests
import streamlit as st

# --- 配置 ---
# 这是我们刚才启动的 FastAPI 后端地址
API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="MedCrux Analysis", page_icon="🩺", layout="wide")

# --- 免责声明（页面顶部） ---
with st.container():
    st.warning(
        "⚠️ **免责声明**：本产品仅供参考，不提供医疗建议。不能替代专业医疗诊断。"
        "如有疑问，请咨询专业医生。使用本产品产生的任何后果，开发者不承担责任。"
    )

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

# --- 数据隐私说明（文件上传区域） ---
st.info("🔒 **数据隐私**：所有处理在本地完成，数据不会上传到服务器。您的报告图片仅在本地处理，不会存储或上传。")

uploaded_file = st.file_uploader("上传报告 (JPG/PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    col1, col2 = st.columns([1, 1.5])

    with col1:
        st.image(uploaded_file, caption="原始影像", use_container_width=True)

    with col2:
        st.subheader("智能分析")

        # 创建一个按钮来触发分析，避免重复请求
        if st.button("开始分析 🚀", type="primary"):
            # 进度提示
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # 1. 准备文件数据
                status_text.text("📤 准备上传文件...")
                progress_bar.progress(10)
                files = {
                    "file": (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type,
                    )
                }

                # 2. OCR识别阶段
                status_text.text("🔍 OCR识别中...")
                progress_bar.progress(30)

                # 3. 发送 POST 请求给 FastAPI
                response = requests.post(f"{API_BASE_URL}/analyze/upload", files=files)

                # 4. RAG检索和AI分析阶段
                status_text.text("🤖 RAG检索和AI分析中...")
                progress_bar.progress(70)

                # 5. 处理结果
                progress_bar.progress(100)
                status_text.text("✅ 分析完成")

                if response.status_code == 200:
                    result = response.json()
                    ai_data = result.get("ai_result", {})

                    # 清除进度提示
                    progress_bar.empty()
                    status_text.empty()

                    # OCR 原文折叠
                    with st.expander("📄 查看 OCR 识别原文", expanded=False):
                        st.text(result.get("ocr_text"))

                    # --- AI 核心分析区 ---
                    st.divider()

                    # 风险警报头
                    risk = ai_data.get("ai_risk_assessment", "Unknown")
                    alert = ai_data.get("inconsistency_alert", False)

                    # 优化风险等级展示（P1需求）
                    if alert or risk == "High":
                        st.error(f"🚨 **风险等级: {risk}** (检测到潜在不一致)")
                    elif risk == "Medium":
                        st.warning(f"⚠️ **风险等级: {risk}**")
                    else:
                        st.success(f"✅ **风险等级: {risk}**")

                    # 详细展示不一致预警（P0需求4）
                    if alert:
                        st.markdown("#### ⚠️ 不一致预警详情")
                        inconsistency_reasons = ai_data.get("inconsistency_reasons", [])
                        if inconsistency_reasons:
                            for reason in inconsistency_reasons:
                                st.markdown(f"- {reason}")
                        else:
                            st.markdown("- 检测到描述与结论存在不一致，但具体原因未提取")

                    # BI-RADS分类显示（P1需求6）
                    birads_class = ai_data.get("birads_class", "")
                    if birads_class:
                        st.markdown("#### 📊 BI-RADS分类")
                        st.markdown(f"- **提取的分类**：BI-RADS {birads_class}类")
                        st.markdown(f"- **原报告结论**：{ai_data.get('original_conclusion', '未提取')}")

                    # 结构化展示提取的形态学特征（P0需求3）
                    st.markdown("#### 🔍 提取的形态学特征")

                    # 数据格式化函数：如果值包含"/"，转换为逗号分隔的列表（医疗产品不能丢失信息）
                    def format_feature_value(value: str) -> str:
                        """
                        格式化特征值，如果包含多个值（用/分隔），转换为逗号分隔的列表
                        医疗产品不能丢失任何信息，特别是风险信号
                        """
                        if not value or value == "未提取":
                            return "未提取"
                        # 如果包含"/"，转换为逗号分隔的列表
                        if "/" in value:
                            values = [v.strip() for v in value.split("/") if v.strip()]
                            # 如果值太多，显示前3个并说明"等"
                            if len(values) > 3:
                                return f"{', '.join(values[:3])}等（共{len(values)}个）"
                            return ", ".join(values)
                        return value.strip()

                    col1, col2 = st.columns(2)
                    with col1:
                        shape = format_feature_value(ai_data.get("extracted_shape", "未提取"))
                        boundary = format_feature_value(ai_data.get("extracted_boundary", "未提取"))
                        st.markdown(f"- **形状**：{shape}")
                        st.markdown(f"- **边界**：{boundary}")
                    with col2:
                        echo = format_feature_value(ai_data.get("extracted_echo", "未提取"))
                        orientation = format_feature_value(ai_data.get("extracted_orientation", "未提取"))
                        st.markdown(f"- **回声**：{echo}")
                        st.markdown(f"- **方位**：{orientation}")

                    # 恶性征象
                    malignant_signs = ai_data.get("extracted_malignant_signs", [])
                    if malignant_signs:
                        st.markdown(f"- **恶性征象**：{', '.join(malignant_signs)}")
                    else:
                        st.markdown("- **恶性征象**：无")

                    st.divider()

                    # 提取的事实和建议
                    c1, c2 = st.columns(2)

                    with c1:
                        st.markdown("#### 📋 提取的事实摘要")
                        findings = ai_data.get("extracted_findings", [])
                        if findings:
                            for finding in findings:
                                st.markdown(f"- {finding}")
                        else:
                            st.markdown("- 未提取到具体事实描述")

                    with c2:
                        st.markdown("#### 💡 MedCrux 建议")
                        advice = ai_data.get("advice", "无建议")
                        st.info(advice)

                else:
                    # 清除进度提示
                    progress_bar.empty()
                    status_text.empty()

                    # 改进错误提示（P1需求8）
                    error_msg = response.text
                    if "OCR" in error_msg or "识别" in error_msg:
                        st.error("❌ **图片识别失败**：请上传清晰的图片，确保图片中的文字清晰可见。")
                    elif "AI" in error_msg or "分析" in error_msg:
                        st.error("❌ **AI分析失败**：请检查网络连接或稍后重试。")
                    else:
                        st.error(f"❌ **分析失败**：{response.status_code} - {error_msg}")

            except requests.exceptions.ConnectionError:
                # 清除进度提示
                progress_bar.empty()
                status_text.empty()
                st.error("❌ **无法连接后端服务**：请检查FastAPI服务是否已启动（http://127.0.0.1:8000）")
            except Exception as e:
                # 清除进度提示
                progress_bar.empty()
                status_text.empty()
                # 改进错误提示
                error_str = str(e)
                if "timeout" in error_str.lower():
                    st.error("❌ **请求超时**：处理时间较长，请稍后重试。")
                else:
                    st.error(f"❌ **发生错误**：{error_str}")
