#!/usr/bin/env python3
"""
从source_data抽取RAG数据到src/medcrux/rag/data/目录

数据源：
1. src/medcrux/rag/data/breast_ultrasound_report_axioms.md（公理系统）
2. source_data/raw/*.pdf（医学指南PDF文件）
3. source_data/raw/*.md（其他Markdown文件）

输出：
- src/medcrux/rag/data/knowledge_layer/entities/（知识实体）
- src/medcrux/rag/data/logic_layer/relations/（逻辑关系）

注意：数据只保存在src/medcrux/rag/data/，这是源码的一部分。
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# 必须在修改sys.path之后导入
from medcrux.rag.extraction.document_parser import DocumentParser  # noqa: E402
from medcrux.rag.extraction.entity_extractor import EntityExtractor  # noqa: E402
from medcrux.rag.extraction.relation_extractor import RelationExtractor  # noqa: E402
from medcrux.utils.logger import setup_logger  # noqa: E402

logger = setup_logger("extract_rag_data")


def main():
    """主函数：执行数据抽取"""
    logger.info("开始数据抽取...")

    # 初始化解析器和提取器
    parser = DocumentParser()
    entity_extractor = EntityExtractor()
    relation_extractor = RelationExtractor()

    # 定义数据源路径
    project_root = Path(__file__).parent.parent
    source_data_dir = project_root / "source_data" / "raw"
    # 公理系统文件在src/medcrux/rag/data/中
    axioms_file = project_root / "src" / "medcrux" / "rag" / "data" / "breast_ultrasound_report_axioms.md"

    # 定义输出路径（输出到src/medcrux/rag/data/）
    output_knowledge_dir = project_root / "src" / "medcrux" / "rag" / "data" / "knowledge_layer" / "entities"
    output_logic_dir = project_root / "src" / "medcrux" / "rag" / "data" / "logic_layer" / "relations"

    # 确保输出目录存在
    output_knowledge_dir.mkdir(parents=True, exist_ok=True)
    output_logic_dir.mkdir(parents=True, exist_ok=True)

    all_entities = []
    all_relations = []

    # 1. 处理公理系统（Markdown）
    if axioms_file.exists():
        logger.info(f"处理公理系统：{axioms_file}")
        try:
            parsed = parser.parse_markdown(axioms_file)
            entities = entity_extractor.extract_from_markdown(parsed)
            relations = relation_extractor.extract_from_markdown(parsed, entities)

            all_entities.extend(entities)
            all_relations.extend(relations)

            logger.info(f"从公理系统提取了 {len(entities)} 个实体，{len(relations)} 个关系")
        except Exception as e:
            logger.error(f"处理公理系统失败：{e}", exc_info=True)

    # 2. 处理PDF文件
    pdf_files = list(source_data_dir.glob("*.pdf")) + list(source_data_dir.glob("*.PDF"))
    logger.info(f"找到 {len(pdf_files)} 个PDF文件")

    for pdf_file in pdf_files:
        logger.info(f"处理PDF文件：{pdf_file.name}")
        try:
            parsed = parser.parse_pdf(pdf_file)
            if parsed.get("error"):
                logger.warning(f"跳过 {pdf_file.name}：{parsed['error']}")
                continue

            entities = entity_extractor.extract_from_pdf(parsed)
            relations = relation_extractor.extract_from_pdf(parsed, entities)

            all_entities.extend(entities)
            all_relations.extend(relations)

            logger.info(f"从 {pdf_file.name} 提取了 {len(entities)} 个实体，{len(relations)} 个关系")
        except Exception as e:
            logger.error(f"处理PDF文件 {pdf_file.name} 失败：{e}", exc_info=True)

    # 3. 处理其他Markdown文件
    md_files = [f for f in source_data_dir.glob("*.md") if f.name != "breast_ultrasound_report_axioms.md"]
    logger.info(f"找到 {len(md_files)} 个Markdown文件")

    for md_file in md_files:
        logger.info(f"处理Markdown文件：{md_file.name}")
        try:
            parsed = parser.parse_markdown(md_file)
            entities = entity_extractor.extract_from_markdown(parsed)
            relations = relation_extractor.extract_from_markdown(parsed, entities)

            all_entities.extend(entities)
            all_relations.extend(relations)

            logger.info(f"从 {md_file.name} 提取了 {len(entities)} 个实体，{len(relations)} 个关系")
        except Exception as e:
            logger.error(f"处理Markdown文件 {md_file.name} 失败：{e}", exc_info=True)

    # 4. 保存知识实体
    logger.info(f"保存 {len(all_entities)} 个知识实体...")
    entity_index = {}
    for entity in all_entities:
        entity_type = entity["type"]
        entity_id = entity["id"]

        # 按类型分类保存
        type_dir = output_knowledge_dir / entity_type
        type_dir.mkdir(parents=True, exist_ok=True)

        entity_file = type_dir / f"{entity_id}.json"
        with open(entity_file, "w", encoding="utf-8") as f:
            json.dump(entity, f, ensure_ascii=False, indent=2)

        # 使用相对于src/medcrux/rag/data的路径
        relative_path = entity_file.relative_to(project_root / "src" / "medcrux" / "rag" / "data")
        entity_index[entity_id] = {
            "type": entity_type,
            "name": entity["name"],
            "file": str(relative_path),
        }

    # 保存实体索引
    index_file = (
        project_root / "src" / "medcrux" / "rag" / "data" / "knowledge_layer" / "metadata" / "entity_index.json"
    )
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(entity_index, f, ensure_ascii=False, indent=2)

    # 5. 保存逻辑关系
    logger.info(f"保存 {len(all_relations)} 个逻辑关系...")
    relation_index = {}
    for relation in all_relations:
        relation_type = relation["relation_type"]
        relation_id = relation["id"]

        # 按关系类型分类保存
        type_dir = output_logic_dir / relation_type
        type_dir.mkdir(parents=True, exist_ok=True)

        relation_file = type_dir / f"{relation_id}.json"
        with open(relation_file, "w", encoding="utf-8") as f:
            json.dump(relation, f, ensure_ascii=False, indent=2)

        # 使用相对于src/medcrux/rag/data的路径
        relative_path = relation_file.relative_to(project_root / "src" / "medcrux" / "rag" / "data")
        relation_index[relation_id] = {
            "type": relation_type,
            "source": relation["source_entity_id"],
            "target": relation["target_entity_id"],
            "file": str(relative_path),
        }

    # 保存关系索引
    index_file = project_root / "src" / "medcrux" / "rag" / "data" / "logic_layer" / "metadata" / "relation_index.json"
    index_file.parent.mkdir(parents=True, exist_ok=True)
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(relation_index, f, ensure_ascii=False, indent=2)

    logger.info("数据抽取完成！")
    logger.info(f"总计：{len(all_entities)} 个实体，{len(all_relations)} 个关系")


if __name__ == "__main__":
    main()
