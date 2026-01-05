# MedCrux 项目结构

> **版本**：v1.3.0  
> **更新时间**：2026-01-05

---

## 📁 目录结构

```
MedCrux/
├── src/                          # Python源代码目录
│   └── medcrux/                  # MedCrux Python包
│       ├── api/                  # FastAPI REST API接口
│       │   └── main.py           # API主入口
│       ├── ingestion/            # 数据摄取模块
│       │   └── ocr_service.py    # OCR文本提取服务
│       ├── analysis/             # AI分析引擎
│       │   └── llm_engine.py     # LLM分析引擎（DeepSeek）
│       ├── rag/                  # RAG知识图谱模块
│       │   ├── graphrag_retriever.py      # GraphRAG检索器
│       │   ├── logical_consistency_checker.py  # 逻辑一致性检查器
│       │   ├── data_paths.py     # 数据路径常量
│       │   ├── data/             # RAG知识库数据
│       │   │   ├── breast_ultrasound_report_axioms.md  # 公理系统
│       │   │   ├── weak_evidence_chain.md  # 弱证据链
│       │   │   ├── knowledge_layer/       # 知识层
│       │   │   └── logic_layer/           # 逻辑层
│       │   └── extraction/       # 知识提取模块
│       │       ├── document_parser.py
│       │       ├── entity_extractor.py
│       │       └── relation_extractor.py
│       ├── ui/                   # Streamlit UI（v1.2.0及之前）
│       │   └── app.py
│       └── utils/                # 工具模块
│           └── logger.py         # 日志工具
│
├── frontend/                     # React前端应用（v1.3.0）
│   ├── src/                      # 前端源代码
│   │   ├── components/           # React组件
│   │   ├── services/             # API服务
│   │   └── types.ts              # TypeScript类型定义
│   ├── package.json
│   └── vite.config.ts
│
├── tests/                        # 测试代码
│   ├── test_api.py               # API测试
│   ├── test_llm_engine.py        # LLM引擎测试
│   └── ...
│
├── scripts/                      # 工具脚本
│   ├── start_api.sh              # 启动后端API
│   ├── start_frontend.sh         # 启动前端
│   ├── test_local.sh             # 本地测试脚本
│   └── test_e2e.sh               # 端到端测试脚本
│
├── docs/                         # 项目文档
│   ├── dev/                      # 开发文档（不跟踪）
│   └── gov/                      # 治理文档（不跟踪）
│
├── pyproject.toml                # Python项目配置
├── uv.lock                       # 依赖锁定文件
└── README.md                     # 项目说明
```

---

## 📦 模块说明

### `medcrux.api`
**职责**：FastAPI REST API接口层

- `main.py`：API主入口，定义所有REST端点
  - `/health`：健康检查
  - `/analyze/upload`：分析报告接口

### `medcrux.ingestion`
**职责**：数据摄取和预处理

- `ocr_service.py`：OCR文本提取服务
  - 使用RapidOCR从图片中提取文本
  - 支持JPG/PNG格式

### `medcrux.analysis`
**职责**：AI分析和推理

- `llm_engine.py`：LLM分析引擎
  - 集成DeepSeek大模型
  - 结合RAG检索结果进行医学逻辑分析
  - BI-RADS一致性检查

### `medcrux.rag`
**职责**：RAG知识图谱和检索

- `graphrag_retriever.py`：GraphRAG检索器
  - 从知识图谱中检索相关医学知识
  - 返回实体、关系和推理路径

- `logical_consistency_checker.py`：逻辑一致性检查器
  - 检查报告描述与BI-RADS分类的一致性

- `data/`：RAG知识库数据
  - `knowledge_layer/`：知识层（实体）
  - `logic_layer/`：逻辑层（关系）

- `extraction/`：知识提取模块
  - 从Markdown文档中提取实体和关系

### `medcrux.ui`
**职责**：Streamlit用户界面（v1.2.0及之前版本）

- `app.py`：Streamlit应用主入口

**注意**：v1.3.0使用React前端，此模块保留用于向后兼容。

### `medcrux.utils`
**职责**：通用工具函数

- `logger.py`：日志工具
  - 统一的日志配置
  - 错误追踪和上下文记录

---

## 🎯 设计原则

### 1. 模块化设计
- 每个模块职责单一、边界清晰
- 模块间通过明确的接口通信

### 2. 分层架构
```
API层 (api/)
    ↓
业务逻辑层 (analysis/)
    ↓
数据层 (ingestion/, rag/)
    ↓
工具层 (utils/)
```

### 3. 依赖方向
- 上层模块可以依赖下层模块
- 下层模块不依赖上层模块
- 工具模块可以被所有模块使用

### 4. 命名规范
- **模块名**：小写，使用下划线（如 `ocr_service.py`）
- **类名**：大驼峰（如 `GraphRAGRetriever`）
- **函数名**：小写，使用下划线（如 `extract_text_from_bytes`）

---

## 🔄 数据流

### 分析流程

```
用户上传图片
    ↓
ingestion.ocr_service (OCR提取文本)
    ↓
rag.graphrag_retriever (RAG检索相关知识)
    ↓
analysis.llm_engine (LLM分析 + 一致性检查)
    ↓
api.main (返回结果)
```

---

## 📝 代码组织规范

### 导入顺序
1. 标准库导入
2. 第三方库导入
3. 本地模块导入

### 文件结构
```python
"""
模块文档字符串
"""
# 导入
import ...

# 常量
CONSTANT = ...

# 类定义
class ClassName:
    ...

# 函数定义
def function_name():
    ...

# 主程序
if __name__ == "__main__":
    ...
```

---

## 🚀 扩展指南

### 添加新功能模块

1. **创建模块目录**
   ```bash
   mkdir -p src/medcrux/new_module
   touch src/medcrux/new_module/__init__.py
   touch src/medcrux/new_module/service.py
   ```

2. **实现功能**
   - 遵循模块职责单一原则
   - 添加适当的文档字符串
   - 使用统一的日志工具

3. **添加测试**
   ```bash
   touch tests/test_new_module.py
   ```

4. **更新文档**
   - 更新本文件
   - 更新README.md（如需要）

---

## 📚 相关文档

- **API文档**：启动后端后访问 `http://localhost:8000/docs`
- **开发指南**：`docs/dev/README.md`
- **版本规划**：`docs/dev/planning/VERSION_PLANNING_v1.3.0.md`

---

**最后更新**：2026-01-05

