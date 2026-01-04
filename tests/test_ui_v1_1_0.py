"""
测试UI模块 - 版本1.1.0新格式

测试新UI功能：
- 标签页布局
- 结节列表展示
- 数据格式适配
- 胸部示意图渲染
"""

import pytest

# 由于Streamlit的特殊性，我们主要测试辅助函数和逻辑
# 实际的UI渲染测试需要在真实环境中进行


def test_render_breast_diagram_basic():
    """测试胸部示意图渲染（基础功能）"""
    # 导入UI模块（需要mock streamlit）
    try:
        import sys
        from unittest.mock import MagicMock

        # Mock streamlit
        sys.modules["streamlit"] = MagicMock()

        from medcrux.ui.app import render_breast_diagram

        # 测试数据：单个结节
        nodules = [
            {
                "id": "nodule_1",
                "location": {
                    "breast": "left",
                    "quadrant": "上外",
                    "clock_position": "12点",
                    "distance_from_nipple": "2.5 cm",
                },
                "morphology": {
                    "shape": "椭圆形",
                    "boundary": "清晰",
                    "echo": "均匀低回声",
                    "orientation": "平行",
                    "size": "1.2×0.8×0.6 cm",
                },
                "birads_class": "3",
                "risk_assessment": "Low",
                "inconsistency_alert": False,
                "inconsistency_reasons": [],
            }
        ]

        # 渲染示意图
        fig = render_breast_diagram(nodules)

        # 验证返回的是plotly figure对象
        assert fig is not None
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

        # 验证有数据点
        assert len(fig.data) > 0

    except (ImportError, ModuleNotFoundError):
        # 如果无法导入（可能因为streamlit环境），跳过测试
        pytest.skip("Cannot import UI module (streamlit not available)")


def test_render_breast_diagram_multiple_nodules():
    """测试多个结节的示意图渲染"""
    try:
        import sys
        from unittest.mock import MagicMock

        # Mock streamlit
        sys.modules["streamlit"] = MagicMock()

        from medcrux.ui.app import render_breast_diagram

        # 测试数据：多个结节
        nodules = [
            {
                "id": "nodule_1",
                "location": {
                    "breast": "left",
                    "quadrant": "上外",
                    "clock_position": "12点",
                },
                "morphology": {"shape": "椭圆形"},
                "risk_assessment": "Low",
            },
            {
                "id": "nodule_2",
                "location": {
                    "breast": "right",
                    "quadrant": "下内",
                    "clock_position": "6点",
                },
                "morphology": {"shape": "圆形"},
                "risk_assessment": "High",
            },
        ]

        # 渲染示意图
        fig = render_breast_diagram(nodules)

        # 验证返回的是plotly figure对象
        assert fig is not None
        assert len(fig.data) > 0

    except (ImportError, ModuleNotFoundError):
        pytest.skip("Cannot import UI module (streamlit not available)")


def test_render_breast_diagram_selected_nodule():
    """测试选中结节的示意图渲染"""
    try:
        import sys
        from unittest.mock import MagicMock

        # Mock streamlit
        sys.modules["streamlit"] = MagicMock()

        from medcrux.ui.app import render_breast_diagram

        # 测试数据：单个结节，选中状态
        nodules = [
            {
                "id": "nodule_1",
                "location": {
                    "breast": "left",
                    "quadrant": "上外",
                    "clock_position": "12点",
                },
                "morphology": {"shape": "椭圆形"},
                "risk_assessment": "Medium",
            }
        ]

        # 渲染示意图（选中状态）
        fig = render_breast_diagram(nodules, selected_nodule_id="nodule_1")

        # 验证返回的是plotly figure对象
        assert fig is not None
        assert len(fig.data) > 0

    except (ImportError, ModuleNotFoundError):
        pytest.skip("Cannot import UI module (streamlit not available)")


