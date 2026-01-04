"""
性能测试：测试OCR+分析各阶段的响应时间

根据PRD_v1.1.md要求：
- OCR识别：< 5秒
- RAG检索：< 2秒
- LLM分析：< 10秒
- 总响应时间：< 20秒
"""

import time
from pathlib import Path

import pytest

from medcrux.analysis.llm_engine import analyze_text_with_deepseek
from medcrux.ingestion.ocr_service import extract_text_from_bytes


class TestPerformance:
    """性能测试类"""

    @pytest.mark.skip(reason="需要真实图片和API Key，手动执行")
    def test_ocr_performance(self, test_image_path: str):
        """
        测试OCR识别性能

        要求：< 5秒
        """
        # 读取测试图片
        image_bytes = Path(test_image_path).read_bytes()

        # 测量OCR时间
        start_time = time.time()
        extract_text_from_bytes(image_bytes)
        ocr_time = time.time() - start_time

        print(f"\nOCR识别时间: {ocr_time:.2f}秒")
        assert ocr_time < 5.0, f"OCR识别时间{ocr_time:.2f}秒超过PRD要求(5秒)"

    @pytest.mark.skip(reason="需要API Key，手动执行")
    def test_rag_retrieval_performance(self, sample_ocr_text: str):
        """
        测试RAG检索性能

        要求：< 2秒
        """
        from medcrux.rag.graphrag_retriever import GraphRAGRetriever

        retriever = GraphRAGRetriever()
        start_time = time.time()
        retrieval_result = retriever.retrieve(sample_ocr_text)
        rag_time = time.time() - start_time

        print(f"\nRAG检索时间: {rag_time:.2f}秒")
        print(f"检索到{len(retrieval_result['entities'])}个实体，{len(retrieval_result['relations'])}个关系")
        assert rag_time < 2.0, f"RAG检索时间{rag_time:.2f}秒超过PRD要求(2秒)"

    @pytest.mark.skip(reason="需要API Key，手动执行")
    def test_llm_analysis_performance(self, sample_ocr_text: str):
        """
        测试LLM分析性能

        要求：< 10秒
        """
        start_time = time.time()
        analyze_text_with_deepseek(sample_ocr_text)
        llm_time = time.time() - start_time

        print(f"\nLLM分析时间: {llm_time:.2f}秒")
        assert llm_time < 10.0, f"LLM分析时间{llm_time:.2f}秒超过PRD要求(10秒)"

    @pytest.mark.skip(reason="需要真实图片和API Key，手动执行")
    def test_end_to_end_performance(self, test_image_path: str):
        """
        测试端到端性能（OCR + RAG + LLM）

        要求：< 20秒
        """
        # 1. OCR识别
        image_bytes = Path(test_image_path).read_bytes()
        ocr_start = time.time()
        ocr_text = extract_text_from_bytes(image_bytes)
        ocr_time = time.time() - ocr_start

        # 2. AI分析（包含RAG检索和LLM分析）
        analysis_start = time.time()
        result = analyze_text_with_deepseek(ocr_text)
        analysis_time = time.time() - analysis_start

        # 总时间
        total_time = time.time() - ocr_start

        print("\n=== 性能测试结果 ===")
        print(f"OCR识别时间: {ocr_time:.2f}秒 (要求<5秒) {'✅' if ocr_time < 5.0 else '❌'}")
        print(f"AI分析时间: {analysis_time:.2f}秒 (包含RAG+LLM)")
        print(f"总响应时间: {total_time:.2f}秒 (要求<20秒) {'✅' if total_time < 20.0 else '❌'}")
        print(f"风险评估: {result.get('ai_risk_assessment', 'Unknown')}")
        print(f"不一致预警: {result.get('inconsistency_alert', False)}")

        # 断言
        assert ocr_time < 5.0, f"OCR识别时间{ocr_time:.2f}秒超过PRD要求(5秒)"
        assert total_time < 20.0, f"总响应时间{total_time:.2f}秒超过PRD要求(20秒)"


def manual_performance_test():
    """
    手动性能测试脚本

    使用方法：
    1. 设置环境变量：export DEEPSEEK_API_KEY="sk-..."
    2. 准备测试图片路径
    3. 运行：python tests/test_performance.py
    """
    import os
    import sys

    # 检查API Key
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ 错误：未设置DEEPSEEK_API_KEY环境变量")
        sys.exit(1)

    # 测试图片路径（需要用户提供）
    if len(sys.argv) < 2:
        print("❌ 错误：请提供测试图片路径")
        print("使用方法: python tests/test_performance.py <图片路径>")
        sys.exit(1)

    test_image_path = sys.argv[1]
    if not Path(test_image_path).exists():
        print(f"❌ 错误：图片文件不存在: {test_image_path}")
        sys.exit(1)

    print("🚀 开始性能测试...")
    print(f"📸 测试图片: {test_image_path}")

    # 1. OCR识别
    print("\n[1/3] OCR识别中...")
    image_bytes = Path(test_image_path).read_bytes()
    ocr_start = time.time()
    ocr_text = extract_text_from_bytes(image_bytes)
    ocr_time = time.time() - ocr_start
    print(f"✅ OCR识别完成: {ocr_time:.2f}秒 (要求<5秒) {'✅' if ocr_time < 5.0 else '❌'}")

    if not ocr_text or len(ocr_text) < 10:
        print("❌ OCR识别结果无效，无法继续测试")
        sys.exit(1)

    # 2. AI分析（包含RAG检索和LLM分析）
    print("\n[2/3] AI分析中（包含RAG检索和LLM分析）...")
    analysis_start = time.time()
    result = analyze_text_with_deepseek(ocr_text)
    analysis_time = time.time() - analysis_start
    print(f"✅ AI分析完成: {analysis_time:.2f}秒 (要求<10秒) {'✅' if analysis_time < 10.0 else '❌'}")

    # 总时间
    total_time = time.time() - ocr_start

    # 输出结果
    print("\n" + "=" * 50)
    print("📊 性能测试结果")
    print("=" * 50)
    print(f"OCR识别时间: {ocr_time:.2f}秒 (要求<5秒) {'✅' if ocr_time < 5.0 else '❌'}")
    print(f"AI分析时间: {analysis_time:.2f}秒 (包含RAG+LLM, 要求<10秒) {'✅' if analysis_time < 10.0 else '❌'}")
    print(f"总响应时间: {total_time:.2f}秒 (要求<20秒) {'✅' if total_time < 20.0 else '❌'}")
    print("\n📋 分析结果:")
    print(f"  - 风险评估: {result.get('ai_risk_assessment', 'Unknown')}")
    print(f"  - 不一致预警: {result.get('inconsistency_alert', False)}")
    if result.get("inconsistency_reasons"):
        print(f"  - 不一致原因: {result.get('inconsistency_reasons')}")

    # PRD符合性判断
    print("\n" + "=" * 50)
    print("📋 PRD符合性判断")
    print("=" * 50)
    all_passed = True
    if ocr_time >= 5.0:
        print("❌ OCR识别时间超过PRD要求(5秒)")
        all_passed = False
    if analysis_time >= 10.0:
        print("❌ AI分析时间超过PRD要求(10秒)")
        all_passed = False
    if total_time >= 20.0:
        print("❌ 总响应时间超过PRD要求(20秒)")
        all_passed = False

    if all_passed:
        print("✅ 所有性能指标符合PRD要求")
    else:
        print("⚠️  部分性能指标不符合PRD要求，需要优化")


if __name__ == "__main__":
    manual_performance_test()
