"""
报告结构解析模块：基于公理1.1解析OCR文本的报告结构

根据公理1.1，完备的乳腺超声检查报告包含以下六个部分：
1. 报告头部：医疗机构名称、检查日期时间、患者基本信息（姓名、性别、年龄、ID号）、检查部位、检查方法
2. 检查技术：设备型号、探头类型和频率、检查方法
3. 检查所见：乳腺结构描述、病变详细描述（如发现）、血流情况、其他发现
4. 影像学诊断：BI-RADS分类、诊断意见
5. 建议：根据BI-RADS分类提出的临床建议
6. 报告尾部：报告医师签名、审核医师签名、报告日期

本模块使用LLM识别报告的各个部分，提取事实性摘要（检查所见）和结论（影像学诊断和建议）。
"""

import json
import os
import re

from openai import OpenAI

from medcrux.utils.logger import log_error_with_context, setup_logger

logger = setup_logger("medcrux.analysis.report_structure")

# 报告头部信息关键词列表（需要排除）
HEADER_KEYWORDS = [
    "姓名",
    "年龄",
    "性别",
    "超声号",
    "住院号",
    "科别",
    "床号",
    "检查部位",
    "仪器名称",
    "院区",
    "超卢描述",
    "超声描述",
]

# 检查所见开始关键词
FINDINGS_START_KEYWORDS = ["检查所见", "超声描述", "超卢描述", "所见"]

# 影像学诊断开始关键词
DIAGNOSIS_START_KEYWORDS = ["影像学诊断", "超声提示", "诊断", "诊断意见"]

# 建议开始关键词
RECOMMENDATION_START_KEYWORDS = ["建议", "处理建议", "临床建议"]

# 报告尾部关键词
FOOTER_KEYWORDS = ["报告医师", "审核医师", "报告日期"]


def _filter_header_info(text: str) -> str:
    """
    过滤文本中的报告头部信息

    Args:
        text: 待过滤的文本

    Returns:
        过滤后的文本
    """
    if not text:
        return text

    # 按行分割
    lines = text.split("\n")
    filtered_lines = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否包含报告头部关键词
        contains_header_keyword = any(keyword in line for keyword in HEADER_KEYWORDS)

        # 检查是否是基础信息格式（如"姓名："、"年龄："等）
        header_pattern = r"(姓名|年龄|性别|超声号|住院号|科别|床号|检查部位|仪器名称|院区)[:：]\s*"
        is_header_format = re.search(header_pattern, line)

        if not contains_header_keyword and not is_header_format:
            filtered_lines.append(line)

    # 如果过滤后为空，尝试更宽松的过滤
    if not filtered_lines:
        # 尝试找到第一个病变描述的位置
        for i, line in enumerate(lines):
            if re.search(r"(查见|可见|发现).*?(低回声|高回声|无回声|异常|结节|病变)", line):
                filtered_lines = lines[i:]
                break

    result = "\n".join(filtered_lines).strip()

    # 如果结果仍然包含头部关键词，尝试更激进的过滤
    if any(keyword in result for keyword in HEADER_KEYWORDS[:5]):  # 只检查前5个关键词
        # 找到第一个病变描述的位置
        match = re.search(r"(查见|可见|发现|在.*?乳腺)", result)
        if match:
            result = result[match.start() :]

    return result


