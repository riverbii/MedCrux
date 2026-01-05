# MedCrux v1.3.0 手动启动指南

> **版本**：v1.3.0  
> **更新时间**：2026-01-05

---

## 📋 前置准备

### 1. 确保依赖已安装

```bash
# 进入项目目录
cd /Users/bixinfang/project/MedCrux

# 同步后端依赖（这会安装Python 3.12和所有Python包）
uv sync

# 安装前端依赖
cd src/frontend
npm install
cd ../..
```

### 2. 设置环境变量（可选）

如果需要AI分析功能，设置API Key：

```bash
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

**注意**：即使没有API Key，OCR功能仍可用。

---

## 🚀 启动步骤

### 方式一：使用启动脚本（推荐）

#### 终端1 - 启动后端

```bash
cd /Users/bixinfang/project/MedCrux
./scripts/start_api.sh
```

**预期输出**：
```
🚀 启动MedCrux API服务（使用uv）...
📦 安装/更新包（可编辑模式）...
✅ 使用uv运行服务...
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx]
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**验证后端启动**：
打开新终端，运行：
```bash
curl http://localhost:8000/health
```

应该返回：
```json
{"status":"operational","version":"1.3.0"}
```

#### 终端2 - 启动前端

```bash
cd /Users/bixinfang/project/MedCrux
./scripts/start_frontend.sh
```

**预期输出**：
```
🚀 启动 MedCrux Frontend (React + Vite)
✅ 启动开发服务器...
📍 前端地址: http://localhost:3000
📍 后端API: http://localhost:8000

  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

**验证前端启动**：
浏览器访问：http://localhost:3000

---

### 方式二：完全手动启动

#### 终端1 - 启动后端（完全手动）

```bash
# 1. 进入项目根目录
cd /Users/bixinfang/project/MedCrux

# 2. 确保依赖已同步
uv sync

# 3. 确保包已安装（可编辑模式）
uv pip install -e .

# 4. 设置PYTHONPATH（确保能找到medcrux模块）
export PYTHONPATH="/Users/bixinfang/project/MedCrux/src:$PYTHONPATH"

# 5. 启动后端服务
uv run uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
```

**关键点**：
- ✅ 必须在项目根目录运行
- ✅ 使用 `uv run` 而不是直接 `python`（确保使用Python 3.12）
- ✅ 设置 `PYTHONPATH` 确保能找到 `medcrux` 模块

#### 终端2 - 启动前端（完全手动）

```bash
# 1. 进入frontend目录
cd /Users/bixinfang/project/MedCrux/src/frontend

# 2. 确保依赖已安装
npm install

# 3. 启动开发服务器
npm run dev
```

**关键点**：
- ✅ 必须在 `src/frontend` 目录运行
- ✅ 使用 `npm run dev`（Vite开发服务器）

---

## ✅ 验证服务运行状态

### 1. 检查后端

```bash
# 健康检查
curl http://localhost:8000/health

# 应该返回：
# {"status":"operational","version":"1.3.0"}
```

### 2. 检查前端

- 打开浏览器访问：http://localhost:3000
- 应该看到MedCrux主页面

### 3. 检查API文档

- 访问：http://localhost:8000/docs
- 应该看到Swagger API文档界面

---

## 🐛 常见问题排查

### 问题1：后端启动失败 - ModuleNotFoundError

**错误信息**：
```
ModuleNotFoundError: No module named 'medcrux'
```

**解决方法**：
```bash
# 1. 确保在项目根目录
cd /Users/bixinfang/project/MedCrux

# 2. 重新同步依赖
uv sync

# 3. 重新安装包
uv pip install -e .

# 4. 设置PYTHONPATH
export PYTHONPATH="/Users/bixinfang/project/MedCrux/src:$PYTHONPATH"

# 5. 重新启动
uv run uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000
```

### 问题2：后端启动失败 - ImportError socksio

**错误信息**：
```
ImportError: Using SOCKS proxy, but the 'socksio' package is not installed.
```

**解决方法**：
```bash
# 重新同步依赖（已添加httpx[socks]依赖）
uv sync
```

### 问题3：端口被占用

**错误信息**：
```
ERROR:    [Errno 48] Address already in use
```

**解决方法**：
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 杀死进程
kill -9 <PID>
```

### 问题4：前端无法连接后端

**错误信息**：
```
Request failed with status code 500
```

**排查步骤**：
1. **确认后端已启动**：
   ```bash
   curl http://localhost:8000/health
   ```

2. **查看后端日志**：
   ```bash
   # 如果使用脚本启动，日志在：
   tail -f /tmp/medcrux_backend.log
   
   # 如果手动启动，日志在终端1中
   ```

3. **检查浏览器控制台**：
   - 按F12打开开发者工具
   - 查看Console标签页的错误信息
   - 查看Network标签页的请求详情

---

## 📝 启动检查清单

### 后端启动检查
- [ ] 在项目根目录运行
- [ ] 已运行 `uv sync`
- [ ] 已运行 `uv pip install -e .`
- [ ] 已设置 `PYTHONPATH`
- [ ] 使用 `uv run` 启动（不是系统python）
- [ ] 看到 "Uvicorn running on http://127.0.0.1:8000"
- [ ] 健康检查返回正常：`curl http://localhost:8000/health`

### 前端启动检查
- [ ] 在 `src/frontend` 目录运行
- [ ] 已运行 `npm install`
- [ ] 使用 `npm run dev` 启动
- [ ] 看到 "VITE ready"
- [ ] 浏览器可以访问 http://localhost:3000

---

## 🎯 快速启动命令总结

### 最简单的方式（使用脚本）

```bash
# 终端1
cd /Users/bixinfang/project/MedCrux
./scripts/start_api.sh

# 终端2（新开一个终端）
cd /Users/bixinfang/project/MedCrux
./scripts/start_frontend.sh
```

### 完全手动方式

```bash
# 终端1 - 后端
cd /Users/bixinfang/project/MedCrux
uv sync
uv pip install -e .
export PYTHONPATH="/Users/bixinfang/project/MedCrux/src:$PYTHONPATH"
uv run uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000

# 终端2 - 前端
cd /Users/bixinfang/project/MedCrux/src/frontend
npm install
npm run dev
```

---

## 📚 相关文档

- **QA测试指南**：`docs/dev/versions/v1.3.0/QA_TESTING_GUIDE.md`
- **测试清单**：`docs/dev/versions/v1.3.0/TEST_CHECKLIST.md`
- **安装指南**：`docs/dev/versions/v1.3.0/INSTALLATION.md`

---

**最后更新**：2026-01-05

