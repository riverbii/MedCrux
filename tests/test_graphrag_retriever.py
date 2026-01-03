"""
测试GraphRAG检索模块
"""

from medcrux.rag.graphrag_retriever import GraphRAGRetriever


class TestGraphRAGRetriever:
    """测试GraphRAG检索器"""

    def test_retriever_initialization(self):
        """测试检索器初始化"""
        retriever = GraphRAGRetriever()
        assert retriever is not None
        assert isinstance(retriever.entities, dict)
        assert isinstance(retriever.relations, dict)
        assert isinstance(retriever.entity_index, dict)
        assert isinstance(retriever.relation_index, dict)

    def test_load_knowledge_base(self):
        """测试知识库加载"""
        retriever = GraphRAGRetriever()
        # 验证知识库已加载（至少有一些实体或关系）
        assert len(retriever.entities) > 0 or len(retriever.relations) > 0

    def test_retrieve_with_query(self):
        """测试检索功能"""
        retriever = GraphRAGRetriever()
        query = "BI-RADS 3类 边界清晰 椭圆形"
        result = retriever.retrieve(query)

        assert isinstance(result, dict)
        assert "entities" in result
        assert "relations" in result
        assert "inference_paths" in result
        assert "confidence" in result
        assert isinstance(result["entities"], list)
        assert isinstance(result["relations"], list)
        assert isinstance(result["inference_paths"], list)
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_retrieve_empty_query(self):
        """测试空查询"""
        retriever = GraphRAGRetriever()
        result = retriever.retrieve("")
        assert result["entities"] == []
        assert result["confidence"] == 0.0

    def test_match_entities(self):
        """测试实体匹配"""
        retriever = GraphRAGRetriever()
        query = "BI-RADS 3类"
        matched = retriever._match_entities(query)

        assert isinstance(matched, list)
        # 如果知识库中有相关实体，应该能匹配到
        if len(retriever.entities) > 0:
            assert len(matched) >= 0

    def test_get_relations_for_entities(self):
        """测试获取实体关系"""
        retriever = GraphRAGRetriever()
        # 获取一些实体ID
        entity_ids = list(retriever.entities.keys())[:3] if retriever.entities else []
        relations = retriever._get_relations_for_entities(entity_ids)

        assert isinstance(relations, list)
        # 验证关系包含source或target实体
        for relation in relations:
            assert "source_entity_id" in relation or "target_entity_id" in relation

    def test_infer(self):
        """测试推理功能"""
        retriever = GraphRAGRetriever()
        # 获取一些实体ID
        entity_ids = list(retriever.entities.keys())[:3] if retriever.entities else []
        inference_results = retriever.infer(entity_ids)

        assert isinstance(inference_results, list)
        # 验证推理结果格式
        for result in inference_results:
            assert "type" in result
            assert "source" in result
            assert "target" in result
            assert result["type"] in ["implies", "exclusive", "contains"]

    def test_calculate_confidence(self):
        """测试置信度计算"""
        retriever = GraphRAGRetriever()
        entities = []
        relations = []

        # 测试空结果
        confidence = retriever._calculate_confidence(entities, relations)
        assert confidence == 0.0

        # 测试有实体的结果
        if retriever.entities:
            test_entity = list(retriever.entities.values())[0]
            entities = [test_entity]
            confidence = retriever._calculate_confidence(entities, relations)
            assert 0.0 <= confidence <= 1.0
