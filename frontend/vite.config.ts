import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // تمام درخواست‌های API به Django
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // اگر می‌خواهید مسیر /api حذف شود (معمولاً نیازی نیست)
        // rewrite: (path) => path.replace(/^\/api/, ''),
      },
      // پنل ادمین Django
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // فایل‌های رسانه (آپلودها)
      '/media': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // اگر فایل‌های استاتیک Django را هم نیاز دارید (اختیاری)
      '/static': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})