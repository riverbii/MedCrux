"""
Pytest配置文件和fixtures
"""

import os
from pathlib import Path

import pytest

# 测试数据目录
TEST_DATA_DIR = Path(__file__).parent / "test_data"


@pytest.fixture
def sample_ocr_text():
    """示例OCR文本"""
    return """超声描述：
左乳上方可见低回声结节，大小1.2×0.8×0.6cm，边界清晰，形态规则，内部回声均匀。
右乳未见明显异常。

影像学诊断：
左乳低回声结节，BI-RADS 3类，建议6个月后复查。

建议：
定期随访。"""


@pytest.fixture
def sample_ocr_text_with_inconsistency():
    """示例OCR文本（包含不一致）"""
    return """超声描述：
左乳上方可见条状低回声，大小1.2×0.8×0.6cm，边界清晰，内部回声均匀。

影像学诊断：
左乳低回声结节，BI-RADS 3类，建议6个月后复查。

建议：
定期随访。"""


@pytest.fixture
def mock_image_bytes():
    """Mock图片字节流（PNG格式）"""
    # 创建一个简单的PNG文件头 + 数据
    # PNG文件头：89 50 4E 47 0D 0A 1A 0A
    png_header = b"\x89PNG\r\n\x1a\n"
    # 简单的PNG数据（实际使用时会被Mock替换）
    png_data = png_header + b"0" * 1000
    return png_data


@pytest.fixture
def mock_ocr_result():
    """Mock OCR识别结果"""
    return [
        [[0, 0, 100, 20], "超声描述", 0.95],
        [[0, 20, 200, 40], "左乳上方可见低回声结节", 0.92],
        [[0, 40, 150, 60], "大小1.2×0.8×0.6cm", 0.90],
        [[0, 60, 200, 80], "边界清晰", 0.88],
        [[0, 80, 200, 100], "BI-RADS 3类", 0.93],
    ]


@pytest.fixture
def mock_llm_response():
    """Mock LLM响应"""
    return {
        "patient_gender": "Female",
        "extracted_findings": ["低回声结节"],
        "extracted_shape": "椭圆形",
        "extracted_boundary": "清晰",
        "extracted_echo": "均匀低回声",
        "extracted_orientation": "平行",
        "extracted_malignant_signs": [],
        "original_conclusion": "BI-RADS 3类",
        "birads_class": "3",
        "ai_risk_assessment": "Low",
        "inconsistency_alert": False,
        "inconsistency_reasons": [],
        "advice": "建议6个月后复查超声以监测变化",
    }


@pytest.fixture
def mock_llm_response_with_inconsistency():
    """Mock LLM响应（包含不一致）"""
    return {
        "patient_gender": "Female",
        "extracted_findings": ["条状低回声"],
        "extracted_shape": "条状",
        "extracted_boundary": "清晰",
        "extracted_echo": "低回声",
        "extracted_orientation": "平行",
        "extracted_malignant_signs": [],
        "original_conclusion": "BI-RADS 3类",
        "birads_class": "3",
        "ai_risk_assessment": "Medium",
        "inconsistency_alert": True,
        "inconsistency_reasons": ["形状不符合：要求椭圆形，实际为条状（非标准术语）"],
        "advice": "检测到不一致，建议进一步检查",
    }


@pytest.fixture
def mock_rag_result():
    """Mock RAG检索结果"""
    return {
        "entities": [
            {
                "id": "concept_birads_3",
                "name": "BI-RADS 3类",
                "content": "可能良性，恶性可能性<2%",
                "type": "concept",
            },
            {
                "id": "term_oval",
                "name": "椭圆形",
                "content": "椭圆形（oval）",
                "type": "term",
            },
        ],
        "relations": [
            {
                "source_entity_id": "concept_birads_3",
                "target_entity_id": "term_oval",
                "type": "contains",
                "content": "BI-RADS 3类要求形状为椭圆形",
            }
        ],
        "inference_paths": [
            ["concept_birads_3", "term_oval"],
        ],
        "confidence": 0.85,
    }


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """自动设置测试环境"""
    # 设置测试API Key（如果未设置）
    if "DEEPSEEK_API_KEY" not in os.environ:
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key-for-testing")


@pytest.fixture
def test_data_dir():
    """测试数据目录"""
    TEST_DATA_DIR.mkdir(exist_ok=True)
    return TEST_DATA_DIR
