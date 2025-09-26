module.exports = {
  root: true,

  parserOptions: {
    ecmaVersion: 2021,
    sourceType: 'module',
    parser: require.resolve('@typescript-eslint/parser'),
  },

  env: {
    browser: true,
    es2021: true,
    node: true,
  },

  extends: [
    'eslint:recommended',
    '@vue/typescript/recommended',
    'plugin:vue/vue3-essential',
    'plugin:vue/vue3-strongly-recommended',
    'plugin:vue/vue3-recommended',
    'prettier',
  ],

  plugins: [
    '@typescript-eslint',
    'vue',
  ],

  rules: {
    // Vue specific rules
    'vue/multi-word-component-names': 'off',
    'vue/no-unused-vars': 'error',

    // TypeScript rules
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',

    // General rules
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
  },

  ignorePatterns: [
    'dist',
    'node_modules',
    '*.config.js'
  ]
}