import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In development /api and /ws go to the local Python devserver (uvicorn, default :8100).
const apiPort = process.env.DIGOUT_API_PORT ?? "8100";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5180,
    strictPort: true,
    // The repo lives on a Windows drive under WSL: no inotify events there, so poll for changes.
    watch: { usePolling: true, interval: 300 },
    proxy: {
      "/api": `http://localhost:${apiPort}`,
      "/ws": { target: `ws://localhost:${apiPort}`, ws: true },
    },
  },
});
