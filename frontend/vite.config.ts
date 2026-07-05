import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite 配置文件
// Vite 是新一代前端构建工具，比 Webpack 快得多
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // 代理配置：将 /api 开头的请求转发到后端（8000端口）
    // 这样前端不用写完整的 http://localhost:8000，直接 /api/xxx 即可
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
