# MedCrux v1.3.0 快速测试指南

> **版本号**：v1.3.0  
> **更新时间**：2026-01-05

---

## 🚀 3步快速测试

### 步骤1：安装依赖（首次运行）

```bash
# 后端依赖
uv sync
# 或
pip install -e .

# 前端依赖
cd frontend
npm install
cd ..
```

### 步骤2：启动服务

**方式一：使用测试脚本（推荐）**

```bash
./test_local.sh
```

**方式二：手动启动**

```bash
# 终端1：启动后端
./scripts/start_api.sh

# 终端2：启动前端
./scripts/start_frontend.sh
```

### 步骤3：访问应用

- **前端地址**：http://localhost:3000
- **后端API**：http://localhost:8000
- **API文档**：http://localhost:8000/docs

---

## ✅ 快速验证清单

### 基础验证（5分钟）

- [ ] 打开 http://localhost:3000，页面正常加载
- [ ] Logo显示正常
- [ ] 导航菜单显示正常
- [ ] 文件上传区域显示正常
- [ ] 页脚显示正常

### 功能验证（10分钟）

- [ ] 上传测试图片（JPG/PNG格式）
- [ ] 图片预览显示
- [ ] 点击"开始分析"按钮
- [ ] 分析状态显示（6个阶段）
- [ ] 分析完成后，结果正确显示

### 交互验证（5分钟）

- [ ] 点击"科普教育" → "BI-RADS分级说明"，模态框打开
- [ ] 点击异常发现列表项，详情更新
- [ ] 点击胸部示意图标记，选择异常发现
- [ ] 点击"Privacy Policy"，模态框打开

---

## 🔧 常见问题

### 问题1：端口被占用

```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 杀死进程
kill -9 <PID>
```

### 问题2：前端无法连接后端

1. 确认后端已启动：访问 http://localhost:8000/health
2. 检查 `frontend/vite.config.ts` 中的代理配置

### 问题3：npm依赖安装失败

```bash
cd frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 📋 详细测试

如需详细测试，请参考：
- `docs/dev/versions/v1.3.0/LOCAL_TESTING.md`（完整测试指南）
- `docs/dev/versions/v1.3.0/TEST_CHECKLIST.md`（测试清单）

---

**MedCrux v1.3.0** - 快速测试指南

