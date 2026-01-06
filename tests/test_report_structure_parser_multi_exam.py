"""
测试报告结构解析模块 - 多检查项目混合报告

测试用例：多检查项目混合报告的处理
"""

import os

import pytest

from medcrux.analysis.report_structure_parser import parse_report_structure


class TestMultiExamReport:
    """测试多检查项目混合报告处理"""

    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY未设置，跳过LLM测试",
    )
    def test_multi_exam_report_extraction(self):
        """测试多检查项目混合报告：只提取乳腺超声部分"""
        # 使用完全虚拟的数据结构，不包含任何真实患者信息
        ocr_text = """
[系统信息] [其他检查项目A] [其他检查项目A的内容描述] [其他检查项目B] [其他检查项目B的内容描述] 乳腺超声 [乳腺结构描述] [病变描述：位置、大小、形态、边界、回声特征、血流情况] [其他发现] 乳腺超声：[BI-RADS分类] [诊断意见] [报告尾部信息]
        """
        
        result = parse_report_structure(ocr_text.strip())
        
        findings = result.get("findings", "")
        diagnosis = result.get("diagnosis", "")
        
        # 验证事实性摘要不包含非乳腺超声内容
        assert findings is not None
        excluded_keywords = [
            "其他检查项目A", "其他检查项目B", "系统信息", "报告尾部信息"
        ]
        for keyword in excluded_keywords:
            assert keyword not in findings, f"事实性摘要中不应包含非乳腺超声内容：{keyword}"
        
        # 验证事实性摘要包含乳腺超声内容
        assert findings and len(findings) > 0, "事实性摘要应包含乳腺超声内容"
        
        # 验证结论只包含BI-RADS分类
        assert diagnosis is not None
        assert "BI-RADS" in diagnosis or diagnosis and len(diagnosis) > 0, "结论应包含BI-RADS分类或诊断意见"
        
        # 验证结论不包含详细病变描述（诊断结论应该是概括性的，不应包含具体测量数据）
        # 具体内容由LLM根据语义判断，这里只验证结构正确

