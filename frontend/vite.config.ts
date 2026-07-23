import path from "node:path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
      "@assets": path.resolve(__dirname, "public"),
    },
    dedupe: ["react", "react-dom"],
  },

  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },

  preview: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
  },

  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});