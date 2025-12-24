import json
import os

from openai import OpenAI

# 初始化客户端 (DeepSeek 兼容 OpenAI SDK)
# 建议将 API KEY 放入环境变量，或者在此处临时硬编码测试
# export DEEPSEEK_API_KEY="sk-..."
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")


def analyze_text_with_deepseek(ocr_text: str) -> dict:
    """
    将 OCR 提取的生文本发送给 DeepSeek 进行医学逻辑分析
    """

    # 1. 定义 System Prompt (人设与规则)
    # 这是 MedCrux 的核心灵魂：基于事实，第一性原理
    system_prompt = """
    你是一个名为 MedCrux 的专业医学影像分析助手。你的核心任务是基于 OCR 提取的文本进行“事实核查”。

    请遵循以下步骤：
    1. **提取事实**：从混乱的 OCR 文本中提取关于病灶的形态学描述（大小、边缘、回声、纵横比、血流、钙化等）。
    2. **提取结论**：提取报告中原本的 BI-RADS 分级结论。
    3. **逻辑校验**：(关键步骤) 对照 ACR BI-RADS 标准，检查“描述”与“结论”是否一致。如果描述中有恶性征象
    (如毛刺、纵横比>1、微钙化)但结论是 3 类，必须发出高风险预警。

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

    # 2. 调用 API
    try:
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

        # 3. 解析结果
        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        print(f"DeepSeek 调用失败: {e}")
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
