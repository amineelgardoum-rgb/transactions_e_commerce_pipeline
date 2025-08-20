import { defineConfig } from "vite";

export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://producer:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/mockoon':{
        target: 'http://mockoon:8001',
        changeOrigin:true,
        rewrite:(path)=>path.replace(/^\/api/,''),
      }
    },
    host: true, // This makes the server accessible externally
    port: 5173, // This is the port your Vite dev server will run on
  },
});