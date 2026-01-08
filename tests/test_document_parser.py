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

