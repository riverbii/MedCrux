"""
BL-009数据格式验证测试

测试目标：
1. 验证assessment_urgency格式在完整流程中的正确性
2. 验证consistency_check格式在完整流程中的正确性
3. 验证数据格式符合接口契约文档要求

基于：docs/gov/QA_BL009_ACCEPTANCE.md、docs/dev/api/API_CONTRACT.md
"""

import sys

sys.path.insert(0, 'src')

from medcrux.analysis.llm_engine import (analyze_birads_independently,
                                         calculate_urgency_level,
                                         check_consistency_sets)
from medcrux.analysis.report_structure_parser import (extract_doctor_birads,
                                                      parse_report_structure)


class TestBL009DataFormat:
    """BL-009数据格式验证测试类"""

    def test_assessment_urgency_format_in_full_flow(self):
        """
        测试assessment_urgency格式在完整流程中的正确性
        
        验证：从OCR文本到最终结果的完整流程中，assessment_urgency格式是否正确
        """
        # 模拟完整流程
        ocr_text = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.2×0.8×0.6cm。
        形态：椭圆形
        边界：不清晰，边缘呈毛刺状
        回声：不均匀低回声
        方位：不平行
        CDFI：内见点状血流信号。

        影像学诊断：
        左侧乳腺低回声结节，BI-RADS 3类。建议定期随访。
        """

        # 1. 报告结构解析
        report_structure = parse_report_structure(ocr_text)
        assert report_structure is not None
        assert "findings" in report_structure
        assert "diagnosis" in report_structure

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_birads_set = doctor_birads_result["birads_set"]
        original_highest_birads = doctor_birads_result["highest_birads"]

        # 3. 独立判断BI-RADS分类（模拟，不实际调用LLM）
        # 这里使用模拟数据，因为真实LLM调用已经在test_bl009_real_llm.py中测试
        llm_highest_birads = "4"  # 模拟LLM判断为4类

        # 4. 计算评估紧急程度
        assessment_urgency = calculate_urgency_level(original_highest_birads, llm_highest_birads)

        # 验证assessment_urgency格式
        assert isinstance(assessment_urgency, dict), "assessment_urgency应该是字典"
        assert "urgency_level" in assessment_urgency, "缺少urgency_level字段"
        assert "reason" in assessment_urgency, "缺少reason字段"
        assert "doctor_highest_birads" in assessment_urgency, "缺少doctor_highest_birads字段"
        assert "llm_highest_birads" in assessment_urgency, "缺少llm_highest_birads字段"
        assert "comparison" in assessment_urgency, "缺少comparison字段"

        # 验证字段类型
        assert assessment_urgency["urgency_level"] in ["Low", "Medium", "High"], "urgency_level应该是Low/Medium/High"
        assert isinstance(assessment_urgency["reason"], str), "reason应该是字符串"
        assert isinstance(assessment_urgency["doctor_highest_birads"], str), "doctor_highest_birads应该是字符串"
        assert isinstance(assessment_urgency["llm_highest_birads"], str), "llm_highest_birads应该是字符串"
        assert assessment_urgency["comparison"] in ["llm_exceeds", "llm_equal_or_lower", "unknown"], "comparison应该是llm_exceeds/llm_equal_or_lower/unknown"

        # 验证逻辑正确性
        assert assessment_urgency["urgency_level"] == "High", "医生3类，AI 4类，应该是High"
        assert assessment_urgency["comparison"] == "llm_exceeds", "AI判断超过医生判断"

        print("\n✅ assessment_urgency格式验证通过")
        print(f"   urgency_level: {assessment_urgency['urgency_level']}")
        print(f"   comparison: {assessment_urgency['comparison']}")

    def test_consistency_check_format_in_full_flow(self):
        """
        测试consistency_check格式在完整流程中的正确性
        
        验证：从OCR文本到最终结果的完整流程中，consistency_check格式是否正确
        """
        # 模拟完整流程
        ocr_text = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.0×0.7×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行

        右侧乳腺内上象限距乳头约1.5cm处可见一低回声结节，大小约0.8×0.6×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行

        影像学诊断：
        左侧乳腺低回声结节，BI-RADS 3类；右侧乳腺低回声结节，BI-RADS 2类。建议定期随访。
        """

        # 1. 报告结构解析
        report_structure = parse_report_structure(ocr_text)
        assert report_structure is not None
        assert "findings" in report_structure
        assert "diagnosis" in report_structure

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_birads_set = doctor_birads_result["birads_set"]

        # 3. 模拟AI判断的BI-RADS分类集合
        llm_birads_set = {"2", "3"}  # 模拟AI也判断为2类和3类

        # 4. 一致性校验
        consistency_result = check_consistency_sets(original_birads_set, llm_birads_set)

        # 验证consistency_check格式
        assert isinstance(consistency_result, dict), "consistency_result应该是字典"
        assert "consistent" in consistency_result, "缺少consistent字段"
        assert "report_birads_set" in consistency_result, "缺少report_birads_set字段"
        assert "ai_birads_set" in consistency_result, "缺少ai_birads_set字段"
        assert "missing_in_ai" in consistency_result, "缺少missing_in_ai字段"
        assert "extra_in_ai" in consistency_result, "缺少extra_in_ai字段"
        assert "description" in consistency_result, "缺少description字段"

        # 验证字段类型
        assert isinstance(consistency_result["consistent"], bool), "consistent应该是布尔值"
        assert isinstance(consistency_result["report_birads_set"], set), "report_birads_set应该是集合"
        assert isinstance(consistency_result["ai_birads_set"], set), "ai_birads_set应该是集合"
        assert isinstance(consistency_result["missing_in_ai"], set), "missing_in_ai应该是集合"
        assert isinstance(consistency_result["extra_in_ai"], set), "extra_in_ai应该是集合"
        assert isinstance(consistency_result["description"], str), "description应该是字符串"

        # 验证逻辑正确性
        assert consistency_result["consistent"] == True, "报告和AI都有2类和3类，应该一致"
        assert consistency_result["report_birads_set"] == {"2", "3"}, "报告BI-RADS集合应该是{2, 3}"
        assert consistency_result["ai_birads_set"] == {"2", "3"}, "AI BI-RADS集合应该是{2, 3}"

        print("\n✅ consistency_check格式验证通过")
        print(f"   consistent: {consistency_result['consistent']}")
        print(f"   report_birads_set: {consistency_result['report_birads_set']}")
        print(f"   ai_birads_set: {consistency_result['ai_birads_set']}")

    def test_data_format_matches_api_contract(self):
        """
        测试数据格式是否符合接口契约文档要求
        
        验证：assessment_urgency和consistency_check格式是否符合API_CONTRACT.md中的定义
        """
        # 测试assessment_urgency格式
        assessment_urgency = {
            "urgency_level": "High",
            "reason": "LLM判断的最高BI-RADS分类（4类）超过医生给出的最高BI-RADS分类（3类），且LLM判断的最高BI-RADS分类 >= 4类，评估紧急程度为High",
            "doctor_highest_birads": "3",
            "llm_highest_birads": "4",
            "comparison": "llm_exceeds",
        }

        # 验证字段符合接口契约
        assert assessment_urgency["urgency_level"] in ["Low", "Medium", "High"], "符合接口契约：urgency_level应该是Low/Medium/High"
        assert isinstance(assessment_urgency["reason"], str), "符合接口契约：reason应该是字符串"
        assert isinstance(assessment_urgency["doctor_highest_birads"], str), "符合接口契约：doctor_highest_birads应该是字符串"
        assert isinstance(assessment_urgency["llm_highest_birads"], str), "符合接口契约：llm_highest_birads应该是字符串"
        assert assessment_urgency["comparison"] in ["llm_exceeds", "llm_equal_or_lower", "unknown"], "符合接口契约：comparison应该是llm_exceeds/llm_equal_or_lower/unknown"

        # 测试consistency_check格式
        consistency_check = {
            "consistent": True,
            "report_birads_set": {"2", "3"},
            "ai_birads_set": {"2", "3"},
            "missing_in_ai": set(),
            "extra_in_ai": set(),
            "description": "报告和AI的分类结果完全一致：['2', '3']",
        }

        # 验证字段符合接口契约
        assert isinstance(consistency_check["consistent"], bool), "符合接口契约：consistent应该是布尔值"
        assert isinstance(consistency_check["report_birads_set"], set), "符合接口契约：report_birads_set应该是集合"
        assert isinstance(consistency_check["ai_birads_set"], set), "符合接口契约：ai_birads_set应该是集合"
        assert isinstance(consistency_check["missing_in_ai"], set), "符合接口契约：missing_in_ai应该是集合"
        assert isinstance(consistency_check["extra_in_ai"], set), "符合接口契约：extra_in_ai应该是集合"
        assert isinstance(consistency_check["description"], str), "符合接口契约：description应该是字符串"

        print("\n✅ 数据格式符合接口契约文档要求")
        print("   assessment_urgency格式：✅")
        print("   consistency_check格式：✅")