def _fix_diagnosis_boundary(diagnosis: str, findings: str) -> tuple[str, str]:
    """
    修正影像学诊断边界，如果诊断中包含病变描述，移到检查所见

    Args:
        diagnosis: 影像学诊断文本
        findings: 检查所见文本

    Returns:
        (修正后的诊断, 修正后的检查所见)
    """
    if not diagnosis:
        return diagnosis, findings

    # 检查诊断中是否包含病变描述（如"在左侧乳腺3点钟方向查见"）
    lesion_pattern = r"在.*?乳腺.*?查见.*?(低回声|高回声|无回声|异常|结节|病变)"
    lesion_match = re.search(lesion_pattern, diagnosis)

    if lesion_match:
        # 找到病变描述的开始位置
        lesion_start = lesion_match.start()

        # 检查病变描述之前是否有"超声提示"等关键词
        before_lesion = diagnosis[:lesion_start]
        has_diagnosis_keyword = any(keyword in before_lesion for keyword in DIAGNOSIS_START_KEYWORDS)

        if has_diagnosis_keyword:
            # 病变描述之前的部分是诊断，之后的部分应该移到检查所见
            diagnosis_part = before_lesion
            findings_part = diagnosis[lesion_start:]

            # 更新诊断和检查所见
            diagnosis = diagnosis_part.strip()
            if findings:
                findings = findings + " " + findings_part.strip()
            else:
                findings = findings_part.strip()

    return diagnosis, findings


# 初始化DeepSeek客户端
api_key = os.getenv("DEEPSEEK_API_KEY")
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com") if api_key else None


def extract_doctor_birads(diagnosis_text: str) -> dict:
    """
    从diagnosis文本中提取原报告的BI-RADS分类集合和最高值
    
    Args:
        diagnosis_text: 影像学诊断文本（例如："超声提示：左侧乳腺低回声结节，BI-RADS 3类；右侧乳腺囊性结节，BI-RADS 2类。"）
    
    Returns:
        {
            "birads_set": set,  # BI-RADS分类集合（去重）
            "birads_list": list,  # BI-RADS分类列表（保留顺序）
            "highest_birads": str,  # 最高BI-RADS分类
            "diagnosis_text": str  # 原始diagnosis文本
        }
    
    支持格式：
    - "BI-RADS 3类"
    - "BI-RADS 2类和3类"
    - "BI-RADS 3类、4类"
    - "BI-RADS 3类；BI-RADS 4类"
    """
    if not diagnosis_text:
        return {
            "birads_set": set(),
            "birads_list": [],
            "highest_birads": None,
            "diagnosis_text": diagnosis_text,
        }

    # 匹配BI-RADS分类（支持数字和字母后缀，如"3"、"4A"、"4B"、"4C"）
    # 支持多种格式：BI-RADS 3类、BI-RADS 3、bi-rads 3类等
    # 支持省略格式：BI-RADS 3类、4类（第二个分类省略了"BI-RADS"）
    pattern = r"BI-RADS\s+(\d+[ABC]?)\s*类?(?:\s*[、，,]\s*(\d+[ABC]?)\s*类?)*"
    all_matches = re.findall(pattern, diagnosis_text, re.IGNORECASE)
    
    # 展开匹配结果（第一个是主匹配，后续是可选匹配）
    matches = []
    for match in all_matches:
        if isinstance(match, tuple):
            # 展开元组：第一个是主匹配，后续是可选匹配
            matches.append(match[0])
            for item in match[1:]:
                if item:
                    matches.append(item)
        else:
            matches.append(match)
    
    # 如果使用复杂正则没有匹配到，回退到简单正则
    if not matches:
        pattern_simple = r"BI-RADS\s+(\d+[ABC]?)\s*类?"
        matches = re.findall(pattern_simple, diagnosis_text, re.IGNORECASE)

    if not matches:
        logger.warning(f"无法从diagnosis文本中提取BI-RADS分类: {diagnosis_text[:100]}")
        return {
            "birads_set": set(),
            "birads_list": [],
            "highest_birads": None,
            "diagnosis_text": diagnosis_text,
        }

    # 转换为数字进行比较（忽略字母后缀）
    birads_list = list(matches)
    birads_set = set(matches)

    # 提取最高BI-RADS分类（比较数字部分）
    try:
        highest_birads = max(matches, key=lambda x: int(re.match(r"\d+", x).group()))
    except (ValueError, AttributeError) as e:
        logger.error(f"提取最高BI-RADS分类失败: {e}, matches: {matches}")
        highest_birads = matches[0] if matches else None

    logger.info(
        f"从diagnosis提取BI-RADS分类成功: 集合={birads_set}, 最高={highest_birads}, "
        f"原始文本长度={len(diagnosis_text)}"
    )

    return {
        "birads_set": birads_set,
        "birads_list": birads_list,
        "highest_birads": highest_birads,
        "diagnosis_text": diagnosis_text,
    }


