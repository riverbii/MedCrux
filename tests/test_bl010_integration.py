"""
BL-010: 风险征兆识别集成测试（v1.3.2简化版）

测试风险征兆识别功能在完整数据流中的集成。
"""

import sys

sys.path.insert(0, 'src')

from medcrux.analysis.risk_sign_identifier import aggregate_risk_signs, identify_risk_signs


class TestBL010Integration:
    """BL-010集成测试类"""

    def test_integration_with_morphology(self):
        """测试风险征兆识别与形态学特征的集成"""
        # 模拟完整的nodule数据结构
        nodules = [
            {
                "id": "nodule_1",
                "name": "异常发现1",
                "morphology": {
                    "shape": "椭圆形",
                    "boundary": "边界不清晰，部分毛刺状",
                    "echo": "均匀低回声",
                    "orientation": "平行"
                },
                "findings_text": "左侧乳腺外上象限可见一低回声结节"
            },
            {
                "id": "nodule_2",
                "name": "异常发现2",
                "morphology": {
                    "shape": "椭圆形",
                    "boundary": "清晰",
                    "echo": "条索状低回声",
                    "orientation": "平行"
                },
                "findings_text": "右侧乳腺内上象限可见一低回声结节"
            }
        ]

        # 测试风险征兆识别
        for nodule in nodules:
            morphology = nodule.get("morphology", {})
            findings_text = nodule.get("findings_text", "")
            risk_signs = identify_risk_signs(morphology, findings_text)
            
            if nodule["id"] == "nodule_1":
                assert len(risk_signs) > 0, "nodule_1应该识别到风险征兆"
                assert any(rs["sign"] == "部分毛刺状边界" for rs in risk_signs), "应该识别到'部分毛刺状边界'"
            elif nodule["id"] == "nodule_2":
                assert len(risk_signs) > 0, "nodule_2应该识别到风险征兆"
                assert any(rs["sign"] == "条索状低回声" for rs in risk_signs), "应该识别到'条索状低回声'"

        # 测试风险征兆汇总
        summary = aggregate_risk_signs(nodules)
        
        assert "strong_evidence" in summary, "应该包含强证据"
        assert "weak_evidence" in summary, "应该包含弱证据"
        assert len(summary["strong_evidence"]) > 0, "应该有强证据"
        assert len(summary["weak_evidence"]) > 0, "应该有弱证据"
        
        # 验证汇总不重复
        strong_signs = [rs["sign"] for rs in summary["strong_evidence"]]
        weak_signs = [rs["sign"] for rs in summary["weak_evidence"]]
        assert len(strong_signs) == len(set(strong_signs)), "强证据不应重复"
        assert len(weak_signs) == len(set(weak_signs)), "弱证据不应重复"

    def test_data_format_completeness(self):
        """测试风险征兆数据格式完整性"""
        morphology = {
            "boundary": "部分毛刺状边界"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        if risk_signs:
            for risk_sign in risk_signs:
                # 验证必需字段
                assert "sign" in risk_sign, "应该包含sign字段"
                assert "evidence_level" in risk_sign, "应该包含evidence_level字段"
                assert "evidence_source" in risk_sign, "应该包含evidence_source字段"
                assert "suggestion" in risk_sign, "应该包含suggestion字段"
                
                # 验证字段值
                assert risk_sign["sign"], "sign不应为空"
                assert risk_sign["evidence_level"] in ["strong", "weak"], "evidence_level应该是strong或weak"
                assert risk_sign["evidence_source"], "evidence_source不应为空"
                assert risk_sign["suggestion"], "suggestion不应为空"

    def test_aggregate_format_completeness(self):
        """测试汇总数据格式完整性"""
        nodules = [
            {
                "id": "nodule_1",
                "morphology": {"boundary": "部分毛刺状边界"},
                "findings_text": ""
            }
        ]
        
        summary = aggregate_risk_signs(nodules)
        
        assert "strong_evidence" in summary, "应该包含strong_evidence字段"
        assert "weak_evidence" in summary, "应该包含weak_evidence字段"
        assert isinstance(summary["strong_evidence"], list), "strong_evidence应该是列表"
        assert isinstance(summary["weak_evidence"], list), "weak_evidence应该是列表"
        
        if summary["strong_evidence"]:
            for evidence in summary["strong_evidence"]:
                assert "sign" in evidence, "应该包含sign字段"
                assert "evidence_source" in evidence, "应该包含evidence_source字段"
                assert "suggestion" in evidence, "应该包含suggestion字段"
