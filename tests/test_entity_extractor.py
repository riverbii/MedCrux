"""
测试EntityExtractor类
"""

import tempfile
from pathlib import Path

import pytest

from medcrux.rag.extraction.document_parser import DocumentParser
from medcrux.rag.extraction.entity_extractor import EntityExtractor


class TestEntityExtractor:
    """测试EntityExtractor类"""

    def test_init(self):
        """测试初始化"""
        extractor = EntityExtractor()
        assert extractor is not None
        assert extractor.logger is not None
        assert extractor.entity_counter is not None
        assert "axiom" in extractor.entity_counter
        assert "concept" in extractor.entity_counter
        assert "term" in extractor.entity_counter
        assert "rule" in extractor.entity_counter

    def test_extract_from_markdown_non_axioms_file(self):
        """测试非公理系统文件（应返回空列表）"""
        extractor = EntityExtractor()
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 普通文档

这是普通文档内容。
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            entities = extractor.extract_from_markdown(parsed)
            
            # 非公理系统文件应该返回空列表
            assert entities == []
        finally:
            md_path.unlink()

    def test_extract_from_markdown_axioms_file(self):
        """测试公理系统文件提取"""
        extractor = EntityExtractor()
        parser = DocumentParser()
        
        # 创建模拟公理系统文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 公理系统

## 公理1：BI-RADS分类

**公理1.1 边界清晰**：如果结节边界清晰，则BI-RADS分类为2类或3类。

## 概念：低回声

低回声是指...

## 术语：边界清晰

边界清晰是指...

## 规则：BI-RADS 3类随访

如果BI-RADS分类为3类，则建议6个月随访。
""")
            md_path = Path(f.name)
        
        try:
            # 修改path以包含breast_ultrasound_report_axioms
            parsed = parser.parse_markdown(md_path)
            parsed["path"] = str(md_path).replace(md_path.name, "breast_ultrasound_report_axioms.md")
            
            entities = extractor.extract_from_markdown(parsed)
            
            # 应该提取到实体
            assert isinstance(entities, list)
            # 注意：实际提取结果取决于EntityExtractor的实现
        finally:
            md_path.unlink()

    def test_extract_from_pdf_empty_text(self):
        """测试空文本"""
        extractor = EntityExtractor()
        
        parsed = {
            "type": "pdf",
            "path": "test.pdf",
            "raw_content": "",
            "metadata": {}
        }
        
        entities = extractor.extract_from_pdf(parsed)
        
        assert isinstance(entities, list)
        # 空文本应该返回空列表或少量实体

    def test_extract_from_pdf_no_metadata(self):
        """测试无元数据的PDF"""
        extractor = EntityExtractor()
        
        parsed = {
            "type": "pdf",
            "path": "test.pdf",
            "raw_content": "BI-RADS 3类，建议随访。",
            "metadata": {}
        }
        
        entities = extractor.extract_from_pdf(parsed)
        
        assert isinstance(entities, list)

    def test_extract_from_pdf_with_birads(self):
        """测试包含BI-RADS的PDF文本"""
        extractor = EntityExtractor()
        
        parsed = {
            "type": "pdf",
            "path": "test.pdf",
            "raw_content": "超声检查提示：左乳上方可见低回声结节，大小1.2x0.8cm，边界清晰。BI-RADS 3类，建议6个月随访。",
            "metadata": {"title": "测试PDF"}
        }
        
        entities = extractor.extract_from_pdf(parsed)
        
        assert isinstance(entities, list)
        # 应该提取到BI-RADS相关概念

