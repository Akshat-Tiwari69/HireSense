module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', 'node_modules', '*.config.js', '*.config.cjs'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: '18.2' } },
  plugins: ['react-refresh'],
  rules: {
    'react/jsx-no-target-blank': 'off',
    // Downgrade unused vars to warnings — they're noise in a project this size
    'no-unused-vars': ['warn', { varsIgnorePattern: '^_', argsIgnorePattern: '^_' }],
    // Prop-types validation is off — TypeScript or runtime validation preferred
    'react/prop-types': 'off',
    // Allow components that export non-components (e.g. constants alongside components)
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    // Hooks exhaustive-deps stays as warning (not error)
    'react-hooks/exhaustive-deps': 'warn',
    // Allow console in development
    'no-console': 'off',
  },
};
