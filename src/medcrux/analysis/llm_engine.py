"""
LLM分析引擎模块：使用DeepSeek进行医学逻辑分析

根据STANDARDS_v1.1.md要求：
- 基础日志记录：记录关键操作和错误
- 错误追踪：所有异常必须被捕获并记录

根据PRD_v1.1.md要求：
- RAG检索：在医学指南知识图谱中检索相关知识
- LLM分析：结合RAG检索的专业知识，分析报告描述与结论的一致性
"""

import json
import os
import re
import time

from openai import OpenAI

from medcrux.rag.graphrag_retriever import GraphRAGRetriever
from medcrux.rag.logical_consistency_checker import LogicalConsistencyChecker
from medcrux.utils.logger import log_error_with_context, setup_logger

# 初始化logger
logger = setup_logger("medcrux.analysis")

# 初始化客户端 (DeepSeek 兼容 OpenAI SDK)
# 建议将 API KEY 放入环境变量，或者在此处临时硬编码测试
# export DEEPSEEK_API_KEY="sk-..."
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    logger.warning("DEEPSEEK_API_KEY未设置，AI分析功能将不可用")
else:
    logger.info("DeepSeek API客户端初始化完成")

client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

# 初始化GraphRAG检索器（单例模式）
_retriever: GraphRAGRetriever | None = None


def _convert_old_format_to_new(old_result: dict) -> dict:
    """
    将旧格式（单一结果）转换为新格式（结节列表）

    旧格式：
    {
        "extracted_shape": "椭圆形",
        "extracted_boundary": "清晰",
        ...
    }

    新格式：
    {
        "nodules": [
            {
                "id": "nodule_1",
                "location": {...},
                "morphology": {...},
                ...
            }
        ],
        "overall_assessment": {...}
    }
    """
    # 检查是否已经是新格式
    if "nodules" in old_result:
        return old_result

    # 转换为新格式
    nodule = {
        "id": "nodule_1",
        "location": {
            "breast": old_result.get("extracted_breast", ""),
            "quadrant": old_result.get("extracted_quadrant", ""),
            "clock_position": old_result.get("extracted_clock_position", ""),
            "distance_from_nipple": old_result.get("extracted_distance_from_nipple", ""),
        },
        "morphology": {
            "shape": old_result.get("extracted_shape", ""),
            "boundary": old_result.get("extracted_boundary", ""),
            "echo": old_result.get("extracted_echo", ""),
            "orientation": old_result.get("extracted_orientation", ""),
            "size": old_result.get("extracted_size", ""),
        },
        "malignant_signs": old_result.get("extracted_malignant_signs", []),
        "birads_class": old_result.get("birads_class", ""),
        "risk_assessment": old_result.get("ai_risk_assessment", "Low"),
        "inconsistency_alert": old_result.get("inconsistency_alert", False),
        "inconsistency_reasons": old_result.get("inconsistency_reasons", []),
    }

    return {
        "patient_gender": old_result.get("patient_gender", "Unknown"),
        "nodules": [nodule],
        "overall_assessment": {
            "total_nodules": 1,
            "highest_risk": old_result.get("ai_risk_assessment", "Low"),
            "summary": old_result.get("extracted_findings", []),
            "advice": old_result.get("advice", ""),
        },
    }


