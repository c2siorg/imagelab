// Using vitest/config (Vitest 2+ idiomatic pattern) for type-safe test options
// without requiring the older triple-slash reference hack.
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { port: 3100 },
  test: {
    include: ["tests/**/*.test.ts"],
    clearMocks: true,
    environment: "node", // explicit; per-file override via @vitest-environment jsdom for React component tests
  },
});
