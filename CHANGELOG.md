# Changelog

本文档记录MedCrux项目的所有重要变更。

格式遵循[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.3.1] - 2026-01-07

### Fixed
- **BUG-001**: 修复 cm/mm 单位转换问题
  - LLM system_prompt 明确要求单位统一为 cm，mm 需转换为 cm（除以10）
  - 前端添加 `parseDistanceFromNipple` 函数，支持多种数据格式解析
  - 添加专门的测试用例 `test_unit_conversion_mm_to_cm` 验证转换逻辑
- **BUG-002**: 修复左乳房11点钟方向可视化错误
  - 根因：前端可视化代码中字符串匹配顺序错误（`clockPosition.includes('1点')` 会匹配"11点"）
  - 修复：使用精确匹配（normalized lookup map）替代模糊匹配（`includes`）
  - 修复字符串匹配顺序：先匹配两位数钟点（12点、11点、10点），再匹配一位数
  - 创建可视化测试工具 `docs/gov/test_clock_positions.html` 验证所有钟点位置
- **BUG-003**: 修复 OCR 信息丢失问题
  - 优化事实性摘要提取逻辑，确保所有 OCR 识别的异常发现信息都能传递到 LLM 分析阶段

### Added
- **位置信息结构化输出优化**
  - LLM 直接输出标准化的位置信息（breast, clock_position, distance_from_nipple）
  - 统一使用4个固定钟点（1、11、5、7）进行象限转换
  - 左右乳房镜像关系正确处理
- **位置可视化 QA Gate**
  - 建立位置可视化黄金用例集（覆盖左右乳1-12点）
  - 象限→钟点固定映射验证机制
  - BUG-002 历史事故点回归测试
  - 详见：`docs/gov/QA_GATE_LOCATION_VISUALIZATION_v1.3.x.md`
- **代码质量改进**
  - 引入 Python 语言规范（Ruff + Google 风格规则）
  - 引入 TypeScript/JavaScript 语言规范（ESLint + React 插件）
  - 配置 pre-commit hooks，自动运行代码质量检查
  - 前端 TypeScript 类型基线对齐，清理类型错误

### Changed
- **代码质量评分机制**
  - 移除主观评分（95分），改为基于证据的客观指标
  - 质量指标：TypeScript 类型检查状态、Lint 工具配置、Pre-commit hooks 状态、关键 Bug 数量

### Technical
- 代码规范文档：`docs/dev/LANGUAGE_STANDARDS.md`、`docs/dev/STANDARDS.md`、`docs/dev/CODE_REVIEW_CHECKLIST.md`
- Framework 语言规范配置方法论：`docs/framework/04_工作规范/LANGUAGE_STANDARDS_SETUP.md`
- 可视化测试工具：`docs/gov/test_clock_positions.html`

---

## [1.3.0] - 2026-01-05

### Known Issues
- ~~左乳房11点钟方向不对（v1.3.1已修复）~~
- ~~cm/mm 单位分不清（v1.3.1已修复）~~
- ~~OCR识别到的异常发现信息，结构化异常发现时丢失（v1.3.1已修复）~~

详见：[v1.3.0已知问题列表](docs/dev/versions/v1.3.0/KNOWN_ISSUES.md)

### Added
- 前端框架升级：从Streamlit迁移到React + TypeScript + Tailwind CSS
- Logo设计：MedCrux专属Logo（瞄准镜主题）
- 患者教育功能：BI-RADS分级说明（通过导航菜单访问）
- 分析状态细化：显示6个分析阶段（准备、OCR、RAG、LLM、一致性检查、完成）
- 异常发现可视化：胸部示意图（基于钟点位置和距乳头距离）
- 导航菜单：智能分析和科普教育下拉菜单
- 页脚信息：版权、License、Privacy Policy、GitHub Issues链接
- 响应式布局：完整的移动端适配
- 组件懒加载：模态框组件按需加载

### Changed
- UI设计：全新的现代化专业界面
- 后端API：添加CORS配置，版本升级到1.3.0
- 性能优化：组件懒加载、代码分割

### Technical
- 前端技术栈：React 18.2.0, TypeScript 5.2.2, Tailwind CSS 3.4.0, Vite 5.0.0
- 构建工具：从Streamlit切换到Vite
- 开发工具：ESLint、TypeScript严格模式

---

## [1.2.0] - 2026-01-04

### Changed
- UI布局优化：原始图像和OCR原文各占1/2宽度（1:1比例）
- 原始图像自适应：根据最长边自适应，保持原比例
- OCR原文默认关闭，可以手动打开
- 分析按钮优化：大按钮，绿色背景，分析后状态切换
- 结节列表优化：圆弧边按钮样式，选中状态高亮
- 示意图优化：移除象限标注，保留钟点标注
- 事实摘要优化：统一显示，不重复

---

## [1.1.0] - 2026-01-04

### Added
- 结节识别和分离功能
- 结节分开展示
- 胸部示意图（基础版）
- 示意图交互（点击查看详情）
- 结节详情页
- 整体评估页

### Changed
- LLM输出格式调整为结节列表
- UI布局改为标签页布局

---

## [1.0.0] - 2026-01-04

### Added
- OCR文字识别功能（基于RapidOCR）
- RAG检索功能（GraphRAG知识图谱）
- LLM智能分析功能（基于DeepSeek）
- BI-RADS一致性检查功能
- 风险评估功能（Low/Medium/High三级）
- Web UI（基于Streamlit）
- 逻辑一致性检查器（通用的充要条件验证）
- UI改进功能（P0和P1需求）
  - 免责声明和数据隐私说明
  - 结构化展示提取的形态学特征
  - 详细的不一致预警显示
  - 加载状态和进度指示器
  - 优化的风险等级展示
  - 改进的错误提示
- 版本号显示功能（UI界面）

### Changed
- 术语匹配逻辑：使用精确匹配，避免"圆形"匹配到"椭圆形"
- 风险评估逻辑：只有恶性征象才是高风险
- UI数据展示：显示所有值（用逗号分隔），不丢失信息

### Fixed
- 修复"条状"不一致提醒缺失的问题
- 修复UI数据展示格式问题（多个值显示）
- 修复OCR空字节流处理（提前检查，抛出ValueError）
- 修复术语匹配问题（精确匹配）
- 修复风险评估问题（只有恶性征象才是高风险）

### Performance
- RAG检索优化：减少实体匹配数量，降低上下文大小
- LLM系统提示优化：精简prompt长度，减少53%字符数
- 性能测试：OCR < 5s, RAG < 2s, LLM < 10s, Total < 20s（符合PRD要求）

### Testing
- 添加自动化性能测试（使用Mock数据）
- 添加自动化功能测试（使用Mock数据）
- 添加自动化边界测试（使用Mock数据）
- 测试覆盖：54个测试通过，4个跳过，0个失败

---

**维护说明**：
- 每次发布时更新CHANGELOG
- 记录所有Added、Changed、Fixed、Deprecated、Removed
- 版本号遵循语义化版本（SemVer）
