import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# --- 配置 ---
# 这是我们刚才启动的 FastAPI 后端地址
API_BASE_URL = "http://127.0.0.1:8000"


def render_breast_diagram(nodules: list, selected_nodule_id: str = None):
    """
    渲染胸部示意图（基础版）

    Args:
        nodules: 结节列表
        selected_nodule_id: 选中的结节ID

    Returns:
        plotly figure对象
    """
    # 创建子图：左右乳腺
    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("左乳", "右乳"),
        horizontal_spacing=0.15,
    )

    # 定义颜色映射
    risk_colors = {
        "Low": "#10B981",  # 绿色
        "Medium": "#F59E0B",  # 橙色
        "High": "#EF4444",  # 红色
    }

    # 绘制左右乳腺的轮廓（简化版：圆形）
    for col_idx, breast_side in enumerate(["left", "right"], 1):
        # 绘制乳腺轮廓（圆形）
        radius = [1.0] * 101
        x = [r * 0.5 * (1 if breast_side == "left" else -1) for r in radius]
        y = [r * 0.5 for r in radius]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                line=dict(color="#1F2937", width=2),
                name=f"{breast_side}轮廓",
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=col_idx,
        )

        # 标记结节位置
        for nodule in nodules:
            location = nodule.get("location", {})
            if location.get("breast", "").lower() == breast_side.lower():
                # 计算位置坐标（简化版：根据象限和钟点）
                quadrant = location.get("quadrant", "")
                clock_position = location.get("clock_position", "")

                # 简化的坐标计算
                x_pos = 0.0
                y_pos = 0.0

                # 根据象限计算基础坐标
                if "上" in quadrant:
                    y_pos = 0.3
                elif "下" in quadrant:
                    y_pos = -0.3
                if "内" in quadrant:
                    x_pos = -0.2 if breast_side == "left" else 0.2
                elif "外" in quadrant:
                    x_pos = 0.2 if breast_side == "left" else -0.2

                # 根据钟点微调
                if "12点" in clock_position:
                    y_pos = 0.4
                elif "3点" in clock_position:
                    x_pos = 0.3 if breast_side == "left" else -0.3
                elif "6点" in clock_position:
                    y_pos = -0.4
                elif "9点" in clock_position:
                    x_pos = -0.3 if breast_side == "left" else 0.3

                # 获取风险等级和颜色
                risk = nodule.get("risk_assessment", "Low")
                color = risk_colors.get(risk, "#10B981")
                size = 15 if nodule.get("id") == selected_nodule_id else 10

                # 添加结节标记
                fig.add_trace(
                    go.Scatter(
                        x=[x_pos],
                        y=[y_pos],
                        mode="markers",
                        marker=dict(
                            size=size,
                            color=color,
                            line=dict(
                                width=3 if nodule.get("id") == selected_nodule_id else 1,
                                color="#2563EB" if nodule.get("id") == selected_nodule_id else color,
                            ),
                        ),
                        name=nodule.get("id", "nodule"),
                        text=f"{nodule.get('id', '')}<br>风险: {risk}",
                        hovertemplate="<b>%{text}</b><extra></extra>",
                        showlegend=False,
                    ),
                    row=1,
                    col=col_idx,
                )

    # 更新布局
    fig.update_layout(
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        xaxis2=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis2=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    return fig


st.set_page_config(page_title="MedCrux Analysis v1.0.0", page_icon="🩺", layout="wide")

# --- 免责声明（页面顶部） ---
with st.container():
    st.warning(
        "⚠️ **免责声明**：本产品仅供参考，不提供医疗建议。不能替代专业医疗诊断。"
        "如有疑问，请咨询专业医生。使用本产品产生的任何后果，开发者不承担责任。"
    )

# --- 侧边栏 ---
with st.sidebar:
    st.title("MedCrux 🛡️")

    # 获取版本号
    try:
        health_res = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if health_res.status_code == 200:
            version = health_res.json().get("version", "1.0.0")
            st.caption(f"版本 v{version}")
            st.success("🟢 系统在线")
        else:
            st.error("🔴 服务异常")
            st.caption("版本 v1.0.0")
    except requests.exceptions.ConnectionError:
        st.error("🔴 无法连接后端 (请检查 FastAPI 是否启动)")
        st.caption("版本 v1.0.0")

    st.divider()
    st.info("后端 API 状态监控")

# --- 主界面 ---
col_title, col_version = st.columns([4, 1])
with col_title:
    st.title("上传医学影像报告")
with col_version:
    # 显示版本号
    try:
        health_res = requests.get(f"{API_BASE_URL}/health", timeout=1)
        if health_res.status_code == 200:
            version = health_res.json().get("version", "1.0.0")
            st.caption(f"v{version}")
    except Exception:
        st.caption("v1.0.0")

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

                    # --- 数据格式适配：检查是否有新格式数据 ---
                    new_format_data = ai_data.get("_new_format")
                    if new_format_data and "nodules" in new_format_data:
                        # 使用新格式数据
                        nodules = new_format_data.get("nodules", [])
                        overall_assessment = new_format_data.get("overall_assessment", {})
                    else:
                        # 使用旧格式数据（转换为新格式）
                        nodules = []
                        if ai_data.get("extracted_shape"):
                            nodules.append(
                                {
                                    "id": "nodule_1",
                                    "location": {
                                        "breast": "",
                                        "quadrant": "",
                                        "clock_position": "",
                                        "distance_from_nipple": "",
                                    },
                                    "morphology": {
                                        "shape": ai_data.get("extracted_shape", ""),
                                        "boundary": ai_data.get("extracted_boundary", ""),
                                        "echo": ai_data.get("extracted_echo", ""),
                                        "orientation": ai_data.get("extracted_orientation", ""),
                                        "size": "",
                                    },
                                    "malignant_signs": ai_data.get("extracted_malignant_signs", []),
                                    "birads_class": ai_data.get("birads_class", ""),
                                    "risk_assessment": ai_data.get("ai_risk_assessment", "Low"),
                                    "inconsistency_alert": ai_data.get("inconsistency_alert", False),
                                    "inconsistency_reasons": ai_data.get("inconsistency_reasons", []),
                                }
                            )
                        overall_assessment = {
                            "total_nodules": len(nodules),
                            "highest_risk": ai_data.get("ai_risk_assessment", "Low"),
                            "summary": ai_data.get("extracted_findings", []),
                            "advice": ai_data.get("advice", ""),
                        }

                    # --- AI 核心分析区：标签页布局 ---
                    st.divider()

                    # 初始化选中结节状态
                    if "selected_nodule_id" not in st.session_state:
                        st.session_state.selected_nodule_id = None

                    # 创建标签页
                    tab1, tab2, tab3 = st.tabs(["📍 示意图", "🔍 结节详情", "📊 整体评估"])

                    with tab1:
                        # 示意图标签页
                        st.markdown("#### 胸部示意图")
                        if nodules:
                            # 渲染示意图
                            fig = render_breast_diagram(nodules, st.session_state.selected_nodule_id)
                            st.plotly_chart(fig, use_container_width=True)

                            # 结节列表
                            st.markdown("#### 结节列表")
                            for idx, nodule in enumerate(nodules):
                                risk = nodule.get("risk_assessment", "Low")
                                alert = nodule.get("inconsistency_alert", False)

                                # 风险等级颜色
                                if alert or risk == "High":
                                    risk_color = "🔴"
                                elif risk == "Medium":
                                    risk_color = "🟡"
                                else:
                                    risk_color = "🟢"

                                # 结节卡片
                                with st.container():
                                    col_id, col_risk, col_btn = st.columns([2, 2, 1])
                                    with col_id:
                                        st.markdown(f"**{nodule.get('id', f'结节{idx+1}')}**")
                                    with col_risk:
                                        st.markdown(f"{risk_color} 风险: {risk}")
                                    with col_btn:
                                        if st.button("查看详情", key=f"view_{nodule.get('id', idx)}"):
                                            st.session_state.selected_nodule_id = nodule.get("id")
                                            st.rerun()
                                    st.divider()
                        else:
                            st.info("未检测到结节")

                    with tab2:
                        # 结节详情标签页
                        st.markdown("#### 结节详情")
                        selected_id = st.session_state.selected_nodule_id

                        if selected_id:
                            # 找到选中的结节
                            selected_nodule = next((n for n in nodules if n.get("id") == selected_id), None)

                            if selected_nodule:
                                # 显示选中结节的详细信息
                                st.markdown(f"**结节ID**: {selected_nodule.get('id', '')}")

                                # 位置信息
                                location = selected_nodule.get("location", {})
                                st.markdown("##### 📍 位置信息")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"- **乳腺**: {location.get('breast', '未提取')}")
                                    st.markdown(f"- **象限**: {location.get('quadrant', '未提取')}")
                                with col2:
                                    st.markdown(f"- **钟点位置**: {location.get('clock_position', '未提取')}")
                                    st.markdown(f"- **距乳头距离**: {location.get('distance_from_nipple', '未提取')}")

                                # 形态学特征
                                morphology = selected_nodule.get("morphology", {})
                                st.markdown("##### 🔍 形态学特征")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"- **形状**: {morphology.get('shape', '未提取')}")
                                    st.markdown(f"- **边界**: {morphology.get('boundary', '未提取')}")
                                with col2:
                                    st.markdown(f"- **回声**: {morphology.get('echo', '未提取')}")
                                    st.markdown(f"- **方位**: {morphology.get('orientation', '未提取')}")
                                if morphology.get("size"):
                                    st.markdown(f"- **大小**: {morphology.get('size', '未提取')}")

                                # BI-RADS分类
                                birads = selected_nodule.get("birads_class", "")
                                if birads:
                                    st.markdown(f"##### 📊 BI-RADS分类: {birads}类")

                                # 恶性征象
                                malignant_signs = selected_nodule.get("malignant_signs", [])
                                if malignant_signs:
                                    st.markdown("##### ⚠️ 恶性征象")
                                    for sign in malignant_signs:
                                        st.markdown(f"- {sign}")

                                # 不一致预警
                                if selected_nodule.get("inconsistency_alert"):
                                    st.markdown("##### ⚠️ 不一致预警")
                                    reasons = selected_nodule.get("inconsistency_reasons", [])
                                    for reason in reasons:
                                        st.markdown(f"- {reason}")
                            else:
                                st.warning("未找到选中的结节")
                        else:
                            st.info("请从示意图标签页选择一个结节查看详情")

                    with tab3:
                        # 整体评估标签页
                        st.markdown("#### 整体评估")

                        # 结节总数和最高风险
                        total_nodules = overall_assessment.get("total_nodules", 0)
                        highest_risk = overall_assessment.get("highest_risk", "Low")

                        st.markdown(f"**结节总数**: {total_nodules}")
                        st.markdown(f"**最高风险等级**: {highest_risk}")

                        # 评估摘要
                        summary = overall_assessment.get("summary", [])
                        if summary:
                            st.markdown("##### 📋 评估摘要")
                            for item in summary:
                                st.markdown(f"- {item}")

                        # 综合建议
                        advice = overall_assessment.get("advice", "")
                        if advice:
                            st.markdown("##### 💡 MedCrux 建议")
                            st.info(advice)

                    # --- 保留旧格式显示（向后兼容，如果用户需要） ---
                    # 如果只有旧格式数据，显示旧格式的详细信息
                    if not new_format_data and ai_data.get("extracted_shape"):
                        st.divider()
                        st.markdown("#### 📋 详细信息（旧格式）")

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
