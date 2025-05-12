import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import eslint from 'vite-plugin-eslint';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => {
  // 加载环境变量，支持 .env 文件
  const env = loadEnv(mode, process.cwd(), ['APP_PORT_1', 'APP_PORT_2', 'API_URL']);

  return {
    plugins: [
      vue(),
      eslint({
        eslintPath: 'eslint',
        include: ['src/**/*.{ts,vue,tsx}'],
        cache: false,
        fix: true,
        useEslintrc: true,
        overrideConfigFile: path.resolve(__dirname, '.eslintrc.cjs'),
      }),
    ],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
        '@utils': path.resolve(__dirname, './src/utils'),
      },
    },
    server: {
      port: parseInt(env.APP_PORT_1 || '3000', 10),
      open: true,
      proxy: {
        '/api': {
          target: env.API_URL || `http://localhost:${env.APP_PORT_2 || '8000'}`,
          changeOrigin: true,
          rewrite: path => path.replace(/^\/api/, ''),
        },
      },
    },
    build: {
      outDir: 'dist',
      assetsDir: 'assets',
      rollupOptions: {
        input: path.resolve(__dirname, 'index.html'),
      },
      // 生产环境注入全局变量
      sourcemap: mode === 'development',
    },
    // 环境变量前缀配置
    envPrefix: 'VITE_',
  };
});