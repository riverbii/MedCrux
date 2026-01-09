"""
BL-010: 风险征兆预设样本数据（v1.3.2简化版）

基于ACR BI-RADS标准和临床研究文献，预设强证据和弱证据的风险征兆列表。
用于v1.3.2的简化版风险征兆识别（基于字符串匹配）。

注意：v1.3.3将基于完整的公理系统和特殊案例库实现更精确的风险征兆识别。
"""

# 预设强证据（基于ACR BI-RADS标准）
STRONG_EVIDENCE_SAMPLES = [
    {
        "sign": "部分毛刺状边界",
        "evidence_level": "strong",
        "evidence_source": "ACR BI-RADS标准",
        "suggestion": "建议更密切的随访或进一步检查",
        "keywords": ["毛刺", "毛刺状", "边界不清晰", "边界模糊", "边界成角", "微小分叶"]
    },
    {
        "sign": "部分不规则形状",
        "evidence_level": "strong",
        "evidence_source": "ACR BI-RADS标准",
        "suggestion": "建议更密切的随访或进一步检查",
        "keywords": ["不规则", "不规则形", "不规则形状", "不规则形态"]
    },
    {
        "sign": "部分不平行方位",
        "evidence_level": "strong",
        "evidence_source": "ACR BI-RADS标准",
        "suggestion": "建议更密切的随访或进一步检查",
        "keywords": ["不平行", "不平行方位", "垂直", "垂直方位"]
    },
    {
        "sign": "不均匀回声",
        "evidence_level": "strong",
        "evidence_source": "ACR BI-RADS标准",
        "suggestion": "建议更密切的随访或进一步检查",
        "keywords": ["不均匀", "不均匀回声", "混合回声", "回声不均匀", "内部回声不均匀"]
    },
    {
        "sign": "丰富血流信号",
        "evidence_level": "strong",
        "evidence_source": "ACR BI-RADS标准",
        "suggestion": "建议更密切的随访或进一步检查",
        "keywords": ["丰富血流", "丰富血流信号", "血流丰富", "血流信号丰富", "CDFI丰富", "彩色多普勒丰富"]
    }
]

# 预设弱证据（基于临床研究文献）
WEAK_EVIDENCE_SAMPLES = [
    {
        "sign": "条索状低回声",
        "evidence_level": "weak",
        "evidence_source": "临床研究文献",
        "suggestion": "建议咨询专业医生，考虑进一步检查",
        "keywords": ["条索", "条索状", "条状", "条状低回声", "条索状低回声"]
    },
    {
        "sign": "导管扩张伴导管内占位",
        "evidence_level": "weak",
        "evidence_source": "临床研究文献",
        "suggestion": "建议咨询专业医生，考虑进一步检查",
        "keywords": ["导管扩张", "导管内占位", "导管扩张伴占位", "导管内占位性病变"]
    },
    {
        "sign": "结构紊乱",
        "evidence_level": "weak",
        "evidence_source": "临床研究文献",
        "suggestion": "建议咨询专业医生，考虑进一步检查",
        "keywords": ["结构紊乱", "结构破坏", "正常结构破坏", "结构异常"]
    }
]
