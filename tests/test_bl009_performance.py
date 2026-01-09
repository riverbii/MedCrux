"""
BL-009性能测试

测试目标：
1. 验证extract_doctor_birads()性能（要求 < 100ms）
2. 验证analyze_birads_independently()性能（要求 < 10s，已在真实LLM测试中验证）

基于：docs/gov/QA_BL009_ACCEPTANCE.md
"""

import time

import pytest

from medcrux.analysis.report_structure_parser import extract_doctor_birads


class TestBL009Performance:
    """BL-009性能测试类"""

    def test_extract_doctor_birads_performance(self):
        """
        测试extract_doctor_birads()性能
        
        要求：< 100ms
        """
        # 测试用例：包含多个BI-RADS分类的diagnosis文本
        diagnosis_text = """
        超声提示：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.0×0.7×0.5cm，BI-RADS 3类。
        右侧乳腺内上象限距乳头约1.5cm处可见一低回声结节，大小约0.8×0.6×0.5cm，BI-RADS 2类。
        左侧乳腺外下象限距乳头约2.5cm处可见一低回声结节，大小约1.2×0.9×0.7cm，BI-RADS 4类。
        """

        # 执行多次测试，取平均值
        iterations = 100
        total_time = 0

        for _ in range(iterations):
            start_time = time.time()
            result = extract_doctor_birads(diagnosis_text)
            elapsed_time = (time.time() - start_time) * 1000  # 转换为毫秒
            total_time += elapsed_time

        avg_time = total_time / iterations

        print(f"\n性能测试结果：")
        print(f"  测试次数: {iterations}")
        print(f"  平均耗时: {avg_time:.2f}ms")
        print(f"  要求: < 100ms")
        print(f"  结果: {'✅ 通过' if avg_time < 100 else '❌ 失败'}")

        # 验证结果正确性
        assert "birads_set" in result
        assert "highest_birads" in result
        assert result["highest_birads"] == "4"

        # 验证性能要求
        assert avg_time < 100, f"extract_doctor_birads()平均耗时{avg_time:.2f}ms超过要求(100ms)"

    def test_extract_doctor_birads_performance_edge_cases(self):
        """
        测试extract_doctor_birads()在边界情况下的性能
        
        要求：< 100ms（即使在边界情况下）
        """
        # 测试用例1：空字符串
        start_time = time.time()
        result1 = extract_doctor_birads("")
        time1 = (time.time() - start_time) * 1000

        # 测试用例2：很长的文本
        long_text = "超声提示：" + "BI-RADS 3类；" * 100
        start_time = time.time()
        result2 = extract_doctor_birads(long_text)
        time2 = (time.time() - start_time) * 1000

        # 测试用例3：包含多种格式
        mixed_text = """
        超声提示：
        左侧乳腺BI-RADS 3类、4类。
        右侧乳腺BI-RADS 2类和3类。
        左侧乳腺BI-RADS 4A类；右侧乳腺BI-RADS 4B类。
        """
        start_time = time.time()
        result3 = extract_doctor_birads(mixed_text)
        time3 = (time.time() - start_time) * 1000

        print(f"\n边界情况性能测试结果：")
        print(f"  空字符串: {time1:.2f}ms")
        print(f"  长文本(100个分类): {time2:.2f}ms")
        print(f"  混合格式: {time3:.2f}ms")

        # 验证性能要求
        assert time1 < 100, f"空字符串处理耗时{time1:.2f}ms超过要求(100ms)"
        assert time2 < 100, f"长文本处理耗时{time2:.2f}ms超过要求(100ms)"
        assert time3 < 100, f"混合格式处理耗时{time3:.2f}ms超过要求(100ms)"

        # 验证结果正确性
        assert result1["birads_set"] == set()
        assert "2" in result3["birads_set"] and "3" in result3["birads_set"]
        assert "4A" in result3["birads_set"] or "4" in result3["birads_set"]