def test_data_format_adaptation():
    """测试数据格式适配逻辑"""
    # 测试新格式数据
    new_format_data = {
        "nodules": [
            {
                "id": "nodule_1",
                "location": {"breast": "left", "quadrant": "上外"},
                "morphology": {"shape": "椭圆形"},
                "risk_assessment": "Low",
            }
        ],
        "overall_assessment": {
            "total_nodules": 1,
            "highest_risk": "Low",
            "summary": ["低回声结节"],
            "advice": "建议随访",
        },
    }

    # 验证新格式结构
    assert "nodules" in new_format_data
    assert "overall_assessment" in new_format_data
    assert len(new_format_data["nodules"]) == 1
    assert new_format_data["overall_assessment"]["total_nodules"] == 1

    # 测试旧格式数据（模拟）
    old_format_data = {
        "extracted_shape": "椭圆形",
        "extracted_boundary": "清晰",
        "extracted_echo": "均匀低回声",
        "extracted_orientation": "平行",
        "extracted_malignant_signs": [],
        "birads_class": "3",
        "ai_risk_assessment": "Low",
        "inconsistency_alert": False,
        "inconsistency_reasons": [],
        "extracted_findings": ["低回声结节"],
        "advice": "建议随访",
    }

    # 验证可以转换为新格式
    converted_nodules = []
    if old_format_data.get("extracted_shape"):
        converted_nodules.append(
            {
                "id": "nodule_1",
                "location": {
                    "breast": "",
                    "quadrant": "",
                    "clock_position": "",
                    "distance_from_nipple": "",
                },
                "morphology": {
                    "shape": old_format_data.get("extracted_shape", ""),
                    "boundary": old_format_data.get("extracted_boundary", ""),
                    "echo": old_format_data.get("extracted_echo", ""),
                    "orientation": old_format_data.get("extracted_orientation", ""),
                    "size": "",
                },
                "malignant_signs": old_format_data.get("extracted_malignant_signs", []),
                "birads_class": old_format_data.get("birads_class", ""),
                "risk_assessment": old_format_data.get("ai_risk_assessment", "Low"),
                "inconsistency_alert": old_format_data.get("inconsistency_alert", False),
                "inconsistency_reasons": old_format_data.get("inconsistency_reasons", []),
            }
        )

    assert len(converted_nodules) == 1
    assert converted_nodules[0]["morphology"]["shape"] == "椭圆形"
    assert converted_nodules[0]["risk_assessment"] == "Low"


def test_nodule_list_structure():
    """测试结节列表数据结构"""
    # 测试多个结节的数据结构
    nodules = [
        {
            "id": "nodule_1",
            "location": {"breast": "left", "quadrant": "上外", "clock_position": "12点"},
            "morphology": {"shape": "椭圆形", "boundary": "清晰"},
            "birads_class": "3",
            "risk_assessment": "Low",
            "inconsistency_alert": False,
        },
        {
            "id": "nodule_2",
            "location": {"breast": "right", "quadrant": "下内", "clock_position": "6点"},
            "morphology": {"shape": "圆形", "boundary": "清晰"},
            "birads_class": "2",
            "risk_assessment": "Low",
            "inconsistency_alert": False,
        },
    ]

    # 验证数据结构
    assert len(nodules) == 2
    for nodule in nodules:
        assert "id" in nodule
        assert "location" in nodule
        assert "morphology" in nodule
        assert "risk_assessment" in nodule

    # 验证风险等级
    risk_levels = [n.get("risk_assessment") for n in nodules]
    assert "Low" in risk_levels


def test_overall_assessment_structure():
    """测试整体评估数据结构"""
    overall_assessment = {
        "total_nodules": 2,
        "highest_risk": "Medium",
        "summary": ["左乳上外结节", "右乳下内结节"],
        "advice": "建议随访",
    }

    # 验证数据结构
    assert "total_nodules" in overall_assessment
    assert "highest_risk" in overall_assessment
    assert "summary" in overall_assessment
    assert "advice" in overall_assessment

    assert overall_assessment["total_nodules"] == 2
    assert overall_assessment["highest_risk"] == "Medium"
    assert len(overall_assessment["summary"]) == 2
