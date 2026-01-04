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

from openai import OpenAI

from medcrux.rag.graphrag_retriever import GraphRAGRetriever
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
    后处理：逻辑一致性检查（如果LLM没有正确执行）

    基于公理8，检查提取的事实是否符合BI-RADS分类的充要条件
    """
    # 标准术语集合（基于公理5.3）
    STANDARD_SHAPES = {"椭圆形", "圆形", "不规则形", "oval", "round", "irregular"}

    # 提取关键信息
    extracted_shape = result.get("extracted_shape", "").lower()
    birads_class = result.get("birads_class", "")
    inconsistency_reasons = result.get("inconsistency_reasons", [])

    # 检查BI-RADS 3类的一致性
    if birads_class == "3":
        # 检查形状是否符合3类定义（要求椭圆形）
        if extracted_shape:
            # 检查是否包含"椭圆"
            is_oval = "椭圆" in extracted_shape or "oval" in extracted_shape
            # 检查是否包含非标准术语（如"条状"、"条索"等）
            is_non_standard = any(
                keyword in extracted_shape for keyword in ["条状", "条索", "条", "linear", "ductal", "striped"]
            )

            # 如果形状不在标准集合中，且不是椭圆形，则不一致
            if is_non_standard or (extracted_shape not in STANDARD_SHAPES and not is_oval):
                if not result.get("inconsistency_alert", False):
                    result["inconsistency_alert"] = True
                    inconsistency_reasons.append(
                        f"形状描述为'{result.get('extracted_shape', '未知')}'，" f"不符合BI-RADS 3类要求的椭圆形"
                    )

                # 如果风险评估不是High，且涉及非标准形状，提升为中风险
                if result.get("ai_risk_assessment") == "Low":
                    result["ai_risk_assessment"] = "Medium"
                    logger.warning(
                        f"检测到形状不一致：{result.get('extracted_shape')} + BI-RADS 3类，" f"已提升风险评估为Medium"
                    )

    # 更新不一致原因列表
    if inconsistency_reasons:
        result["inconsistency_reasons"] = inconsistency_reasons
        # 如果不一致但建议中没有提到，补充建议
        advice = result.get("advice", "")
        if "不一致" not in advice and "重新评估" not in advice:
            result["advice"] = (
                f"{advice} " f"⚠️ 注意：报告中描述的特征与BI-RADS分类存在不一致，" f"建议重新评估或进一步检查。"
            )

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
    try:
        retriever = _get_retriever()
        retrieval_result = retriever.retrieve(ocr_text)

        if retrieval_result["entities"]:
            rag_context = "\n\n## 相关医学知识（来自RAG知识库）：\n\n"

            # 添加相关实体
            rag_context += "### 相关医学概念和规则：\n"
            for entity in retrieval_result["entities"][:10]:  # 最多10个实体
                entity_name = entity.get("name", "")
                entity_content = entity.get("content", "")
                if entity_name and entity_content:
                    rag_context += f"- **{entity_name}**：{entity_content[:200]}...\n"

            # 添加相关关系（推理路径）
            if retrieval_result["inference_paths"]:
                rag_context += "\n### 逻辑推理路径：\n"
                for path in retrieval_result["inference_paths"][:5]:  # 最多5条路径
                    rag_context += f"- {' → '.join(path)}\n"

            logger.info(
                f"RAG检索完成：{len(retrieval_result['entities'])} 个实体，"
                f"{len(retrieval_result['relations'])} 个关系，"
                f"置信度：{retrieval_result['confidence']:.2f}"
            )
        else:
            logger.warning("RAG检索未找到相关知识")
    except Exception as e:
        log_error_with_context(logger, e, context={"ocr_text_length": len(ocr_text)}, operation="RAG检索")
        # RAG检索失败不影响LLM分析，继续执行

    # 2. 定义 System Prompt (人设与规则)
    # 这是 MedCrux 的核心灵魂：基于事实，第一性原理
    system_prompt = (
        """
    你是一个名为 MedCrux 的专业医学影像分析助手。你的核心任务是基于 OCR 提取的文本进行"事实核查"。

    请遵循以下步骤：
    1. **提取事实**：从混乱的 OCR 文本中提取关于病灶的形态学描述（大小、形状、边缘、回声、纵横比、血流、钙化等）。
       - **重要**：必须提取形状描述，即使是非标准术语（如"条状"、"条索状"等）也要提取。
       - **重要**：必须提取边界、回声、方位等所有形态学特征。

    2. **提取结论**：提取报告中原本的 BI-RADS 分级结论。

    3. **术语标准化检查**（基于公理5）：
       - 检查提取的形状是否在标准术语集合中：{椭圆形, 圆形, 不规则形}
       - 如果不在标准集合中（如"条状"、"条索状"等），标记为非标准术语
       - **非标准术语 ≠ 椭圆形**，如果BI-RADS分类要求椭圆形，则不一致

    4. **逻辑一致性检查**（关键步骤，基于公理8）：
       对照BI-RADS分类的充要条件（公理3），检查提取的事实是否满足该充要条件。

       **通用检查逻辑**（不针对任何特定特征）：
       - 将提取的形态学特征与公理3中该BI-RADS分类的充要条件进行对照
       - 如果提取的特征不符合该分类的充要条件，**必须**识别为不一致
       - 系统会自动检查形状、边界、回声、方位、恶性征象等所有特征

       **示例（BI-RADS 3类的充要条件）**：
       - 形状：椭圆形（oval）
       - 边界：清晰或大部分清晰（circumscribed或mostly circumscribed）
       - 回声：均匀低回声（homogeneous hypoechoic）
       - 方位：平行（parallel，纵横比<1）
       - 无恶性征象

       **重要**：系统会自动检查任何不符合充要条件的情况，无论具体特征是什么。

    5. **评估不一致严重程度**：
       - **高风险**：提取到恶性征象但分类为2类或3类，或提取的特征明显违反分类定义且提示恶性可能
       - **中风险**：提取的特征不符合分类定义（如形状不是椭圆形），但不涉及明确的恶性征象
       - **低风险**：提取的特征与分类定义存在轻微不符

    请以纯 JSON 格式返回结果，不要包含 markdown 格式标记。JSON 结构如下：
    {
        "patient_gender": "Unknown/Female/Male",
        "extracted_findings": ["描述1", "描述2"],
        "original_conclusion": "报告原本的结论",
        "ai_risk_assessment": "Low/Medium/High",
        "inconsistency_alert": true/false, (如果描述与结论不符则为 true)
        "advice": "给患者的建议"
    }
    """
        + rag_context
    )

    # 3. 调用 API
    context = {"ocr_text_length": len(ocr_text)}
    logger.debug(f"开始调用DeepSeek API [文本长度: {len(ocr_text)}]")

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

        logger.debug("DeepSeek API调用成功")

        # 3. 解析结果
        content = response.choices[0].message.content
        result = json.loads(content)

        # 4. 后处理：逻辑一致性检查（如果LLM没有正确执行）
        result = _post_process_consistency_check(result, ocr_text)

        logger.info(
            f"AI分析完成 [风险评估: {result.get('ai_risk_assessment', 'Unknown')}, "
            f"不一致预警: {result.get('inconsistency_alert', False)}]"
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
