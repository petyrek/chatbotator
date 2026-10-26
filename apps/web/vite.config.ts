import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // "@data/..." points at the repo-root data/ folder the API also reads.
    // Keep in sync with "paths" in tsconfig.json.
    alias: { "@data": fileURLToPath(new URL("../../data", import.meta.url)) },
  },
  server: {
    port: 5174,
    strictPort: true,
    proxy: { "/api": "http://127.0.0.1:3001" },
  },
});
