"""
测试API端点
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from medcrux.api.main import app

client = TestClient(app)


class TestAPI:
    """测试API端点"""

    def test_health_check(self):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["version"] == "0.1.0"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_success(self, mock_extract, mock_analyze):
        """测试分析报告接口成功"""
        # Mock OCR结果
        mock_extract.return_value = "超声描述：左乳上方可见低回声结节，大小1.2x0.8cm，边界清晰。"

        # Mock AI分析结果
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_findings": ["低回声结节"],
            "original_conclusion": "BI-RADS 3类",
            "ai_risk_assessment": "Low",
            "inconsistency_alert": False,
            "advice": "建议随访",
        }

        # 创建测试图片文件
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        response = client.post("/analyze/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.jpg"
        assert "ocr_text" in data
        assert "ai_result" in data
        assert data["message"] == "分析完成"
        assert mock_extract.called
        assert mock_analyze.called

    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_ocr_failure(self, mock_extract):
        """测试OCR识别失败"""
        # Mock OCR失败
        mock_extract.side_effect = ValueError("无法解析图像文件")

        image_bytes = b"invalid image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        response = client.post("/analyze/upload", files=files)

        assert response.status_code == 500
        assert "OCR识别失败" in response.json()["detail"]

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_ai_failure(self, mock_extract, mock_analyze):
        """测试AI分析失败"""
        # Mock OCR成功
        mock_extract.return_value = "超声描述：左乳上方可见低回声结节。"

        # Mock AI分析失败
        mock_analyze.side_effect = Exception("AI分析失败")

        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        response = client.post("/analyze/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["ocr_text"] != ""
        assert data["ai_result"]["ai_risk_assessment"] == "Error"
        assert "AI分析失败" in data["message"]

    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_short_text(self, mock_extract):
        """测试OCR识别结果过短"""
        # Mock OCR结果过短
        mock_extract.return_value = "短文本"

        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}

        response = client.post("/analyze/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["ocr_text"] == ""
        assert "未能识别出有效文字" in data["message"]
