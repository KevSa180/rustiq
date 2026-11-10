import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// En desarrollo (npm run dev) las llamadas a /api se reenvían al servidor Flask.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": "http://localhost:5001" },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
