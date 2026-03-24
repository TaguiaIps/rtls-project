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
  }
});
