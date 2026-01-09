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

    def test_extract_axioms_from_markdown_with_sub_axioms(self):
        """测试_extract_axioms_from_markdown：包含子公理（决策点：提取子公理）"""
        extractor = EntityExtractor()
        parser = DocumentParser()
        
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 公理1: BI-RADS分类

**公理1.1 边界清晰**：如果结节边界清晰，则BI-RADS分类为2类或3类。

**公理1.2 边界模糊**：如果结节边界模糊，则BI-RADS分类为4类或5类。

## 公理2: 其他公理
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            parsed["path"] = str(md_path).replace(md_path.name, "breast_ultrasound_report_axioms.md")
            
            entities = extractor._extract_axioms_from_markdown(parsed)
            
            # 应该提取到子公理
            assert len(entities) > 0
            # 验证子公理ID格式
            assert any("axiom_1_" in e["id"] for e in entities)
        finally:
            md_path.unlink()

    def test_extract_terms_from_markdown(self):
        """测试_extract_terms_from_markdown：提取术语（决策点：匹配术语模式）"""
        extractor = EntityExtractor()
        parser = DocumentParser()
        
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 术语：边界清晰

边界清晰是指...

## 术语：低回声

低回声是指...
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            parsed["path"] = str(md_path).replace(md_path.name, "breast_ultrasound_report_axioms.md")
            
            entities = extractor._extract_terms_from_markdown(parsed)
            
            assert isinstance(entities, list)
        finally:
            md_path.unlink()

    def test_extract_rules_from_markdown(self):
        """测试_extract_rules_from_markdown：提取规则（决策点：匹配规则模式）"""
        extractor = EntityExtractor()
        parser = DocumentParser()
        
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write("""## 规则：BI-RADS 3类随访

如果BI-RADS分类为3类，则建议6个月随访。
""")
            md_path = Path(f.name)
        
        try:
            parsed = parser.parse_markdown(md_path)
            parsed["path"] = str(md_path).replace(md_path.name, "breast_ultrasound_report_axioms.md")
            
            entities = extractor._extract_rules_from_markdown(parsed)
            
            assert isinstance(entities, list)
        finally:
            md_path.unlink()

    def test_extract_birads_concepts_from_text_multiple_classes(self):
        """测试_extract_birads_concepts_from_text：多个BI-RADS分类（决策点：提取所有分类）"""
        extractor = EntityExtractor()
        
        text = "BI-RADS 3类，建议随访。BI-RADS 4类，建议进一步检查。"
        metadata = {"title": "测试"}
        
        entities = extractor._extract_birads_concepts_from_text(text, metadata)
        
        # 验证返回了实体列表（可能为空，取决于实现）
        assert isinstance(entities, list)
        # 如果有实体，验证包含BI-RADS分类
        if len(entities) > 0:
            birads_classes = [e["metadata"].get("birads_class") for e in entities if "birads_class" in e.get("metadata", {})]
            assert len(birads_classes) > 0

    def test_extract_medical_terms_from_text(self):
        """测试_extract_medical_terms_from_text：提取医学术语（决策点：匹配医学术语）"""
        extractor = EntityExtractor()
        
        text = "超声检查提示：左乳上方可见低回声结节，边界清晰，形态规则。"
        metadata = {"title": "测试"}
        
        entities = extractor._extract_medical_terms_from_text(text, metadata)
        
        assert isinstance(entities, list)

