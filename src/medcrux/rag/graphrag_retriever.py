"""
GraphRAG检索模块：基于知识图谱的检索和推理

根据ARCHITECTURE_GraphRAG_v1.0.md设计：
- 从知识层检索相关实体
- 从逻辑层检索相关关系
- 基于逻辑关系进行推理
"""

import json

from medcrux.rag.data_paths import (
    ENTITY_INDEX_FILE,
    RAG_DATA_DIR,
    RELATION_INDEX_FILE,
)
from medcrux.utils.logger import log_error_with_context, setup_logger

logger = setup_logger("medcrux.rag.graphrag")


class GraphRAGRetriever:
    """GraphRAG检索器：基于知识图谱的检索和推理"""

    def __init__(self):
        """初始化检索器，加载知识库数据"""
        self.entities: dict[str, dict] = {}
        self.relations: dict[str, dict] = {}
        self.entity_index: dict[str, dict] = {}
        self.relation_index: dict[str, dict] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        """加载知识库数据"""
        try:
            # 加载实体索引
            if ENTITY_INDEX_FILE.exists():
                with open(ENTITY_INDEX_FILE, encoding="utf-8") as f:
                    self.entity_index = json.load(f)
                logger.info(f"加载实体索引：{len(self.entity_index)} 个实体")

                # 加载所有实体
                for entity_id, entity_info in self.entity_index.items():
                    entity_file = RAG_DATA_DIR / entity_info["file"]
                    if entity_file.exists():
                        with open(entity_file, encoding="utf-8") as f:
                            self.entities[entity_id] = json.load(f)
                logger.info(f"加载实体数据：{len(self.entities)} 个实体")

            # 加载关系索引
            if RELATION_INDEX_FILE.exists():
                with open(RELATION_INDEX_FILE, encoding="utf-8") as f:
                    self.relation_index = json.load(f)
                logger.info(f"加载关系索引：{len(self.relation_index)} 个关系")

                # 加载所有关系
                for relation_id, relation_info in self.relation_index.items():
                    relation_file = RAG_DATA_DIR / relation_info["file"]
                    if relation_file.exists():
                        with open(relation_file, encoding="utf-8") as f:
                            self.relations[relation_id] = json.load(f)
                logger.info(f"加载关系数据：{len(self.relations)} 个关系")

        except Exception as e:
            log_error_with_context(logger, e, context={"operation": "加载知识库"}, operation="GraphRAG初始化")
            raise

    def retrieve(self, query: str) -> dict:
        """
        检索相关知识

        Args:
            query: 查询文本（如OCR识别的报告文本）

        Returns:
            {
                "entities": List[dict],  # 相关实体
                "relations": List[dict],  # 相关关系
                "inference_paths": List[List[str]],  # 推理路径
                "confidence": float  # 置信度
            }
        """
        try:
            # 1. 关键词匹配检索实体
            relevant_entities = self._match_entities(query)
            logger.debug(f"匹配到 {len(relevant_entities)} 个相关实体")

            # 2. 检索相关关系
            relevant_relations = self._get_relations_for_entities([e["id"] for e in relevant_entities])
            logger.debug(f"匹配到 {len(relevant_relations)} 个相关关系")

            # 3. 生成推理路径
            inference_paths = self._generate_inference_paths([e["id"] for e in relevant_entities], relevant_relations)

            # 4. 计算置信度（基于匹配度和关系强度）
            confidence = self._calculate_confidence(relevant_entities, relevant_relations)

            return {
                "entities": relevant_entities,
                "relations": relevant_relations,
                "inference_paths": inference_paths,
                "confidence": confidence,
            }

        except Exception as e:
            log_error_with_context(logger, e, context={"query": query}, operation="GraphRAG检索")
            return {
                "entities": [],
                "relations": [],
                "inference_paths": [],
                "confidence": 0.0,
            }

    def _match_entities(self, query: str) -> list[dict]:
        """根据查询文本匹配相关实体"""
        matched_entities = []
        query_lower = query.lower()

        for entity_id, entity in self.entities.items():
            score = 0.0

            # 匹配实体名称
            if entity.get("name"):
                name_lower = entity["name"].lower()
                if name_lower in query_lower or query_lower in name_lower:
                    score += 0.5

            # 匹配实体内容
            if entity.get("content"):
                content_lower = entity["content"].lower()
                # 计算关键词匹配度
                query_words = set(query_lower.split())
                content_words = set(content_lower.split())
                common_words = query_words & content_words
                if common_words:
                    score += len(common_words) / max(len(query_words), len(content_words))

            # 匹配实体ID中的关键词（如birads_3, malignant_毛刺状边界）
            entity_id_lower = entity_id.lower()
            for word in query_lower.split():
                if word in entity_id_lower:
                    score += 0.3

            if score > 0.1:  # 阈值
                matched_entities.append(
                    {
                        "id": entity_id,
                        "entity": entity,
                        "score": score,
                    }
                )

        # 按分数排序
        matched_entities.sort(key=lambda x: x["score"], reverse=True)
        # 返回前20个最相关的实体
        return [e["entity"] for e in matched_entities[:20]]

    def _get_relations_for_entities(self, entity_ids: list[str]) -> list[dict]:
        """获取与实体相关的关系"""
        relevant_relations = []

        for relation in self.relations.values():
            source_id = relation.get("source_entity_id")
            target_id = relation.get("target_entity_id")

            if source_id in entity_ids or target_id in entity_ids:
                relevant_relations.append(relation)

        return relevant_relations

    def _generate_inference_paths(self, entity_ids: list[str], relations: list[dict]) -> list[list[str]]:
        """生成推理路径"""
        paths = []

        # 简单的路径生成：找到实体之间的连接路径
        for relation in relations:
            source_id = relation.get("source_entity_id")
            target_id = relation.get("target_entity_id")

            if source_id in entity_ids and target_id in entity_ids:
                paths.append([source_id, target_id])

        return paths

    def _calculate_confidence(self, entities: list[dict], relations: list[dict]) -> float:
        """计算检索结果的置信度"""
        if not entities:
            return 0.0

        # 基于实体数量和关系强度计算置信度
        entity_score = min(len(entities) / 10.0, 1.0)  # 最多10个实体得满分

        relation_strength_sum = sum(r.get("strength", 0.5) for r in relations if r.get("strength"))
        relation_score = min(relation_strength_sum / len(relations), 1.0) if relations else 0.0

        # 综合置信度
        confidence = entity_score * 0.6 + relation_score * 0.4
        return min(confidence, 1.0)

    def infer(self, entity_ids: list[str]) -> list[dict]:
        """
        基于逻辑关系进行推理

        Args:
            entity_ids: 实体ID列表

        Returns:
            List[dict]: 推理结果和推理路径
        """
        try:
            inference_results = []

            # 1. 获取与这些实体相关的所有关系
            relevant_relations = self._get_relations_for_entities(entity_ids)

            # 2. 基于关系类型进行推理
            for relation in relevant_relations:
                relation_type = relation.get("relation_type")
                source_id = relation.get("source_entity_id")
                target_id = relation.get("target_entity_id")

                if relation_type == "implies":
                    # 蕴含关系：如果source存在，则target可能成立
                    if source_id in entity_ids:
                        inference_results.append(
                            {
                                "type": "implies",
                                "source": source_id,
                                "target": target_id,
                                "strength": relation.get("strength", 0.5),
                                "path": [source_id, target_id],
                            }
                        )

                elif relation_type == "exclusive":
                    # 互斥关系：如果source存在，则target不成立
                    if source_id in entity_ids:
                        inference_results.append(
                            {
                                "type": "exclusive",
                                "source": source_id,
                                "target": target_id,
                                "strength": relation.get("strength", 0.5),
                                "path": [source_id, target_id],
                            }
                        )

                elif relation_type == "contains":
                    # 包含关系：如果source存在，则target是source的一部分
                    if source_id in entity_ids:
                        inference_results.append(
                            {
                                "type": "contains",
                                "source": source_id,
                                "target": target_id,
                                "strength": relation.get("strength", 0.5),
                                "path": [source_id, target_id],
                            }
                        )

            return inference_results

        except Exception as e:
            log_error_with_context(
                logger,
                e,
                context={"entity_ids": entity_ids},
                operation="GraphRAG推理",
            )
            return []
