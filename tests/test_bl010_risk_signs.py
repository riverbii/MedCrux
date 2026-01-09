"""
BL-010: 风险征兆识别单元测试（v1.3.2简化版）

测试基于预设列表的风险征兆识别功能。
"""

import sys

sys.path.insert(0, 'src')

from medcrux.analysis.risk_sign_identifier import aggregate_risk_signs, identify_risk_signs


class TestRiskSignIdentification:
    """风险征兆识别测试类"""

    def test_identify_strong_evidence_1(self):
        """测试识别强证据：部分毛刺状边界"""
        morphology = {
            "boundary": "边界不清晰，部分毛刺状",
            "shape": "椭圆形",
            "echo": "均匀低回声"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        assert len(risk_signs) > 0, "应该识别到风险征兆"
        assert any(rs["sign"] == "部分毛刺状边界" for rs in risk_signs), "应该识别到'部分毛刺状边界'"
        assert any(rs["evidence_level"] == "strong" for rs in risk_signs), "应该是强证据"

    def test_identify_strong_evidence_2(self):
        """测试识别强证据：不均匀回声"""
        morphology = {
            "echo": "不均匀回声，内部回声不均匀",
            "shape": "椭圆形",
            "boundary": "清晰"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        assert len(risk_signs) > 0, "应该识别到风险征兆"
        assert any(rs["sign"] == "不均匀回声" for rs in risk_signs), "应该识别到'不均匀回声'"
        assert any(rs["evidence_level"] == "strong" for rs in risk_signs), "应该是强证据"

    def test_identify_weak_evidence_1(self):
        """测试识别弱证据：条索状低回声"""
        morphology = {
            "echo": "条索状低回声",
            "shape": "椭圆形",
            "boundary": "清晰"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        assert len(risk_signs) > 0, "应该识别到风险征兆"
        assert any(rs["sign"] == "条索状低回声" for rs in risk_signs), "应该识别到'条索状低回声'"
        assert any(rs["evidence_level"] == "weak" for rs in risk_signs), "应该是弱证据"

    def test_identify_no_risk_signs(self):
        """测试无风险征兆的情况"""
        morphology = {
            "shape": "椭圆形",
            "boundary": "清晰",
            "echo": "均匀低回声",
            "orientation": "平行"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        assert len(risk_signs) == 0, "不应该识别到风险征兆"

    def test_aggregate_risk_signs(self):
        """测试汇总风险征兆"""
        nodules = [
            {
                "id": "nodule_1",
                "morphology": {
                    "boundary": "部分毛刺状边界",
                    "shape": "椭圆形"
                }
            },
            {
                "id": "nodule_2",
                "morphology": {
                    "echo": "条索状低回声",
                    "shape": "椭圆形"
                }
            }
        ]
        
        summary = aggregate_risk_signs(nodules)
        
        assert "strong_evidence" in summary, "应该包含强证据"
        assert "weak_evidence" in summary, "应该包含弱证据"
        assert len(summary["strong_evidence"]) > 0, "应该有强证据"
        assert len(summary["weak_evidence"]) > 0, "应该有弱证据"

    def test_risk_signs_format(self):
        """测试风险征兆数据格式"""
        morphology = {
            "boundary": "部分毛刺状边界"
        }
        
        risk_signs = identify_risk_signs(morphology)
        
        if risk_signs:
            risk_sign = risk_signs[0]
            assert "sign" in risk_sign, "应该包含sign字段"
            assert "evidence_level" in risk_sign, "应该包含evidence_level字段"
            assert "evidence_source" in risk_sign, "应该包含evidence_source字段"
            assert "suggestion" in risk_sign, "应该包含suggestion字段"
            assert risk_sign["evidence_level"] in ["strong", "weak"], "evidence_level应该是strong或weak"
