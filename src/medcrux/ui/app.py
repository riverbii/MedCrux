import io
import math

import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image
from plotly.subplots import make_subplots

# --- 配置 ---
API_BASE_URL = "http://127.0.0.1:8000"


def calculate_nodule_marker_size(size_str: str, diagram_radius: float = 0.85) -> int:
    """
    根据结节实际大小计算标记大小（按比例计算）

    Args:
        size_str: 结节大小字符串，格式如 "1.2×0.8×0.6 cm" 或 "1.2 cm"
        diagram_radius: 示意图中乳腺的半径（单位：示意图坐标）

    Returns:
        标记大小（像素）
    """
    if not size_str or "cm" not in size_str:
        return 10  # 默认大小

    try:
        # 提取长径（第一个数字）
        parts = size_str.split("×")
        if parts:
            long_axis_cm = float(parts[0].strip().replace("cm", "").strip())
        else:
            return 10

        # 实际乳腺尺寸：单侧胸部一般15cm左右（直径），半径约7.5cm
        actual_breast_radius_cm = 7.5  # cm
        
        # 计算比例：示意图半径 / 实际半径
        scale = diagram_radius / actual_breast_radius_cm
        
        # 计算结节在示意图中的大小（像素）
        nodule_size_in_diagram = long_axis_cm * scale
        
        # 转换为plotly的marker size（plotly的size单位大约是像素的1/3）
        # 最小8px，最大20px
        marker_size = max(8, min(20, int(nodule_size_in_diagram * 10)))
        
        return marker_size
    except (ValueError, IndexError):
        return 10  # 默认大小


