module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    // Google TypeScript Style Guide基础规则
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:@typescript-eslint/recommended-requiring-type-checking',
    // React最佳实践
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs', 'node_modules'],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: './tsconfig.json',
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

    // TypeScript特定规则（严格模式）
    '@typescript-eslint/no-explicit-any': 'error', // 禁止any（严格模式）
    '@typescript-eslint/explicit-function-return-type': 'warn', // 要求显式返回类型
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-floating-promises': 'error', // 禁止未处理的Promise
    '@typescript-eslint/no-misused-promises': 'error', // 禁止Promise误用

    // 防御式编程规则（基于BUG-002教训）
    'no-console': ['warn', { allow: ['warn', 'error'] }], // 允许console.warn/error
    'no-debugger': 'error', // 禁止debugger
    'no-alert': 'error', // 禁止alert

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
