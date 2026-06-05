import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import path from 'path'

export default defineConfig({
  plugins: [uni()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  build: {
    rollupOptions: {
      onwarn(warning, warn) {
        if (warning.code === 'MISSING_EXPORT' && warning.message.includes('normalizeCssVarValue')) {
          return
        }
        warn(warning)
      }
    }
  }
})
