// jest.config.ts
import type { Config } from "jest";

const config: Config = {
  // Пресет для работы с TypeScript
  preset: "ts-jest",

  // Указываем ts-jest, как обрабатывать JSX
  transform: {
    "^.+\\.tsx?$": [
      "ts-jest",
      {
        tsconfig: "tsconfig.jest.json",
      },
    ],
  },

  // Окружение для тестирования, имитирующее DOM
  testEnvironment: "jest-environment-jsdom",

  // Пути, которые Jest будет игнорировать при поиске тестов
  testPathIgnorePatterns: ["/node_modules/", "/dist/"],

  // Настройка для импорта дополнительных матчеров jest-dom
  setupFilesAfterEnv: ["<rootDir>/src/setupTests.ts"],

  // Обработка статических файлов (CSS, SCSS и т.д.)
  moduleNameMapper: {
    "\\.(css|less|scss|sass)$": "identity-obj-proxy",
  },

  // Включаем автоматическую очистку моков между тестами
  clearMocks: true,

  // Собирать информацию о покрытии кода тестами
  collectCoverage: true,
  coverageDirectory: "coverage",
  coverageProvider: "v8",
};

export default config;
