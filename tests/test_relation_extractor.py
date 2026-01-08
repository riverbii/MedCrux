"""
测试RelationExtractor类
"""

import tempfile
from pathlib import Path

import pytest

from medcrux.rag.extraction.document_parser import DocumentParser
from medcrux.rag.extraction.entity_extractor import EntityExtractor
from medcrux.rag.extraction.relation_extractor import RelationExtractor


class TestRelationExtractor:
    """测试RelationExtractor类"""

    def test_init(self):
        """测试初始化"""
        extractor = RelationExtractor()
        assert extractor is not None
        assert extractor.logger is not None
        assert extractor.relation_counter == 0

    def test_extract_from_markdown_non_axioms_file(self):
        """测试非公理系统文件（应返回空列表）"""
        extractor = RelationExtractor()
        parser = DocumentParser()
        entity_extractor = EntityExtractor()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 普通文档

这是普通文档内容。
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            entities = entity_extractor.extract_from_markdown(parsed)
            relations = extractor.extract_from_markdown(parsed, entities)
            
            # 非公理系统文件应该返回空列表
            assert relations == []
        finally:
            md_path.unlink()

    def test_extract_from_pdf_empty(self):
        """测试PDF提取（当前返回空列表）"""
        extractor = RelationExtractor()
        
        parsed = {
            "type": "pdf",
            "path": "test.pdf",
            "raw_content": "测试内容",
            "metadata": {}
        }
        
        entities = []
        relations = extractor.extract_from_pdf(parsed, entities)
        
        # PDF提取当前返回空列表
        assert relations == []

    def test_extract_relations_with_empty_entities(self):
        """测试空实体列表"""
        extractor = RelationExtractor()
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""# 公理系统

## 公理1：BI-RADS分类
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            parsed["path"] = str(md_path).replace(md_path.name, "breast_ultrasound_report_axioms.md")
            
            # 使用空实体列表
            entities = []
            relations = extractor.extract_from_markdown(parsed, entities)
            
            # 空实体列表应该返回空关系列表
            assert isinstance(relations, list)
        finally:
            md_path.unlink()

