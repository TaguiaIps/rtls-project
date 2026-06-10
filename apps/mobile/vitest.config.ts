import { resolve } from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@rtls/contracts": resolve(__dirname, "../../packages/contracts/src/index.ts"),
      "@rtls/config": resolve(__dirname, "../../packages/config/src/index.ts")
    }
  },
  test: {
    globals: true,
    environment: "jsdom",
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
