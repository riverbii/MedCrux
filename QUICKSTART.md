# MedCrux 快速启动指南

> **创建日期**：2026-01-03 22:24:48

## 问题排查

如果后台服务启动失败，请按以下步骤检查：

### 1. 检查Python版本

```bash
python3 --version
```

**要求**：Python >= 3.12（推荐）或 >= 3.9（最低要求）

**注意**：如果使用Python 3.9，代码已兼容，但建议升级到3.12以获得更好的性能。

### 2. 安装依赖

**使用uv（推荐）**：
```bash
uv sync
```

**使用pip**：
```bash
pip install -e .
```

**验证安装**：
```bash
python3 -c "import fastapi; import streamlit; print('依赖安装成功')"
```

### 3. 配置环境变量

```bash
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

**验证**：
```bash
echo $DEEPSEEK_API_KEY
```

### 4. 检查模块导入

```bash
# 测试API模块
python3 -c "import sys; sys.path.insert(0, 'src'); import medcrux.api.main; print('API模块导入成功')"

# 测试GraphRAG模块
python3 -c "import sys; sys.path.insert(0, 'src'); from medcrux.rag.graphrag_retriever import GraphRAGRetriever; print('GraphRAG模块导入成功')"
```

### 5. 启动服务

**启动API服务**：
```bash
./scripts/start_api.sh
```

或手动启动：
```bash
uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
```

**启动UI界面**（新终端）：
```bash
./scripts/start_ui.sh
```

或手动启动：
```bash
streamlit run src/medcrux/ui/app.py
```

## 常见问题

### 问题1：ModuleNotFoundError: No module named 'fastapi'

**原因**：依赖未安装

**解决**：
```bash
pip install -e .
# 或
uv sync
```

### 问题2：TypeError: unsupported operand type(s) for |: 'type' and 'NoneType'

**原因**：Python版本过低（< 3.10），代码使用了`dict | None`语法

**解决**：代码已修复为`Optional[dict]`，兼容Python 3.9+。如果仍有问题，请确保使用最新代码。

### 问题3：无法连接后端

**原因**：API服务未启动或端口被占用

**解决**：
1. 检查API服务是否运行：`curl http://127.0.0.1:8000/health`
2. 检查端口是否被占用：`lsof -i :8000`
3. 如果端口被占用，修改启动脚本中的端口号

### 问题4：RAG知识库加载失败

**原因**：知识库数据文件缺失

**解决**：
1. 检查数据文件是否存在：`ls -la src/medcrux/rag/data/knowledge_layer/metadata/`
2. 如果缺失，运行数据抽取脚本：`python scripts/extract_rag_data.py`

## 验证服务状态

### 检查API服务

```bash
curl http://127.0.0.1:8000/health
```

预期响应：
```json
{"status":"operational","version":"0.1.0"}
```

### 检查UI界面

访问 `http://localhost:8501`，应该能看到上传界面。

---

**最后更新**：2026-01-03 22:24:48
