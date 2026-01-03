# RAG知识库数据

> **位置**：`src/medcrux/rag/data/`
> **用途**：存储GraphRAG知识层和逻辑层数据

## 目录结构

```
data/
├── breast_ultrasound_report_axioms.md  # MD建立的公理系统（原始文件）
├── knowledge_layer/                    # 知识层
│   ├── entities/                      # 知识实体
│   │   ├── axiom/                     # 公理实体
│   │   ├── concept/                   # 概念实体
│   │   ├── term/                      # 术语实体
│   │   └── rule/                      # 规则实体
│   ├── embeddings/                     # 向量嵌入（待生成）
│   └── metadata/
│       └── entity_index.json          # 实体索引
└── logic_layer/                        # 逻辑层
    ├── relations/                      # 逻辑关系
    │   ├── implies/                    # 蕴含关系
    │   ├── equivalent/                 # 等价关系
    │   ├── exclusive/                  # 互斥关系
    │   └── contains/                   # 包含关系
    ├── graph/                          # 图结构（待生成）
    └── metadata/
        └── relation_index.json        # 关系索引
```

## 数据统计

- **知识实体**：61个
  - 公理实体：38个
  - 概念实体：12个
  - 术语实体：10个
  - 规则实体：1个

- **逻辑关系**：173个
  - 蕴含关系：10个
  - 互斥关系：21个
  - 包含关系：84个
  - 其他关系：58个

## 数据来源

1. **公理系统**：`breast_ultrasound_report_axioms.md`（MD建立）
2. **医学指南**：`source_data/raw/*.pdf`（待处理，需要PDF解析库）

## 数据更新

运行数据抽取脚本更新数据：

```bash
python scripts/extract_rag_data.py
```

脚本会从以下数据源提取知识：
- `src/medcrux/rag/data/breast_ultrasound_report_axioms.md`（公理系统）
- `source_data/raw/*.pdf`（医学指南PDF文件）
- `source_data/raw/*.md`（其他Markdown文件）

提取的数据会保存到`src/medcrux/rag/data/`目录（覆盖现有数据）。

## 代码引用

在代码中使用`data_paths.py`模块获取数据路径：

```python
from medcrux.rag.data_paths import (
    RAG_DATA_DIR,
    ENTITIES_DIR,
    RELATIONS_DIR,
    ENTITY_INDEX_FILE,
    RELATION_INDEX_FILE,
)
```

---

**版本**：v1.0
**创建日期**：2026-01-03
**最后更新**：2026-01-03 21:56:57
