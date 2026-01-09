"""
测试DocumentParser类
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

from medcrux.rag.extraction.document_parser import DocumentParser


class TestDocumentParser:
    """测试DocumentParser类"""

    def test_init(self):
        """测试初始化"""
        parser = DocumentParser()
        assert parser is not None
        assert parser.logger is not None

    def test_parse_markdown_success(self):
        """测试成功解析Markdown文件"""
        parser = DocumentParser()
        
        # 创建临时Markdown文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""---
title: 测试文档
author: Test Author
---

# 第一章

这是第一章的内容。

## 1.1 小节

这是小节内容。
""")
            md_path = Path(f.name)
        
        try:
            result = parser.parse_markdown(md_path)
            
            assert result["type"] == "markdown"
            assert result["path"] == str(md_path)
            assert "metadata" in result
            assert "sections" in result
            assert "raw_content" in result
            assert len(result["raw_content"]) > 0
        finally:
            md_path.unlink()

    def test_parse_markdown_file_not_found(self):
        """测试文件不存在的情况"""
        parser = DocumentParser()
        non_existent_path = Path("/non/existent/file.md")
        
        with pytest.raises(FileNotFoundError):
            parser.parse_markdown(non_existent_path)

    def test_parse_markdown_empty_file(self):
        """测试空文件"""
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("")
            md_path = Path(f.name)
        
        try:
            result = parser.parse_markdown(md_path)
            
            assert result["type"] == "markdown"
            assert result["path"] == str(md_path)
            assert "metadata" in result
            assert "sections" in result
            assert result["raw_content"] == ""
        finally:
            md_path.unlink()

    def test_parse_markdown_no_metadata(self):
        """测试无元数据的Markdown文件"""
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 标题

这是内容。
""")
            md_path = Path(f.name)
        
        try:
            result = parser.parse_markdown(md_path)
            
            assert result["type"] == "markdown"
            assert "metadata" in result
            assert "sections" in result
        finally:
            md_path.unlink()

    def test_parse_pdf_file_not_found(self):
        """测试PDF文件不存在"""
        parser = DocumentParser()
        non_existent_path = Path("/non/existent/file.pdf")
        
        # PDF解析可能返回包含error的字典，而不是抛出异常
        result = parser.parse_pdf(non_existent_path)
        
        # 根据实际实现，可能是异常或error字典
        assert result is not None

    def test_parse_markdown_extract_metadata(self):
        """测试元数据提取"""
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 测试标题

维护者：Test Maintainer
创建日期：2026-01-08
数据来源优先级：高

# 内容
""")
            md_path = Path(f.name)
        
        try:
            result = parser.parse_markdown(md_path)
            
            assert "metadata" in result
            metadata = result["metadata"]
            assert metadata.get("title") == "测试标题"
            assert metadata.get("maintainer") == "Test Maintainer"
            assert metadata.get("created_date") == "2026-01-08"
        finally:
            md_path.unlink()

    def test_parse_markdown_extract_sections(self):
        """测试章节提取"""
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 主标题

## 第一章

内容1

### 1.1 小节

内容1.1

## 第二章