def _post_process_consistency_check(result: dict, ocr_text: str) -> dict:
    """
    后处理：通用的逻辑一致性检查（基于公理8）

    支持新格式（结节列表）和旧格式（单一结果）
    使用LogicalConsistencyChecker进行通用的充要条件验证，
    不针对任何特定形态学特征写规则。
    """
    try:
        # 转换为新格式（如果还是旧格式）
        result = _convert_old_format_to_new(result)

        # 初始化逻辑一致性检查器
        checker = LogicalConsistencyChecker()

        # 数据清理：如果值包含"/"，需要检查所有值，不能只取第一个（医疗产品不能丢失风险信息）
        def extract_primary_value(value: str) -> str:
            """
            提取主要值用于逻辑一致性检查
            如果包含多个值（用/分隔），优先选择非标准术语（如"条状"），否则选择第一个
            医疗产品不能丢失风险信号
            """
            if not value:
                return ""
            if "/" in value:
                values = [v.strip() for v in value.split("/") if v.strip()]
                # 优先选择非标准术语（如"条状"、"条索状"），因为这些是风险信号
                non_standard_terms = ["条状", "条索状", "管状", "线状"]
                for val in values:
                    if any(term in val for term in non_standard_terms):
                        return val
                # 如果没有非标准术语，选择第一个
                return values[0] if values else ""
            return value.strip()

        # 对每个结节进行一致性检查
        nodules = result.get("nodules", [])
        highest_risk = "Low"
        all_inconsistency_reasons = []

        for nodule in nodules:
            morphology = nodule.get("morphology", {})
            extracted_findings = {
                "shape": extract_primary_value(morphology.get("shape", "")),
                "boundary": extract_primary_value(morphology.get("boundary", "")),
                "echo": extract_primary_value(morphology.get("echo", "")),
                "orientation": extract_primary_value(morphology.get("orientation", "")),
                "aspect_ratio": nodule.get("aspect_ratio"),
                "malignant_signs": nodule.get("malignant_signs", []),
            }
            birads_class = nodule.get("birads_class", "")

            # 如果BI-RADS分类为空，跳过检查
            if not birads_class:
                continue

            # 执行通用的逻辑一致性检查
            consistency_result = checker.check_consistency(extracted_findings, birads_class)

            # 如果检测到不一致，更新结节结果
            if consistency_result["inconsistency"]:
                nodule["inconsistency_alert"] = True
                nodule["inconsistency_reasons"] = consistency_result["violations"]
                all_inconsistency_reasons.extend(consistency_result["violations"])

                # 更新风险评估（如果当前评估低于检查结果）
                current_risk = nodule.get("risk_assessment", "Low")
                checked_risk = consistency_result["risk_assessment"]

                # 风险等级：Low < Medium < High
                risk_levels = {"Low": 1, "Medium": 2, "High": 3}
                if risk_levels.get(checked_risk, 0) > risk_levels.get(current_risk, 0):
                    nodule["risk_assessment"] = checked_risk
                    logger.warning(
                        f"结节{nodule.get('id', 'unknown')}逻辑一致性检查发现不一致："
                        f"{consistency_result['violations']}，已提升风险评估为{checked_risk}"
                    )

                # 更新最高风险
                if risk_levels.get(checked_risk, 0) > risk_levels.get(highest_risk, 0):
                    highest_risk = checked_risk

        # 更新整体评估
        if nodules:
            result["overall_assessment"]["highest_risk"] = highest_risk
            if all_inconsistency_reasons:
                advice = result["overall_assessment"].get("advice", "")
                if "不一致" not in advice and "重新评估" not in advice:
                    result["overall_assessment"]["advice"] = (
                        f"{advice} "
                        f"⚠️ 注意：报告中描述的特征与BI-RADS分类存在不一致："
                        f"{'; '.join(set(all_inconsistency_reasons))}。"
                        f"建议重新评估或进一步检查。"
                    )

    except Exception as e:
        log_error_with_context(logger, e, context={"result": result}, operation="后处理逻辑一致性检查")
        # 检查失败不影响主流程，返回原结果

    return result


def _get_retriever() -> GraphRAGRetriever:
    """获取GraphRAG检索器实例（单例模式）"""
    global _retriever
    if _retriever is None:
        _retriever = GraphRAGRetriever()
        logger.info("GraphRAG检索器初始化完成")
    return _retriever


