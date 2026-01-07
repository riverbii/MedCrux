module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    // Google TypeScript Style Guide基础规则
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    // React最佳实践
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'node_modules'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react-refresh', '@typescript-eslint', 'react'],
  settings: {
    react: {
      version: 'detect',
    },
  },
  rules: {
    // React特定规则
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    'react/react-in-jsx-scope': 'off', // React 18不需要
    'react/prop-types': 'off', // TypeScript已提供类型检查

    // TypeScript特定规则（分阶段收紧）
    '@typescript-eslint/no-explicit-any': 'warn', // 暂时降级为warning，后续在增量迁移中逐步消除any
    '@typescript-eslint/explicit-function-return-type': 'warn', // 要求显式返回类型
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-floating-promises': 'off', // 关闭依赖parserServices的规则，后续单独在关键路径上用tsc和测试兜底
    '@typescript-eslint/no-misused-promises': 'off', // 同上，避免在未配置project时报错

    // 防御式编程规则（基于BUG-002教训）
    'no-console': ['warn', { allow: ['warn', 'error'] }], // 允许console.warn/error
    'no-debugger': 'error', // 禁止debugger
    'no-alert': 'warn', // 先标记为warning，后续用更友好的UI替代alert

    // 代码质量规则
    'prefer-const': 'error', // 优先使用const
    'no-var': 'error', // 禁止var
    'object-shorthand': 'error', // 对象简写
    'prefer-arrow-callback': 'error', // 优先使用箭头函数

    // 字符串匹配规则（基于BUG-002教训）
    // 警告：使用includes进行关键逻辑判断可能导致误匹配
    'no-warning-comments': ['warn', { terms: ['includes', 'TODO', 'FIXME'], location: 'start' }],
  },
}
