"""
测试LLM分析引擎模块
"""

import os
from unittest.mock import MagicMock, patch

from medcrux.analysis.llm_engine import _get_retriever, analyze_text_with_deepseek


class TestLLMEngine:
    """测试LLM分析引擎"""

    def test_get_retriever_singleton(self):
        """测试检索器单例模式"""
        retriever1 = _get_retriever()
        retriever2 = _get_retriever()
        assert retriever1 is retriever2

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    def test_analyze_text_with_rag(self, mock_get_retriever, mock_client):
        """测试带RAG检索的分析"""
        # Mock RAG检索结果
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = {
            "entities": [
                {
                    "id": "concept_birads_3",
                    "name": "BI-RADS 3类",
                    "content": "可能良性，恶性可能性<2%",
                }
            ],
            "relations": [],
            "inference_paths": [],
            "confidence": 0.8,
        }
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        '{"patient_gender": "Female", "extracted_findings": ["低回声结节"], '
                        '"original_conclusion": "BI-RADS 3类", "ai_risk_assessment": "Low", '
                        '"inconsistency_alert": false, "advice": "建议随访"}'
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # 设置API Key
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 执行分析
        result = analyze_text_with_deepseek("超声描述：左乳上方可见低回声结节，大小1.2x0.8cm，边界清晰。")

        # 验证结果
        assert isinstance(result, dict)
        assert "ai_risk_assessment" in result
        assert mock_retriever.retrieve.called

    @patch("medcrux.analysis.llm_engine.client")
    def test_analyze_text_without_api_key(self, mock_client):
        """测试没有API Key的情况"""
        # 移除API Key
        if "DEEPSEEK_API_KEY" in os.environ:
            del os.environ["DEEPSEEK_API_KEY"]

        result = analyze_text_with_deepseek("测试文本")
        assert result["ai_risk_assessment"] == "Error"
        assert "advice" in result

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    def test_analyze_text_rag_failure(self, mock_get_retriever, mock_client):
        """测试RAG检索失败的情况"""
        # Mock RAG检索失败
        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = Exception("RAG检索失败")
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"ai_risk_assessment": "Low", "advice": "建议随访"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # 设置API Key
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 执行分析（应该继续执行，不因RAG失败而中断）
        result = analyze_text_with_deepseek("测试文本")
        assert isinstance(result, dict)
        assert "ai_risk_assessment" in result