def analyze_text_with_deepseek(ocr_text: str) -> dict:
    """
    将 OCR 提取的生文本发送给 DeepSeek 进行医学逻辑分析

    流程：
    1. 使用GraphRAG检索相关知识
    2. 将检索结果作为上下文传递给LLM
    3. LLM基于专业知识进行分析
    """

    # 1. RAG检索：从知识图谱中检索相关知识
    rag_context = ""
    rag_start_time = time.time()
    rag_time = 0.0
    try:
        retriever = _get_retriever()
        retrieval_result = retriever.retrieve(ocr_text)
        rag_time = time.time() - rag_start_time

        if retrieval_result["entities"]:
            rag_context = "\n\n## 相关医学知识（来自RAG知识库）：\n\n"

            # 添加相关实体（减少数量，提高性能）
            rag_context += "### 相关医学概念和规则：\n"
            for entity in retrieval_result["entities"][:5]:  # 减少到5个实体
                entity_name = entity.get("name", "")
                entity_content = entity.get("content", "")
                if entity_name and entity_content:
                    # 减少内容长度，只取前150字符
                    rag_context += f"- **{entity_name}**：{entity_content[:150]}...\n"

            # 添加相关关系（推理路径，减少数量）
            if retrieval_result["inference_paths"]:
                rag_context += "\n### 逻辑推理路径：\n"
                for path in retrieval_result["inference_paths"][:3]:  # 减少到3条路径
                    rag_context += f"- {' → '.join(path)}\n"

            logger.info(
                f"RAG检索完成：{len(retrieval_result['entities'])} 个实体，"
                f"{len(retrieval_result['relations'])} 个关系，"
                f"置信度：{retrieval_result['confidence']:.2f}，"
                f"耗时：{rag_time:.2f}秒"
            )
        else:
            logger.warning(f"RAG检索未找到相关知识，耗时：{rag_time:.2f}秒")
    except Exception as e:
        rag_time = time.time() - rag_start_time
        log_error_with_context(logger, e, context={"ocr_text_length": len(ocr_text)}, operation="RAG检索")
        logger.warning(f"RAG检索失败，耗时：{rag_time:.2f}秒")
        # RAG检索失败不影响LLM分析，继续执行

    # 2. 定义 System Prompt (人设与规则)
    # 版本1.1.0：支持多个结节识别和分离
    system_prompt = (
        """你是MedCrux医学影像分析助手，基于OCR文本进行事实核查。

重要：请识别报告中的所有结节，为每个结节提取完整信息。

步骤：
1. **识别所有结节**：
   - 仔细阅读报告，识别所有提到的结节
   - 为每个结节分配唯一ID（nodule_1, nodule_2等）
   - 如果报告中没有明确提到结节，返回空列表

2. **提取每个结节的信息**：
   a. **位置信息**（必须提取并标准化）：
      - breast：左乳/右乳（必须，输出"left"或"right"）
      - clock_position：钟点位置（必须，优先使用）
        * 如果报告中明确提到钟点方向（如"3点"、"12点"），直接使用
        * 如果报告中只提到象限（如"外下"、"上内"），**必须根据左右乳房进行镜像转换，统一使用4个固定钟点（1、11、5、7）**：
          - **左乳**：
            - "外上" → "11点"（左乳上外象限，固定使用11点）
            - "外下" → "7点"（左乳下外象限，固定使用7点）
            - "内上" → "1点"（左乳上内象限，固定使用1点）
            - "内下" → "5点"（左乳下内象限，固定使用5点）
          - **右乳**：
            - "外上" → "1点"（右乳上外象限，固定使用1点，镜像）
            - "外下" → "5点"（右乳下外象限，固定使用5点，镜像）
            - "内上" → "11点"（右乳上内象限，固定使用11点，镜像）
            - "内下" → "7点"（右乳下内象限，固定使用7点，镜像）
          - **通用**（左右乳房相同）：
            - "上方" → "12点"
            - "下方" → "6点"
            - "乳头旁"/"乳晕区" → "12点"
        * **重要**：象限转换时，统一只使用4个固定钟点（1、11、5、7），不要使用10点、2点、4点、9点等其他钟点
        * 输出格式：必须是"X点"（如"3点"、"11点"），不能是"3点钟"或"3点钟方向"
      - quadrant：象限（可选，如果报告只提到象限）
        * 如果已转换为钟点方向，可以省略
        * 如果报告只提到象限，保留象限信息
      - distance_from_nipple：距乳头距离（必须，如果有提到距离）
        * 单位必须统一为cm
        * 如果报告中是mm，转换为cm（除以10，如"27mm" → "2.7"）
        * 如果单位不明确，根据数值大小判断（>10可能是mm，<10可能是cm）
        * 输出格式：数值（如"2.5"），不带单位

   b. **形态学特征**（必须提取）：
      - shape：形状（椭圆形/圆形/不规则形/条状/条索状/其他）
      - boundary：边界（清晰/大部分清晰/模糊/成角/微小分叶/毛刺状）
      - echo：回声（均匀低回声/不均匀回声/无回声/等回声/高回声/复合回声）
      - orientation：方位（平行/不平行）
      - size：大小（格式：长径×横径×前后径 cm，如"1.2×0.8×0.6 cm"）

   c. **其他信息**：
      - malignant_signs：恶性征象列表（如有）
      - birads_class：BI-RADS分级
      - risk_assessment：风险评估（Low/Medium/High）

3. **术语标准化**：
   - 标准术语：形状{椭圆形,圆形,不规则形} 边界{清晰,大部分清晰,模糊,成角,微小分叶,毛刺状}
     回声{均匀低回声,不均匀回声,无回声,等回声,高回声,复合回声} 方位{平行,不平行}
   - 同义词处理："清楚"→"清晰" "circumscribed"→"清晰" "低回声"（未明确"均匀"）保持为"低回声"
   - 非标准术语：保持原样输出（如"条状"保持为"条状"，不标准化为"椭圆形"）

4. **逻辑一致性检查**：
   - 对照BI-RADS分类充要条件检查每个结节的特征
   - 不符合充要条件必须识别为不一致
   - 示例（BI-RADS 3类）：形状椭圆形、边界清晰/大部分清晰、回声均匀低回声（"低回声"≠"均匀低回声"）、方位平行、无恶性征象

5. **整体评估**：
   - total_nodules：结节总数
   - highest_risk：所有结节中的最高风险等级
   - summary：整体评估摘要
   - advice：综合建议

返回JSON（无markdown）：
{
    "patient_gender": "Unknown/Female/Male",
    "nodules": [
        {
            "id": "nodule_1",
            "location": {
                "breast": "left/right",
                "clock_position": "X点",  // 必须，标准钟点方向（象限转换统一使用1、11、5、7点，明确钟点方向直接使用）
                "quadrant": "上内/上外/下内/下外/中央区",  // 可选
                "distance_from_nipple": "X.X"  // 必须（如果有提到距离），数值格式，单位cm
            },
            "morphology": {
                "shape": "椭圆形/圆形/不规则形/条状/条索状/其他",
                "boundary": "清晰/大部分清晰/模糊/成角/微小分叶/毛刺状",
                "echo": "均匀低回声/不均匀回声/无回声/等回声/高回声/复合回声",
                "orientation": "平行/不平行",
                "size": "长径×横径×前后径 cm"
            },
            "malignant_signs": ["恶性征象1", "恶性征象2"],
            "birads_class": "3",
            "risk_assessment": "Low/Medium/High",
            "inconsistency_alert": true/false,
            "inconsistency_reasons": ["原因1", "原因2"]
        }
    ],
    "overall_assessment": {
        "total_nodules": 1,
        "highest_risk": "Low/Medium/High",
        "summary": "整体评估摘要",
        "advice": "综合建议"
    }
}

要求：
- 必须识别所有结节，不能遗漏
- 必须提取每个结节的位置信息（如果报告中提到）
- **位置信息必须标准化**：
  - 象限转换时，统一只使用4个固定钟点（1、11、5、7），不要使用10点、2点、4点、9点等其他钟点
  - 距离单位必须统一为cm，mm需要转换为cm（除以10）
  - clock_position输出格式必须是"X点"（如"11点"、"1点"），不能是"X点钟"或"X点钟方向"
  - distance_from_nipple输出格式必须是数值（如"2.7"），不带单位
- 必须提取所有形态学特征和BI-RADS分类
- 如检测到不一致，必须在inconsistency_reasons中说明原因
- 如果报告中没有结节，返回空列表：{"nodules": [], "overall_assessment": {"total_nodules": 0, ...}}

**位置信息提取示例**：

示例1：原文"在左侧乳腺3点钟方向距乳头约1.9cm处"
→ {"breast": "left", "clock_position": "3点", "distance_from_nipple": "1.9"}

示例2：原文"在右侧乳腺外下象限距乳头约2.7cm处"
→ {"breast": "right", "clock_position": "5点", "quadrant": "下外", "distance_from_nipple": "2.7"}

示例3：原文"在左侧乳腺外上象限距乳头约2.0cm处"
→ {"breast": "left", "clock_position": "11点", "quadrant": "上外", "distance_from_nipple": "2.0"}

示例4：原文"在右侧乳腺外上象限距乳头约2.0cm处"
→ {"breast": "right", "clock_position": "1点", "quadrant": "上外", "distance_from_nipple": "2.0"}

示例5：原文"在左侧乳腺外下象限距乳头约27mm处"
→ {"breast": "left", "clock_position": "7点", "distance_from_nipple": "2.7"}"""
        + rag_context
    )

    # 3. 调用 API
    context = {"ocr_text_length": len(ocr_text)}
    logger.debug(f"开始调用DeepSeek API [文本长度: {len(ocr_text)}]")

    llm_start_time = time.time()
    try:
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY未设置")

        response = client.chat.completions.create(
            model="deepseek-chat",  # 使用 DeepSeek V3
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"这是 OCR 识别出的医学报告文本，请分析：\n\n{ocr_text}",
                },
            ],
            temperature=0.1,  # 医学分析需要严谨，温度设低
            stream=False,
            response_format={"type": "json_object"},  # 强制返回 JSON (DeepSeek 支持)
        )

        llm_api_time = time.time() - llm_start_time
        logger.debug(f"DeepSeek API调用成功，耗时：{llm_api_time:.2f}秒")

        # 3. 解析结果
        content = response.choices[0].message.content
        result = json.loads(content)

        # 4. 格式转换：确保是新格式（如果LLM返回旧格式，转换为新格式）
        result = _convert_old_format_to_new(result)

        # 5. 后处理：逻辑一致性检查（如果LLM没有正确执行）
        post_process_start = time.time()
        result = _post_process_consistency_check(result, ocr_text)
        post_process_time = time.time() - post_process_start

        total_llm_time = time.time() - llm_start_time
        nodules_count = len(result.get("nodules", []))
        highest_risk = result.get("overall_assessment", {}).get("highest_risk", "Unknown")
        has_inconsistency = any(n.get("inconsistency_alert", False) for n in result.get("nodules", []))
        logger.info(
            f"AI分析完成 [结节数: {nodules_count}, 最高风险: {highest_risk}, "
            f"不一致预警: {has_inconsistency}, "
            f"总耗时: {total_llm_time:.2f}秒 (API: {llm_api_time:.2f}秒, 后处理: {post_process_time:.2f}秒)]"
        )
        return result

    except json.JSONDecodeError as e:
        log_error_with_context(logger, e, context=context, operation="AI分析结果解析")
        return {
            "ai_risk_assessment": "Error",
            "advice": "AI分析结果解析失败，请稍后重试。",
            "details": str(e),
        }
    except Exception as e:
        log_error_with_context(logger, e, context=context, operation="DeepSeek API调用")
        # 返回一个兜底的错误结构
        return {
            "ai_risk_assessment": "Error",
            "advice": "无法连接 AI 大脑进行分析，请检查网络或 Key 配置。",
            "details": str(e),
        }


