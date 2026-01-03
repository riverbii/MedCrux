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
    1. **提取事实**：从混乱的 OCR 文本中提取关于病灶的形态学描述（大小、边缘、回声、纵横比、血流、钙化等）。
    2. **提取结论**：提取报告中原本的 BI-RADS 分级结论。
    3. **逻辑校验**：(关键步骤) 对照 ACR BI-RADS 标准，检查"描述"与"结论"是否一致。

    **⚠️ 重要：恶性征象识别**
    以下征象单独或组合出现时，高度提示恶性（必须仔细识别）：
    - 毛刺状边界（毛刺、毛刺状、spiculated）
    - 不平行方位（纵横比>1、垂直生长）
    - 微钙化（微小钙化）
    - 声影（后方回声衰减）
    - 不规则形状 + 不清晰边界
    - **条状低回声（条索状、条索样）** ⚠️ 重要恶性征象，必须识别！

    **关键规则**：
    - 如果描述中出现**任何**上述恶性征象，但结论是 BI-RADS 3类或更低，
      **必须**发出高风险预警（inconsistency_alert: true）
    - 风险评估应设为 High（如果出现恶性征象但结论是3类）
    - 建议中应明确提示需要进一步检查或活检

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

        logger.info(f"AI分析完成 [风险评估: {result.get('ai_risk_assessment', 'Unknown')}]")
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
