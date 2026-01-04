"""
测试逻辑一致性检查器：通用的逻辑一致性检查测试

测试原则：
- 不针对任何特定形态学特征写测试
- 测试通用的充要条件验证逻辑
- 测试术语标准化检查
- 测试各种不符合分类定义的情况
"""

from medcrux.rag.logical_consistency_checker import LogicalConsistencyChecker


class TestLogicalConsistencyChecker:
    """测试逻辑一致性检查器"""

    def test_terminology_check_standard_shape(self):
        """测试标准形状术语检查"""
        checker = LogicalConsistencyChecker()
        result = checker.check_terminology("椭圆形", "shape")
        assert result["is_standard"] is True
        assert result["standard_term"] == "椭圆形"

    def test_terminology_check_non_standard_shape(self):
        """测试非标准形状术语检查（通用测试，不针对具体术语）"""
        checker = LogicalConsistencyChecker()

        # 测试各种非标准术语
        non_standard_shapes = ["条状", "条索状", "管状", "线状", "unknown_shape"]

        for shape in non_standard_shapes:
            result = checker.check_terminology(shape, "shape")
            assert result["is_standard"] is False
            assert result["non_standard"] == shape
            assert result["standard_term"] is None

    def test_birads_3_consistency_with_oval_shape(self):
        """测试BI-RADS 3类 + 椭圆形（应该一致）"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result = checker.check_consistency(extracted_findings, "3")
        assert result["inconsistency"] is False
        assert len(result["violations"]) == 0

    def test_birads_3_inconsistency_with_non_oval_shape(self):
        """测试BI-RADS 3类 + 非椭圆形（应该不一致，通用测试）"""
        checker = LogicalConsistencyChecker()

        # 测试各种非椭圆形形状
        non_oval_shapes = ["不规则形", "圆形", "条状", "条索状", "管状", "unknown"]

        for shape in non_oval_shapes:
            extracted_findings = {
                "shape": shape,
                "boundary": "清晰",
                "echo": "均匀低回声",
                "orientation": "平行",
                "aspect_ratio": 0.8,
                "malignant_signs": [],
            }
            result = checker.check_consistency(extracted_findings, "3")

            # 如果形状不是椭圆形，应该不一致
            if shape not in ["椭圆形", "oval"]:
                assert result["inconsistency"] is True
                assert any("形状不符合" in v for v in result["violations"])

    def test_birads_3_inconsistency_with_non_clear_boundary(self):
        """测试BI-RADS 3类 + 不清晰边界（应该不一致，通用测试）"""
        checker = LogicalConsistencyChecker()

        # 测试各种不清晰边界
        non_clear_boundaries = ["模糊", "成角", "毛刺状", "微小分叶", "unknown"]

        for boundary in non_clear_boundaries:
            extracted_findings = {
                "shape": "椭圆形",
                "boundary": boundary,
                "echo": "均匀低回声",
                "orientation": "平行",
                "aspect_ratio": 0.8,
                "malignant_signs": [],
            }
            result = checker.check_consistency(extracted_findings, "3")

            # 如果边界不清晰，应该不一致
            if boundary not in ["清晰", "circumscribed", "大部分清晰", "mostly circumscribed"]:
                assert result["inconsistency"] is True
                assert any("边界不符合" in v for v in result["violations"])

    def test_birads_3_inconsistency_with_malignant_signs(self):
        """测试BI-RADS 3类 + 恶性征象（应该不一致，通用测试）"""
        checker = LogicalConsistencyChecker()

        # 测试各种恶性征象
        malignant_signs_list = [
            ["毛刺状边界"],
            ["微钙化"],
            ["不平行方位"],
            ["声影"],
            ["毛刺状边界", "微钙化"],  # 多个恶性征象
        ]

        for malignant_signs in malignant_signs_list:
            extracted_findings = {
                "shape": "椭圆形",
                "boundary": "清晰",
                "echo": "均匀低回声",
                "orientation": "平行",
                "aspect_ratio": 0.8,
                "malignant_signs": malignant_signs,
            }
            result = checker.check_consistency(extracted_findings, "3")
            assert result["inconsistency"] is True
            assert any("恶性征象" in v for v in result["violations"])
            assert result["risk_assessment"] == "High"  # 恶性征象应该是高风险

    def test_birads_3_inconsistency_with_aspect_ratio_geq_1(self):
        """测试BI-RADS 3类 + 纵横比≥1（应该不一致）"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "不平行",
            "aspect_ratio": 1.2,  # 纵横比>1
            "malignant_signs": [],
        }
        result = checker.check_consistency(extracted_findings, "3")
        assert result["inconsistency"] is True
        assert any("纵横比" in v for v in result["violations"])

    def test_risk_assessment_without_malignant_signs(self):
        """测试风险评估：无恶性征象的不一致应该是中风险"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "shape": "不规则形",  # 不符合3类定义，但不是恶性征象
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result = checker.check_consistency(extracted_findings, "3")
        assert result["inconsistency"] is True
        assert result["risk_assessment"] == "Medium"  # 无恶性征象，中风险

    def test_risk_assessment_with_malignant_signs(self):
        """测试风险评估：有恶性征象的不一致应该是高风险"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": ["微钙化"],  # 有恶性征象
        }
        result = checker.check_consistency(extracted_findings, "3")
        assert result["inconsistency"] is True
        assert result["risk_assessment"] == "High"  # 有恶性征象，高风险

    def test_multiple_violations(self):
        """测试多个违反条件的情况"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "shape": "不规则形",  # 违反形状要求
            "boundary": "模糊",  # 违反边界要求
            "echo": "不均匀回声",  # 违反回声要求
            "orientation": "不平行",
            "aspect_ratio": 1.2,  # 违反纵横比要求
            "malignant_signs": ["微钙化"],  # 违反恶性征象要求
        }
        result = checker.check_consistency(extracted_findings, "3")
        assert result["inconsistency"] is True
        assert len(result["violations"]) > 1  # 应该有多个违反条件
        assert result["risk_assessment"] == "High"  # 有恶性征象，高风险

    def test_birads_2_inconsistency_with_malignant_signs(self):
        """测试BI-RADS 2类 + 恶性征象（应该不一致）"""
        checker = LogicalConsistencyChecker()
        extracted_findings = {
            "malignant_signs": ["毛刺状边界"],
        }
        result = checker.check_consistency(extracted_findings, "2")
        assert result["inconsistency"] is True
        assert any("恶性征象" in v for v in result["violations"])