def analyze_birads_independently(factual_text: str) -> dict:
    """
    基于事实性描述（检查所见）独立判断BI-RADS分类
    
    Args:
        factual_text: 仅事实性描述（检查所见），不包含影像学诊断和建议
    
    Returns:
        {
            "nodules": [
                {
                    "id": "nodule_1",
                    "location": {...},
                    "morphology": {...},
                    "llm_birads_class": "4",
                    "llm_birads_reasoning": "判断理由"
                }
            ],
            "llm_highest_birads": "4"
        }
    
    重要规则：
    1. 只基于事实性描述（检查所见）判断，不要参考任何结论性内容
    2. 必须识别所有异常发现，为每个异常发现提取完整信息
    3. 基于公理体系、知识图谱和形态学特征独立判断BI-RADS分类
    4. 必须提供判断理由
    """
    if not factual_text or len(factual_text.strip()) < 10:
        logger.warning("事实性描述文本为空或过短")
        return {
            "nodules": [],
            "llm_highest_birads": None,
        }

    # 1. RAG检索：从知识图谱中检索相关知识
    rag_context = ""
    rag_start_time = time.time()
    try:
        retriever = _get_retriever()
        retrieval_result = retriever.retrieve(factual_text)
        rag_time = time.time() - rag_start_time

        if retrieval_result["entities"]:
            rag_context = "\n\n## 相关医学知识（来自RAG知识库）：\n\n"
            rag_context += "### 相关医学概念和规则：\n"
            for entity in retrieval_result["entities"][:5]:
                entity_name = entity.get("name", "")
                entity_content = entity.get("content", "")
                if entity_name and entity_content:
                    rag_context += f"- **{entity_name}**：{entity_content[:150]}...\n"

            if retrieval_result["inference_paths"]:
                rag_context += "\n### 逻辑推理路径：\n"
                for path in retrieval_result["inference_paths"][:3]:
                    rag_context += f"- {' → '.join(path)}\n"

            logger.info(f"RAG检索完成：{len(retrieval_result['entities'])} 个实体，耗时：{rag_time:.2f}秒")
        else:
            logger.warning(f"RAG检索未找到相关知识，耗时：{rag_time:.2f}秒")
    except Exception as e:
        rag_time = time.time() - rag_start_time
        log_error_with_context(logger, e, context={"factual_text_length": len(factual_text)}, operation="RAG检索")
        logger.warning(f"RAG检索失败，耗时：{rag_time:.2f}秒，继续执行LLM分析")

    # 2. 构建System Prompt
    system_prompt = (
        """你是MedCrux医学影像分析助手，基于事实性描述（检查所见）识别异常发现并独立判断BI-RADS分类。

重要规则：
1. **只基于事实性描述（检查所见）判断**，不要参考任何结论性内容（如影像学诊断、建议等）
2. **必须识别所有异常发现**，为每个异常发现提取完整信息（位置、形态学特征）
3. **基于公理体系、知识图谱和形态学特征独立判断BI-RADS分类**
4. **必须提供判断理由**，说明为什么判断为该BI-RADS分类

步骤：
1. **识别所有异常发现**：
   - 仔细阅读事实性描述，识别所有提到的异常发现
   - 为每个异常发现分配唯一ID（nodule_1, nodule_2等）

2. **提取每个异常发现的信息**：
   - 位置信息（breast、clock_position、distance_from_nipple等）
   - 形态学特征（shape、boundary、echo、orientation、size等）

3. **独立判断BI-RADS分类**：
   - 基于形态学特征、公理体系、知识图谱独立判断BI-RADS分类
   - 不要参考原报告的BI-RADS分类
   - 必须提供判断理由（llm_birads_reasoning）

4. **提取最高BI-RADS分类**：
   - 从所有异常发现中提取最高BI-RADS分类

返回JSON格式（无markdown）：
{
    "nodules": [
        {
            "id": "nodule_1",
            "location": {
                "breast": "left/right",
                "clock_position": "X点",
                "distance_from_nipple": "X.X"
            },
            "morphology": {
                "shape": "椭圆形/圆形/不规则形",
                "boundary": "清晰/大部分清晰/模糊/成角/微小分叶/毛刺状",
                "echo": "均匀低回声/不均匀回声/无回声/等回声/高回声/复合回声",
                "orientation": "平行/不平行",
                "size": "长径×横径×前后径 cm"
            },
            "llm_birads_class": "3",
            "llm_birads_reasoning": "基于形态学特征（椭圆形、边界清晰、均匀低回声、平行方位）判断为3类"
        }
    ],
    "llm_highest_birads": "3"
}

要求：
- 必须识别所有异常发现，不能遗漏
- 必须为每个异常发现提供BI-RADS分类和判断理由
- 判断理由必须基于形态学特征和公理体系
- 如果报告中没有异常发现，返回空列表：{"nodules": [], "llm_highest_birads": null}"""
        + rag_context
    )

    # 3. 调用 API
    context = {"factual_text_length": len(factual_text)}
    logger.debug(f"开始调用DeepSeek API进行独立BI-RADS判断 [文本长度: {len(factual_text)}]")

    llm_start_time = time.time()
    try:
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY未设置")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"这是检查所见（事实性描述），请识别所有异常发现并独立判断BI-RADS分类：\n\n{factual_text}",
                },
            ],
            temperature=0.1,
            stream=False,
            response_format={"type": "json_object"},
        )

        llm_api_time = time.time() - llm_start_time
        logger.debug(f"DeepSeek API调用成功，耗时：{llm_api_time:.2f}秒")

        # 4. 解析结果
        content = response.choices[0].message.content
        result = json.loads(content)

        # 4.1 规范化结节ID，确保唯一且连续（nodule_1, nodule_2, ...）
        nodules = result.get("nodules", []) or []
        seen_ids: set[str] = set()
        for idx, nodule in enumerate(nodules):
            original_id = str(nodule.get("id") or "").strip() or f"nodule_{idx + 1}"
            # 如果LLM给出的id重复或为空，则重新分配一个规范id
            if original_id in seen_ids:
                new_id = f"nodule_{idx + 1}"
                logger.warning(
                    f"独立BI-RADS判断返回的结节ID重复或无效：{original_id}，已重命名为 {new_id}"
                )
                nodule["id"] = new_id
                seen_ids.add(new_id)
            else:
                nodule["id"] = original_id
                seen_ids.add(original_id)

        result["nodules"] = nodules

        # 5. 提取最高BI-RADS分类
        llm_highest_birads = result.get("llm_highest_birads")
        
        # 如果没有提供llm_highest_birads，从nodules中提取
        if not llm_highest_birads and nodules:
            birads_classes = []
            for nodule in nodules:
                birads_class = nodule.get("llm_birads_class")
                if birads_class:
                    try:
                        # 提取数字部分
                        birads_num = int(re.match(r"\d+", birads_class).group())
                        birads_classes.append((birads_num, birads_class))
                    except (ValueError, AttributeError):
                        pass
            
            if birads_classes:
                llm_highest_birads = max(birads_classes, key=lambda x: x[0])[1]
                result["llm_highest_birads"] = llm_highest_birads

        total_time = time.time() - llm_start_time
        nodules_count = len(nodules)
        logger.info(
            f"独立BI-RADS判断完成 [异常发现数: {nodules_count}, "
            f"最高BI-RADS: {llm_highest_birads}, 总耗时: {total_time:.2f}秒]"
        )
        
        return result

    except json.JSONDecodeError as e:
        log_error_with_context(logger, e, context=context, operation="独立BI-RADS判断结果解析")
        return {
            "nodules": [],
            "llm_highest_birads": None,
            "error": "AI分析结果解析失败",
        }
    except Exception as e:
        log_error_with_context(logger, e, context=context, operation="DeepSeek API调用（独立BI-RADS判断）")
        return {
            "nodules": [],
            "llm_highest_birads": None,
            "error": f"无法连接 AI 进行分析：{str(e)}",
        }


