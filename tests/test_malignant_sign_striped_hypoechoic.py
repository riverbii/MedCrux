"""
测试：条状低回声（条索状）恶性征象识别

这是针对真实案例的测试：
- 报告描述：存在"条状低回声"（条索状）
- 实际结果：乳腺癌（已病理证实）
- 系统应能识别出这是恶性征象，并发出高风险预警
"""

import pytest

from medcrux.analysis.llm_engine import analyze_text_with_deepseek
from medcrux.rag.graphrag_retriever import GraphRAGRetriever


class TestMalignantSignStripedHypoechoic:
    """测试条状低回声恶性征象识别"""

    def test_rag_retrieval_striped_hypoechoic(self):
        """测试RAG能否检索到条状低回声实体"""
        retriever = GraphRAGRetriever()

        # 测试用例1：条状低回声
        query1 = "左侧乳腺可见条状低回声，大小约1.2cm"
        result1 = retriever.retrieve(query1)
        assert len(result1["entities"]) > 0, "应检索到相关实体"

        # 检查是否包含条状低回声相关实体
        entity_names = [e.get("name", "") for e in result1["entities"]]
        assert any(
            "条状" in name or "条索" in name for name in entity_names
        ), f"应检索到条状低回声实体，实际检索到: {entity_names}"

        # 测试用例2：条索状（同义词）
        query2 = "左侧乳腺可见条索状低回声"
        result2 = retriever.retrieve(query2)
        entity_names2 = [e.get("name", "") for e in result2["entities"]]
        assert any(
            "条状" in name or "条索" in name for name in entity_names2
        ), f"应通过同义词匹配到条状低回声实体，实际检索到: {entity_names2}"

        # 测试用例3：条索样（同义词）
        query3 = "左侧乳腺可见条索样低回声"
        result3 = retriever.retrieve(query3)
        entity_names3 = [e.get("name", "") for e in result3["entities"]]
        assert any(
            "条状" in name or "条索" in name for name in entity_names3
        ), f"应通过同义词匹配到条状低回声实体，实际检索到: {entity_names3}"

    def test_rag_retrieval_striped_hypoechoic_with_birads_3(self):
        """测试条状低回声 + BI-RADS 3类的情况（应识别为不一致）"""
        retriever = GraphRAGRetriever()

        # 真实案例：条状低回声但结论是BI-RADS 3类
        query = """
        超声描述：左侧乳腺上外象限可见条状低回声，大小约1.2×0.8cm，边界清晰，形态规则。
        CDFI：内见点状血流信号。
        提示：BI-RADS 3类。
        """

        result = retriever.retrieve(query)

        # 应检索到条状低回声实体
        entity_names = [e.get("name", "") for e in result["entities"]]
        assert any(
            "条状" in name or "条索" in name for name in entity_names
        ), f"应检索到条状低回声实体，实际检索到: {entity_names}"

        # 应检索到BI-RADS 3类实体
        assert any(
            "birads" in e.get("id", "").lower() and "3" in e.get("id", "") for e in result["entities"]
        ), "应检索到BI-RADS 3类实体"

    @pytest.mark.skip(reason="需要DEEPSEEK_API_KEY，仅在有API Key时运行")
    def test_llm_analysis_striped_hypoechoic_birads_3(self):
        """测试LLM分析：条状低回声 + BI-RADS 3类应发出高风险预警"""
        # 真实案例文本
        ocr_text = """
        超声描述：左侧乳腺上外象限可见条状低回声，大小约1.2×0.8cm，边界清晰，形态规则。
        CDFI：内见点状血流信号。
        提示：BI-RADS 3类。
        """

        result = analyze_text_with_deepseek(ocr_text)

        # 验证结果
        assert result["ai_risk_assessment"] == "High", (
            f"条状低回声是恶性征象，但结论是BI-RADS 3类，风险评估应为High，" f"实际为: {result['ai_risk_assessment']}"
        )

        assert result["inconsistency_alert"] is True, (
            f"条状低回声是恶性征象，但结论是BI-RADS 3类，应发出不一致预警，" f"实际为: {result['inconsistency_alert']}"
        )

        # 验证建议中包含进一步检查或活检
        advice = result.get("advice", "").lower()
        assert any(
            keyword in advice for keyword in ["活检", "进一步检查", "建议", "高风险"]
        ), f"建议应包含进一步检查或活检提示，实际建议: {result.get('advice')}"

        # 验证提取的事实中包含条状低回声
        findings = result.get("extracted_findings", [])
        findings_text = " ".join(findings).lower()
        assert any(
            keyword in findings_text for keyword in ["条状", "条索"]
        ), f"提取的事实应包含条状低回声，实际提取: {findings}"
