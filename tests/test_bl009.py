"""
BL-009单元测试：评估紧急程度架构

测试内容：
1. extract_doctor_birads() - 从diagnosis提取BI-RADS分类
2. check_consistency_sets() - 一致性校验
3. calculate_urgency_level() - 计算评估紧急程度
"""

import pytest

from medcrux.analysis.llm_engine import calculate_urgency_level, check_consistency_sets
from medcrux.analysis.report_structure_parser import extract_doctor_birads


class TestExtractDoctorBirads:
    """测试extract_doctor_birads函数"""

    def test_normal_case(self):
        """正常情况：diagnosis包含BI-RADS分类"""
        diagnosis = "超声提示：左侧乳腺低回声结节，BI-RADS 3类；右侧乳腺囊性结节，BI-RADS 2类。"
        result = extract_doctor_birads(diagnosis)
        
        assert result["birads_set"] == {"2", "3"}
        assert "2" in result["birads_list"]
        assert "3" in result["birads_list"]
        assert result["highest_birads"] == "3"
        assert result["diagnosis_text"] == diagnosis

    def test_single_birads(self):
        """单个BI-RADS分类"""
        diagnosis = "超声提示：左侧乳腺低回声结节，BI-RADS 3类。"
        result = extract_doctor_birads(diagnosis)
        
        assert result["birads_set"] == {"3"}
        assert result["birads_list"] == ["3"]
        assert result["highest_birads"] == "3"

    def test_multiple_formats(self):
        """多种格式：分号分隔、顿号分隔"""
        diagnosis1 = "BI-RADS 3类；BI-RADS 4类"
        result1 = extract_doctor_birads(diagnosis1)
        assert result1["birads_set"] == {"3", "4"}
        
        diagnosis2 = "BI-RADS 3类、4类"
        result2 = extract_doctor_birads(diagnosis2)
        assert result2["birads_set"] == {"3", "4"}

    def test_with_letter_suffix(self):
        """带字母后缀的BI-RADS分类（4A、4B、4C）"""
        diagnosis = "超声提示：BI-RADS 4A类；BI-RADS 4B类"
        result = extract_doctor_birads(diagnosis)
        
        assert "4A" in result["birads_set"]
        assert "4B" in result["birads_set"]
        assert result["highest_birads"] in ["4A", "4B"]  # 最高值应该是4A或4B

    def test_empty_diagnosis(self):
        """diagnosis为空"""
        result = extract_doctor_birads("")
        
        assert result["birads_set"] == set()
        assert result["birads_list"] == []
        assert result["highest_birads"] is None

    def test_no_birads(self):
        """diagnosis中不包含BI-RADS分类"""
        diagnosis = "超声提示：左侧乳腺低回声结节。"
        result = extract_doctor_birads(diagnosis)
        
        assert result["birads_set"] == set()
        assert result["birads_list"] == []
        assert result["highest_birads"] is None


class TestCheckConsistencySets:
    """测试check_consistency_sets函数"""

    def test_fully_consistent(self):
        """完全一致"""
        result = check_consistency_sets({"2", "3"}, {"2", "3"})
        
        assert result["consistent"] is True
        assert result["missing_in_ai"] == set()
        assert result["extra_in_ai"] == set()

    def test_ai_has_extra_lower_risk(self):
        """AI有额外的低风险分类"""
        result = check_consistency_sets({"3"}, {"2", "3"})
        
        assert result["consistent"] is True  # 额外的2类风险不更高
        assert result["missing_in_ai"] == set()
        assert result["extra_in_ai"] == {"2"}

    def test_ai_has_extra_higher_risk(self):
        """AI有额外的高风险分类"""
        result = check_consistency_sets({"2", "3"}, {"2", "3", "4"})
        
        assert result["consistent"] is False  # 额外的4类风险更高
        assert result["missing_in_ai"] == set()
        assert result["extra_in_ai"] == {"4"}

    def test_ai_missing_classification(self):
        """AI缺少某些分类"""
        result = check_consistency_sets({"2", "3"}, {"3"})
        
        assert result["consistent"] is False
        assert result["missing_in_ai"] == {"2"}
        assert result["extra_in_ai"] == set()

    def test_both_missing_and_extra(self):
        """AI既有缺少又有额外"""
        result = check_consistency_sets({"2", "3"}, {"3", "4"})
        
        assert result["consistent"] is False
        assert result["missing_in_ai"] == {"2"}
        assert result["extra_in_ai"] == {"4"}

    def test_empty_sets(self):
        """两个集合都为空"""
        result = check_consistency_sets(set(), set())
        
        assert result["consistent"] is True
        assert result["missing_in_ai"] == set()
        assert result["extra_in_ai"] == set()


class TestCalculateUrgencyLevel:
    """测试calculate_urgency_level函数"""

    def test_high_urgency(self):
        """High紧急程度：LLM判断4类，医生判断3类"""
        result = calculate_urgency_level("3", "4")
        
        assert result["urgency_level"] == "High"
        assert result["comparison"] == "llm_exceeds"
        assert result["doctor_highest_birads"] == "3"
        assert result["llm_highest_birads"] == "4"

    def test_medium_urgency(self):
        """Medium紧急程度：LLM判断3类，医生判断2类"""
        result = calculate_urgency_level("2", "3")
        
        assert result["urgency_level"] == "Medium"
        assert result["comparison"] == "llm_exceeds"
        assert result["doctor_highest_birads"] == "2"
        assert result["llm_highest_birads"] == "3"

    def test_low_urgency_equal(self):
        """Low紧急程度：LLM判断等于医生判断"""
        result = calculate_urgency_level("3", "3")
        
        assert result["urgency_level"] == "Low"
        assert result["comparison"] == "llm_equal_or_lower"
        assert result["doctor_highest_birads"] == "3"
        assert result["llm_highest_birads"] == "3"

    def test_low_urgency_lower(self):
        """Low紧急程度：LLM判断低于医生判断"""
        result = calculate_urgency_level("4", "3")
        
        assert result["urgency_level"] == "Low"
        assert result["comparison"] == "llm_equal_or_lower"
        assert result["doctor_highest_birads"] == "4"
        assert result["llm_highest_birads"] == "3"

    def test_with_letter_suffix(self):
        """带字母后缀的BI-RADS分类"""
        result = calculate_urgency_level("3", "4A")
        
        assert result["urgency_level"] == "High"
        assert result["comparison"] == "llm_exceeds"

    def test_empty_values(self):
        """空值处理"""
        result = calculate_urgency_level("", "3")
        
        assert result["urgency_level"] == "Low"
        assert result["comparison"] == "unknown"

