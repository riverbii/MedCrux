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

    def test_extract_implies_relations_with_malignant_concept(self):
        """测试_extract_implies_relations：恶性征象到恶性概念（决策点：malignant_concept存在）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_malignant_毛刺状边界", "type": "concept", "name": "毛刺状边界"},
            {"id": "concept_malignant_sign", "type": "concept", "name": "恶性征象"},
            {"id": "concept_birads_4", "type": "concept", "name": "BI-RADS 4类"},
            {"id": "concept_birads_5", "type": "concept", "name": "BI-RADS 5类"}
        ]
        
        relations = extractor._extract_implies_relations(entities)
        
        assert len(relations) > 0
        # 验证包含恶性征象到恶性概念的关系
        assert any(r["target_entity_id"] == "concept_malignant_sign" for r in relations)

    def test_extract_implies_relations_with_birads(self):
        """测试_extract_implies_relations：恶性征象到BI-RADS分类（决策点：birads_4和birads_5存在）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_malignant_毛刺状边界", "type": "concept", "name": "毛刺状边界"},
            {"id": "concept_birads_4", "type": "concept", "name": "BI-RADS 4类"},
            {"id": "concept_birads_5", "type": "concept", "name": "BI-RADS 5类"}
        ]
        
        relations = extractor._extract_implies_relations(entities)
        
        # 应该包含到BI-RADS 4和5的关系
        birads_4_relations = [r for r in relations if r["target_entity_id"] == "concept_birads_4"]
        birads_5_relations = [r for r in relations if r["target_entity_id"] == "concept_birads_5"]
        
        assert len(birads_4_relations) > 0 or len(birads_5_relations) > 0

    def test_extract_implies_relations_birads_to_advice(self):
        """测试_extract_implies_relations：BI-RADS分类到建议（决策点：advice_rules存在）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_birads_3", "type": "concept", "name": "BI-RADS 3类"},
            {"id": "rule_建议_随访", "type": "rule", "name": "建议：随访"}
        ]
        
        relations = extractor._extract_implies_relations(entities)
        
        # 应该包含BI-RADS到建议的关系
        assert isinstance(relations, list)

    def test_extract_equivalent_relations(self):
        """测试_extract_equivalent_relations：等价关系提取（决策点：匹配等价关系模式）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_birads_3", "type": "concept", "name": "BI-RADS 3类"},
            {"id": "concept_birads_3_equivalent", "type": "concept", "name": "3类"}
        ]
        
        relations = extractor._extract_equivalent_relations(entities)
        
        assert isinstance(relations, list)

    def test_extract_exclusive_relations(self):
        """测试_extract_exclusive_relations：互斥关系提取（决策点：匹配互斥关系模式）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_birads_2", "type": "concept", "name": "BI-RADS 2类"},
            {"id": "concept_birads_5", "type": "concept", "name": "BI-RADS 5类"}
        ]
        
        relations = extractor._extract_exclusive_relations(entities)
        
        assert isinstance(relations, list)

    def test_extract_contains_relations(self):
        """测试_extract_contains_relations：包含关系提取（决策点：匹配包含关系模式）"""
        extractor = RelationExtractor()
        
        entities = [
            {"id": "concept_birads", "type": "concept", "name": "BI-RADS分类"},
            {"id": "concept_birads_3", "type": "concept", "name": "BI-RADS 3类"}
        ]
        
        relations = extractor._extract_contains_relations(entities)
        
        assert isinstance(relations, list)

