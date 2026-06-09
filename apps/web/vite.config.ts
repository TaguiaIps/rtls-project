/// <reference types="vitest" />
import { resolve } from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@rtls/contracts": resolve(__dirname, "../../packages/contracts/src/index.ts"),
      "@rtls/config": resolve(__dirname, "../../packages/config/src/index.ts")
    }
  },
  test: {
    environment: "jsdom",
    globals: true,
    coverage: {
      provider: "v8",
      reporter: ["text", "lcov", "html"],
      reportsDirectory: "./coverage",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/**/*.d.ts", "src/**/*.test.{ts,tsx}"],
      thresholds: {
        lines: 75,
        functions: 75,
        branches: 60
      }
    }
  }
});
