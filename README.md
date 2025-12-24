# MedCrux 🛡️

> 医学影像报告智能质控与决策辅助系统

MedCrux 是一个基于 OCR 和大语言模型的医学影像报告分析系统，能够自动识别报告文本并进行 BI-RADS 一致性检查，帮助发现潜在的风险和不一致问题。

## ✨ 功能特性

- **📸 OCR 文字识别**：基于 RapidOCR 和 OpenCV，支持从 JPG/PNG 格式的医学报告图片中提取文本
- **🤖 AI 智能分析**：集成 DeepSeek 大模型，对提取的文本进行医学逻辑分析
- **🔍 BI-RADS 一致性检查**：对照 ACR BI-RADS 标准，检查报告描述与结论的一致性
- **⚠️ 风险等级评估**：自动评估风险等级（Low/Medium/High）并给出预警
- **💡 智能建议**：基于分析结果提供面向患者的建议
- **🌐 Web 界面**：基于 Streamlit 的友好用户界面，支持图片上传和结果可视化

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **前端框架**：Streamlit
- **OCR 引擎**：RapidOCR (ONNXRuntime)
- **图像处理**：OpenCV
- **AI 模型**：DeepSeek (OpenAI-compatible API)
- **代码质量**：Ruff (linting & formatting)
- **包管理**：uv

## 📋 前置要求

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (推荐) 或 pip
- DeepSeek API Key（用于 AI 分析功能）

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd MedCrux
```

### 2. 安装依赖

使用 uv（推荐）：

```bash
uv sync
```

或使用 pip：

```bash
pip install -e .
```

### 3. 配置环境变量

设置 DeepSeek API Key：

```bash
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

### 4. 启动后端服务

```bash
uvicorn medcrux.api.main:app --reload
```

后端服务将在 `http://127.0.0.1:8000` 启动。

### 5. 启动前端界面

在另一个终端中：

```bash
streamlit run src/medcrux/ui/app.py
```

前端界面将在浏览器中自动打开（默认 `http://localhost:8501`）。

## 📖 使用说明

1. **上传报告图片**：在 Streamlit 界面中点击上传按钮，选择医学影像报告图片（JPG/PNG 格式）
2. **查看原始图片**：上传后可在左侧查看原始影像
3. **开始分析**：点击"开始分析"按钮，系统将：
   - 使用 OCR 提取图片中的文字
   - 调用 AI 模型进行医学逻辑分析
   - 检查 BI-RADS 一致性
   - 评估风险等级
4. **查看结果**：
   - OCR 识别原文（可展开查看）
   - 提取的医学事实
   - 风险等级评估
   - AI 分析建议

## 🔌 API 文档

启动后端服务后，访问以下地址查看自动生成的 API 文档：

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 主要接口

#### 健康检查

```http
GET /health
```

返回服务状态和版本信息。

#### 分析报告

```http
POST /analyze/upload
Content-Type: multipart/form-data

file: <image_file>
```

上传医学报告图片进行分析，返回 OCR 文本和 AI 分析结果。

**响应示例**：

```json
{
  "filename": "report.jpg",
  "ocr_text": "超声描述：左乳上方可见低回声结节...",
  "ai_result": {
    "patient_gender": "Female",
    "extracted_findings": ["低回声结节", "边界不清", "毛刺状边缘"],
    "original_conclusion": "BI-RADS 3类",
    "ai_risk_assessment": "High",
    "inconsistency_alert": true,
    "advice": "建议进一步检查..."
  },
  "message": "分析完成"
}
```

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
│       └── ui/            # Streamlit 前端界面
│           └── app.py
├── pyproject.toml         # 项目配置和依赖
├── uv.lock               # 依赖锁定文件
└── README.md
```

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

## ⚠️ 注意事项

- 本项目为 MVP 原型，仅供学习和研究使用
- 医学诊断应咨询专业医生，本系统不提供医疗建议
- OCR 识别准确度受图片质量影响，建议使用清晰的报告图片
- DeepSeek API 调用需要网络连接和有效的 API Key

## 📝 许可证

详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 Issue 联系。