def check_consistency_sets(original_birads_set: set, llm_birads_set: set) -> dict:
    """
    检查报告分类结果和AI分类结果的一致性
    
    Args:
        original_birads_set: 原报告的BI-RADS分类集合（例如：{"2", "3"}）
        llm_birads_set: AI判断的BI-RADS分类集合（例如：{"2", "3", "4"}）
    
    Returns:
        {
            "consistent": bool,  # 是否一致
            "report_birads_set": set,  # 原报告的BI-RADS分类集合
            "ai_birads_set": set,  # AI判断的BI-RADS分类集合
            "missing_in_ai": set,  # AI缺少的分类
            "extra_in_ai": set,  # AI额外的分类
            "description": str  # 一致性说明
        }
    
    逻辑：
    - 如果报告说有3类和2类（但没有注明有几个），而AI的分类结果也有3类和2类，就算"一致的"
    - 如果AI的分类结果包含报告中的所有分类，且没有额外的更高风险分类，也算"一致的"
    - 如果AI的分类结果缺少报告中的某些分类，或包含报告中没有的更高风险分类，则算"不一致的"
    """
    if not original_birads_set and not llm_birads_set:
        return {
            "consistent": True,
            "report_birads_set": set(),
            "ai_birads_set": set(),
            "missing_in_ai": set(),
            "extra_in_ai": set(),
            "description": "报告和AI都没有BI-RADS分类",
        }

    if not original_birads_set:
        return {
            "consistent": False,
            "report_birads_set": set(),
            "ai_birads_set": llm_birads_set,
            "missing_in_ai": set(),
            "extra_in_ai": llm_birads_set,
            "description": f"报告没有BI-RADS分类，AI判断有：{sorted(llm_birads_set)}",
        }

    if not llm_birads_set:
        return {
            "consistent": False,
            "report_birads_set": original_birads_set,
            "ai_birads_set": set(),
            "missing_in_ai": original_birads_set,
            "extra_in_ai": set(),
            "description": f"报告有BI-RADS分类：{sorted(original_birads_set)}，AI没有判断",
        }

    # 计算差异
    missing_in_ai = original_birads_set - llm_birads_set  # AI缺少的分类
    extra_in_ai = llm_birads_set - original_birads_set  # AI额外的分类

    # 判断是否一致
    if not missing_in_ai and not extra_in_ai:
        # 完全一致
        consistent = True
        description = f"报告和AI的分类结果完全一致：{sorted(original_birads_set)}"
    elif not missing_in_ai and extra_in_ai:
        # AI有额外的分类，需要判断是否是更高风险
        # 如果AI额外的分类都是更高风险（数字更大），则不一致
        original_max = max(int(re.match(r"\d+", x).group()) for x in original_birads_set)
        extra_max = max(int(re.match(r"\d+", x).group()) for x in extra_in_ai)
        if extra_max > original_max:
            consistent = False
            description = f"AI分类结果包含报告中没有的更高风险分类：{sorted(extra_in_ai)}"
        else:
            consistent = True
            description = f"AI分类结果包含报告中的所有分类，且额外分类风险不更高：{sorted(extra_in_ai)}"
    else:
        # AI缺少某些分类，或既有缺少又有额外
        consistent = False
        parts = []
        if missing_in_ai:
            parts.append(f"AI缺少报告中的分类：{sorted(missing_in_ai)}")
        if extra_in_ai:
            parts.append(f"AI包含报告中没有的分类：{sorted(extra_in_ai)}")
        description = "；".join(parts)

    return {
        "consistent": consistent,
        "report_birads_set": original_birads_set,
        "ai_birads_set": llm_birads_set,
        "missing_in_ai": missing_in_ai,
        "extra_in_ai": extra_in_ai,
        "description": description,
    }


