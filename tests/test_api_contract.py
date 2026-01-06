"""
接口契约测试：验证前后端接口数据结构匹配

测试目标：
1. 验证后端返回的数据结构与前端期望的数据结构匹配
2. 验证函数签名和调用匹配
3. 验证数据传递正确性

基于：docs/dev/api/API_CONTRACT.md
"""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from medcrux.analysis.report_structure_parser import parse_report_structure
from medcrux.api.main import app

client = TestClient(app)


class TestAPIContract:
    """接口契约测试类"""

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_report_structure_backend_contract(self):
        """
        测试报告结构解析后端接口契约

        验证后端返回的数据结构符合接口契约定义
        """
        # 使用抽象占位符的测试数据
        ocr_text = """
检查所见：[乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况]

影像学诊断：[BI-RADS分类] [诊断意见]

建议：[临床建议]
        """

        result = parse_report_structure(ocr_text.strip())

        # 验证返回结构符合接口契约
        assert isinstance(result, dict), "返回结果应该是字典类型"

        # 验证必需字段存在
        assert "findings" in result, "返回结果必须包含findings字段"
        assert "diagnosis" in result, "返回结果必须包含diagnosis字段"
        assert "recommendation" in result, "返回结果必须包含recommendation字段"

        # 验证字段类型符合接口契约
        assert result["findings"] is None or isinstance(
            result["findings"], str
        ), "findings字段类型应该是str | None"
        assert result["diagnosis"] is None or isinstance(
            result["diagnosis"], str
        ), "diagnosis字段类型应该是str | None"
        assert result["recommendation"] is None or isinstance(
            result["recommendation"], str
        ), "recommendation字段类型应该是str | None"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_report_structure_api_response_contract(self, mock_extract, mock_analyze):
        """
        测试报告结构解析API响应接口契约

        验证API响应中的report_structure字段结构符合接口契约定义
        """
        # Mock OCR结果
        mock_extract.return_value = """
检查所见：[乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况]

影像学诊断：[BI-RADS分类] [诊断意见]
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
        with patch("medcrux.api.main.parse_report_structure") as mock_parse:
            mock_parse.return_value = {
                "findings": "[乳腺结构描述] [病变描述]",
                "diagnosis": "[BI-RADS分类] [诊断意见]",
                "recommendation": None,
            }

            # 创建测试图片文件
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

            # 发送请求
            response = client.post("/api/analyze/upload", files=files)

            # 验证响应
            assert response.status_code == 200
            data = response.json()

            # 验证report_structure字段存在
            assert "report_structure" in data, "API响应必须包含report_structure字段"

            # 验证report_structure字段结构
            report_structure = data["report_structure"]
            assert report_structure is not None, "report_structure字段不应该为None"

            # 验证字段类型符合接口契约
            assert "findings" in report_structure, "report_structure必须包含findings字段"
            assert "diagnosis" in report_structure, "report_structure必须包含diagnosis字段"
            assert "recommendation" in report_structure, "report_structure必须包含recommendation字段"

            assert isinstance(
                report_structure["findings"], (str, type(None))
            ), "findings字段类型应该是str | None"
            assert isinstance(
                report_structure["diagnosis"], (str, type(None))
            ), "diagnosis字段类型应该是str | None"
            assert isinstance(
                report_structure["recommendation"], (str, type(None))
            ), "recommendation字段类型应该是str | None"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_report_structure_api_response_optional(self, mock_extract, mock_analyze):
        """
        测试report_structure字段可选性

        验证当后端解析失败时，report_structure字段可以为None
        """
        # Mock OCR结果
        mock_extract.return_value = "[测试OCR文本]"

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

            # 验证report_structure字段可以为None或不存在
            # 如果不存在，说明后端正确处理了异常
            if "report_structure" in data:
                assert (
                    data["report_structure"] is None
                ), "当解析失败时，report_structure应该为None"

    def test_health_check_contract(self):
        """
        测试健康检查接口契约

        验证健康检查接口的响应结构符合接口契约定义
        """
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        # 验证响应结构符合接口契约
        assert "status" in data, "响应必须包含status字段"
        assert "version" in data, "响应必须包含version字段"

        # 验证字段类型
        assert isinstance(data["status"], str), "status字段类型应该是str"
        assert isinstance(data["version"], str), "version字段类型应该是str"

        # 验证字段值
        assert data["status"] == "operational", "status字段值应该是operational"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_response_contract(self, mock_extract, mock_analyze):
        """
        测试分析报告接口响应契约

        验证分析报告接口的响应结构符合接口契约定义
        """
        # Mock OCR结果
        mock_extract.return_value = "[测试OCR文本]"

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

        # 验证响应结构符合接口契约
        assert "filename" in data, "响应必须包含filename字段"
        assert "ocr_text" in data, "响应必须包含ocr_text字段"
        assert "ai_result" in data, "响应必须包含ai_result字段"
        assert "message" in data, "响应必须包含message字段"

        # 验证字段类型
        assert isinstance(data["filename"], str), "filename字段类型应该是str"
        assert isinstance(data["ocr_text"], str), "ocr_text字段类型应该是str"
        assert isinstance(data["ai_result"], dict), "ai_result字段类型应该是dict"
        assert isinstance(data["message"], str), "message字段类型应该是str"

        # 验证report_structure字段可选性
        # report_structure字段可能不存在（如果解析失败）或为None
        if "report_structure" in data:
            assert data["report_structure"] is None or isinstance(
                data["report_structure"], dict
            ), "report_structure字段类型应该是dict | None"

