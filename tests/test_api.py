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
        assert data["version"] == "1.2.0"

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

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    @patch("medcrux.api.main.parse_report_structure")
    def test_analyze_report_with_report_structure(self, mock_parse, mock_extract, mock_analyze):
        """测试包含报告结构解析的结果"""
        # Mock OCR结果
        mock_extract.return_value = "检查所见：左乳上方可见低回声结节。\n影像学诊断：BI-RADS 3类\n建议：随访"
        
        # Mock AI分析结果（新格式）
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "nodules": [{
                "id": "nodule_1",
                "morphology": {
                    "shape": "椭圆形",
                    "boundary": "清晰"
                },
                "birads_class": "3",
                "risk_assessment": "Low"
            }],
            "overall_assessment": {
                "total_nodules": 1,
                "highest_risk": "Low",
                "summary": ["低回声结节"],
                "advice": "建议随访"
            }
        }
        
        # Mock报告结构解析结果
        mock_parse.return_value = {
            "findings": "左乳上方可见低回声结节",
            "diagnosis": "BI-RADS 3类",
            "recommendation": "随访"
        }
        
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        
        response = client.post("/api/analyze/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "report_structure" in data
        assert data["report_structure"]["findings"] == "左乳上方可见低回声结节"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_new_format_conversion(self, mock_extract, mock_analyze):
        """测试新格式转旧格式的转换逻辑"""
        # Mock OCR结果
        mock_extract.return_value = "检查所见：左乳上方可见低回声结节。"
        
        # Mock AI分析结果（新格式，无结节）
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "nodules": [],
            "overall_assessment": {
                "total_nodules": 0,
                "highest_risk": "Low",
                "summary": [],
                "advice": "无异常"
            }
        }
        
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        
        response = client.post("/api/analyze/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        ai_result = data["ai_result"]
        # 验证无结节时的转换结果
        assert ai_result["extracted_shape"] == "未提取"
        assert ai_result["extracted_boundary"] == "未提取"
        assert ai_result["ai_risk_assessment"] == "Low"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_new_format_with_nodules(self, mock_extract, mock_analyze):
        """测试新格式（有结节）转旧格式"""
        # Mock OCR结果
        mock_extract.return_value = "检查所见：左乳上方可见低回声结节，大小1.2x0.8cm。"
        
        # Mock AI分析结果（新格式，有结节）
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "nodules": [{
                "id": "nodule_1",
                "morphology": {
                    "shape": "椭圆形",
                    "boundary": "清晰",
                    "echo": "低回声",
                    "orientation": "平行"
                },
                "birads_class": "3",
                "risk_assessment": "Low"
            }],
            "overall_assessment": {
                "total_nodules": 1,
                "highest_risk": "Low",
                "summary": ["低回声结节"],
                "advice": "建议随访"
            }
        }
        
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        
        response = client.post("/api/analyze/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        ai_result = data["ai_result"]
        # 验证转换后的旧格式字段
        assert ai_result["extracted_shape"] == "椭圆形"
        assert ai_result["extracted_boundary"] == "清晰"
        assert ai_result["extracted_echo"] == "低回声"
        assert ai_result["extracted_orientation"] == "平行"
        assert ai_result["birads_class"] == "3"

    @patch("medcrux.api.main.analyze_text_with_deepseek")
    @patch("medcrux.api.main.extract_text_from_bytes")
    def test_analyze_report_already_old_format(self, mock_extract, mock_analyze):
        """测试如果已经是旧格式，直接返回"""
        # Mock OCR结果
        mock_extract.return_value = "检查所见：左乳上方可见低回声结节。"
        
        # Mock AI分析结果（已经是旧格式）
        mock_analyze.return_value = {
            "patient_gender": "Female",
            "extracted_shape": "椭圆形",
            "extracted_boundary": "清晰",
            "ai_risk_assessment": "Low"
        }
        
        image_bytes = b"fake image data"
        files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
        
        response = client.post("/api/analyze/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        ai_result = data["ai_result"]
        # 验证旧格式直接返回，不转换
        assert ai_result["extracted_shape"] == "椭圆形"
        assert "nodules" not in ai_result

    def test_global_exception_handler(self):
        """测试全局异常处理器（决策点：捕获未处理的异常）"""
        from unittest.mock import MagicMock, patch

        from fastapi import Request

        from medcrux.api.main import global_exception_handler

        # 创建模拟的request和exception
        mock_request = MagicMock(spec=Request)
        mock_request.url = "http://test.com/test"
        mock_request.method = "GET"
        test_exception = Exception("测试异常")
        
        # 测试全局异常处理器
        import asyncio
        with patch('medcrux.api.main.log_error_with_context') as mock_log:
            result = asyncio.run(global_exception_handler(mock_request, test_exception))
            
            # 验证返回500状态码
            assert result.status_code == 500
            assert "服务器内部错误" in result.body.decode()
            
            # 验证错误被记录
            mock_log.assert_called_once()

    def test_convert_new_to_old_format_already_old(self):
        """测试convert_new_to_old_format：已经是旧格式（决策点：extracted_shape存在）"""
        from medcrux.api.main import analyze_report, app

        # 这个函数是analyze_report内部的，需要通过API测试
        # 或者需要提取出来作为独立函数
        # 暂时通过API测试验证
        pass

    def test_convert_new_to_old_format_no_nodules(self):
        """测试convert_new_to_old_format：无结节（决策点：nodules为空）"""
        from unittest.mock import patch

        from fastapi.testclient import TestClient
        
        mock_extract = patch("medcrux.api.main.extract_text_from_bytes")
        mock_analyze = patch("medcrux.api.main.analyze_text_with_deepseek")
        
        with mock_extract as m_extract, mock_analyze as m_analyze:
            m_extract.return_value = "检查所见：无异常发现。"
            m_analyze.return_value = {
                "patient_gender": "Female",
                "nodules": [],  # 无结节
                "overall_assessment": {
                    "total_nodules": 0,
                    "highest_risk": "Low",
                    "summary": [],
                    "advice": "无异常"
                }
            }
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            response = client.post("/api/analyze/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            ai_result = data["ai_result"]
            # 验证无结节时的转换结果
            assert ai_result["extracted_shape"] == "未提取"
            assert ai_result["extracted_boundary"] == "未提取"
            assert ai_result["extracted_echo"] == "未提取"
            assert ai_result["extracted_orientation"] == "未提取"
            assert ai_result["ai_risk_assessment"] == "Low"

    def test_convert_new_to_old_format_single_nodule(self):
        """测试convert_new_to_old_format：单结节（决策点：nodules长度为1）"""
        from unittest.mock import patch
        
        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze:
            mock_extract.return_value = "检查所见：左乳上方可见低回声结节。"
            mock_analyze.return_value = {
                "patient_gender": "Female",
                "nodules": [{
                    "id": "nodule_1",
                    "morphology": {
                        "shape": "椭圆形",
                        "boundary": "清晰",
                        "echo": "低回声",
                        "orientation": "平行"
                    },
                    "birads_class": "3",
                    "risk_assessment": "Low"
                }],
                "overall_assessment": {
                    "total_nodules": 1,
                    "highest_risk": "Low",
                    "summary": ["低回声结节"],
                    "advice": "建议随访"
                }
            }
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            response = client.post("/api/analyze/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            ai_result = data["ai_result"]
            # 验证单结节转换
            assert ai_result["extracted_shape"] == "椭圆形"
            assert ai_result["extracted_boundary"] == "清晰"
            assert ai_result["extracted_echo"] == "低回声"
            assert ai_result["extracted_orientation"] == "平行"
            assert ai_result["birads_class"] == "3"

    def test_convert_new_to_old_format_multiple_nodules(self):
        """测试convert_new_to_old_format：多结节（决策点：使用第一个结节）"""
        from unittest.mock import patch
        
        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze:
            mock_extract.return_value = "检查所见：左乳上方可见两个低回声结节。"
            mock_analyze.return_value = {
                "patient_gender": "Female",
                "nodules": [
                    {
                        "id": "nodule_1",
                        "morphology": {"shape": "椭圆形", "boundary": "清晰"},
                        "birads_class": "3"
                    },
                    {
                        "id": "nodule_2",
                        "morphology": {"shape": "不规则形", "boundary": "模糊"},
                        "birads_class": "4"
                    }
                ],
                "overall_assessment": {
                    "total_nodules": 2,
                    "highest_risk": "Medium",
                    "summary": ["低回声结节"],
                    "advice": "建议进一步检查"
                }
            }
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            response = client.post("/api/analyze/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            ai_result = data["ai_result"]
            # 验证使用第一个结节的数据
            assert ai_result["extracted_shape"] == "椭圆形"
            assert ai_result["extracted_boundary"] == "清晰"
            assert ai_result["birads_class"] == "3"

    def test_convert_new_to_old_format_missing_morphology(self):
        """测试convert_new_to_old_format：缺少morphology字段（边界条件）"""
        from unittest.mock import patch
        
        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract, \
             patch("medcrux.api.main.analyze_text_with_deepseek") as mock_analyze:
            mock_extract.return_value = "检查所见：左乳上方可见低回声结节。"
            mock_analyze.return_value = {
                "patient_gender": "Female",
                "nodules": [{
                    "id": "nodule_1",
                    # 缺少morphology字段
                    "birads_class": "3"
                }],
                "overall_assessment": {
                    "total_nodules": 1,
                    "highest_risk": "Low",
                    "summary": ["低回声结节"],
                    "advice": "建议随访"
                }
            }
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            response = client.post("/api/analyze/upload", files=files)
            
            assert response.status_code == 200
            data = response.json()
            ai_result = data["ai_result"]
            # 验证缺少字段时使用默认值或空字符串
            assert ai_result["extracted_shape"] == ""
            assert ai_result["extracted_boundary"] == ""

    def test_analyze_report_http_exception_re_raise(self):
        """测试analyze_report：HTTPException直接抛出（决策点：HTTPException不被捕获）"""
        from unittest.mock import patch

        from fastapi import HTTPException
        
        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract:
            mock_extract.side_effect = HTTPException(status_code=400, detail="Bad Request")
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            # HTTPException应该直接抛出，不被捕获
            response = client.post("/api/analyze/upload", files=files)
            assert response.status_code == 400

    def test_analyze_report_general_exception_handled(self):
        """测试analyze_report：一般异常被捕获（决策点：Exception被转换为HTTPException）"""
        from unittest.mock import patch
        
        with patch("medcrux.api.main.extract_text_from_bytes") as mock_extract:
            mock_extract.side_effect = Exception("未预期的错误")
            
            image_bytes = b"fake image data"
            files = {"file": ("test.jpg", image_bytes, "image/jpeg")}
            
            response = client.post("/api/analyze/upload", files=files)
            
            # 一般异常应该被捕获并转换为500
            assert response.status_code == 500
            assert "分析过程中发生错误" in response.json()["detail"]