def calculate_urgency_level(doctor_highest_birads: str, llm_highest_birads: str) -> dict:
    """
    计算评估紧急程度
    
    Args:
        doctor_highest_birads: 医生给出的最高BI-RADS分类（例如："3"）
        llm_highest_birads: LLM判断的最高BI-RADS分类（例如："4"）
    
    Returns:
        {
            "urgency_level": str,  # Low / Medium / High
            "reason": str,  # 评估理由
            "doctor_highest_birads": str,  # 医生最高BI-RADS
            "llm_highest_birads": str,  # LLM最高BI-RADS
            "comparison": str  # llm_exceeds / llm_equal_or_lower
        }
    
    逻辑：
    - 如果LLM判断的最高BI-RADS分类 > 医生给出的最高BI-RADS分类：
      - 如果LLM判断的最高BI-RADS分类 >= 4类：High
      - 否则：Medium
    - 否则：Low
    """
    if not doctor_highest_birads or not llm_highest_birads:
        return {
            "urgency_level": "Low",
            "reason": "无法比较：医生或AI的最高BI-RADS分类为空",
            "doctor_highest_birads": doctor_highest_birads or "Unknown",
            "llm_highest_birads": llm_highest_birads or "Unknown",
            "comparison": "unknown",
        }

    try:
        # 提取数字部分进行比较（忽略字母后缀如4A、4B等）
        doctor_birads_int = int(re.match(r"\d+", doctor_highest_birads).group())
        llm_birads_int = int(re.match(r"\d+", llm_highest_birads).group())
    except (ValueError, AttributeError) as e:
        logger.error(f"解析BI-RADS分类失败: doctor={doctor_highest_birads}, llm={llm_highest_birads}, error={e}")
        return {
            "urgency_level": "Low",
            "reason": f"无法解析BI-RADS分类：{str(e)}",
            "doctor_highest_birads": doctor_highest_birads,
            "llm_highest_birads": llm_highest_birads,
            "comparison": "unknown",
        }

    if llm_birads_int > doctor_birads_int:
        comparison = "llm_exceeds"
        if llm_birads_int >= 4:
            urgency_level = "High"
            reason = (
                f"LLM判断的最高BI-RADS分类（{llm_highest_birads}类）超过医生给出的最高BI-RADS分类（{doctor_highest_birads}类），"
                f"且LLM判断的最高BI-RADS分类 >= 4类，评估紧急程度为High"
            )
        else:
            urgency_level = "Medium"
            reason = (
                f"LLM判断的最高BI-RADS分类（{llm_highest_birads}类）超过医生给出的最高BI-RADS分类（{doctor_highest_birads}类），"
                f"但LLM判断的最高BI-RADS分类 < 4类，评估紧急程度为Medium"
            )
    else:
        comparison = "llm_equal_or_lower"
        urgency_level = "Low"
        reason = (
            f"LLM判断的最高BI-RADS分类（{llm_highest_birads}类）不超过医生给出的最高BI-RADS分类（{doctor_highest_birads}类），"
            f"评估紧急程度为Low"
        )

    return {
        "urgency_level": urgency_level,
        "reason": reason,
        "doctor_highest_birads": doctor_highest_birads,
        "llm_highest_birads": llm_highest_birads,
        "comparison": comparison,
    }


if __name__ == "__main__":
    # 测试代码
    sample_text = "超声描述：左乳上方可见低回声结节，大小1.2x0.8cm，边界不清，边缘呈毛刺状。\
    CDFI：内见点状血流信号。 提示：BI-RADS 3类。"
    print(analyze_text_with_deepseek(sample_text))
