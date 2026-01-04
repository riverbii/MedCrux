"""
自动化功能测试：使用Mock数据测试功能

不需要真实环境，使用Mock数据模拟真实场景
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from medcrux.api.main import app

client = TestClient(app)


class TestFunctionalAutomated:
    """自动化功能测试类（使用Mock数据）"""

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_ui_workflow_success(self, mock_extract, mock_analyze):
        """
        测试UI工作流程（成功场景）

        模拟完整的用户操作流程：
        1. 上传图片
        2. OCR识别
        3. AI分析
        4. 显示结果
        """
        # Mock OCR结果
        mock_extract.return_value = """超声描述：
左乳上方可见低回声结节，大小1.2×0.8×0.6cm，边界清晰，形态规则，内部回声均匀。
右乳未见明显异常。

影像学诊断：
左乳低回声结节，BI-RADS 3类，建议6个月后复查。"""

        # Mock AI分析结果
        mock_analyze.return_value = {
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

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        # 发送请求
        response = client.post("/analyze/upload", files=files)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.jpg"
        assert "ocr_text" in data
        assert "ai_result" in data
        assert data["ai_result"]["ai_risk_assessment"] == "Low"
        assert data["ai_result"]["inconsistency_alert"] is False
        assert "extracted_shape" in data["ai_result"]
        assert "extracted_boundary" in data["ai_result"]
        assert "extracted_echo" in data["ai_result"]
        assert "extracted_orientation" in data["ai_result"]

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_ui_workflow_with_inconsistency(self, mock_extract, mock_analyze):
        """
        测试UI工作流程（不一致场景）

        测试系统能正确识别和显示不一致情况
        """
        # Mock OCR结果（包含不一致的描述）
        mock_extract.return_value = """超声描述：
左乳上方可见条状低回声，大小1.2×0.8×0.6cm，边界清晰。

影像学诊断：
左乳低回声结节，BI-RADS 3类，建议6个月后复查。"""

        # Mock AI分析结果（检测到不一致）
        mock_analyze.return_value = {
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

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        # 发送请求
        response = client.post("/analyze/upload", files=files)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["ai_result"]["inconsistency_alert"] is True
        assert len(data["ai_result"]["inconsistency_reasons"]) > 0
        assert "条状" in data["ai_result"]["inconsistency_reasons"][0]
        assert data["ai_result"]["ai_risk_assessment"] == "Medium"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_ui_display_all_features(self, mock_extract, mock_analyze):
        """
        测试UI显示所有特征

        验证所有形态学特征都能正确显示
        """
        # Mock OCR结果
        mock_extract.return_value = "超声描述：左乳上方可见低回声结节，大小1.2×0.8×0.6cm，边界清晰。"

        # Mock AI分析结果（包含所有特征）
        mock_analyze.return_value = {
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
            "advice": "建议6个月后复查",
        }

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        # 发送请求
        response = client.post("/analyze/upload", files=files)

        # 验证所有特征都在响应中
        assert response.status_code == 200
        data = response.json()
        ai_result = data["ai_result"]

        # 验证所有必需字段
        assert "extracted_shape" in ai_result
        assert "extracted_boundary" in ai_result
        assert "extracted_echo" in ai_result
        assert "extracted_orientation" in ai_result
        assert "birads_class" in ai_result
        assert "ai_risk_assessment" in ai_result
        assert "inconsistency_alert" in ai_result
        assert "inconsistency_reasons" in ai_result
        assert "advice" in ai_result

        # 验证特征值不为空
        assert ai_result["extracted_shape"] != ""
        assert ai_result["extracted_boundary"] != ""
        assert ai_result["extracted_echo"] != ""
        assert ai_result["extracted_orientation"] != ""
        assert ai_result["birads_class"] != ""

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_ui_multiple_values_handling(self, mock_extract, mock_analyze):
        """
        测试UI处理多个值的情况

        验证系统能正确处理LLM返回的多个值（用/分隔）
        """
        # Mock OCR结果
        mock_extract.return_value = "超声描述：左乳上方可见低回声结节。"

        # Mock AI分析结果（包含多个值）
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": ["低回声结节"],
            "extracted_shape": "椭圆形/圆形/条状/其他",
            "extracted_boundary": "清晰/清晰/清晰/清晰",
            "extracted_echo": "无回声/低回声/低回声/低回声",
            "extracted_orientation": "平行/平行/平行/平行",
            "extracted_malignant_signs": [],
            "original_conclusion": "BI-RADS 3类",
            "birads_class": "3",
            "ai_risk_assessment": "Medium",
            "inconsistency_alert": True,
            "inconsistency_reasons": ["形状不符合：要求椭圆形，实际为条状（非标准术语）"],
            "advice": "检测到不一致，建议进一步检查",
        }

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        # 发送请求
        response = client.post("/analyze/upload", files=files)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        ai_result = data["ai_result"]

        # 验证多个值被正确处理
        assert "/" in ai_result["extracted_shape"]  # 包含多个值
        assert ai_result["inconsistency_alert"] is True  # 应该检测到不一致（条状）

    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["version"] == "0.1.0"
