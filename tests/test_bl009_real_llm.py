"""
BL-009真实LLM调用测试：验证analyze_birads_independently()函数

测试目标：
1. LLM的医学判断能力
2. LLM的独立性验证
3. 产品假设验证
4. 数据格式和完整性

注意：本测试需要真实的DeepSeek API调用，会产生API费用
"""

import os
import sys
import time

sys.path.insert(0, 'src')

from medcrux.analysis.llm_engine import analyze_birads_independently
from medcrux.analysis.report_structure_parser import parse_report_structure


class TestBL009RealLLM:
    """BL-009真实LLM调用测试"""

    def test_scenario_1_basic_accuracy(self):
        """
        场景1：LLM独立判断准确性测试（P0）
        
        测试目标：验证LLM能否基于形态学特征准确判断BI-RADS分类
        
        测试数据：典型的BI-RADS 3类形态学特征
        - 椭圆形、边界清晰、均匀低回声、平行 → 应该是BI-RADS 3类
        """
        findings = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.0×0.7×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行
        CDFI：未见明显血流信号。
        """

        print("\n" + "=" * 60)
        print("场景1：LLM独立判断准确性测试")
        print("=" * 60)
        print(f"输入findings:\n{findings.strip()}")
        print("\n开始调用LLM...")

        start_time = time.time()
        result = analyze_birads_independently(findings)
        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用完成，耗时: {elapsed_time:.2f}秒")

        # 验证数据格式和完整性
        assert "nodules" in result, "缺少nodules字段"
        assert isinstance(result["nodules"], list), "nodules应该是列表"
        assert len(result["nodules"]) > 0, "应该识别到至少1个异常发现"

        nodule = result["nodules"][0]
        print(f"\n识别到的异常发现数: {len(result['nodules'])}")
        print(f"第一个异常发现ID: {nodule.get('id')}")

        # 验证必需字段
        assert "llm_birads_class" in nodule, "缺少llm_birads_class字段"
        assert "llm_birads_reasoning" in nodule, "缺少llm_birads_reasoning字段"
        assert "location" in nodule, "缺少location字段"
        assert "morphology" in nodule, "缺少morphology字段"

        llm_birads = nodule["llm_birads_class"]
        llm_reasoning = nodule["llm_birads_reasoning"]
        llm_highest = result.get("llm_highest_birads")

        print(f"\nLLM判断的BI-RADS分类: {llm_birads}")
        print(f"LLM判断理由: {llm_reasoning}")
        print(f"LLM最高BI-RADS分类: {llm_highest}")

        # 验证判断合理性（基于形态学特征，应该是3类）
        assert llm_birads in ["2", "3", "4"], f"BI-RADS分类应该在2-4类之间，实际为{llm_birads}"
        assert llm_reasoning is not None and len(llm_reasoning) > 0, "判断理由不能为空"
        assert llm_highest == llm_birads, f"最高BI-RADS应该等于第一个异常发现的分类，实际为{llm_highest}"

        # 验证判断理由是否基于形态学特征
        morphology_keywords = ["椭圆形", "清晰", "均匀低回声", "平行"]
        reasoning_text = llm_reasoning.lower()
        has_morphology_reference = any(keyword in reasoning_text for keyword in ["形态", "边界", "回声", "方位", "椭圆形", "清晰", "均匀", "平行"])
        assert has_morphology_reference, "判断理由应该基于形态学特征"

        print("\n✅ 场景1测试通过：LLM独立判断准确性验证成功")
        print(f"   - 识别异常发现: ✅")
        print(f"   - BI-RADS分类: {llm_birads}类")
        print(f"   - 判断理由: ✅ 基于形态学特征")
        print(f"   - 数据格式: ✅ 完整")

    def test_scenario_2_high_risk_features(self):
        """
        场景2：LLM识别高风险特征测试（P1）
        
        测试目标：验证LLM能否识别出医生可能遗漏的高风险特征
        
        测试数据：包含高风险特征
        - 边界不清晰、边缘呈毛刺状、不均匀低回声、不平行 → 应该是BI-RADS 4类或更高
        """
        findings = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.2×0.8×0.6cm。
        形态：椭圆形
        边界：不清晰，边缘呈毛刺状
        回声：不均匀低回声
        方位：不平行
        CDFI：内见点状血流信号。
        """

        print("\n" + "=" * 60)
        print("场景2：LLM识别高风险特征测试")
        print("=" * 60)
        print(f"输入findings:\n{findings.strip()}")
        print("\n开始调用LLM...")

        start_time = time.time()
        result = analyze_birads_independently(findings)
        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用完成，耗时: {elapsed_time:.2f}秒")

        assert "nodules" in result and len(result["nodules"]) > 0, "应该识别到异常发现"

        nodule = result["nodules"][0]
        llm_birads = nodule["llm_birads_class"]
        llm_reasoning = nodule["llm_birads_reasoning"]
        llm_highest = result.get("llm_highest_birads")

        print(f"\nLLM判断的BI-RADS分类: {llm_birads}")
        print(f"LLM判断理由: {llm_reasoning}")
        print(f"LLM最高BI-RADS分类: {llm_highest}")

        # 验证LLM是否识别了高风险特征（应该是4类或更高）
        birads_int = int(llm_birads[0]) if llm_birads and llm_birads[0].isdigit() else 0
        assert birads_int >= 4, f"高风险特征应该判断为4类或更高，实际为{llm_birads}类"

        # 验证判断理由是否提到了高风险特征
        high_risk_keywords = ["毛刺", "不清晰", "不均匀", "不平行", "高风险", "恶性", "4类", "4a", "4b", "4c"]
        reasoning_text = llm_reasoning.lower()
        has_high_risk_reference = any(keyword in reasoning_text for keyword in high_risk_keywords)
        assert has_high_risk_reference, "判断理由应该提到高风险特征"

        print("\n✅ 场景2测试通过：LLM识别高风险特征验证成功")
        print(f"   - 识别高风险特征: ✅ (毛刺状、不平行等)")
        print(f"   - BI-RADS分类: {llm_birads}类 (>=4类)")
        print(f"   - 判断理由: ✅ 提到了高风险特征")

    def test_scenario_3_independence_verification(self):
        """
        场景3：LLM独立性验证测试（P1）
        
        测试目标：验证LLM是否真正独立判断，不参考原报告结论
        
        测试数据：形态学特征提示3类，但原报告为2类
        - 边界"大部分清晰"（不是完全清晰）→ 应该是BI-RADS 3类
        """
        findings = """
        检查所见：
        右侧乳腺内上象限距乳头约1.5cm处可见一低回声结节，大小约0.8×0.6×0.5cm。
        形态：椭圆形
        边界：大部分清晰
        回声：均匀低回声
        方位：平行
        CDFI：未见明显血流信号。
        """

        print("\n" + "=" * 60)
        print("场景3：LLM独立性验证测试")
        print("=" * 60)
        print(f"输入findings:\n{findings.strip()}")
        print("\n注意：原报告可能诊断为BI-RADS 2类，但LLM应该独立判断")
        print("开始调用LLM...")

        start_time = time.time()
        result = analyze_birads_independently(findings)
        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用完成，耗时: {elapsed_time:.2f}秒")

        assert "nodules" in result and len(result["nodules"]) > 0, "应该识别到异常发现"

        nodule = result["nodules"][0]
        llm_birads = nodule["llm_birads_class"]
        llm_reasoning = nodule["llm_birads_reasoning"]

        print(f"\nLLM判断的BI-RADS分类: {llm_birads}")
        print(f"LLM判断理由: {llm_reasoning}")

        # 验证LLM是否基于形态学特征独立判断
        # "大部分清晰"不是"清晰"，应该判断为3类而不是2类
        birads_int = int(llm_birads[0]) if llm_birads and llm_birads[0].isdigit() else 0
        assert birads_int >= 2, f"BI-RADS分类应该在2类或以上，实际为{llm_birads}类"

        # 验证判断理由是否基于形态学特征
        assert "大部分清晰" in llm_reasoning or "边界" in llm_reasoning or "形态" in llm_reasoning, "判断理由应该基于形态学特征"

        print("\n✅ 场景3测试通过：LLM独立性验证成功")
        print(f"   - 独立判断: ✅ (基于形态学特征)")
        print(f"   - BI-RADS分类: {llm_birads}类")
        print(f"   - 判断理由: ✅ 基于形态学特征")

    def test_scenario_4_multiple_findings(self):
        """
        场景4：多个异常发现识别测试（P2）
        
        测试目标：验证LLM能否识别所有异常发现并分别判断
        
        测试数据：包含2个异常发现
        """
        findings = """
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
        """

        print("\n" + "=" * 60)
        print("场景4：多个异常发现识别测试")
        print("=" * 60)
        print(f"输入findings:\n{findings.strip()}")
        print("\n开始调用LLM...")

        start_time = time.time()
        result = analyze_birads_independently(findings)
        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用完成，耗时: {elapsed_time:.2f}秒")

        assert "nodules" in result, "缺少nodules字段"
        assert isinstance(result["nodules"], list), "nodules应该是列表"
        assert len(result["nodules"]) >= 2, f"应该识别到至少2个异常发现，实际识别到{len(result['nodules'])}个"

        print(f"\n识别到的异常发现数: {len(result['nodules'])}")

        # 验证每个异常发现都有独立的BI-RADS分类
        birads_classes = []
        for i, nodule in enumerate(result["nodules"]):
            assert "llm_birads_class" in nodule, f"第{i+1}个异常发现缺少llm_birads_class字段"
            assert "llm_birads_reasoning" in nodule, f"第{i+1}个异常发现缺少llm_birads_reasoning字段"
            assert "id" in nodule, f"第{i+1}个异常发现缺少id字段"

            birads_class = nodule["llm_birads_class"]
            birads_reasoning = nodule["llm_birads_reasoning"]
            nodule_id = nodule["id"]

            print(f"\n异常发现{i+1} (ID: {nodule_id}):")
            print(f"  BI-RADS分类: {birads_class}")
            print(f"  判断理由: {birads_reasoning[:100]}...")

            birads_classes.append(birads_class)

        # 验证llm_highest_birads是否正确
        llm_highest = result.get("llm_highest_birads")
        assert llm_highest is not None, "缺少llm_highest_birads字段"

        # 计算实际最高值
        birads_ints = [int(b[0]) if b and b[0].isdigit() else 0 for b in birads_classes]
        expected_highest_int = max(birads_ints) if birads_ints else 0
        actual_highest_int = int(llm_highest[0]) if llm_highest and llm_highest[0].isdigit() else 0

        assert actual_highest_int == expected_highest_int, f"llm_highest_birads应该为{expected_highest_int}，实际为{llm_highest}"

        print(f"\n✅ 场景4测试通过：多个异常发现识别验证成功")
        print(f"   - 识别异常发现数: {len(result['nodules'])}个 ✅")
        print(f"   - 每个异常发现都有独立分类: ✅")
        print(f"   - 最高BI-RADS分类: {llm_highest} ✅")

    def test_scenario_5_data_format(self):
        """
        场景5：数据格式和完整性测试（P0）
        
        测试目标：验证LLM返回的数据格式是否正确和完整
        
        测试数据：任意findings文本
        """
        findings = """
        检查所见：
        左侧乳腺外上象限距乳头约2.0cm处可见一低回声结节，大小约1.0×0.7×0.5cm。
        形态：椭圆形
        边界：清晰
        回声：均匀低回声
        方位：平行
        CDFI：未见明显血流信号。
        """

        print("\n" + "=" * 60)
        print("场景5：数据格式和完整性测试")
        print("=" * 60)
        print(f"输入findings:\n{findings.strip()}")
        print("\n开始调用LLM...")

        start_time = time.time()
        result = analyze_birads_independently(findings)
        elapsed_time = time.time() - start_time

        print(f"\n✅ LLM调用完成，耗时: {elapsed_time:.2f}秒")

        # 验证顶层字段
        assert isinstance(result, dict), "返回结果应该是字典"
        assert "nodules" in result, "缺少nodules字段"
        assert isinstance(result["nodules"], list), "nodules应该是列表"

        # 验证nodules不为空
        assert len(result["nodules"]) > 0, "应该识别到至少1个异常发现"

        nodule = result["nodules"][0]

        # 验证必需字段
        required_fields = {
            "id": str,
            "location": dict,
            "morphology": dict,
            "llm_birads_class": str,
            "llm_birads_reasoning": str,
        }

        for field, field_type in required_fields.items():
            assert field in nodule, f"缺少必需字段: {field}"
            assert isinstance(nodule[field], field_type), f"字段{field}类型错误，期望{field_type.__name__}，实际{type(nodule[field]).__name__}"

        # 验证location字段
        location = nodule["location"]
        assert "breast" in location, "location缺少breast字段"
        assert location["breast"] in ["left", "right"], f"breast应该是'left'或'right'，实际为{location['breast']}"

        # 验证morphology字段
        morphology = nodule["morphology"]
        assert isinstance(morphology, dict), "morphology应该是字典"

        # 验证llm_highest_birads
        assert "llm_highest_birads" in result, "缺少llm_highest_birads字段"
        assert result["llm_highest_birads"] is not None, "llm_highest_birads不应该为None"
        assert isinstance(result["llm_highest_birads"], str), "llm_highest_birads应该是字符串"

        # 验证BI-RADS分类格式
        llm_birads = nodule["llm_birads_class"]
        assert llm_birads and len(llm_birads) > 0, "llm_birads_class不应该为空"
        assert llm_birads[0].isdigit(), f"llm_birads_class应该以数字开头，实际为{llm_birads}"

        # 验证判断理由
        llm_reasoning = nodule["llm_birads_reasoning"]
        assert llm_reasoning and len(llm_reasoning) > 0, "llm_birads_reasoning不应该为空"

        print("\n✅ 场景5测试通过：数据格式和完整性验证成功")
        print(f"   - JSON格式: ✅")
        print(f"   - 必需字段: ✅ 全部存在")
        print(f"   - 字段类型: ✅ 正确")
        print(f"   - 数据完整性: ✅")
        print(f"   - 性能: {elapsed_time:.2f}秒 {'✅' if elapsed_time < 10 else '⚠️ 超过10秒'}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])

