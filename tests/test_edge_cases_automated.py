"""
自动化边界测试：测试各种边界情况

不需要真实环境，使用Mock数据测试边界情况
"""

from medcrux.rag.logical_consistency_checker import LogicalConsistencyChecker


class TestEdgeCasesAutomated:
    """自动化边界测试类"""

    def test_various_shape_terms(self):
        """测试各种形状术语（标准/非标准）"""
        checker = LogicalConsistencyChecker()

        # 标准术语
        standard_shapes = ["椭圆形", "圆形", "不规则形"]
        for shape in standard_shapes:
            result = checker.check_terminology(shape, "shape")
            assert result["is_standard"] is True
            assert result["standard_term"] == shape

        # 非标准术语
        non_standard_shapes = ["条状", "条索状", "管状", "线状", "unknown"]
        for shape in non_standard_shapes:
            result = checker.check_terminology(shape, "shape")
            assert result["is_standard"] is False
            assert result["non_standard"] == shape

    def test_various_boundary_terms(self):
        """测试各种边界术语"""
        checker = LogicalConsistencyChecker()

        # 标准术语
        standard_boundaries = ["清晰", "大部分清晰", "模糊", "成角", "微小分叶", "毛刺状"]
        for boundary in standard_boundaries:
            result = checker.check_terminology(boundary, "boundary")
            assert result["is_standard"] is True

    def test_various_echo_terms(self):
        """测试各种回声术语"""
        checker = LogicalConsistencyChecker()

        # 标准术语
        standard_echoes = [
            "均匀低回声",
            "不均匀回声",
            "无回声",
            "等回声",
            "高回声",
            "复合回声",
        ]

        for echo in standard_echoes:
            result = checker.check_terminology(echo, "echo")
            assert result["is_standard"] is True

        # 测试"低回声" vs "均匀低回声"的严格区分
        result_low = checker.check_terminology("低回声", "echo")
        result_homogeneous = checker.check_terminology("均匀低回声", "echo")
        # "低回声"不是标准术语，"均匀低回声"是标准术语
        assert result_low["is_standard"] is False
        assert result_homogeneous["is_standard"] is True

    def test_various_birads_classes(self):
        """测试各种BI-RADS分类"""
        checker = LogicalConsistencyChecker()

        # 测试BI-RADS 2类
        extracted_findings_2 = {
            "malignant_signs": [],
        }
        result_2 = checker.check_consistency(extracted_findings_2, "2")
        assert result_2["inconsistency"] is False  # 无恶性征象，应该一致

        # 测试BI-RADS 3类（一致）
        extracted_findings_3_consistent = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result_3_consistent = checker.check_consistency(extracted_findings_3_consistent, "3")
        assert result_3_consistent["inconsistency"] is False

        # 测试BI-RADS 3类（不一致 - 非标准形状）
        extracted_findings_3_inconsistent = {
            "shape": "条状",  # 非标准术语
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result_3_inconsistent = checker.check_consistency(extracted_findings_3_inconsistent, "3")
        assert result_3_inconsistent["inconsistency"] is True
        assert any("形状不符合" in v for v in result_3_inconsistent["violations"])

    def test_inconsistency_detection_striped(self):
        """测试不一致检测（条状情况）"""
        checker = LogicalConsistencyChecker()

        # 条状不符合BI-RADS 3类的椭圆形要求
        extracted_findings = {
            "shape": "条状",  # 非标准术语
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result = checker.check_consistency(extracted_findings, "3")

        assert result["inconsistency"] is True
        assert any("形状不符合" in v for v in result["violations"])
        assert result["risk_assessment"] == "Medium"  # 无恶性征象，中风险

    def test_echo_strict_matching(self):
        """测试回声术语的严格匹配"""
        checker = LogicalConsistencyChecker()

        # BI-RADS 3类要求"均匀低回声"
        extracted_findings_required = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",  # 标准术语
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result_required = checker.check_consistency(extracted_findings_required, "3")
        assert result_required["inconsistency"] is False

        # "低回声" ≠ "均匀低回声"（严格匹配）
        extracted_findings_not_required = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "低回声",  # 非标准术语，不匹配"均匀低回声"
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result_not_required = checker.check_consistency(extracted_findings_not_required, "3")
        assert result_not_required["inconsistency"] is True
        assert any("回声不符合" in v for v in result_not_required["violations"])

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

    def test_empty_or_missing_fields(self):
        """测试空值或缺失字段的处理"""
        checker = LogicalConsistencyChecker()

        # 测试空值
        result_empty = checker.check_terminology("", "shape")
        assert result_empty["is_standard"] is False

        # 测试缺失字段
        extracted_findings_missing = {
            "shape": "",  # 空值
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行",
            "aspect_ratio": 0.8,
            "malignant_signs": [],
        }
        result_missing = checker.check_consistency(extracted_findings_missing, "3")
        # 空值应该不影响其他字段的检查
        assert isinstance(result_missing, dict)
        assert "inconsistency" in result_missing
