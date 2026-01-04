# Changelog

本文档记录MedCrux项目的所有重要变更。

格式遵循[Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.1.0] - 开发中

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
