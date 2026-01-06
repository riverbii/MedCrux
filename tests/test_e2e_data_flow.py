"""
端到端数据流测试：验证从后端到前端的完整数据流

测试目标：
1. 验证reportStructure数据从后端到前端的完整传递
2. 验证前端是否正确使用reportStructure
3. 验证Fallback逻辑是否正确

基于：docs/dev/api/API_CONTRACT.md
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from medcrux.api.main import app

client = TestClient(app)


class TestE2EDataFlow:
    """端到端数据流测试类"""

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_report_structure_data_flow_complete(self, mock_extract, mock_analyze):
        """
        测试reportStructure数据流完整性

        验证数据从后端parse_report_structure到前端extractOriginalReportSummary的完整传递
        """
        # Mock OCR结果（使用抽象占位符）
        mock_extract.return_value = """
检查所见：[乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况]

影像学诊断：[BI-RADS分类] [诊断意见]

建议：[临床建议]
        """

        # Mock AI分析结果
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": ["低回声结节"],
            "original_conclusion": "BI-RADS X类",
            "ai_risk_assessment": "Low",
            "inconsistency_alert": False,
            "advice": "建议随访",
        }

        # Mock报告结构解析结果
        mock_report_structure = {
            "findings": "[乳腺结构描述] [病变描述]",
            "diagnosis": "[BI-RADS分类] [诊断意见]",
            "recommendation": "[临床建议]",
        }

        with patch("medcrux.api.main.parse_report_structure") as mock_parse:
            mock_parse.return_value = mock_report_structure

            # 创建测试图片文件
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

            # 发送请求
            response = client.post("/api/analyze/upload", files=files)

            # 验证响应
            assert response.status_code == 200
            data = response.json()

            # 验证数据流第1步：后端返回report_structure
            assert "report_structure" in data, "API响应必须包含report_structure字段"
            assert data["report_structure"] is not None, "report_structure不应该为None"

            # 验证数据流第2步：report_structure结构正确
            report_structure = data["report_structure"]
            assert report_structure["findings"] == mock_report_structure["findings"]
            assert report_structure["diagnosis"] == mock_report_structure["diagnosis"]
            assert report_structure["recommendation"] == mock_report_structure["recommendation"]

            # 验证数据流第3步：数据可以被前端使用
            # 注意：这里只验证后端数据传递，前端使用逻辑需要在前端测试中验证
            assert isinstance(report_structure["findings"], str), "findings应该可以被前端使用"
            assert isinstance(report_structure["diagnosis"], str), "diagnosis应该可以被前端使用"
            assert isinstance(
                report_structure["recommendation"], str
            ), "recommendation应该可以被前端使用"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_report_structure_data_flow_fallback(self, mock_extract, mock_analyze):
        """
        测试reportStructure数据流Fallback逻辑

        验证当后端解析失败时，前端可以使用Fallback逻辑
        """
        # Mock OCR结果
        mock_extract.return_value = """
检查所见：[乳腺结构描述] [病变描述]

影像学诊断：[BI-RADS分类] [诊断意见]
        """

        # Mock AI分析结果
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": [],
            "ai_risk_assessment": "Low",
        }

        # Mock报告结构解析失败
        with patch("medcrux.api.main.parse_report_structure") as mock_parse:
            mock_parse.side_effect = Exception("解析失败")

            # 创建测试图片文件
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

            # 发送请求
            response = client.post("/api/analyze/upload", files=files)

            # 验证响应
            assert response.status_code == 200
            data = response.json()

            # 验证Fallback逻辑：report_structure可以为None或不存在
            # 前端应该能够处理这种情况，使用正则表达式从ocr_text中提取
            if "report_structure" in data:
                assert (
                    data["report_structure"] is None
                ), "当解析失败时，report_structure应该为None"

            # 验证ocr_text存在，前端可以使用Fallback逻辑
            assert "ocr_text" in data, "ocr_text必须存在，用于Fallback逻辑"
            assert isinstance(data["ocr_text"], str), "ocr_text应该是字符串类型"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_report_structure_data_flow_partial(self, mock_extract, mock_analyze):
        """
        测试reportStructure数据流部分字段

        验证当某些字段为None时，数据流仍然正常
        """
        # Mock OCR结果（只有检查所见，没有建议）
        mock_extract.return_value = """
检查所见：[乳腺结构描述] [病变描述]

影像学诊断：[BI-RADS分类] [诊断意见]
        """

        # Mock AI分析结果
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": [],
            "ai_risk_assessment": "Low",
        }

        # Mock报告结构解析结果（recommendation为None）
        mock_report_structure = {
            "findings": "[乳腺结构描述] [病变描述]",
            "diagnosis": "[BI-RADS分类] [诊断意见]",
            "recommendation": None,
        }

        with patch("medcrux.api.main.parse_report_structure") as mock_parse:
            mock_parse.return_value = mock_report_structure

            # 创建测试图片文件
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

            # 发送请求
            response = client.post("/api/analyze/upload", files=files)

            # 验证响应
            assert response.status_code == 200
            data = response.json()

            # 验证数据流：部分字段为None时仍然正常
            assert "report_structure" in data
            report_structure = data["report_structure"]
            assert report_structure is not None

            # 验证部分字段为None
            assert report_structure["findings"] is not None, "findings不应该为None"
            assert report_structure["diagnosis"] is not None, "diagnosis不应该为None"
            assert (
                report_structure["recommendation"] is None
            ), "recommendation可以为None"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_report_structure_data_flow_empty_ocr(self, mock_extract, mock_analyze):
        """
        测试reportStructure数据流（OCR文本为空）

        验证当OCR文本为空时，数据流仍然正常
        """
        # Mock OCR结果为空
        mock_extract.return_value = ""

        # Mock AI分析结果
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": [],
            "ai_risk_assessment": "Low",
        }

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        # 发送请求
        response = client.post("/api/analyze/upload", files=files)

        # 验证响应
        assert response.status_code == 200
        data = response.json()

        # 验证当OCR文本为空时，report_structure可能为None或不存在
        # 这是正常情况，前端应该能够处理
        if "report_structure" in data:
            assert (
                data["report_structure"] is None
            ), "当OCR文本为空时，report_structure应该为None"

