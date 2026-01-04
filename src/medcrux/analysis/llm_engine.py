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


def _post_process_consistency_check(result: dict, ocr_text: str) -> dict:
    """
    后处理：通用的逻辑一致性检查（基于公理8）

    使用LogicalConsistencyChecker进行通用的充要条件验证，
    不针对任何特定形态学特征写规则。
    """
    try:
        # 初始化逻辑一致性检查器
        checker = LogicalConsistencyChecker()

        # 提取关键信息
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

        extracted_findings = {
            "shape": extract_primary_value(result.get("extracted_shape", "")),
            "boundary": extract_primary_value(result.get("extracted_boundary", "")),
            "echo": extract_primary_value(result.get("extracted_echo", "")),
            "orientation": extract_primary_value(result.get("extracted_orientation", "")),
            "aspect_ratio": result.get("extracted_aspect_ratio"),
            "malignant_signs": result.get("extracted_malignant_signs", []),
        }
        birads_class = result.get("birads_class", "")

        # 如果BI-RADS分类为空，无法检查
        if not birads_class:
            return result

        # 执行通用的逻辑一致性检查
        consistency_result = checker.check_consistency(extracted_findings, birads_class)

        # 如果检测到不一致，更新结果
        if consistency_result["inconsistency"]:
            result["inconsistency_alert"] = True
            result["inconsistency_reasons"] = consistency_result["violations"]

            # 更新风险评估（如果当前评估低于检查结果）
            current_risk = result.get("ai_risk_assessment", "Low")
            checked_risk = consistency_result["risk_assessment"]

            # 风险等级：Low < Medium < High
            risk_levels = {"Low": 1, "Medium": 2, "High": 3}
            if risk_levels.get(checked_risk, 0) > risk_levels.get(current_risk, 0):
                result["ai_risk_assessment"] = checked_risk
                logger.warning(
                    f"逻辑一致性检查发现不一致：{consistency_result['violations']}，" f"已提升风险评估为{checked_risk}"
                )

            # 如果不一致但建议中没有提到，补充建议
            advice = result.get("advice", "")
            if "不一致" not in advice and "重新评估" not in advice:
                result["advice"] = (
                    f"{advice} "
                    f"⚠️ 注意：报告中描述的特征与BI-RADS分类存在不一致："
                    f"{'; '.join(consistency_result['violations'])}。"
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
    # 优化：精简prompt长度，保持功能完整性
    system_prompt = (
        """你是MedCrux医学影像分析助手，基于OCR文本进行事实核查。

步骤：
1. **提取事实**：提取形态学描述（大小、形状、边缘、回声、纵横比、血流、钙化等）。
   - 必须提取形状（包括非标准术语如"条状"、"条索状"）
   - 必须提取边界、回声、方位等所有特征

2. **术语标准化**：
   - 标准术语：形状{椭圆形,圆形,不规则形} 边界{清晰,大部分清晰,模糊,成角,微小分叶,毛刺状}
     回声{均匀低回声,不均匀回声,无回声,等回声,高回声,复合回声} 方位{平行,不平行}
   - 同义词处理："清楚"→"清晰" "circumscribed"→"清晰" "低回声"（未明确"均匀"）保持为"低回声"
   - 非标准术语：保持原样输出（如"条状"保持为"条状"，不标准化为"椭圆形"）

3. **提取结论**：提取BI-RADS分级

4. **逻辑一致性检查**：
   - 对照BI-RADS分类充要条件检查提取特征
   - 不符合充要条件必须识别为不一致
   - 示例（BI-RADS 3类）：形状椭圆形、边界清晰/大部分清晰、回声均匀低回声（"低回声"≠"均匀低回声"）、方位平行、无恶性征象

5. **评估风险**：高风险（恶性征象+2/3类）、中风险（特征不符但不涉及恶性）、低风险（轻微不符）

返回JSON（无markdown）：
{
    "patient_gender": "Unknown/Female/Male",
    "extracted_findings": ["描述1", "描述2"],
    "extracted_shape": "椭圆形/圆形/不规则形/条状/条索状/其他",
    "extracted_boundary": "清晰/不清晰/模糊/成角/毛刺状/其他",
    "extracted_echo": "均匀低回声/不均匀回声/其他",
    "extracted_orientation": "平行/不平行/其他",
    "extracted_malignant_signs": ["恶性征象1", "恶性征象2"],
    "original_conclusion": "报告原本的结论",
    "birads_class": "3",
    "ai_risk_assessment": "Low/Medium/High",
    "inconsistency_alert": true/false,
    "inconsistency_reasons": ["原因1", "原因2"],
    "advice": "给患者的建议"
}

要求：必须提取所有形态学特征和BI-RADS分类；如检测到不一致，必须在inconsistency_reasons中说明原因。"""
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

        # 4. 后处理：逻辑一致性检查（如果LLM没有正确执行）
        post_process_start = time.time()
        result = _post_process_consistency_check(result, ocr_text)
        post_process_time = time.time() - post_process_start

        total_llm_time = time.time() - llm_start_time
        logger.info(
            f"AI分析完成 [风险评估: {result.get('ai_risk_assessment', 'Unknown')}, "
            f"不一致预警: {result.get('inconsistency_alert', False)}, "
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


if __name__ == "__main__":
    # 测试代码
    sample_text = "超声描述：左乳上方可见低回声结节，大小1.2x0.8cm，边界不清，边缘呈毛刺状。\
    CDFI：内见点状血流信号。 提示：BI-RADS 3类。"
    print(analyze_text_with_deepseek(sample_text))
