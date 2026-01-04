"""
逻辑一致性检查模块：基于公理3和公理5的通用逻辑一致性检查

根据公理8要求：
- 基于离散数学（命题逻辑、集合论）进行逻辑推理
- 不针对任何特定形态学特征写规则
- 自动从公理3解析充要条件
- 自动从公理5解析标准术语集合
- 通用的充要条件验证
"""

from medcrux.utils.logger import log_error_with_context, setup_logger

logger = setup_logger("medcrux.rag.logical_consistency")


class LogicalConsistencyChecker:
    """逻辑一致性检查器：基于公理3和公理5的通用检查"""

    def __init__(self):
        """初始化检查器，定义标准术语集合和BI-RADS分类的充要条件"""
        # 标准术语集合（基于公理5）
        # 注意：只使用中文术语，英文术语仅用于匹配，不用于输出
        # 同义词、近义词等语言层面的问题由LLM在提取阶段处理，这里只检查医学逻辑
        self.standard_shapes = {"椭圆形", "圆形", "不规则形"}
        self.standard_boundaries = {
            "清晰",
            "大部分清晰",
            "模糊",
            "成角",
            "微小分叶",
            "毛刺状",
        }
        self.standard_echoes = {
            "均匀低回声",
            "不均匀回声",
            "无回声",
            "等回声",
            "高回声",
            "复合回声",
        }
        self.standard_orientations = {"平行", "不平行"}

        # BI-RADS分类的充要条件（基于公理3）
        # 注意：只使用中文术语，英文术语仅用于匹配
        self.birads_conditions = {
            "3": {
                "shape": {"椭圆形"},  # 要求椭圆形
                "boundary": {"清晰", "大部分清晰"},  # 要求清晰或大部分清晰
                "echo": {"均匀低回声"},  # 要求均匀低回声（注意："低回声" ≠ "均匀低回声"）
                "orientation": {"平行"},  # 要求平行
                "aspect_ratio": "<1",  # 要求纵横比<1
                "malignant_signs": False,  # 要求无恶性征象
            },
            "2": {
                "malignant_signs": False,  # 要求无恶性征象
            },
            # 其他分类的充要条件可以后续添加
        }

    def check_terminology(self, extracted_value: str, terminology_type: str) -> dict:
        """
        检查提取的术语是否在标准术语集合中（基于公理5）

        注意：同义词、近义词等语言层面的问题由LLM在提取阶段处理。
        这里只检查医学逻辑，不处理语言问题。

        Args:
            extracted_value: 提取的术语值（应该已经由LLM标准化）
            terminology_type: 术语类型（shape, boundary, echo, orientation）

        Returns:
            {
                "is_standard": bool,
                "standard_term": str | None,  # 标准中文术语
                "non_standard": str | None
            }
        """
        if not extracted_value:
            return {"is_standard": False, "standard_term": None, "non_standard": None}

        extracted_lower = extracted_value.lower()

        if terminology_type == "shape":
            standard_set = self.standard_shapes
        elif terminology_type == "boundary":
            standard_set = self.standard_boundaries
        elif terminology_type == "echo":
            standard_set = self.standard_echoes
        elif terminology_type == "orientation":
            standard_set = self.standard_orientations
        else:
            return {"is_standard": False, "standard_term": None, "non_standard": extracted_value}

        # 检查是否在标准集合中（直接匹配）
        # 注意：LLM应该在提取阶段已经处理了同义词、近义词等语言问题
        for standard_term in standard_set:
            if standard_term.lower() in extracted_lower or extracted_lower in standard_term.lower():
                return {"is_standard": True, "standard_term": standard_term, "non_standard": None}

        # 不在标准集合中
        return {"is_standard": False, "standard_term": None, "non_standard": extracted_value}

    def check_necessary_sufficient_condition(self, extracted_findings: dict, birads_class: str) -> dict:
        """
        检查提取的事实是否满足BI-RADS分类的充要条件（基于公理3）

        Args:
            extracted_findings: 提取的事实描述
                {
                    "shape": str,
                    "boundary": str,
                    "echo": str,
                    "orientation": str,
                    "aspect_ratio": float,
                    "malignant_signs": List[str]
                }
            birads_class: BI-RADS分类（"2", "3", "4", "5"等）

        Returns:
            {
                "satisfies": bool,  # 是否满足充要条件
                "violations": List[str],  # 违反的条件列表
                "inconsistency": bool  # 是否存在不一致
            }
        """
        if birads_class not in self.birads_conditions:
            # 如果该分类的充要条件未定义，返回无不一致
            return {"satisfies": True, "violations": [], "inconsistency": False}

        conditions = self.birads_conditions[birads_class]
        violations = []

        # 检查形状（如果该分类有形状要求）
        # 注意：extracted_shape可能是标准术语（如"椭圆形"），也可能是非标准术语（如"条状"）
        # LLM已处理同义词（如"清楚" → "清晰"），但非标准术语保持原样
        if "shape" in conditions:
            extracted_shape = extracted_findings.get("shape", "")
            if extracted_shape:
                # 先检查是否为标准术语
                term_check = self.check_terminology(extracted_shape, "shape")
                is_standard = term_check["is_standard"]

                # 如果非标准术语，直接判断为不符合要求
                if not is_standard:
                    required_shape_cn = list(conditions["shape"])[0]
                    violations.append(f"形状不符合：要求{required_shape_cn}，实际为{extracted_shape}（非标准术语）")
                else:
                    # 如果是标准术语，检查是否满足要求
                    shape_satisfies = False
                    for required_shape in conditions["shape"]:
                        if required_shape in extracted_shape or extracted_shape in required_shape:
                            shape_satisfies = True
                            break

                    if not shape_satisfies:
                        required_shape_cn = list(conditions["shape"])[0]
                        violations.append(f"形状不符合：要求{required_shape_cn}，实际为{extracted_shape}")

        # 检查边界（如果该分类有边界要求）
        # 注意：extracted_boundary应该已经由LLM标准化为标准术语（包括同义词处理）
        if "boundary" in conditions:
            extracted_boundary = extracted_findings.get("boundary", "")
            if extracted_boundary:
                # 检查提取的边界是否满足要求（直接匹配，LLM已处理同义词）
                boundary_satisfies = False
                for required_boundary in conditions["boundary"]:
                    if required_boundary in extracted_boundary or extracted_boundary in required_boundary:
                        boundary_satisfies = True
                        break

                if not boundary_satisfies:
                    required_boundary_cn = list(conditions["boundary"])[0]
                    violations.append(f"边界不符合：要求{required_boundary_cn}，实际为{extracted_boundary}")

        # 检查回声（如果该分类有回声要求）
        # 注意：extracted_echo应该已经由LLM标准化为标准术语
        # 医学判断：根据MD定义，"低回声" ≠ "均匀低回声"（这是医学专用术语的判断）
        if "echo" in conditions:
            extracted_echo = extracted_findings.get("echo", "")
            if extracted_echo:
                # 检查提取的回声是否满足要求
                # 严格匹配：必须完全匹配，不能部分匹配（医学专用术语要求）
                echo_satisfies = False
                for required_echo in conditions["echo"]:
                    if required_echo == extracted_echo:
                        echo_satisfies = True
                        break

                if not echo_satisfies:
                    required_echo_cn = list(conditions["echo"])[0]
                    violations.append(f"回声不符合：要求{required_echo_cn}，实际为{extracted_echo}")

        # 检查方位（如果该分类有方位要求）
        # 注意：extracted_orientation应该已经由LLM标准化为标准术语
        if "orientation" in conditions:
            extracted_orientation = extracted_findings.get("orientation", "")
            if extracted_orientation:
                # 检查提取的方位是否满足要求（直接匹配，LLM已处理同义词）
                orientation_satisfies = False
                for required_orientation in conditions["orientation"]:
                    if required_orientation in extracted_orientation or extracted_orientation in required_orientation:
                        orientation_satisfies = True
                        break

                if not orientation_satisfies:
                    required_orientation_cn = list(conditions["orientation"])[0]
                    violations.append(f"方位不符合：要求{required_orientation_cn}，实际为{extracted_orientation}")

        # 检查纵横比（如果该分类有纵横比要求）
        if "aspect_ratio" in conditions:
            aspect_ratio = extracted_findings.get("aspect_ratio")
            if aspect_ratio is not None:
                if conditions["aspect_ratio"] == "<1" and aspect_ratio >= 1:
                    violations.append(f"纵横比不符合：要求<1，实际为{aspect_ratio}")

        # 检查恶性征象（如果该分类要求无恶性征象）
        if conditions.get("malignant_signs") is False:
            malignant_signs = extracted_findings.get("malignant_signs", [])
            if malignant_signs:
                violations.append(f"存在恶性征象：{malignant_signs}，但该分类要求无恶性征象")

        return {
            "satisfies": len(violations) == 0,
            "violations": violations,
            "inconsistency": len(violations) > 0,
        }

    def check_consistency(self, extracted_findings: dict, birads_class: str) -> dict:
        """
        通用的逻辑一致性检查（基于公理8）

        Args:
            extracted_findings: 提取的事实描述
            birads_class: BI-RADS分类

        Returns:
            {
                "inconsistency": bool,
                "violations": List[str],
                "risk_assessment": "Low/Medium/High"
            }
        """
        try:
            # 1. 充要条件验证
            condition_result = self.check_necessary_sufficient_condition(extracted_findings, birads_class)

            # 2. 评估风险等级
            risk_assessment = self._assess_risk(condition_result, extracted_findings)

            return {
                "inconsistency": condition_result["inconsistency"],
                "violations": condition_result["violations"],
                "risk_assessment": risk_assessment,
            }

        except Exception as e:
            log_error_with_context(
                logger,
                e,
                context={"extracted_findings": extracted_findings, "birads_class": birads_class},
                operation="逻辑一致性检查",
            )
            return {"inconsistency": False, "violations": [], "risk_assessment": "Low"}

    def _assess_risk(self, condition_result: dict, extracted_findings: dict) -> str:
        """
        评估不一致的严重程度（基于公理8.6）

        Args:
            condition_result: 充要条件验证结果
            extracted_findings: 提取的事实描述

        Returns:
            "Low" / "Medium" / "High"
        """
        if not condition_result["inconsistency"]:
            return "Low"

        # 检查是否涉及恶性征象
        malignant_signs = extracted_findings.get("malignant_signs", [])
        if malignant_signs:
            return "High"

        # 检查是否违反关键定义（形状、边界等）
        violations = condition_result["violations"]
        if any("形状" in v or "边界" in v or "恶性征象" in v for v in violations):
            return "High"

        # 其他不一致为中风险
        return "Medium"
