import js from "@eslint/js";
import globals from "globals";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import tseslint from "typescript-eslint";
import { defineConfig, globalIgnores } from "eslint/config";

const tsFiles = ["**/*.{ts,tsx}"];

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: tsFiles,
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    rules: {
      'no-delete-var': 'off',
    },
  },
  {
    ...js.configs.recommended,
    files: tsFiles,
  },
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: tsFiles,
  })),
  {
    ...reactHooks.configs.flat.recommended,
    files: tsFiles,
  },
  {
    ...reactRefresh.configs.vite,
    files: tsFiles,
  },
  {
    files: tsFiles,
    rules: {
      "no-delete-var": "off",
    },
  },
]);
