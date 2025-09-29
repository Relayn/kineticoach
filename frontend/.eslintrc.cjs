module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:security/recommended",
    "prettier", // Важно: prettier должен быть последним, чтобы отключать конфликтующие правила
  ],
  ignorePatterns: ["dist", ".eslintrc.cjs"],
  parser: "@typescript-eslint/parser",
  plugins: ["react-refresh", "prettier"],
  rules: {
    "prettier/prettier": "error", // Подсвечивать несоответствия Prettier как ошибки ESLint
    "react/react-in-jsx-scope": "off", // В новых версиях React это не требуется
    "react-refresh/only-export-components": [
      "warn",
      { allowConstantExport: true },
    ],
  },
  settings: {
    react: {
      version: "detect", // Автоматически определять версию React
    },
  },
};
