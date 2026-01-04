"""
测试LLM分析引擎模块 - 版本1.1.0新格式

测试新格式（结节列表）功能：
- 新格式输出
- 格式转换（旧格式转新格式）
- 多结节处理
- 位置信息提取
"""

import os
from unittest.mock import MagicMock, patch

from medcrux.analysis.llm_engine import (
    _convert_old_format_to_new,
    _post_process_consistency_check,
    analyze_text_with_deepseek,
)


class TestLLMEngineV1_1_0:
    """测试LLM分析引擎 - 版本1.1.0新格式"""

    def test_convert_old_format_to_new_single_nodule(self):
        """测试旧格式转新格式（单个结节）"""
        old_format = {
            "patient_gender": "Female",
            "extracted_findings": ["低回声结节"],
            "extracted_shape": "椭圆形",
            "extracted_boundary": "清晰",
            "extracted_echo": "均匀低回声",
            "extracted_orientation": "平行",
            "extracted_malignant_signs": [],
            "birads_class": "3",
            "ai_risk_assessment": "Low",
            "inconsistency_alert": False,
            "inconsistency_reasons": [],
            "advice": "建议随访",
        }

        new_format = _convert_old_format_to_new(old_format)

        # 验证新格式结构
        assert "nodules" in new_format
        assert "overall_assessment" in new_format
        assert len(new_format["nodules"]) == 1

        # 验证结节数据
        nodule = new_format["nodules"][0]
        assert nodule["id"] == "nodule_1"
        assert nodule["morphology"]["shape"] == "椭圆形"
        assert nodule["morphology"]["boundary"] == "清晰"
        assert nodule["birads_class"] == "3"
        assert nodule["risk_assessment"] == "Low"

        # 验证整体评估
        overall = new_format["overall_assessment"]
        assert overall["total_nodules"] == 1
        assert overall["highest_risk"] == "Low"

    def test_convert_old_format_to_new_already_new_format(self):
        """测试如果已经是新格式，直接返回"""
        new_format = {
            "nodules": [{"id": "nodule_1", "morphology": {"shape": "椭圆形"}}],
            "overall_assessment": {"total_nodules": 1},
        }

        result = _convert_old_format_to_new(new_format)
        assert result is new_format  # 应该直接返回，不修改

    def test_convert_old_format_to_new_no_nodules(self):
        """测试无结节情况"""
        old_format = {
            "patient_gender": "Female",
            "extracted_findings": [],
            "ai_risk_assessment": "Low",
            "advice": "无异常",
        }

        new_format = _convert_old_format_to_new(old_format)

        # 应该转换为包含一个空结节或空列表
        assert "nodules" in new_format
        assert "overall_assessment" in new_format

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    def test_analyze_text_with_new_format(self, mock_get_retriever, mock_client):
        """测试新格式输出（结节列表）"""
        # Mock RAG检索结果
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = {
            "entities": [],
            "relations": [],
            "inference_paths": [],
            "confidence": 0.8,
        }
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应（新格式）
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        '{"patient_gender": "Female", '
                        '"nodules": ['
                        "{"
                        '"id": "nodule_1", '
                        '"location": {"breast": "left", "quadrant": "上外", '
                        '"clock_position": "12点", "distance_from_nipple": "2.5 cm"}, '
                        '"morphology": {"shape": "椭圆形", "boundary": "清晰", '
                        '"echo": "均匀低回声", "orientation": "平行", '
                        '"size": "1.2×0.8×0.6 cm"}, '
                        '"malignant_signs": [], '
                        '"birads_class": "3", '
                        '"risk_assessment": "Low", '
                        '"inconsistency_alert": false, '
                        '"inconsistency_reasons": []'
                        "}"
                        "], "
                        '"overall_assessment": {'
                        '"total_nodules": 1, '
                        '"highest_risk": "Low", '
                        '"summary": ["低回声结节"], '
                        '"advice": "建议随访"'
                        "}"
                        "}"
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # 设置API Key
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 执行分析
        result = analyze_text_with_deepseek("超声描述：左乳上外12点可见低回声结节，大小1.2×0.8×0.6cm，边界清晰。")

        # 验证新格式结构
        assert "nodules" in result
        assert "overall_assessment" in result
        assert len(result["nodules"]) == 1

        # 验证结节数据
        nodule = result["nodules"][0]
        assert nodule["id"] == "nodule_1"
        assert nodule["location"]["breast"] == "left"
        assert nodule["location"]["quadrant"] == "上外"
        assert nodule["location"]["clock_position"] == "12点"
        assert nodule["morphology"]["shape"] == "椭圆形"

        # 验证整体评估
        overall = result["overall_assessment"]
        assert overall["total_nodules"] == 1
        assert overall["highest_risk"] == "Low"

    @patch("medcrux.analysis.llm_engine.client")
    @patch("medcrux.analysis.llm_engine._get_retriever")
    def test_analyze_text_with_multiple_nodules(self, mock_get_retriever, mock_client):
        """测试多个结节的情况"""
        # Mock RAG检索结果
        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = {
            "entities": [],
            "relations": [],
            "inference_paths": [],
            "confidence": 0.8,
        }
        mock_get_retriever.return_value = mock_retriever

        # Mock LLM响应（多个结节）
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=(
                        '{"patient_gender": "Female", '
                        '"nodules": ['
                        "{"
                        '"id": "nodule_1", '
                        '"location": {"breast": "left", "quadrant": "上外", "clock_position": "12点"}, '
                        '"morphology": {"shape": "椭圆形", "boundary": "清晰", "echo": "均匀低回声"}, '
                        '"birads_class": "3", '
                        '"risk_assessment": "Low", '
                        '"inconsistency_alert": false, '
                        '"inconsistency_reasons": []'
                        "}, "
                        "{"
                        '"id": "nodule_2", '
                        '"location": {"breast": "right", "quadrant": "下内", "clock_position": "6点"}, '
                        '"morphology": {"shape": "圆形", "boundary": "清晰", "echo": "无回声"}, '
                        '"birads_class": "2", '
                        '"risk_assessment": "Low", '
                        '"inconsistency_alert": false, '
                        '"inconsistency_reasons": []'
                        "}"
                        "], "
                        '"overall_assessment": {'
                        '"total_nodules": 2, '
                        '"highest_risk": "Low", '
                        '"summary": ["左乳上外结节", "右乳下内结节"], '
                        '"advice": "建议随访"'
                        "}"
                        "}"
                    )
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # 设置API Key
        os.environ["DEEPSEEK_API_KEY"] = "test-key"

        # 执行分析
        result = analyze_text_with_deepseek("超声描述：左乳上外12点可见低回声结节，右乳下内6点可见无回声结节。")

        # 验证新格式结构
        assert "nodules" in result
        assert len(result["nodules"]) == 2

        # 验证第一个结节
        nodule1 = result["nodules"][0]
        assert nodule1["id"] == "nodule_1"
        assert nodule1["location"]["breast"] == "left"
        assert nodule1["birads_class"] == "3"

        # 验证第二个结节
        nodule2 = result["nodules"][1]
        assert nodule2["id"] == "nodule_2"
        assert nodule2["location"]["breast"] == "right"
        assert nodule2["birads_class"] == "2"

        # 验证整体评估
        overall = result["overall_assessment"]
        assert overall["total_nodules"] == 2

    def test_post_process_consistency_check_with_nodules(self):
        """测试后处理逻辑一致性检查（结节列表格式）"""
        # 准备测试数据（新格式）
        result = {
            "patient_gender": "Female",
            "nodules": [
                {
                    "id": "nodule_1",
                    "morphology": {
                        "shape": "条状",  # 非标准术语，应该被检测为不一致
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                    "birads_class": "3",
                    "risk_assessment": "Low",
                    "inconsistency_alert": False,
                    "inconsistency_reasons": [],
                }
            ],
            "overall_assessment": {
                "total_nodules": 1,
                "highest_risk": "Low",
                "summary": [],
                "advice": "",
            },
        }

        # 执行后处理
        processed_result = _post_process_consistency_check(result, "测试文本")

        # 验证一致性检查结果
        nodule = processed_result["nodules"][0]
        # 条状不符合BI-RADS 3类要求（要求椭圆形），应该被检测为不一致
        assert nodule["inconsistency_alert"] is True
        assert len(nodule["inconsistency_reasons"]) > 0
        assert "形状不符合" in "".join(nodule["inconsistency_reasons"])

        # 验证整体评估更新
        overall = processed_result["overall_assessment"]
        assert overall["highest_risk"] in ["Medium", "High"]  # 风险应该提升

    def test_post_process_consistency_check_multiple_nodules(self):
        """测试后处理逻辑一致性检查（多个结节）"""
        # 准备测试数据（多个结节，其中一个不一致）
        result = {
            "patient_gender": "Female",
            "nodules": [
                {
                    "id": "nodule_1",
                    "morphology": {
                        "shape": "椭圆形",
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                    "birads_class": "3",
                    "risk_assessment": "Low",
                    "inconsistency_alert": False,
                    "inconsistency_reasons": [],
                },
                {
                    "id": "nodule_2",
                    "morphology": {
                        "shape": "条状",  # 不一致
                        "boundary": "清晰",
                        "echo": "均匀低回声",
                        "orientation": "平行",
                    },
                    "birads_class": "3",
                    "risk_assessment": "Low",
                    "inconsistency_alert": False,
                    "inconsistency_reasons": [],
                },
            ],
            "overall_assessment": {
                "total_nodules": 2,
                "highest_risk": "Low",
                "summary": [],
                "advice": "",
            },
        }

        # 执行后处理
        processed_result = _post_process_consistency_check(result, "测试文本")

        # 验证第一个结节（一致）
        nodule1 = processed_result["nodules"][0]
        assert nodule1["inconsistency_alert"] is False

        # 验证第二个结节（不一致）
        nodule2 = processed_result["nodules"][1]
        assert nodule2["inconsistency_alert"] is True

        # 验证整体评估（应该反映最高风险）
        overall = processed_result["overall_assessment"]
        assert overall["highest_risk"] in ["Medium", "High"]
