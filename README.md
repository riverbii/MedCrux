# MedCrux 🛡️

> 医学影像报告智能质控与决策辅助系统

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/riverbii/MedCrux/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Issues](https://img.shields.io/github/issues/riverbii/MedCrux)](https://github.com/riverbii/MedCrux/issues)

---

## 📖 项目简介

MedCrux 是一个基于 OCR 和大语言模型的医学影像报告智能分析系统，专注于乳腺超声报告的自动识别、分析和质控。系统能够自动提取报告文本，进行 BI-RADS 一致性检查，评估风险等级，并提供面向患者的智能建议。

### 核心能力

- **📸 OCR 文字识别**：基于 RapidOCR，支持从 JPG/PNG 格式的医学报告图片中提取文本
- **🤖 AI 智能分析**：集成 DeepSeek 大模型，对提取的文本进行医学逻辑分析
- **🔍 BI-RADS 一致性检查**：对照 ACR BI-RADS 标准，检查报告描述与结论的一致性
- **⚠️ 风险等级评估**：自动评估风险等级（Low/Medium/High）并给出预警
- **💡 智能建议**：基于分析结果提供面向患者的建议
- **🌐 Web 界面**：友好的用户界面，支持图片上传和结果可视化

---

## 🎯 项目定位

MedCrux 旨在为患者提供医学影像报告的第二意见参考，帮助患者更好地理解报告内容，发现潜在的不一致问题。系统**不提供医疗诊断**，所有分析结果仅供参考，不能替代专业医生的诊断和治疗建议。

### 适用场景

- **患者自查**：患者上传自己的医学影像报告，获取智能分析结果
- **第二意见**：作为专业医生诊断的补充参考
- **报告质控**：帮助发现报告中的潜在不一致问题
- **患者教育**：帮助患者理解 BI-RADS 分级制度和报告内容

### 不适用场景

- ❌ **不能替代专业医生诊断**
- ❌ **不能用于紧急医疗决策**
- ❌ **不能用于临床诊断**

---

## ✨ 功能概览

### 当前版本（v1.3.0）

#### 核心功能
- ✅ **OCR 文字识别**：支持 JPG/PNG 格式的医学报告图片
- ✅ **AI 智能分析**：基于 DeepSeek 大模型的医学逻辑分析
- ✅ **BI-RADS 一致性检查**：对照 ACR BI-RADS 标准检查一致性
- ✅ **风险等级评估**：自动评估风险等级（Low/Medium/High）
- ✅ **异常发现可视化**：胸部示意图展示异常发现位置
- ✅ **患者教育**：BI-RADS 分级制度说明

#### UI/UX 特性
- ✅ **现代化界面**：基于 React + TypeScript + Tailwind CSS（v1.3.0）
- ✅ **响应式设计**：支持桌面端和移动端
- ✅ **实时分析状态**：显示所有分析阶段（OCR、RAG、LLM、一致性检查）
- ✅ **交互式可视化**：异常发现列表、详情、示意图联动

### 技术架构

- **后端框架**：FastAPI
- **前端框架**：React + TypeScript + Tailwind CSS（v1.3.0），Streamlit（v1.2.0及之前）
- **OCR 引擎**：RapidOCR (ONNXRuntime)
- **图像处理**：OpenCV
- **AI 模型**：DeepSeek (OpenAI-compatible API)
- **知识图谱**：GraphRAG（基于医学公理系统）
- **代码质量**：Ruff (linting & formatting)
- **包管理**：uv

---

## 🚀 安装 / 使用

### 前置要求

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- DeepSeek API Key（用于 AI 分析功能）

### 快速开始

#### 1. 克隆项目

```bash
git clone https://github.com/riverbii/MedCrux.git
cd MedCrux
```

#### 2. 安装依赖

使用 uv（推荐）：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

#### 3. 配置环境变量

设置 DeepSeek API Key：

```bash
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

#### 4. 启动服务

**方式一：使用启动脚本（推荐）**

```bash
# 终端1：启动API服务
./scripts/start_api.sh

# 终端2：启动UI界面
./scripts/start_ui.sh
```

**方式二：手动启动（使用uv）**

```bash
# 终端1：启动API服务
uv run uvicorn medcrux.api.main:app --reload --host 127.0.0.1 --port 8000

# 终端2：启动UI界面
uv run streamlit run src/medcrux/ui/app.py
```

**注意**：
- 后端服务将在 `http://127.0.0.1:8000` 启动
- 前端界面将在浏览器中自动打开（默认 `http://localhost:8501`）
- 启动脚本使用 `uv run` 来运行服务，会自动使用正确的Python版本和依赖环境

### 使用说明

1. **上传报告图片**：在界面中点击上传按钮，选择医学影像报告图片（JPG/PNG 格式）
2. **查看原始图片**：上传后可在界面中查看原始影像
3. **开始分析**：点击"开始分析"按钮，系统将：
   - 使用 OCR 提取图片中的文字
   - 调用 AI 模型进行医学逻辑分析
   - 检查 BI-RADS 一致性
   - 评估风险等级
4. **查看结果**：
   - OCR 识别原文（可展开查看）
   - 异常发现列表和详情
   - 胸部示意图（标注异常发现位置）
   - 整体评估和建议

### API 文档

启动后端服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

#### 主要接口

**健康检查**

```http
GET /health
```

返回服务状态和版本信息。

**分析报告**

```http
POST /analyze/upload
Content-Type: multipart/form-data

file: <image_file>
```

上传医学报告图片进行分析，返回 OCR 文本和 AI 分析结果。

---

## 📝 License

本项目采用 [Apache License 2.0](https://github.com/riverbii/MedCrux/blob/main/LICENSE) 开源协议。

### 许可证要点

- ✅ **商业使用**：允许商业使用
- ✅ **修改**：允许修改代码
- ✅ **分发**：允许分发
- ✅ **专利使用**：允许专利使用
- ✅ **私人使用**：允许私人使用

### 许可证要求

- ⚠️ **许可证和版权声明**：必须包含许可证和版权声明
- ⚠️ **状态变更**：必须说明对源代码所做的更改

详细内容请查看 [LICENSE](LICENSE) 文件。

---

## ⚠️ 免责声明

**重要提示**：MedCrux 是一个医学影像报告智能分析辅助工具，旨在为患者提供第二意见参考。

### 核心声明

1. **不提供医疗诊断**：本系统不能替代专业医生的诊断和治疗建议，所有分析结果仅供参考。

2. **不承担医疗责任**：使用本系统产生的任何后果，开发者不承担责任。如有任何健康问题，请及时咨询专业医生。

3. **数据准确性**：
   - OCR 识别准确度受图片质量影响，建议使用清晰的报告图片
   - AI 分析结果可能存在误差，不应作为唯一决策依据

4. **紧急情况**：本系统不适用于紧急医疗情况。如有紧急医疗需求，请立即就医。

5. **数据隐私**：所有数据处理在本地完成，不会上传到服务器。但请注意，您有责任保护您的设备和数据安全。

**使用本系统即表示您已理解并同意上述免责声明。**

---

## 🗺️ Roadmap

### v1.3.0（进行中）

- [x] 前端框架升级：从 Streamlit 升级到 React + TypeScript + Tailwind CSS
- [x] UI/UX 全面优化：现代化界面设计
- [x] Logo 设计：MedCrux 专属 logo
- [x] 患者教育功能：BI-RADS 分级制度说明
- [x] 分析状态细化：显示所有分析阶段
- [ ] 响应式布局优化：移动端适配

### v1.4.0（计划中）

- [ ] 多语言支持：中英文切换
- [ ] 报告导出功能：PDF/Word 格式
- [ ] 历史记录功能：保存分析历史
- [ ] 用户账户系统：个人数据管理

### v2.0.0（未来）

- [ ] 多模态分析：支持更多影像类型
- [ ] 云端服务：可选的云端分析服务
- [ ] 专业版功能：面向医生的专业功能
- [ ] API 开放：提供公开 API 服务

---

## 🔓 开源 & 商业边界

### 开源部分

✅ **核心代码完全开源**：本项目采用 Apache License 2.0 开源协议，所有源代码完全开放。

✅ **可自由使用**：
- 可以自由使用、修改、分发本项目的源代码
- 可以用于商业用途
- 可以基于本项目开发衍生项目

✅ **社区贡献**：欢迎社区贡献代码、报告问题、提出建议。

### 商业边界

⚠️ **不承诺免费在线服务**：
- 本项目**不承诺**提供免费的在线服务
- 本项目**不承诺**提供免费的 API 服务
- 本项目**不承诺**提供免费的技术支持

⚠️ **可能的商业服务**：
- 未来可能提供付费的云端分析服务
- 未来可能提供付费的专业版功能
- 未来可能提供付费的技术支持服务

### 使用建议

- **本地部署**：推荐在本地部署使用，所有数据处理在本地完成
- **自建服务**：可以基于开源代码自建服务
- **商业使用**：可以基于开源代码开发商业产品

---

## 🤝 贡献方式

我们欢迎所有形式的贡献！

### 如何贡献

#### 1. 报告问题

如果您发现了 bug 或有功能建议，请通过 [GitHub Issues](https://github.com/riverbii/MedCrux/issues) 提交。

**提交 Issue 时请包含**：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息（Python 版本、操作系统等）

#### 2. 提交代码

1. **Fork 项目**：Fork 本项目到您的 GitHub 账户
2. **创建分支**：从 `main` 分支创建新分支
3. **开发**：在新分支上进行开发
4. **测试**：确保代码通过测试
5. **提交 PR**：提交 Pull Request 到 `main` 分支

**代码规范**：
- 使用 Ruff 进行代码格式化
- 遵循项目的代码风格
- 添加必要的注释和文档
- 确保代码通过测试

#### 3. 改进文档

- 完善 README
- 改进 API 文档
- 添加使用示例
- 修复文档错误

#### 4. 其他贡献

- 分享使用经验
- 提出改进建议
- 帮助其他用户
- 推广项目

### 贡献指南

- 请遵循项目的代码风格和规范
- 提交前请运行测试确保代码正常工作
- 提交 PR 时请提供清晰的描述
- 欢迎讨论和反馈

---

## 📁 项目结构

```
MedCrux/
├── src/
│   └── medcrux/
│       ├── api/           # FastAPI 后端接口
│       │   └── main.py
│       ├── ingestion/     # OCR 文本提取模块
│       │   └── ocr_service.py
│       ├── analysis/      # AI 分析引擎
│       │   └── llm_engine.py
│       ├── rag/           # GraphRAG 知识图谱
│       │   ├── graphrag_retriever.py
│       │   └── data/      # 知识库数据
│       └── ui/            # Streamlit 前端界面
│           └── app.py
├── docs/                 # 项目文档（公开文档）
├── scripts/              # 工具脚本
├── pyproject.toml        # 项目配置和依赖
├── uv.lock               # 依赖锁定文件
└── README.md
```

---

## 🧪 开发

### 代码格式化与检查

项目使用 Ruff 进行代码格式化和 linting：

```bash
# 格式化代码
ruff format .

# 检查代码
ruff check .

# 自动修复可修复的问题
ruff check --fix .
```

### 运行测试

```bash
pytest
```

### Pre-commit hooks

安装 pre-commit hooks：

```bash
pre-commit install
```

---

## 📧 联系方式

- **GitHub Issues**：[提交问题或建议](https://github.com/riverbii/MedCrux/issues)
- **License**：[Apache License 2.0](https://github.com/riverbii/MedCrux/blob/main/LICENSE)

---

## 🙏 致谢

感谢所有为本项目做出贡献的开发者和用户！

---

**最后更新**：2026-01-05
