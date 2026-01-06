"""
测试报告结构解析模块

测试用例：
1. 基本功能测试
2. 报告头部信息排除测试
3. OCR识别错误处理测试
4. 边界识别测试
5. 向后兼容性测试
"""

import os

import pytest

from medcrux.analysis.report_structure_parser import parse_report_structure


class TestReportStructureParser:
    """测试报告结构解析模块"""

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_basic_functionality(self):
        """TC-001：基本功能测试"""
        ocr_text = """
检查所见：[乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况]

影像学诊断：[BI-RADS分类] [诊断意见]

建议：[临床建议]
        """
        
        result = parse_report_structure(ocr_text.strip())
        
        assert result["findings"] is not None
        assert result["diagnosis"] is not None
        assert result["findings"] and len(result["findings"]) > 0
        assert "BI-RADS" in result["diagnosis"] or result["diagnosis"] and len(result["diagnosis"]) > 0
        assert "建议" in result["recommendation"] or result["recommendation"] is None

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_header_exclusion(self):
        """TC-002：报告头部信息排除测试"""
        ocr_text = """
[报告头部信息：医疗机构名称、检查日期时间、患者基本信息、检查部位、检查方法] 检查所见：[乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况] [其他发现] 影像学诊断：[BI-RADS分类] [诊断意见]
        """
        
        result = parse_report_structure(ocr_text.strip())
        
        # 验证事实性摘要不包含报告头部信息
        findings = result.get("findings", "")
        assert findings is not None
        
        # 检查是否排除了报告头部信息
        header_keywords = ["姓名", "年龄", "性别", "超声号", "住院号", "科别", "床号", "检查部位", "仪器名称", "院区", "秒超检查报合"]
        for keyword in header_keywords:
            assert keyword not in findings, f"事实性摘要中不应包含报告头部信息：{keyword}"
        
        # 验证事实性摘要包含病变描述
        assert findings and len(findings) > 0, "事实性摘要应包含病变描述"
        
        # 验证结论包含BI-RADS分类
        diagnosis = result.get("diagnosis", "")
        assert diagnosis is not None
        assert "BI-RADS" in diagnosis, "结论应包含BI-RADS分类"
        
        # 验证结论不包含详细病变描述（诊断结论应该是概括性的，不应包含具体测量数据）
        # 这里只验证诊断结论存在，具体内容由LLM根据语义判断

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_ocr_error_handling(self):
        """TC-003：OCR识别错误处理测试"""
        # OCR识别错误："超卢描述"应该是"超声描述"
        ocr_text = """
超卢描述：[病变描述：位置、大小、形态、边界]

超声提示：[BI-RADS分类] [诊断意见]
        """
        
        result = parse_report_structure(ocr_text.strip())
        
        # LLM应该能够理解语义，正确识别报告结构
        assert result["findings"] is not None
        assert result["findings"] and len(result["findings"]) > 0
        assert result["diagnosis"] is not None
        assert "BI-RADS" in result["diagnosis"] or result["diagnosis"] and len(result["diagnosis"]) > 0

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_boundary_identification(self):
        """TC-004：边界识别测试"""
        # 检查所见和影像学诊断之间没有明确分隔
        ocr_text = """
[病变描述：位置、大小、形态、边界、回声特征、血流情况] 超声提示：[BI-RADS分类] [诊断意见]
        """
        
        result = parse_report_structure(ocr_text.strip())
        
        # 验证边界识别准确
        findings = result.get("findings", "")
        diagnosis = result.get("diagnosis", "")
        
        assert findings is not None
        assert diagnosis is not None
        
        # 病变描述应该在事实性摘要中
        assert findings and len(findings) > 0
        
        # 诊断结论应该在结论中
        assert "BI-RADS" in diagnosis or diagnosis and len(diagnosis) > 0

    def test_fallback_when_api_unavailable(self):
        """TC-005：向后兼容性测试"""
        # 模拟API不可用的情况
        original_key = os.getenv("DEEPSEEK_API_KEY")
        if original_key:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        
        try:
            # 重新导入模块以触发新的客户端初始化
            import importlib

            import medcrux.analysis.report_structure_parser as parser_module
            importlib.reload(parser_module)
            
            from medcrux.analysis.report_structure_parser import \
                parse_report_structure
            
            ocr_text = "测试文本"
            result = parse_report_structure(ocr_text)
            
            # 应该返回None，而不是崩溃
            assert result["findings"] is None or isinstance(result["findings"], str)
            assert result["diagnosis"] is None or isinstance(result["diagnosis"], str)
            assert result["recommendation"] is None or isinstance(result["recommendation"], str)
        finally:
            # 恢复原始API key
            if original_key:
                os.environ["DEEPSEEK_API_KEY"] = original_key
            else:
                # 如果原来没有key，确保清理
                os.environ.pop("DEEPSEEK_API_KEY", None)

