# RAG知识库数据

> **位置**：`src/medcrux/rag/data/`  
> **用途**：存储GraphRAG知识层和逻辑层数据

## 目录结构

```
data/
├── breast_ultrasound_report_axioms.md  # 公理系统（最终版本）
├── weak_evidence_chain.md              # 弱证据链知识库（最终版本）
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

1. **公理系统**：`breast_ultrasound_report_axioms.md`（基于ACR BI-RADS等权威标准）
2. **弱证据链知识库**：`weak_evidence_chain.md`（未经充分验证的医学知识）

## 数据更新

运行数据抽取脚本更新数据：

```bash
python scripts/extract_rag_data.py
```

脚本会从以下数据源提取知识：
- `src/medcrux/rag/data/breast_ultrasound_report_axioms.md`（公理系统）
- `src/medcrux/rag/data/weak_evidence_chain.md`（弱证据链知识库）

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

**注意**：本文档为数据目录的说明文档。详细的版本历史和研发过程请参考开发文档。