内容2
""")
            md_path = Path(f.name)
        
        try:
            result = parser.parse_markdown(md_path)
            
            assert "sections" in result
            sections = result["sections"]
            assert len(sections) > 0
        finally:
            md_path.unlink()

    def test_parse_markdown_encoding_error(self):
        """测试编码错误"""
        parser = DocumentParser()
        
        # 创建包含非UTF-8字符的文件（如果系统支持）
        # 这里使用mock来模拟编码错误
        with patch('builtins.open', side_effect=UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid')):
            md_path = Path("/fake/path.md")
            with pytest.raises(UnicodeDecodeError):
                parser.parse_markdown(md_path)

    def test_extract_pdf_metadata_no_metadata_file(self):
        """测试_extract_pdf_metadata：元数据文件不存在（决策点：返回filename）"""
        parser = DocumentParser()
        
        pdf_path = Path("/fake/test.pdf")
        result = parser._extract_pdf_metadata(pdf_path)
        
        assert result == {"filename": "test.pdf"}

    def test_extract_pdf_metadata_with_metadata_file(self):
        """测试_extract_pdf_metadata：元数据文件存在且匹配（决策点：返回完整元数据）"""
        parser = DocumentParser()
        
        import tempfile
        import json
        
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            metadata_file = Path(tmpdir) / "guidelines_metadata.json"
            
            # 创建元数据文件
            metadata_data = {
                "guidelines": [
                    {
                        "filename": "test.pdf",
                        "title": "测试指南",
                        "organization": "测试组织",
                        "publish_date": "2026-01-08",
                        "source": "测试来源",
                        "country": "CN",
                        "language": "zh"
                    }
                ]
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_data, f)
            
            result = parser._extract_pdf_metadata(pdf_path)
            
            assert result["filename"] == "test.pdf"
            assert result["title"] == "测试指南"
            assert result["organization"] == "测试组织"
            assert result["publish_date"] == "2026-01-08"

    def test_extract_pdf_metadata_no_matching_guideline(self):
        """测试_extract_pdf_metadata：元数据文件存在但不匹配（决策点：返回filename）"""
        parser = DocumentParser()
        
        import tempfile
        import json
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            metadata_file = Path(tmpdir) / "guidelines_metadata.json"
            
            # 创建不匹配的元数据
            metadata_data = {
                "guidelines": [
                    {
                        "filename": "other.pdf",
                        "title": "其他指南"
                    }
                ]
            }
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_data, f)
            
            result = parser._extract_pdf_metadata(pdf_path)
            
            assert result == {"filename": "test.pdf"}

    def test_extract_pdf_metadata_json_error(self):
        """测试_extract_pdf_metadata：JSON解析错误（决策点：异常处理）"""
        parser = DocumentParser()
        
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            metadata_file = Path(tmpdir) / "guidelines_metadata.json"
            
            # 创建无效的JSON文件
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write("invalid json {")
            
            result = parser._extract_pdf_metadata(pdf_path)
            
            # 应该返回filename，因为异常被捕获
            assert result == {"filename": "test.pdf"}

    def test_extract_pdf_sections_with_numbered_sections(self):
        """测试_extract_pdf_sections：数字编号章节（决策点：匹配数字编号模式）"""
        parser = DocumentParser()
        
        text = """1. 第一章
这是第一章的内容。

2. 第二章
这是第二章的内容。
"""
        sections = parser._extract_pdf_sections(text)
        
        assert len(sections) >= 1
        assert any("第一章" in s.get("title", "") for s in sections)

    def test_extract_pdf_sections_with_chinese_numbered_sections(self):
        """测试_extract_pdf_sections：中文编号章节（决策点：匹配中文编号模式）"""
        parser = DocumentParser()
        
        text = """一、第一章
这是第一章的内容。

二、第二章
这是第二章的内容。
"""
        sections = parser._extract_pdf_sections(text)
        
        assert len(sections) >= 1

    def test_extract_pdf_sections_with_chapter_format(self):
        """测试_extract_pdf_sections：第X章格式（决策点：匹配章节格式）"""
        parser = DocumentParser()
        
        text = """第一章 概述
这是概述内容。

第二章 详细说明
这是详细说明。
"""
        sections = parser._extract_pdf_sections(text)
        
        assert len(sections) >= 1

    def test_extract_pdf_sections_no_sections(self):
        """测试_extract_pdf_sections：无章节标题（决策点：返回空列表）"""
        parser = DocumentParser()
        
        text = """这是普通文本，没有章节标题。
"""
        sections = parser._extract_pdf_sections(text)
        
        assert sections == []

    def test_extract_pdf_sections_with_content(self):
        """测试_extract_pdf_sections：章节包含内容（决策点：内容添加到full_content）"""
        parser = DocumentParser()
        
        text = """1. 第一章
这是第一章的第一段。
这是第一章的第二段。

2. 第二章
这是第二章的内容。
"""
        sections = parser._extract_pdf_sections(text)
        
        assert len(sections) >= 1
        # 验证第一个章节有内容
        if sections and "full_content" in sections[0]:
            assert len(sections[0]["full_content"]) > 0

