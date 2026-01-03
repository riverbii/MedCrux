"""
关系提取模块：从解析后的文档和实体中提取逻辑关系
"""

from datetime import datetime

from medcrux.utils.logger import setup_logger

logger = setup_logger("medcrux.rag.extraction")


class RelationExtractor:
    """逻辑关系提取器"""

    def __init__(self):
        self.logger = logger
        self.relation_counter = 0

    def extract_from_markdown(self, parsed: dict, entities: list[dict]) -> list[dict]:
        """
        从Markdown文档中提取逻辑关系

        Args:
            parsed: 解析后的Markdown文档
            entities: 已提取的知识实体

        Returns:
            逻辑关系列表
        """
        relations = []

        # 从公理系统中提取关系
        if "breast_ultrasound_report_axioms" in parsed["path"]:
            relations.extend(self._extract_implies_relations(entities))
            relations.extend(self._extract_equivalent_relations(entities))
            relations.extend(self._extract_exclusive_relations(entities))
            relations.extend(self._extract_contains_relations(entities))

        return relations

    def extract_from_pdf(self, parsed: dict, entities: list[dict]) -> list[dict]:
        """
        从PDF文档中提取逻辑关系

        Args:
            parsed: 解析后的PDF文档
            entities: 已提取的知识实体

        Returns:
            逻辑关系列表
        """
        relations = []

        # 从PDF中提取的关系较少，主要是概念之间的关联
        # 这里可以扩展更复杂的关系提取逻辑

        return relations

    def _extract_implies_relations(self, entities: list[dict]) -> list[dict]:
        """提取蕴含关系（A → B）"""
        relations = []

        # 恶性征象 → 恶性可能性
        malignant_signs = [e for e in entities if e["id"].startswith("concept_malignant_")]
        malignant_concept = next((e for e in entities if e["id"] == "concept_malignant_sign"), None)

        if malignant_concept:
            for sign_entity in malignant_signs:
                relation_id = f"rel_implies_{sign_entity['id']}_to_malignant"
                self.relation_counter += 1

                relations.append(
                    {
                        "id": relation_id,
                        "source_entity_id": sign_entity["id"],
                        "target_entity_id": "concept_malignant_sign",
                        "relation_type": "implies",
                        "strength": 0.95,
                        "conditions": None,
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "confidence": 0.95,
                        },
                    }
                )

        # 恶性征象 → BI-RADS 4类或5类
        birads_4 = next((e for e in entities if e["id"] == "concept_birads_4"), None)
        birads_5 = next((e for e in entities if e["id"] == "concept_birads_5"), None)

        for sign_entity in malignant_signs:
            if birads_4:
                relation_id = f"rel_implies_{sign_entity['id']}_to_birads_4"
                self.relation_counter += 1

                relations.append(
                    {
                        "id": relation_id,
                        "source_entity_id": sign_entity["id"],
                        "target_entity_id": "concept_birads_4",
                        "relation_type": "implies",
                        "strength": 0.80,
                        "conditions": {"multiple_signs": False},
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "confidence": 0.80,
                        },
                    }
                )

            if birads_5:
                relation_id = f"rel_implies_{sign_entity['id']}_to_birads_5"
                self.relation_counter += 1

                relations.append(
                    {
                        "id": relation_id,
                        "source_entity_id": sign_entity["id"],
                        "target_entity_id": "concept_birads_5",
                        "relation_type": "implies",
                        "strength": 0.90,
                        "conditions": {"multiple_signs": True},
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "confidence": 0.90,
                        },
                    }
                )

        # BI-RADS分类 → 建议
        birads_concepts = [e for e in entities if e["id"].startswith("concept_birads_")]
        advice_rules = [e for e in entities if e["id"].startswith("rule_") and "建议" in e.get("name", "")]

        for birads_entity in birads_concepts:
            birads_class = birads_entity["id"].split("_")[-1]
            # 查找对应的建议规则
            for rule_entity in advice_rules:
                if birads_class in rule_entity.get("content", ""):
                    relation_id = f"rel_implies_{birads_entity['id']}_to_{rule_entity['id']}"
                    self.relation_counter += 1

                    relations.append(
                        {
                            "id": relation_id,
                            "source_entity_id": birads_entity["id"],
                            "target_entity_id": rule_entity["id"],
                            "relation_type": "requires",
                            "strength": 1.0,
                            "conditions": None,
                            "metadata": {
                                "created_date": datetime.now().strftime("%Y-%m-%d"),
                                "author": "MD",
                                "confidence": 1.0,
                            },
                        }
                    )

        return relations

    def _extract_equivalent_relations(self, entities: list[dict]) -> list[dict]:
        """提取等价关系（A ↔ B）"""
        relations = []

        # BI-RADS 3类 ↔ 可能良性
        birads_3 = next((e for e in entities if e["id"] == "concept_birads_3"), None)
        probably_benign = next((e for e in entities if e["id"] == "concept_probably_benign"), None)

        if birads_3 and probably_benign:
            relation_id = "rel_equivalent_birads_3_probably_benign"
            self.relation_counter += 1

            relations.append(
                {
                    "id": relation_id,
                    "source_entity_id": birads_3["id"],
                    "target_entity_id": probably_benign["id"],
                    "relation_type": "equivalent",
                    "strength": 1.0,
                    "conditions": None,
                    "metadata": {
                        "created_date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "MD",
                        "confidence": 1.0,
                    },
                }
            )

        return relations

    def _extract_exclusive_relations(self, entities: list[dict]) -> list[dict]:
        """提取互斥关系（A ⊥ B）"""
        relations = []

        # BI-RADS分类之间互斥
        birads_concepts = [e for e in entities if e["id"].startswith("concept_birads_")]

        for i, entity1 in enumerate(birads_concepts):
            for entity2 in birads_concepts[i + 1 :]:
                # 排除4A、4B、4C之间的互斥（它们是4类的细分）
                class1 = entity1["id"].split("_")[-1]
                class2 = entity2["id"].split("_")[-1]

                if class1.startswith("4") and class2.startswith("4"):
                    continue  # 4A、4B、4C不互斥

                relation_id = f"rel_exclusive_{entity1['id']}_{entity2['id']}"
                self.relation_counter += 1

                relations.append(
                    {
                        "id": relation_id,
                        "source_entity_id": entity1["id"],
                        "target_entity_id": entity2["id"],
                        "relation_type": "exclusive",
                        "strength": 1.0,
                        "conditions": None,
                        "metadata": {
                            "created_date": datetime.now().strftime("%Y-%m-%d"),
                            "author": "MD",
                            "confidence": 1.0,
                        },
                    }
                )

        return relations

    def _extract_contains_relations(self, entities: list[dict]) -> list[dict]:
        """提取包含关系（A contains B）"""
        relations = []

        # 公理包含术语
        axioms = [e for e in entities if e["type"] == "axiom"]
        terms = [e for e in entities if e["type"] == "term"]

        for axiom in axioms:
            axiom_content = axiom.get("content", "").lower()

            for term in terms:
                term_name = term.get("name", "").lower()
                # 如果公理内容包含术语
                if term_name in axiom_content:
                    relation_id = f"rel_contains_{axiom['id']}_{term['id']}"
                    self.relation_counter += 1

                    relations.append(
                        {
                            "id": relation_id,
                            "source_entity_id": axiom["id"],
                            "target_entity_id": term["id"],
                            "relation_type": "contains",
                            "strength": 1.0,
                            "conditions": None,
                            "metadata": {
                                "created_date": datetime.now().strftime("%Y-%m-%d"),
                                "author": "MD",
                                "confidence": 0.8,
                            },
                        }
                    )

        # 规则包含概念
        rules = [e for e in entities if e["type"] == "rule"]
        concepts = [e for e in entities if e["type"] == "concept"]

        for rule in rules:
            rule_content = rule.get("content", "").lower()

            for concept in concepts:
                concept_name = concept.get("name", "").lower()
                if concept_name in rule_content:
                    relation_id = f"rel_contains_{rule['id']}_{concept['id']}"
                    self.relation_counter += 1

                    relations.append(
                        {
                            "id": relation_id,
                            "source_entity_id": rule["id"],
                            "target_entity_id": concept["id"],
                            "relation_type": "contains",
                            "strength": 1.0,
                            "conditions": None,
                            "metadata": {
                                "created_date": datetime.now().strftime("%Y-%m-%d"),
                                "author": "MD",
                                "confidence": 0.8,
                            },
                        }
                    )

        return relations