def parse_report_structure(ocr_text: str) -> dict:
    """
    解析OCR文本，识别报告的各个部分

    Args:
        ocr_text: OCR识别的文本

    Returns:
        {
            "header": {...},  # 报告头部（不用于展示）
            "check_technique": "...",  # 检查技术（可选）
            "findings": "...",  # 检查所见（事实性摘要）
            "diagnosis": "...",  # 影像学诊断（结论）
            "recommendation": "...",  # 建议（结论）
            "footer": {...}  # 报告尾部（不用于展示）
        }
    """
    if not ocr_text or len(ocr_text.strip()) == 0:
        return {
            "findings": None,
            "diagnosis": None,
            "recommendation": None,
        }

    if not client:
        logger.warning("DEEPSEEK_API_KEY未设置，无法使用LLM解析报告结构")
        return {
            "findings": None,
            "diagnosis": None,
            "recommendation": None,
        }

    # 设计prompt，基于公理1.1的结构定义，添加明确的规则和示例
    system_prompt = """你是MedCrux报告结构解析助手，负责识别医学影像报告的各个部分。

## 报告结构定义

一个完备的乳腺超声检查报告包含以下六个部分：
1. **报告头部**：医疗机构名称、检查日期时间、患者基本信息（姓名、性别、年龄、ID号、超声号、住院号、科别、床号等）、检查部位、检查方法、仪器名称  # noqa: E501
2. **检查技术**：设备型号、探头类型和频率、检查方法（二维、彩色多普勒、弹性成像等）
3. **检查所见**：乳腺结构描述、病变详细描述（如发现）、血流情况、其他发现
4. **影像学诊断**：BI-RADS分类、诊断意见（如"超声提示"、"诊断"等）
5. **建议**：根据BI-RADS分类提出的临床建议
6. **报告尾部**：报告医师签名、审核医师签名、报告日期

## 提取要求

请仔细阅读OCR文本，识别报告的各个部分，并提取以下内容：

### 1. 检查所见（findings）
- **必须排除的内容**：
  - 报告头部信息：姓名、年龄、性别、超声号、住院号、科别、床号、检查部位、仪器名称、院区、床号等
  - 任何包含"姓名"、"年龄"、"性别"、"超声号"、"住院号"、"科别"、"床号"、"检查部位"、"仪器名称"、"院区"等关键词的文本
- **必须包含的内容**：
  - 乳腺结构描述（如"双乳结构清晰"、"腺体回声均匀"等）
  - 病变详细描述（如"在左侧乳腺3点钟方向查见..."）
  - 血流情况（如"CDFI：未见明显血流信号"）
  - 其他发现（如"导管未见扩张"、"乳腺后间隙结构清晰"等）
- **边界识别**：
  - 从"检查所见"、"超声描述"、"超卢描述"等关键词之后开始
  - 到"影像学诊断"、"超声提示"、"诊断"等关键词之前结束
  - 如果文本开头就是病变描述，从第一个病变描述开始

### 2. 影像学诊断（diagnosis）
- **必须包含的内容**：
  - BI-RADS分类（如"BI-RADS 3类"）
  - 诊断意见（如"左侧乳腺低回声结节"）
- **边界识别**：
  - 从"影像学诊断"、"超声提示"、"诊断"等关键词之后开始
  - 到"建议"关键词之前结束
  - 如果只有"超声提示"，从"超声提示"之后开始

### 3. 建议（recommendation）
- **必须包含的内容**：
  - 根据BI-RADS分类提出的临床建议（如"建议6个月后复查"、"建议活检"等）
- **边界识别**：
  - 从"建议"关键词之后开始
  - 到"报告医师"、"审核医师"、"报告日期"等关键词之前结束

## 重要规则

1. **严格排除报告头部信息**：
   - 如果"检查所见"中包含以下任何关键词，必须删除包含该关键词的整段文本：
     - "姓名"、"年龄"、"性别"、"超声号"、"住院号"、"科别"、"床号"、"检查部位"、"仪器名称"、"院区"、"秒超检查报合"等
   - 示例：如果文本是"姓名：[患者姓名] 性别：[性别] 年龄：[年龄] 在左侧乳腺..."，必须只提取"在左侧乳腺..."部分

2. **准确识别边界**：
   - 如果文本开头就是报告头部信息（如"[医疗机构名称] 院区：[院区名称]..."），必须跳过这些内容
   - 如果"检查所见"和"影像学诊断"之间没有明确分隔，必须根据内容特征判断边界
   - 如果"影像学诊断"部分包含病变描述（如"在左侧乳腺3点钟方向查见..."），这些内容应该属于"检查所见"，而不是"影像学诊断"

3. **如果某个部分不存在**：返回null

## 示例

**错误示例**：
```json
{
    "findings": "[报告头部信息：医疗机构名称、检查日期时间、患者基本信息] 在左侧乳腺...",
    "diagnosis": "[病变描述：位置、大小、形态] 超声提示：BI-RADS X类"
}
```

**正确示例**：
```json
{
    "findings": (
        "在左侧乳腺X点钟方向距乳头约Xcm处查见约X×X×Xcm低回声，"
        "形态规则，边界清楚，CDFI：未见明显血流信号。"
        "余乳腺腺体层回声均匀，导管未见扩张，乳腺后间隙结构清晰。"
    ),
    "diagnosis": "超声提示：左侧乳腺低回声结节，BI-RADS X类；右侧乳腺囊性结节，BI-RADS X类。",
    "recommendation": null
}
```

返回JSON格式（无markdown，严格按照上述规则）：
{
    "findings": "检查所见的内容（严格排除报告头部信息，只包含病变描述和结构描述）",
    "diagnosis": "影像学诊断的内容（只包含BI-RADS分类和诊断意见，不包含病变描述）",
    "recommendation": "建议的内容（如果有，否则为null）"
}"""

    try:
        logger.debug(f"开始解析报告结构 [文本长度: {len(ocr_text)}]")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"请解析以下OCR文本的报告结构：\n\n{ocr_text}",
                },
            ],
            temperature=0.1,  # 结构解析需要严谨，温度设低
            stream=False,
            response_format={"type": "json_object"},  # 强制返回 JSON
        )

        content = response.choices[0].message.content
        result = json.loads(content)

        # 后处理：过滤和修正结果
        findings = result.get("findings")
        diagnosis = result.get("diagnosis")
        recommendation = result.get("recommendation")

        # 后处理1：过滤检查所见中的报告头部信息
        if findings:
            findings = _filter_header_info(findings)

        # 后处理2：修正影像学诊断边界（如果包含病变描述，移到检查所见）
        if diagnosis and findings:
            diagnosis, findings = _fix_diagnosis_boundary(diagnosis, findings)

        logger.info(
            f"报告结构解析完成 [检查所见: {len(findings or '')} 字符, "
            f"诊断: {len(diagnosis or '')} 字符, "
            f"建议: {len(recommendation or '')} 字符]"
        )

        return {
            "findings": findings,
            "diagnosis": diagnosis,
            "recommendation": recommendation,
        }

    except Exception as e:
        log_error_with_context(
            logger,
            e,
            context={"ocr_text_length": len(ocr_text)},
            operation="报告结构解析",
        )
        logger.warning("报告结构解析失败，返回空结果")
        return {
            "findings": None,
            "diagnosis": None,
            "recommendation": None,
        }
