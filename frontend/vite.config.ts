import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  define: {
    global: "globalThis",
  },
  resolve: {
    alias: {
      stream: "stream-browserify",
      util: "util",
    },
  },
  optimizeDeps: {
    include: ["pino", "pino-pretty"],
  },
  server: {
    port: 3001,
    proxy: {
      "/api": {
        // Use environment variable when available during dev; otherwise
        // default to local backend running on port 8080.
        target: process.env.VITE_API_BASE_URL || "http://localhost:8080",
        changeOrigin: true,
      },
    },
  },
});
