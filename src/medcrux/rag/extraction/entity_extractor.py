"""
实体提取模块：从解析后的文档中提取知识实体
"""

import re
from datetime import datetime

from medcrux.utils.logger import setup_logger

logger = setup_logger("medcrux.rag.extraction")


class EntityExtractor:
    """知识实体提取器"""

    def __init__(self):
        self.logger = logger
        self.entity_counter = {"axiom": 0, "concept": 0, "term": 0, "rule": 0}

    def extract_from_markdown(self, parsed: dict) -> list[dict]:
        """
        从Markdown文档中提取知识实体

        Args:
            parsed: 解析后的Markdown文档

        Returns:
            知识实体列表
        """
        entities = []

        # 从公理系统中提取实体
        if "breast_ultrasound_report_axioms" in parsed["path"]:
            entities.extend(self._extract_axioms_from_markdown(parsed))
            entities.extend(self._extract_concepts_from_markdown(parsed))
            entities.extend(self._extract_terms_from_markdown(parsed))
            entities.extend(self._extract_rules_from_markdown(parsed))

        return entities

    def extract_from_pdf(self, parsed: dict) -> list[dict]:
        """
        从PDF文档中提取知识实体

        Args:
            parsed: 解析后的PDF文档

        Returns:
            知识实体列表
        """
        entities = []

        # 从PDF文本中提取概念、术语等
        text = parsed.get("raw_content", "")
        metadata = parsed.get("metadata", {})

        # 提取BI-RADS相关概念
        entities.extend(self._extract_birads_concepts_from_text(text, metadata))

        # 提取医学术语
        entities.extend(self._extract_medical_terms_from_text(text, metadata))

        return entities

    def _extract_axioms_from_markdown(self, parsed: dict) -> list[dict]:
        """从Markdown中提取公理实体"""
        entities = []
        content = parsed.get("raw_content", "")

        # 匹配公理标题：## 公理X: ...
        axiom_pattern = r"^##\s+公理(\d+):\s*(.+)$"
        matches = re.finditer(axiom_pattern, content, re.MULTILINE)

        for match in matches:
            axiom_num = match.group(1)
            axiom_title = match.group(2).strip()
            start_pos = match.start()

            # 找到下一个公理或章节的位置
            next_match = re.search(
                r"^##\s+(?:公理\d+|数据来源|公理系统的自洽性)", content[start_pos + 1 :], re.MULTILINE
            )
            if next_match:
                end_pos = start_pos + 1 + next_match.start()
                axiom_content = content[start_pos:end_pos]
            else:
                axiom_content = content[start_pos:]

            # 提取公理的子项（公理X.Y）
            sub_axioms = re.finditer(r"^\*\*公理(\d+)\.(\d+)\s+(.+?)\*\*", axiom_content, re.MULTILINE)

            for sub_match in sub_axioms:
                sub_num = sub_match.group(2)
                sub_title = sub_match.group(3).strip()

                # 提取子公理的内容（到下一个**或##）
                sub_start = sub_match.end()
                sub_end_match = re.search(r"^\*\*|^##", content[start_pos + sub_start :], re.MULTILINE)
                if sub_end_match:
                    sub_content = content[start_pos + sub_start : start_pos + sub_start + sub_end_match.start()].strip()
                else:
                    sub_content = content[start_pos + sub_start :].strip()

                entity_id = f"axiom_{axiom_num}_{sub_num}"
                self.entity_counter["axiom"] += 1

                entities.append(
                    {
                        "id": entity_id,
                        "type": "axiom",
                        "name": f"{axiom_title} - {sub_title}",
                        "content": sub_content,
                        "source": "ACR BI-RADS v2025",
                        "priority": 1,
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "references": [parsed["path"]],
                            "axiom_number": f"{axiom_num}.{sub_num}",
                        },
                        "embeddings": [],  # 后续生成
                    }
                )

        return entities

    def _extract_concepts_from_markdown(self, parsed: dict) -> list[dict]:
        """从Markdown中提取概念实体（如BI-RADS分类）"""
        entities = []
        content = parsed.get("raw_content", "")

        # 提取BI-RADS分类概念
        birads_pattern = r"BI-RADS\s+(\d+[ABC]?)\s*类"
        matches = re.finditer(birads_pattern, content, re.IGNORECASE)

        birads_classes = set()
        for match in matches:
            birads_class = match.group(1)
            birads_classes.add(birads_class)

        # 为每个BI-RADS分类创建概念实体
        for birads_class in birads_classes:
            entity_id = f"concept_birads_{birads_class}"
            self.entity_counter["concept"] += 1

            # 提取该分类的描述
            pattern = rf"公理3\.\d+\s+BI-RADS\s+{birads_class}\s*类定级依据.*?(?=公理3\.\d+|##)"
            desc_match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            description = desc_match.group(0) if desc_match else f"BI-RADS {birads_class}类"

            entities.append(
                {
                    "id": entity_id,
                    "type": "concept",
                    "name": f"BI-RADS {birads_class}类",
                    "content": description,
                    "source": "ACR BI-RADS v2025",
                    "priority": 1,
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "MD",
                        "references": [parsed["path"]],
                        "birads_class": birads_class,
                    },
                    "embeddings": [],
                }
            )

        # 提取恶性征象概念
        malignant_signs = [
            "毛刺状边界",
            "不平行方位",
            "微钙化",
            "声影",
            "不规则形状",
            "条状低回声",  # 条索状、条索样
        ]

        for sign in malignant_signs:
            entity_id = f"concept_malignant_{sign.replace(' ', '_')}"
            self.entity_counter["concept"] += 1

            entities.append(
                {
                    "id": entity_id,
                    "type": "concept",
                    "name": sign,
                    "content": f"{sign}是高度可疑恶性征象",
                    "source": "ACR BI-RADS v2025",
                    "priority": 1,
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "MD",
                        "references": [parsed["path"]],
                    },
                    "embeddings": [],
                }
            )

        return entities

    def _extract_terms_from_markdown(self, parsed: dict) -> list[dict]:
        """从Markdown中提取术语实体"""
        entities = []
        content = parsed.get("raw_content", "")

        # 提取术语（从公理5：术语标准化）
        term_sections = re.finditer(r"公理5\.\d+\s+(.+?)\s*\*\*.*?\*\*(.+?)(?=公理5\.\d+|##)", content, re.DOTALL)

        for section_match in term_sections:
            section_title = section_match.group(1).strip()
            section_content = section_match.group(2)

            # 提取术语列表
            terms = re.findall(r"[-•]\s*([^（(]+?)[（(]?([^）)]+?)[）)]?", section_content)

            for term_cn, term_en in terms:
                term_cn = term_cn.strip()
                term_en = term_en.strip() if term_en else ""

                entity_id = f"term_{term_cn.replace(' ', '_')}"
                self.entity_counter["term"] += 1

                entities.append(
                    {
                        "id": entity_id,
                        "type": "term",
                        "name": term_cn,
                        "content": f"{term_cn}（{term_en}）" if term_en else term_cn,
                        "source": "ACR BI-RADS v2025",
                        "priority": 1,
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "references": [parsed["path"]],
                            "category": section_title,
                        },
                        "embeddings": [],
                    }
                )

        return entities

    def _extract_rules_from_markdown(self, parsed: dict) -> list[dict]:
        """从Markdown中提取规则实体"""
        entities = []
        content = parsed.get("raw_content", "")

        # 提取规则（如报告完整性规则）
        rule_pattern = r"公理8\.\d+\s+(.+?)\s*\*\*(.+?)\*\*(.+?)(?=公理8\.\d+|##)"
        matches = re.finditer(rule_pattern, content, re.DOTALL)

        for match in matches:
            rule_title = match.group(1).strip()
            rule_content = match.group(3).strip()

            entity_id = f"rule_{rule_title.replace(' ', '_')}"
            self.entity_counter["rule"] += 1

            entities.append(
                {
                    "id": entity_id,
                    "type": "rule",
                    "name": rule_title,
                    "content": rule_content,
                    "source": "ACR BI-RADS v2025",
                    "priority": 1,
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "MD",
                        "references": [parsed["path"]],
                    },
                    "embeddings": [],
                }
            )

        return entities

    def _extract_birads_concepts_from_text(self, text: str, metadata: dict) -> list[dict]:
        """从PDF文本中提取BI-RADS相关概念"""
        entities = []

        # 查找BI-RADS分类提及
        birads_pattern = r"BI-RADS\s*[：:]\s*(\d+[ABC]?)"
        matches = re.finditer(birads_pattern, text, re.IGNORECASE)

        birads_classes = set()
        for match in matches:
            birads_classes.add(match.group(1))

        for birads_class in birads_classes:
            entity_id = f"concept_birads_{birads_class}_pdf"
            entities.append(
                {
                    "id": entity_id,
                    "type": "concept",
                    "name": f"BI-RADS {birads_class}类",
                    "content": f"从{metadata.get('title', 'PDF文档')}中提取的BI-RADS {birads_class}类相关信息",
                    "source": metadata.get("title", "PDF文档"),
                    "priority": 2,  # PDF优先级低于公理系统
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "Extractor",
                        "references": [metadata.get("filename", "")],
                    },
                    "embeddings": [],
                }
            )

        return entities

    def _extract_medical_terms_from_text(self, text: str, metadata: dict) -> list[dict]:
        """从PDF文本中提取医学术语"""
        entities = []

        # 常见的医学术语模式
        term_patterns = [
            r"([^，。；：\s]+?)[（(]([A-Za-z\s]+)[）)]",  # 中文（英文）
            r"([A-Za-z\s]+)[（(]([^）)]+)[）)]",  # 英文（中文）
        ]

        terms_found = set()
        for pattern in term_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                term = match.group(1).strip()
                if len(term) > 2 and len(term) < 50:  # 过滤太短或太长的
                    terms_found.add(term)

        for term in list(terms_found)[:50]:  # 限制数量
            entity_id = f"term_{term.replace(' ', '_')[:30]}"
            entities.append(
                {
                    "id": entity_id,
                    "type": "term",
                    "name": term,
                    "content": term,
                    "source": metadata.get("title", "PDF文档"),
                    "priority": 2,
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "Extractor",
                        "references": [metadata.get("filename", "")],
                    },
                    "embeddings": [],
                }
            )

        return entities
