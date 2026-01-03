"""
文档解析模块：解析PDF和Markdown文档，提取文本和结构化内容
"""

import json
import re
from pathlib import Path

from medcrux.utils.logger import log_error_with_context, setup_logger

logger = setup_logger("medcrux.rag.extraction")


class DocumentParser:
    """文档解析器：支持PDF和Markdown格式"""

    def __init__(self):
        self.logger = logger

    def parse_markdown(self, md_path: Path) -> dict:
        """
        解析Markdown文档，提取结构化内容

        Args:
            md_path: Markdown文件路径

        Returns:
            包含结构化内容的字典
        """
        try:
            with open(md_path, encoding="utf-8") as f:
                content = f.read()

            # 提取文档元数据
            metadata = self._extract_markdown_metadata(content)

            # 提取章节结构
            sections = self._extract_markdown_sections(content)

            return {
                "type": "markdown",
                "path": str(md_path),
                "metadata": metadata,
                "sections": sections,
                "raw_content": content,
            }
        except Exception as e:
            log_error_with_context(self.logger, e, context={"file": str(md_path)}, operation="解析Markdown")
            raise

    def parse_pdf(self, pdf_path: Path) -> dict:
        """
        解析PDF文档，提取文本内容

        Args:
            pdf_path: PDF文件路径

        Returns:
            包含文本内容的字典
        """
        try:
            # 使用PyPDF2或pdfplumber解析PDF
            try:
                import pdfplumber

                text_content = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            text_content.append(text)

                full_text = "\n".join(text_content)

            except ImportError:
                # 如果没有pdfplumber，尝试使用PyPDF2
                try:
                    import PyPDF2

                    text_content = []
                    with open(pdf_path, "rb") as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        for page in pdf_reader.pages:
                            text = page.extract_text()
                            if text:
                                text_content.append(text)

                    full_text = "\n".join(text_content)

                except ImportError:
                    self.logger.warning("未安装PDF解析库（pdfplumber或PyPDF2），无法解析PDF文件")
                    return {
                        "type": "pdf",
                        "path": str(pdf_path),
                        "metadata": {},
                        "sections": [],
                        "raw_content": "",
                        "error": "未安装PDF解析库",
                    }

            # 提取PDF元数据（从guidelines_metadata.json）
            metadata = self._extract_pdf_metadata(pdf_path)

            # 尝试提取章节结构（基于文本格式）
            sections = self._extract_pdf_sections(full_text)

            return {
                "type": "pdf",
                "path": str(pdf_path),
                "metadata": metadata,
                "sections": sections,
                "raw_content": full_text,
            }
        except Exception as e:
            log_error_with_context(self.logger, e, context={"file": str(pdf_path)}, operation="解析PDF")
            raise

    def _extract_markdown_metadata(self, content: str) -> dict:
        """提取Markdown文档的元数据"""
        metadata = {}

        # 提取文档标题
        title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 提取文档属性（如维护者、创建日期等）
        maintainer_match = re.search(r"维护者[：:]\s*(.+)", content)
        if maintainer_match:
            metadata["maintainer"] = maintainer_match.group(1).strip()

        date_match = re.search(r"创建日期[：:]\s*(\d{4}-\d{2}-\d{2})", content)
        if date_match:
            metadata["created_date"] = date_match.group(1)

        # 提取数据来源优先级
        priority_match = re.search(r"数据来源优先级[：:]\s*(.+)", content, re.DOTALL)
        if priority_match:
            metadata["source_priority"] = priority_match.group(1).strip()

        return metadata

    def _extract_markdown_sections(self, content: str) -> list[dict]:
        """提取Markdown文档的章节结构"""
        sections = []

        # 匹配所有标题（## 或 ###）
        pattern = r"^(#{2,3})\s+(.+)$"
        matches = re.finditer(pattern, content, re.MULTILINE)

        for match in matches:
            level = len(match.group(1))  # ## = 2, ### = 3
            title = match.group(2).strip()
            start_pos = match.start()

            # 找到下一个标题的位置（作为当前章节的结束位置）
            next_match = None
            for next_match_iter in re.finditer(pattern, content[start_pos + 1 :], re.MULTILINE):
                next_match = next_match_iter
                break

            if next_match:
                end_pos = start_pos + 1 + next_match.start()
                section_content = content[start_pos:end_pos]
            else:
                section_content = content[start_pos:]

            sections.append(
                {
                    "level": level,
                    "title": title,
                    "content": section_content,
                    "start_pos": start_pos,
                }
            )

        return sections

    def _extract_pdf_metadata(self, pdf_path: Path) -> dict:
        """从guidelines_metadata.json提取PDF元数据"""
        metadata_file = pdf_path.parent / "guidelines_metadata.json"

        if not metadata_file.exists():
            return {"filename": pdf_path.name}

        try:
            with open(metadata_file, encoding="utf-8") as f:
                metadata_data = json.load(f)

            # 查找匹配的PDF文件
            filename = pdf_path.name
            for guideline in metadata_data.get("guidelines", []):
                if guideline.get("filename") == filename:
                    return {
                        "filename": filename,
                        "title": guideline.get("title", ""),
                        "organization": guideline.get("organization", ""),
                        "publish_date": guideline.get("publish_date", ""),
                        "source": guideline.get("source", ""),
                        "country": guideline.get("country", ""),
                        "language": guideline.get("language", ""),
                    }

            return {"filename": filename}
        except Exception as e:
            self.logger.warning(f"无法读取PDF元数据：{e}")
            return {"filename": pdf_path.name}

    def _extract_pdf_sections(self, text: str) -> list[dict]:
        """尝试从PDF文本中提取章节结构"""
        sections = []

        # 尝试匹配常见的章节标题格式
        # 例如：数字编号（1. 2. 3.）或中文编号（一、二、三、）
        patterns = [
            r"^(\d+[\.、])\s*(.+)$",  # 1. 或 1、
            r"^([一二三四五六七八九十]+[、．])\s*(.+)$",  # 一、或 一．
            r"^第([一二三四五六七八九十]+)章\s*(.+)$",  # 第一章
            r"^第(\d+)章\s*(.+)$",  # 第1章
        ]

        lines = text.split("\n")
        current_section = None

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 尝试匹配章节标题
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    if current_section:
                        sections.append(current_section)

                    current_section = {
                        "level": 1,
                        "title": match.group(2) if len(match.groups()) > 1 else line,
                        "content": line,
                        "start_line": i,
                    }
                    break

            # 如果不是标题，添加到当前章节内容
            if current_section and not any(re.match(p, line) for p in patterns):
                if "full_content" not in current_section:
                    current_section["full_content"] = []
                current_section["full_content"].append(line)

        if current_section:
            sections.append(current_section)

        return sections
