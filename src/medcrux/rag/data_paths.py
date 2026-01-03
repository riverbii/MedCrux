"""
RAG数据路径常量模块

定义RAG知识库数据文件的路径，方便代码中引用
"""

from pathlib import Path

# 获取当前模块所在目录（src/medcrux/rag/）
RAG_MODULE_DIR = Path(__file__).parent

# RAG数据根目录
RAG_DATA_DIR = RAG_MODULE_DIR / "data"

# 知识层路径
KNOWLEDGE_LAYER_DIR = RAG_DATA_DIR / "knowledge_layer"
ENTITIES_DIR = KNOWLEDGE_LAYER_DIR / "entities"
EMBEDDINGS_DIR = KNOWLEDGE_LAYER_DIR / "embeddings"
KNOWLEDGE_METADATA_DIR = KNOWLEDGE_LAYER_DIR / "metadata"

# 逻辑层路径
LOGIC_LAYER_DIR = RAG_DATA_DIR / "logic_layer"
RELATIONS_DIR = LOGIC_LAYER_DIR / "relations"
GRAPH_DIR = LOGIC_LAYER_DIR / "graph"
LOGIC_METADATA_DIR = LOGIC_LAYER_DIR / "metadata"

# 公理系统文件
AXIOMS_FILE = RAG_DATA_DIR / "breast_ultrasound_report_axioms.md"

# 实体索引文件
ENTITY_INDEX_FILE = KNOWLEDGE_METADATA_DIR / "entity_index.json"

# 关系索引文件
RELATION_INDEX_FILE = LOGIC_METADATA_DIR / "relation_index.json"

# 实体类型目录
AXIOM_DIR = ENTITIES_DIR / "axiom"
CONCEPT_DIR = ENTITIES_DIR / "concept"
TERM_DIR = ENTITIES_DIR / "term"
RULE_DIR = ENTITIES_DIR / "rule"

# 关系类型目录
IMPLIES_DIR = RELATIONS_DIR / "implies"
EQUIVALENT_DIR = RELATIONS_DIR / "equivalent"
EXCLUSIVE_DIR = RELATIONS_DIR / "exclusive"
CONTAINS_DIR = RELATIONS_DIR / "contains"