def render_breast_diagram(nodules: list, selected_nodule_id: str = None, on_nodule_click=None):
    """
    渲染胸部示意图（真实乳腺轮廓）

    Args:
        nodules: 结节列表
        selected_nodule_id: 选中的结节ID
        on_nodule_click: 点击结节时的回调函数（用于更新选中状态）

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

    # 绘制左右乳腺的轮廓（真实乳腺形状：圆形，略向下倾斜）
    for col_idx, breast_side in enumerate(["left", "right"], 1):
        # 绘制真实乳腺轮廓（圆形）
        # 参数：中心点、半径
        # 实际乳腺尺寸：单侧胸部一般15cm左右（直径），半径约7.5cm
        # 示意图中半径设为0.85（保持比例）
        center_x = 0.0
        center_y = 0.0
        radius = 0.85  # 半径（圆形）

        # 生成圆形轮廓点（确保是正圆）
        theta = [i * 2 * math.pi / 100 for i in range(101)]
        x_breast = [center_x + radius * math.cos(t) * (1 if breast_side == "left" else -1) for t in theta]
        y_breast = [center_y + radius * math.sin(t) for t in theta]  # 正圆，不向下倾斜

        fig.add_trace(
            go.Scatter(
                x=x_breast,
                y=y_breast,
                mode="lines",
                line=dict(color="#1F2937", width=2),
                name=f"{breast_side}轮廓",
                showlegend=False,
                hoverinfo="skip",
            ),
            row=1,
            col=col_idx,
        )

        # 标注钟点（移除象限标注）
        # 可选：标注主要钟点位置（12点、3点、6点、9点）
        # 如果需要，可以在这里添加钟点标注

        # 标记结节位置
        for nodule in nodules:
            location = nodule.get("location", {})
            if location.get("breast", "").lower() == breast_side.lower():
                # 计算位置坐标（根据钟点和距离乳头距离）
                clock_position = location.get("clock_position", "")
                distance_str = location.get("distance_from_nipple", "")

                # 从钟点位置计算角度（12点为90度，顺时针递减）
                # 在标准坐标系中：12点=90度(上), 3点=0度(右), 6点=-90度(下), 9点=180度(左)
                # 11点应该在12点(90度)和9点(180度)之间，即左上方，角度应该是120度
                clock_angle = 90.0  # 默认12点方向（上方）
                if "12点" in clock_position:
                    clock_angle = 90.0  # 上方
                elif "1点" in clock_position:
                    clock_angle = 60.0  # 右上方
                elif "2点" in clock_position:
                    clock_angle = 30.0  # 右上方
                elif "3点" in clock_position:
                    clock_angle = 0.0  # 右侧
                elif "4点" in clock_position:
                    clock_angle = -30.0  # 右下方
                elif "5点" in clock_position:
                    clock_angle = -60.0  # 右下方
                elif "6点" in clock_position:
                    clock_angle = -90.0  # 下方
                elif "7点" in clock_position:
                    clock_angle = -120.0  # 左下方
                elif "8点" in clock_position:
                    clock_angle = -150.0  # 左下方
                elif "9点" in clock_position:
                    clock_angle = 180.0  # 左侧
                elif "10点" in clock_position:
                    clock_angle = 150.0  # 左上方
                elif "11点" in clock_position:
                    clock_angle = 120.0  # 左上方（12点和9点之间）

                # 从距离乳头距离计算半径（假设乳腺半径约为4-5cm，示意图半径0.85）
                distance_cm = 0.0
                try:
                    if distance_str and "cm" in distance_str:
                        distance_cm = float(distance_str.replace("cm", "").strip())
                except (ValueError, AttributeError):
                    distance_cm = 0.0

                # 计算比例：实际乳腺半径约7.5cm（单侧胸部一般15cm直径），示意图半径0.85
                actual_breast_radius = 7.5  # cm
                diagram_radius = 0.85
                if distance_cm > 0:
                    # 根据距离计算在示意图中的位置
                    ratio = min(distance_cm / actual_breast_radius, 0.9)  # 限制在90%以内
                    r = diagram_radius * ratio
                else:
                    # 如果没有距离信息，使用象限和钟点估算
                    quadrant = location.get("quadrant", "")
                    if "上" in quadrant:
                        r = 0.4
                    elif "下" in quadrant:
                        r = 0.5
                    else:
                        r = 0.45

                # 转换为弧度
                angle_rad = math.radians(clock_angle)

                # 计算坐标（乳头在中心）
                # 使用标准极坐标：x = r*cos(angle), y = r*sin(angle)
                # 在标准坐标系中：0度=右侧(3点), 90度=上方(12点), 180度=左侧(9点)
                # 
                # 对于左乳：直接使用计算出的坐标
                # 对于右乳：需要镜像x坐标（因为右乳在示意图右侧，但钟点定义是相对于患者视角）
                # 
                # 修正逻辑：对于右乳，所有钟点的x坐标都需要镜像
                # 但医学示意图中，右乳显示在右侧，所以：
                # - 3点应该在右乳的右侧（x正）
                # - 9点应该在右乳的左侧（x负）
                # - 11点应该在右乳的左侧上方（x负，y正）
                x_pos_base = r * math.cos(angle_rad)
                y_pos = r * math.sin(angle_rad)
                
                # 对于左乳：直接使用
                # 对于右乳：镜像x坐标
                if breast_side == "left":
                    x_pos = x_pos_base
                else:  # right
                    x_pos = -x_pos_base  # 镜像x坐标

                # 获取风险等级和颜色
                risk = nodule.get("risk_assessment", "Low")
                color = risk_colors.get(risk, "#10B981")

                # 计算结节标记大小（根据实际大小，按比例计算）
                morphology = nodule.get("morphology", {})
                size_str = morphology.get("size", "")
                marker_size = calculate_nodule_marker_size(size_str, diagram_radius)

                # 选中状态：加粗边框
                is_selected = nodule.get("id") == selected_nodule_id
                if is_selected:
                    marker_size += 2
                    border_color = "#2563EB"
                    border_width = 3
                else:
                    border_color = color
                    border_width = 1

                # 添加结节标记
                fig.add_trace(
                    go.Scatter(
                        x=[x_pos if breast_side == "left" else -x_pos],
                        y=[y_pos],
                        mode="markers",
                        marker=dict(
                            size=marker_size,
                            color=color,
                            line=dict(width=border_width, color=border_color),
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


def get_nodule_chinese_name(nodule_id: str, index: int) -> str:
    """将结节ID转换为中文名称"""
    if "nodule_" in nodule_id:
        num = nodule_id.replace("nodule_", "")
        try:
            return f"结节{int(num)}"
        except ValueError:
            return f"结节{index + 1}"
    return f"结节{index + 1}"


def get_highest_risk_nodule(nodules: list) -> str:
    """获取风险最高的结节ID（High > Medium > Low）"""
    if not nodules:
        return None

    risk_priority = {"High": 3, "Medium": 2, "Low": 1}
    highest_risk_nodule = max(
        nodules,
        key=lambda n: (
            risk_priority.get(n.get("risk_assessment", "Low"), 0),
            n.get("inconsistency_alert", False),
        ),
    )
    return highest_risk_nodule.get("id")


st.set_page_config(page_title="MedCrux Analysis v1.2.0", page_icon="🩺", layout="wide")

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
            version = health_res.json().get("version", "1.2.0")
            st.caption(f"版本 v{version}")
            st.success("🟢 系统在线")
        else:
            st.error("🔴 服务异常")
            st.caption("版本 v1.2.0")
    except requests.exceptions.ConnectionError:
        st.error("🔴 无法连接后端 (请检查 FastAPI 是否启动)")
        st.caption("版本 v1.2.0")

    st.divider()
    st.info("后端 API 状态监控")

    # OCR原文查看（移到主界面，与原始图像并列显示）

# --- 主界面 ---
col_title, col_version = st.columns([4, 1])
with col_title:
    st.title("上传医学影像报告")
with col_version:
    # 显示版本号
    try:
        health_res = requests.get(f"{API_BASE_URL}/health", timeout=1)
        if health_res.status_code == 200:
            version = health_res.json().get("version", "1.2.0")
            st.caption(f"v{version}")
    except Exception:
        st.caption("v1.2.0")

# --- 数据隐私说明（文件上传区域） ---
st.info("🔒 **数据隐私**：所有处理在本地完成，数据不会上传到服务器。您的报告图片仅在本地处理，不会存储或上传。")

uploaded_file = st.file_uploader("上传报告 (JPG/PNG)", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    # 显示原始图像和OCR原文（并列显示，各占1/2）
    col_img, col_ocr = st.columns([1, 1])
    
    with col_img:
        # 原始图像根据最长边自适应
        # 获取图像尺寸
        image_bytes = uploaded_file.getvalue()
        image = Image.open(io.BytesIO(image_bytes))
        img_width, img_height = image.size
        is_landscape = img_width >= img_height
        
        if is_landscape:
            # 横向：宽度占满容器，高度自适应
            st.image(uploaded_file, caption="原始影像", use_container_width=True)
        else:
            # 纵向：设置最大高度（600px），宽度自适应
            max_height = 600
            scale = max_height / img_height
            display_width = int(img_width * scale)
            st.image(uploaded_file, caption="原始影像", width=display_width)
    
    with col_ocr:
        # OCR原文：默认关闭，可以手动打开
        if st.session_state.get("analysis_complete", False) and st.session_state.get("ocr_text"):
            with st.expander("📄 查看 OCR 识别原文", expanded=False):
                st.text_area("", value=st.session_state.get("ocr_text", ""), height=400, disabled=True, label_visibility="collapsed")
        else:
            # 分析前不展示OCR相关内容，置空
            st.empty()

    # 初始化选中结节状态
    if "selected_nodule_id" not in st.session_state:
        st.session_state.selected_nodule_id = None

    # 创建一个按钮来触发分析，避免重复请求
    # 分析前：大按钮，绿色
    # 分析后：按钮变为已按状态，文字"分析完成 ✅"
    analysis_complete = st.session_state.get("analysis_complete", False)
    
    if analysis_complete:
        # 分析后：按钮变为已按状态
        st.button("分析完成 ✅", disabled=True, use_container_width=True)
    else:
        # 分析前：大按钮，绿色（使用CSS自定义样式）
        st.markdown("""
        <style>
        .stButton > button {
            background-color: #10B981 !important;
            color: white !important;
            font-size: 18px !important;
            font-weight: bold !important;
            padding: 0.75rem 2rem !important;
            border-radius: 0.5rem !important;
        }
        .stButton > button:hover {
            background-color: #059669 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button("开始分析 🚀", type="primary", use_container_width=True):
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

                    # 保存OCR原文到session_state
                    st.session_state.ocr_text = result.get("ocr_text", "")

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

                    # 默认选中风险最高的结节
                    if not st.session_state.selected_nodule_id and nodules:
                        st.session_state.selected_nodule_id = get_highest_risk_nodule(nodules)

                    # 保存数据到session_state
                    st.session_state.nodules = nodules
                    st.session_state.overall_assessment = overall_assessment
                    st.session_state.ai_data = ai_data
                    st.session_state.analysis_complete = True

                    st.rerun()

                else:
                    # 清除进度提示
                    progress_bar.empty()
                    status_text.empty()

                    # 改进错误提示
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

    # --- 显示分析结果 ---
    if st.session_state.get("analysis_complete", False):
        nodules = st.session_state.get("nodules", [])
        overall_assessment = st.session_state.get("overall_assessment", {})
        ai_data = st.session_state.get("ai_data", {})

        # --- 移除分析后的原始图像显示（分析前已显示） ---
        st.divider()

        if nodules:
            # --- 中间区域：结节列表（左侧）+ 示意图（右侧） ---
            col_list, col_diagram = st.columns([1, 4])

            with col_list:
                st.markdown("#### 结节列表")
                # 结节列表（圆弧边按钮样式，竖列）
                
                # 添加CSS样式：圆弧边按钮和高亮效果
                st.markdown("""
                <style>
                /* 所有结节按钮的圆弧边样式 */
                div[data-testid*="column"] button[kind="secondary"],
                div[data-testid*="column"] button[kind="primary"] {
                    border-radius: 20px !important;
                    padding: 12px 16px !important;
                    margin-bottom: 8px !important;
                    font-size: 14px !important;
                    transition: all 0.3s ease !important;
                }
                /* 未选中状态 */
                div[data-testid*="column"] button[kind="secondary"] {
                    background-color: #F9FAFB !important;
                    border: 2px solid #E5E7EB !important;
                    color: #1F2937 !important;
                    font-weight: normal !important;
                }
                div[data-testid*="column"] button[kind="secondary"]:hover {
                    background-color: #F3F4F6 !important;
                    border-color: #D1D5DB !important;
                }
                /* 选中状态（高亮） */
                div[data-testid*="column"] button[kind="primary"] {
                    background-color: #EFF6FF !important;
                    border: 2px solid #2563EB !important;
                    color: #1E40AF !important;
                    font-weight: bold !important;
                }
                div[data-testid*="column"] button[kind="primary"]:hover {
                    background-color: #DBEAFE !important;
                    border-color: #1D4ED8 !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # 渲染每个结节为圆弧边按钮
                for idx, nodule in enumerate(nodules):
                    nodule_id = nodule.get("id")
                    risk = nodule.get("risk_assessment", "Low")
                    alert = nodule.get("inconsistency_alert", False)

                    # 风险等级颜色
                    if alert or risk == "High":
                        risk_color = "🔴"
                    elif risk == "Medium":
                        risk_color = "🟡"
                    else:
                        risk_color = "🟢"

                    # 中文名称
                    chinese_name = get_nodule_chinese_name(nodule_id, idx)
                    
                    # 判断是否选中
                    is_selected = nodule_id == st.session_state.selected_nodule_id
                    
                    # 使用button，选中时使用primary类型（高亮），未选中时使用secondary类型
                    button_key = f"nodule_btn_{nodule_id}"
                    if st.button(
                        f"{chinese_name} {risk_color}",
                        key=button_key,
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        st.session_state.selected_nodule_id = nodule_id
                        st.rerun()

            with col_diagram:
                st.markdown("#### 胸部示意图")
                # 渲染示意图
                fig = render_breast_diagram(nodules, st.session_state.selected_nodule_id)
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # --- 底部：两个大卡片并列 ---
            col_detail, col_assessment = st.columns(2)

            with col_detail:
                st.markdown("### 乳腺结节详情")
                selected_id = st.session_state.selected_nodule_id

                if selected_id:
                    # 找到选中的结节
                    selected_nodule = next((n for n in nodules if n.get("id") == selected_id), None)

                    if selected_nodule:
                        # 显示选中结节的详细信息
                        chinese_name = get_nodule_chinese_name(selected_id, nodules.index(selected_nodule))
                        st.markdown(f"**{chinese_name}**")

                        # 位置信息
                        location = selected_nodule.get("location", {})
                        with st.container():
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
                        with st.container():
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

                        # 风险评估
                        risk = selected_nodule.get("risk_assessment", "Low")
                        st.markdown(f"##### 📊 风险评估: {risk}")

                        # 恶性征象
                        malignant_signs = selected_nodule.get("malignant_signs", [])
                        if malignant_signs:
                            with st.container():
                                st.markdown("##### ⚠️ 恶性征象")
                                for sign in malignant_signs:
                                    st.markdown(f"- {sign}")

                        # 不一致预警
                        if selected_nodule.get("inconsistency_alert"):
                            with st.container():
                                st.markdown("##### ⚠️ 不一致预警")
                                reasons = selected_nodule.get("inconsistency_reasons", [])
                                for reason in reasons:
                                    st.markdown(f"- {reason}")
                    else:
                        st.warning("未找到选中的结节")
                else:
                    st.info("请选择一个结节查看详情")

            with col_assessment:
                st.markdown("### 整体评估")

                # 结节总数和最高风险
                total_nodules = overall_assessment.get("total_nodules", 0)
                highest_risk = overall_assessment.get("highest_risk", "Low")

                with st.container():
                    st.markdown("##### 📊 整体风险评估")
                    st.markdown(f"- **结节总数**: {total_nodules}个")
                    
                    # 最高风险等级（带颜色）
                    risk_colors_display = {
                        "High": "🔴",
                        "Medium": "🟡",
                        "Low": "🟢",
                    }
                    risk_color = risk_colors_display.get(highest_risk, "⚪")
                    st.markdown(f"- **最高风险等级**: {risk_color} {highest_risk}")

                    # 风险分布（如有多个结节）
                    if total_nodules > 1:
                        risk_dist = {"Low": 0, "Medium": 0, "High": 0}
                        for nodule in nodules:
                            risk = nodule.get("risk_assessment", "Low")
                            risk_dist[risk] = risk_dist.get(risk, 0) + 1
                        st.markdown("##### 📊 风险分布")
                        st.markdown(f"- 低风险: {risk_dist.get('Low', 0)}个")
                        st.markdown(f"- 中风险: {risk_dist.get('Medium', 0)}个")
                        st.markdown(f"- 高风险: {risk_dist.get('High', 0)}个")
                    
                    # 不一致预警总结
                    inconsistency_count = sum(1 for n in nodules if n.get("inconsistency_alert", False))
                    if inconsistency_count > 0:
                        st.markdown("##### ⚠️ 不一致预警总结")
                        st.warning(f"检测到 **{inconsistency_count}个结节** 存在描述与结论不一致的情况，建议重新评估或咨询专业医生。")
                        
                        # 列出所有不一致的结节
                        inconsistency_nodules = [n for n in nodules if n.get("inconsistency_alert", False)]
                        for idx, nodule in enumerate(inconsistency_nodules):
                            chinese_name = get_nodule_chinese_name(nodule.get("id"), nodules.index(nodule))
                            reasons = nodule.get("inconsistency_reasons", [])
                            if reasons:
                                reasons_str = "；".join(reasons)
                                st.markdown(f"- **{chinese_name}**：{reasons_str}")
                            else:
                                st.markdown(f"- **{chinese_name}**：检测到不一致，但具体原因未提取")

                # 事实摘要（统一，不重复）- v1.2.0
                # 优先使用LLM返回的summary，如果为空或不够详细，则自动生成
                summary = overall_assessment.get("summary", "")
                
                # 判断summary是否为空或不够详细
                summary_is_empty = (
                    not summary or 
                    (isinstance(summary, list) and not any(summary)) or 
                    (isinstance(summary, str) and not summary.strip())
                )
                
                summary_is_insufficient = False
                if summary and not summary_is_empty:
                    if isinstance(summary, list):
                        # 如果summary列表长度小于结节数，认为不够详细
                        summary_is_insufficient = len(summary) < len(nodules)
                    else:
                        # 如果summary字符串长度小于结节数*50字符，认为不够详细
                        summary_is_insufficient = len(summary) < len(nodules) * 50
                
                # 只显示一个事实摘要
                with st.container():
                    st.markdown("##### 📋 事实摘要")
                    
                    if summary_is_empty or summary_is_insufficient:
                        # 自动生成详细摘要
                        for idx, nodule in enumerate(nodules):
                            chinese_name = get_nodule_chinese_name(nodule.get("id"), idx)
                            location = nodule.get("location", {})
                            morphology = nodule.get("morphology", {})
                            birads = nodule.get("birads_class", "")
                            risk = nodule.get("risk_assessment", "Low")
                            malignant_signs = nodule.get("malignant_signs", [])
                            inconsistency = nodule.get("inconsistency_alert", False)
                            
                            # 位置信息（不包含象限）
                            location_parts = []
                            if location.get("breast"):
                                location_parts.append(location.get("breast"))
                            if location.get("clock_position"):
                                location_parts.append(location.get("clock_position"))
                            if location.get("distance_from_nipple"):
                                location_parts.append(f"距乳头{location.get('distance_from_nipple')}")
                            location_str = "".join(location_parts) if location_parts else "位置未提取"
                            
                            # 形态学特征
                            shape_str = morphology.get("shape", "")
                            boundary_str = morphology.get("boundary", "")
                            echo_str = morphology.get("echo", "")
                            orientation_str = morphology.get("orientation", "")
                            size_str = morphology.get("size", "")
                            
                            # 构建详细摘要
                            summary_parts = [f"{chinese_name}（{location_str}）"]
                            
                            if size_str:
                                summary_parts.append(f"大小{size_str}")
                            if shape_str:
                                summary_parts.append(f"形状{shape_str}")
                            if boundary_str:
                                summary_parts.append(f"边界{boundary_str}")
                            if echo_str:
                                summary_parts.append(f"回声{echo_str}")
                            if orientation_str:
                                summary_parts.append(f"方位{orientation_str}")
                            
                            if malignant_signs:
                                summary_parts.append(f"恶性征象：{', '.join(malignant_signs)}")
                            
                            if birads:
                                summary_parts.append(f"BI-RADS {birads}类")
                            
                            summary_parts.append(f"风险等级{risk}")
                            
                            if inconsistency:
                                summary_parts.append("⚠️存在不一致")
                            
                            summary_item = "，".join(summary_parts)
                            st.markdown(f"- {summary_item}")
                    else:
                        # 使用LLM返回的summary
                        if isinstance(summary, list):
                            for item in summary:
                                if item:  # 确保不是空字符串
                                    st.markdown(f"- {item}")
                        else:
                            if summary:  # 确保不是空字符串
                                st.markdown(f"{summary}")

                # 综合建议（更具体）
                advice = overall_assessment.get("advice", "")
                if not advice or len(advice.strip()) < 10:  # 如果建议太短，生成更具体的建议
                    # 根据结节情况生成具体建议
                    advice_parts = []
                    for nodule in nodules:
                        birads = nodule.get("birads_class", "")
                        risk = nodule.get("risk_assessment", "Low")
                        inconsistency = nodule.get("inconsistency_alert", False)
                        
                        if inconsistency:
                            advice_parts.append("检测到报告描述与结论存在不一致，建议重新评估或咨询专业医生。")
                        elif birads == "3":
                            advice_parts.append("BI-RADS 3类结节建议6个月后复查超声，监测变化。")
                        elif birads in ["4", "5"]:
                            advice_parts.append(f"BI-RADS {birads}类结节建议尽快进行进一步检查（如穿刺活检）以明确诊断。")
                        elif risk == "High":
                            advice_parts.append("高风险结节建议尽快就医，进行专业评估。")
                        elif risk == "Medium":
                            advice_parts.append("中风险结节建议3-6个月后复查，密切观察。")
                        else:
                            advice_parts.append("低风险结节建议定期随访，保持观察。")
                    
                    if advice_parts:
                        advice = " ".join(advice_parts)
                
                if advice:
                    with st.container():
                        st.markdown("##### 💡 MedCrux 建议")
                        st.info(advice)

        else:
            st.info("未检测到结节")
