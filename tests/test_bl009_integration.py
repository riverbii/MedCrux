"""
BL-009集成测试：从OCR文本开始的模拟真实数据测试

测试完整流程：
1. OCR文本 -> 报告结构解析
2. 提取原报告BI-RADS分类
3. 独立判断BI-RADS分类
4. 一致性校验
5. 计算评估紧急程度
"""

import sys

sys.path.insert(0, 'src')

from medcrux.analysis.llm_engine import (analyze_birads_independently,
                                         calculate_urgency_level,
                                         check_consistency_sets)
from medcrux.analysis.report_structure_parser import (extract_doctor_birads,
                                                      parse_report_structure)


class TestBL009Integration:
    """BL-009集成测试：从OCR文本开始的完整流程测试"""

    def test_scenario_1_high_urgency(self):
        """
        场景1：High紧急程度
        - 医生诊断：BI-RADS 3类
        - AI判断：BI-RADS 4类
        - 期望：评估紧急程度 = High
        """
        # 模拟OCR文本
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
        assert report_structure is not None, "报告结构解析失败"
        assert "findings" in report_structure, "缺少findings"
        assert "diagnosis" in report_structure, "缺少diagnosis"

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_birads_set = doctor_birads_result["birads_set"]
        original_highest_birads = doctor_birads_result["highest_birads"]

        print(f"\n[场景1] 原报告BI-RADS分类: {original_birads_set}, 最高: {original_highest_birads}")
        assert original_highest_birads == "3", f"期望原报告最高BI-RADS为3，实际为{original_highest_birads}"

        # 3. 独立判断BI-RADS分类（模拟，实际需要LLM调用）
        # 注意：这里我们模拟AI判断为4类（因为形态学特征提示高风险）
        # 实际测试中，analyze_birads_independently会调用LLM
        llm_birads_set = {"4"}  # 模拟AI判断
        llm_highest_birads = "4"  # 模拟AI最高判断

        print(f"[场景1] AI判断BI-RADS分类: {llm_birads_set}, 最高: {llm_highest_birads}")

        # 4. 一致性校验
        consistency_result = check_consistency_sets(original_birads_set, llm_birads_set)
        print(f"[场景1] 一致性校验: {consistency_result['consistent']}, 描述: {consistency_result['description']}")
        assert consistency_result["consistent"] is False, "AI有额外高风险分类，应该不一致"

        # 5. 计算评估紧急程度
        urgency_result = calculate_urgency_level(original_highest_birads, llm_highest_birads)
        print(f"[场景1] 评估紧急程度: {urgency_result['urgency_level']}, 理由: {urgency_result['reason']}")
        assert urgency_result["urgency_level"] == "High", f"期望High，实际为{urgency_result['urgency_level']}"
        assert urgency_result["comparison"] == "llm_exceeds", "LLM判断应该超过医生判断"

        print("✅ 场景1测试通过：High紧急程度")

    def test_scenario_2_medium_urgency(self):
        """
        场景2：Medium紧急程度
        - 医生诊断：BI-RADS 2类
        - AI判断：BI-RADS 3类
        - 期望：评估紧急程度 = Medium
        """
        # 模拟OCR文本
        ocr_text = """
        检查所见：
        右侧乳腺内上象限距乳头约1.5cm处可见一低回声结节，大小约0.8×0.6×0.5cm。
        形态：椭圆形
        边界：大部分清晰
        回声：均匀低回声
        方位：平行
        CDFI：未见明显血流信号。

        影像学诊断：
        右侧乳腺低回声结节，BI-RADS 2类。建议定期随访。
        """

        # 1. 报告结构解析
        report_structure = parse_report_structure(ocr_text)
        assert report_structure is not None, "报告结构解析失败"

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_highest_birads = doctor_birads_result["highest_birads"]

        print(f"\n[场景2] 原报告最高BI-RADS: {original_highest_birads}")
        assert original_highest_birads == "2", f"期望原报告最高BI-RADS为2，实际为{original_highest_birads}"

        # 3. 模拟AI判断为3类
        llm_highest_birads = "3"

        # 4. 计算评估紧急程度
        urgency_result = calculate_urgency_level(original_highest_birads, llm_highest_birads)
        print(f"[场景2] 评估紧急程度: {urgency_result['urgency_level']}")
        assert urgency_result["urgency_level"] == "Medium", f"期望Medium，实际为{urgency_result['urgency_level']}"

        print("✅ 场景2测试通过：Medium紧急程度")

    def test_scenario_3_low_urgency(self):
        """
        场景3：Low紧急程度
        - 医生诊断：BI-RADS 3类
        - AI判断：BI-RADS 3类
        - 期望：评估紧急程度 = Low
        """
        # 模拟OCR文本
        ocr_text = """
        检查所见：
        左侧乳腺外上象限距乳头约2.5cm处可见一低回声结节，大小约1.0×0.7×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行
        CDFI：未见明显血流信号。

        影像学诊断：
        左侧乳腺低回声结节，BI-RADS 3类。建议定期随访。
        """

        # 1. 报告结构解析
        report_structure = parse_report_structure(ocr_text)
        assert report_structure is not None, "报告结构解析失败"

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_highest_birads = doctor_birads_result["highest_birads"]

        print(f"\n[场景3] 原报告最高BI-RADS: {original_highest_birads}")
        assert original_highest_birads == "3", f"期望原报告最高BI-RADS为3，实际为{original_highest_birads}"

        # 3. 模拟AI判断也为3类
        llm_highest_birads = "3"

        # 4. 计算评估紧急程度
        urgency_result = calculate_urgency_level(original_highest_birads, llm_highest_birads)
        print(f"[场景3] 评估紧急程度: {urgency_result['urgency_level']}")
        assert urgency_result["urgency_level"] == "Low", f"期望Low，实际为{urgency_result['urgency_level']}"

        print("✅ 场景3测试通过：Low紧急程度")

    def test_scenario_4_multiple_birads(self):
        """
        场景4：多个BI-RADS分类
        - 医生诊断：BI-RADS 2类和3类
        - AI判断：BI-RADS 2类、3类和4类
        - 期望：一致性校验 = False（AI有额外高风险），评估紧急程度 = High
        """
        # 模拟OCR文本
        ocr_text = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.2×0.8×0.6cm。
        形态：椭圆形
        边界：不清晰，边缘呈毛刺状
        回声：不均匀低回声
        方位：不平行
        CDFI：内见点状血流信号。

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
        assert report_structure is not None, "报告结构解析失败"

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_birads_set = doctor_birads_result["birads_set"]
        original_highest_birads = doctor_birads_result["highest_birads"]

        print(f"\n[场景4] 原报告BI-RADS分类: {original_birads_set}, 最高: {original_highest_birads}")
        assert original_birads_set == {"2", "3"}, f"期望{{'2', '3'}}，实际为{original_birads_set}"
        assert original_highest_birads == "3", f"期望最高为3，实际为{original_highest_birads}"

        # 3. 模拟AI判断：2类、3类和4类
        llm_birads_set = {"2", "3", "4"}
        llm_highest_birads = "4"

        # 4. 一致性校验
        consistency_result = check_consistency_sets(original_birads_set, llm_birads_set)
        print(f"[场景4] 一致性校验: {consistency_result['consistent']}, 描述: {consistency_result['description']}")
        assert consistency_result["consistent"] is False, "AI有额外高风险分类，应该不一致"
        assert "4" in consistency_result["extra_in_ai"], "AI额外的分类应该包含4"

        # 5. 计算评估紧急程度
        urgency_result = calculate_urgency_level(original_highest_birads, llm_highest_birads)
        print(f"[场景4] 评估紧急程度: {urgency_result['urgency_level']}")
        assert urgency_result["urgency_level"] == "High", f"期望High，实际为{urgency_result['urgency_level']}"

        print("✅ 场景4测试通过：多个BI-RADS分类，AI有额外高风险")

    def test_scenario_5_consistent_sets(self):
        """
        场景5：一致性校验 - 完全一致
        - 医生诊断：BI-RADS 2类和3类
        - AI判断：BI-RADS 2类和3类
        - 期望：一致性校验 = True
        """
        # 模拟OCR文本
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
        assert report_structure is not None, "报告结构解析失败"

        # 2. 提取原报告BI-RADS分类
        doctor_birads_result = extract_doctor_birads(report_structure["diagnosis"])
        original_birads_set = doctor_birads_result["birads_set"]

        print(f"\n[场景5] 原报告BI-RADS分类: {original_birads_set}")

        # 3. 模拟AI判断也为2类和3类
        llm_birads_set = {"2", "3"}

        # 4. 一致性校验
        consistency_result = check_consistency_sets(original_birads_set, llm_birads_set)
        print(f"[场景5] 一致性校验: {consistency_result['consistent']}, 描述: {consistency_result['description']}")
        assert consistency_result["consistent"] is True, "完全一致，应该返回True"
        assert consistency_result["missing_in_ai"] == set(), "不应该有缺少的分类"
        assert consistency_result["extra_in_ai"] == set(), "不应该有额外的分类"

        print("✅ 场景5测试通过：完全一致")

    def test_scenario_6_no_diagnosis(self):
        """
        场景6：diagnosis为空或没有BI-RADS分类
        - 期望：extract_doctor_birads返回空集合，流程不崩溃
        """
        # 模拟OCR文本（没有diagnosis部分）
        ocr_text = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.0×0.7×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行
        """

        # 1. 报告结构解析
        report_structure = parse_report_structure(ocr_text)
        assert report_structure is not None, "报告结构解析失败"

        # 2. 提取原报告BI-RADS分类（diagnosis可能为空）
        diagnosis = report_structure.get("diagnosis", "")
        doctor_birads_result = extract_doctor_birads(diagnosis)
        original_birads_set = doctor_birads_result["birads_set"]
        original_highest_birads = doctor_birads_result["highest_birads"]

        print(f"\n[场景6] 原报告BI-RADS分类: {original_birads_set}, 最高: {original_highest_birads}")
        assert original_birads_set == set(), "没有BI-RADS分类，应该返回空集合"
        assert original_highest_birads is None, "没有BI-RADS分类，最高值应该为None"

        # 3. 计算评估紧急程度（应该返回Low，因为无法比较）
        llm_highest_birads = "3"
        urgency_result = calculate_urgency_level(original_highest_birads, llm_highest_birads)
        print(f"[场景6] 评估紧急程度: {urgency_result['urgency_level']}")
        assert urgency_result["urgency_level"] == "Low", "无法比较时应该返回Low"

        print("✅ 场景6测试通过：diagnosis为空，流程不崩溃")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])

