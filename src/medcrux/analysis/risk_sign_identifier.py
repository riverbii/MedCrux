"""
BL-010: 风险征兆识别模块（v1.3.2简化版）

基于预设的强证据和弱证据列表，进行简单的字符串匹配来识别风险征兆。

注意：v1.3.3将基于完整的公理系统和特殊案例库实现更精确的风险征兆识别。
"""

from typing import List, Dict, Any
from .risk_sign_samples import STRONG_EVIDENCE_SAMPLES, WEAK_EVIDENCE_SAMPLES


def identify_risk_signs(morphology: Dict[str, Any], findings_text: str = "") -> List[Dict[str, str]]:
    """
    识别风险征兆（v1.3.2简化版：基于预设列表匹配）
    
    Args:
        morphology: 形态学特征字典，包含shape、boundary、echo、orientation等字段
        findings_text: 检查所见文本（可选，用于补充匹配）
    
    Returns:
        风险征兆列表，每个元素包含：
        - sign: 风险征兆名称
        - evidence_level: 证据强度（"strong"或"weak"）
        - evidence_source: 证据来源
        - suggestion: 建议
    """
    risk_signs = []
    
    # 合并形态学特征文本
    morphology_text_parts = []
    if morphology:
        morphology_text_parts.extend([
            str(morphology.get("shape", "")),
            str(morphology.get("boundary", "")),
            str(morphology.get("echo", "")),
            str(morphology.get("orientation", "")),
            str(morphology.get("posterior_features", "")),
            str(morphology.get("calcification", "")),
            str(morphology.get("blood_flow", "")),
        ])
    if findings_text:
        morphology_text_parts.append(findings_text)
    
    morphology_text = " ".join(morphology_text_parts).lower()
    
    # 匹配强证据
    for evidence in STRONG_EVIDENCE_SAMPLES:
        if any(keyword.lower() in morphology_text for keyword in evidence["keywords"]):
            # 检查是否已经匹配到相同的风险征兆
            if not any(rs["sign"] == evidence["sign"] for rs in risk_signs):
                risk_signs.append({
                    "sign": evidence["sign"],
                    "evidence_level": "strong",
                    "evidence_source": evidence["evidence_source"],
                    "suggestion": evidence["suggestion"]
                })
    
    # 匹配弱证据（如果还没有匹配到强证据，或者弱证据是独立的）
    for evidence in WEAK_EVIDENCE_SAMPLES:
        if any(keyword.lower() in morphology_text for keyword in evidence["keywords"]):
            # 检查是否已经匹配到相同的风险征兆
            if not any(rs["sign"] == evidence["sign"] for rs in risk_signs):
                risk_signs.append({
                    "sign": evidence["sign"],
                    "evidence_level": "weak",
                    "evidence_source": evidence["evidence_source"],
                    "suggestion": evidence["suggestion"]
                })
    
    return risk_signs


def aggregate_risk_signs(all_nodules: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, str]]]:
    """
    汇总所有异常发现的风险征兆
    
    Args:
        all_nodules: 所有异常发现的列表，每个元素应包含morphology字段
    
    Returns:
        包含strong_evidence和weak_evidence的字典
    """
    strong_evidence = []
    weak_evidence = []
    seen_signs = set()  # 避免重复
    
    for nodule in all_nodules:
        morphology = nodule.get("morphology", {})
        findings_text = nodule.get("findings_text", "")
        
        risk_signs = identify_risk_signs(morphology, findings_text)
        
        for risk_sign in risk_signs:
            sign_name = risk_sign["sign"]
            if sign_name not in seen_signs:
                seen_signs.add(sign_name)
                if risk_sign["evidence_level"] == "strong":
                    strong_evidence.append({
                        "sign": risk_sign["sign"],
                        "evidence_source": risk_sign["evidence_source"],
                        "suggestion": risk_sign["suggestion"]
                    })
                else:
                    weak_evidence.append({
                        "sign": risk_sign["sign"],
                        "evidence_source": risk_sign["evidence_source"],
                        "suggestion": risk_sign["suggestion"]
                    })
    
    return {
        "strong_evidence": strong_evidence,
        "weak_evidence": weak_evidence
    }
