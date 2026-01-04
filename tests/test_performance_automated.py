"""
自动化性能测试：使用Mock数据测试性能

不需要真实图片和API Key，使用Mock数据模拟真实环境
"""

import time
from unittest.mock import MagicMock, patch

import numpy as np

from medcrux.analysis.llm_engine import analyze_text_with_deepseek
from medcrux.ingestion.ocr_service import extract_text_from_bytes
from medcrux.rag.graphrag_retriever import GraphRAGRetriever


class TestPerformanceAutomated:
    """自动化性能测试类（使用Mock数据）"""

    @patch("medcrux.ingestion.ocr_service.engine")
    @patch("cv2.imdecode")
    def test_ocr_performance_automated(self, mock_imdecode, mock_engine):
        """
        测试OCR识别性能（自动化，使用Mock数据）

        要求：< 5秒
        """
        # Mock图像解码
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        # Mock OCR结果（模拟真实OCR识别时间）
        def mock_ocr_with_delay(img):
            time.sleep(0.1)  # 模拟OCR处理时间（100ms，远小于5秒要求）
            return (
                [
                    [[0, 0, 100, 20], "超声描述", 0.95],
                    [[0, 20, 200, 40], "左乳上方可见低回声结节", 0.92],
                    [[0, 40, 150, 60], "大小1.2×0.8×0.6cm", 0.90],
                ],
                None,
            )

        mock_engine.return_value = mock_ocr_with_delay(mock_image)

        # 创建测试图片字节流
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 1000

        # 测量OCR时间
        start_time = time.time()
        result = extract_text_from_bytes(image_bytes)
        ocr_time = time.time() - start_time

        print(f"\nOCR识别时间: {ocr_time:.2f}秒 (要求<5秒)")
        assert ocr_time < 5.0, f"OCR识别时间{ocr_time:.2f}秒超过PRD要求(5秒)"
        assert len(result) > 0, "OCR识别结果不应为空"

    def test_rag_retrieval_performance_automated(self, sample_ocr_text):
        """
        测试RAG检索性能（自动化，使用真实RAG检索器）

        要求：< 2秒
        """
        retriever = GraphRAGRetriever()
        start_time = time.time()
        retrieval_result = retriever.retrieve(sample_ocr_text)
        rag_time = time.time() - start_time

        print(f"\nRAG检索时间: {rag_time:.2f}秒 (要求<2秒)")
        print(f"检索到{len(retrieval_result['entities'])}个实体，{len(retrieval_result['relations'])}个关系")
        assert rag_time < 2.0, f"RAG检索时间{rag_time:.2f}秒超过PRD要求(2秒)"
        assert isinstance(retrieval_result, dict)
        assert "entities" in retrieval_result
        assert "confidence" in retrieval_result

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    def test_llm_analysis_performance_automated(
        self, mock_get_retriever, mock_client, sample_ocr_text, mock_rag_result
    ):
        """
        测试LLM分析性能（自动化，使用Mock LLM）

        要求：< 10秒
        """
        # Mock RAG检索器
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_rag_result
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应（模拟真实LLM响应时间）
        def mock_llm_with_delay(*args, **kwargs):
            time.sleep(0.5)  # 模拟LLM处理时间（500ms，远小于10秒要求）
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message=MagicMock(
                        content=(
                            '{"patient_gender": "Female", "extracted_findings": ["低回声结节"], '
                            '"extracted_shape": "椭圆形", "extracted_boundary": "清晰", '
                            '"extracted_echo": "均匀低回声", "extracted_orientation": "平行", '
                            '"extracted_malignant_signs": [], "original_conclusion": "BI-RADS 3类", '
                            '"birads_class": "3", "ai_risk_assessment": "Low", '
                            '"inconsistency_alert": false, "inconsistency_reasons": [], '
                            '"advice": "建议6个月后复查"}'
                        )
                    )
                )
            ]
            return mock_response

        mock_client.chat.completions.create.side_effect = mock_llm_with_delay

        # 设置API Key
        import os

        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 测量LLM分析时间
        start_time = time.time()
        result = analyze_text_with_deepseek(sample_ocr_text)
        llm_time = time.time() - start_time

        print(f"\nLLM分析时间: {llm_time:.2f}秒 (要求<10秒)")
        assert llm_time < 10.0, f"LLM分析时间{llm_time:.2f}秒超过PRD要求(10秒)"
        assert isinstance(result, dict)
        assert "ai_risk_assessment" in result

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    @patch("medcrux.ingestion.ocr_service.engine")
    @patch("cv2.imdecode")
    def test_end_to_end_performance_automated(
        self,
        mock_imdecode,
        mock_engine,
        mock_get_retriever,
        mock_client,
        mock_rag_result,
    ):
        """
        测试端到端性能（自动化，使用Mock数据）

        要求：< 20秒
        """
        # Mock图像解码
        mock_image = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_imdecode.return_value = mock_image

        # Mock OCR结果
        def mock_ocr_with_delay(img):
            time.sleep(0.1)  # 模拟OCR处理时间
            return (
                [
                    [[0, 0, 100, 20], "超声描述", 0.95],
                    [[0, 20, 200, 40], "左乳上方可见低回声结节", 0.92],
                    [[0, 40, 150, 60], "大小1.2×0.8×0.6cm", 0.90],
                    [[0, 60, 200, 80], "边界清晰", 0.88],
                    [[0, 80, 200, 100], "BI-RADS 3类", 0.93],
                ],
                None,
            )

        mock_engine.return_value = mock_ocr_with_delay(mock_image)

        # Mock RAG检索器
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = mock_rag_result
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应
        def mock_llm_with_delay(*args, **kwargs):
            time.sleep(0.5)  # 模拟LLM处理时间
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message=MagicMock(
                        content=(
                            '{"patient_gender": "Female", "extracted_findings": ["低回声结节"], '
                            '"extracted_shape": "椭圆形", "extracted_boundary": "清晰", '
                            '"extracted_echo": "均匀低回声", "extracted_orientation": "平行", '
                            '"extracted_malignant_signs": [], "original_conclusion": "BI-RADS 3类", '
                            '"birads_class": "3", "ai_risk_assessment": "Low", '
                            '"inconsistency_alert": false, "inconsistency_reasons": [], '
                            '"advice": "建议6个月后复查"}'
                        )
                    )
                )
            ]
            return mock_response

        mock_client.chat.completions.create.side_effect = mock_llm_with_delay

        # 设置API Key
        import os

        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 创建测试图片字节流
        image_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 1000

        # 1. OCR识别
        ocr_start = time.time()
        ocr_text = extract_text_from_bytes(image_bytes)
        ocr_time = time.time() - ocr_start

        # 2. AI分析（包含RAG检索和LLM分析）
        analysis_start = time.time()
        result = analyze_text_with_deepseek(ocr_text)
        analysis_time = time.time() - analysis_start

        # 总时间
        total_time = time.time() - ocr_start

        print("\n=== 性能测试结果（自动化） ===")
        print(f"OCR识别时间: {ocr_time:.2f}秒 (要求<5秒) {'✅' if ocr_time < 5.0 else '❌'}")
        print(f"AI分析时间: {analysis_time:.2f}秒 (包含RAG+LLM, 要求<10秒) {'✅' if analysis_time < 10.0 else '❌'}")
        print(f"总响应时间: {total_time:.2f}秒 (要求<20秒) {'✅' if total_time < 20.0 else '❌'}")
        print(f"风险评估: {result.get('ai_risk_assessment', 'Unknown')}")
        print(f"不一致预警: {result.get('inconsistency_alert', False)}")

        # 断言
        assert ocr_time < 5.0, f"OCR识别时间{ocr_time:.2f}秒超过PRD要求(5秒)"
        assert analysis_time < 10.0, f"AI分析时间{analysis_time:.2f}秒超过PRD要求(10秒)"
        assert total_time < 20.0, f"总响应时间{total_time:.2f}秒超过PRD要求(20秒)"
        assert isinstance(result, dict)
        assert "ai_risk_assessment" in result
