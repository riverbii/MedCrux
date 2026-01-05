# MedCrux Frontend

> React + TypeScript + Tailwind CSS 前端应用

## 快速开始

### 方式一：使用测试脚本（推荐）

在项目根目录运行：

```bash
./test_local.sh
```

这会自动：
- 检查环境
- 安装依赖（如需要）
- 启动后端API
- 启动前端开发服务器

### 方式二：手动启动

#### 1. 安装依赖

```bash
npm install
```

#### 2. 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

**注意**：确保后端API已启动（`./scripts/start_api.sh`）

#### 3. 构建生产版本

```bash
npm run build
```

#### 4. 预览生产版本

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── components/      # React组件
│   ├── services/        # API服务
│   ├── types/           # TypeScript类型定义
│   ├── App.tsx          # 主应用组件
│   ├── main.tsx         # 入口文件
│   └── index.css        # 全局样式
├── public/              # 静态资源
├── index.html           # HTML模板
├── vite.config.ts       # Vite配置
├── tailwind.config.js   # Tailwind配置
└── package.json         # 项目配置
```

## 技术栈

- **React 18**: UI框架
- **TypeScript**: 类型安全
- **Tailwind CSS**: 样式框架
- **Vite**: 构建工具
- **Axios**: HTTP客户端

## 开发说明

### 后端API

前端通过 `/api` 代理到后端服务（http://localhost:8000）。

确保后端服务已启动：
```bash
./scripts/start_api.sh
```

### 环境变量

创建 `.env` 文件（可选）：
```
VITE_API_BASE_URL=http://localhost:8000
```

## 代码规范

- 使用 TypeScript 严格模式
- 遵循 React Hooks 最佳实践
- 使用 Tailwind CSS 进行样式设计
- 组件使用函数式组件和 Hooks


