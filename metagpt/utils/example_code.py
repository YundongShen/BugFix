package_example_code = """
```code
{
  "name": "example-app",
  "version": "1.0.0",
  "description": "A Vue 3 and TypeScript-based example app application with modern UI/UX design.",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .ts,.vue,.tsx --fix --no-error-on-unmatched-pattern",
    "type-check": "vue-tsc --noEmit",
  },
  "dependencies": {
    "@iconify/vue": "4.1.1",
    "@vueuse/core": "10.9.0",
    "axios": "1.6.7",
    "dayjs": "1.11.10",
    "element-plus": "2.5.6",
    "lodash-es": "4.17.21",
    "mitt": "3.0.1",
    "nprogress": "0.2.0",
    "pinia": "2.1.7",
    "pinia-plugin-persistedstate": "3.2.1",
    "vue": "3.4.20",
    "vue-router": "4.3.0",
    "vue-i18n": "9.9.1"
  },
  "devDependencies": {
    "@intlify/unplugin-vue-i18n": "2.0.0",
    "@types/node": "20.11.21",
    "@typescript-eslint/eslint-plugin": "7.1.0",
    "@typescript-eslint/parser": "7.1.0",
    "@vitejs/plugin-vue": "5.0.4",
    "eslint": "8.57.0",
    "eslint-config-prettier": "9.1.0",
    "eslint-plugin-prettier": "5.1.3",
    "eslint-plugin-vue": "9.22.0",
    "less": "4.2.0",
    "prettier": "3.2.5",
    "typescript": "5.3.3",
    "vite": "5.1.4",
    "vite-plugin-ejs": "1.7.0",
    "vite-plugin-eslint": "1.8.1",
    "vite-plugin-progress": "0.0.7",
    "vite-plugin-purge-icons": "0.10.0",
    "vite-plugin-style-import": "2.0.0",
    "vite-plugin-svg-icons": "2.0.1",
    "vue-tsc": "1.8.27",
    "consola": "3.2.2",
    "terser": "5.26.0",z
    "eslint-define-config": "^2.1.0" 
  },
  "eslintIgnore": [
    "node_modules",
    "dist",
    "*.config.js"
  ],
  "imports": {
    "#/*": "./src/*"
  },
  "exports": {
    ".": {
      "import": "./src/main.ts"
    }
  },
  "browserslist": [
    "> 1%",
    "last 2 versions",
    "not dead"
  ],
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  }
}
```
"""

vite_example_code = {
    """
```code
// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import eslint from 'vite-plugin-eslint'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  plugins: [
    vue(),
    eslint({
      eslintPath: 'eslint',
      include: ['src/**/*.{ts,vue,tsx}'],
      cache: false,
      fix: true,
      useEslintrc: true,
      overrideConfigFile: path.resolve(__dirname, '.eslintrc.cjs')
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@utils': path.resolve(__dirname, './src/utils')
    }
  },
  server: {
    port: parseInt(process.env.APP_PORT_1 || '3000', 10),
    open: true,
    proxy: {
      '/api': {
        target: `http://localhost:${process.env.APP_PORT_2 || '8000'}`,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html')
    }
  }
})
```
"""
}


example_code = """
```
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { createStyleImportPlugin } from 'vite-plugin-style-import'
import { createSvgIconsPlugin } from 'vite-plugin-svg-icons'
import PurgeIcons from 'vite-plugin-purge-icons'

export default defineConfig({
  root: path.resolve(__dirname),
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components')
    }
  },
  plugins: [
    vue(),
    createStyleImportPlugin({
      libs: [{
        libraryName: 'element-plus',
        esModule: true,
        resolveStyle: (name) => `element-plus/es/components/${name}/style/css`
      }]
    }),
    createSvgIconsPlugin({
      iconDirs: [path.resolve(__dirname, 'src/assets/icons')],
      symbolId: 'icon-[dir]-[name]'
    }),
    PurgeIcons()
  ],
  build: {
    rollupOptions: {
      input: path.resolve(__dirname, 'index.html'), // 修正路径
      output: {
        assetFileNames: (assetInfo) => {
          if (assetInfo.name?.endsWith('.css')) {
            return 'assets/css/[name]-[hash][extname]' // CSS单独输出目录
          }
          return 'assets/[name]-[hash][extname]'
        }
      }
    },
    outDir: 'dist',
    assetsDir: 'assets',
    cssCodeSplit: true, // 启用CSS代码分割
    sourcemap: process.env.NODE_ENV === 'development',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "@/styles/variables.scss";` // 全局SCSS变量
      }
    },
    modules: {
      localsConvention: 'camelCase' // CSS模块命名规范
    }
  }
})
```
"""

database_example_code = """
```
# settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    # 异步数据库配置
    mysql_host: str = os.getenv('mysql_host', 'localhost')
    mysql_port: int = int(os.getenv('mysql_port', '3306'))
    mysql_database: str = os.getenv('mysql_database', 'default_db')
    mysql_user: str = os.getenv('mysql_user', 'root')
    mysql_password: str = os.getenv('mysql_password', '123456')

    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    DB_DEBUG: bool = os.getenv('DB_DEBUG', 'False').lower() == 'true'

    @property
    def DB_URL(self) -> str:
        # 动态生成连接字符串
        return f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```

```
# connect.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from fastapi import HTTPException
from settings import DatabaseSettings

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 核心数据库管理器
class DatabaseManager:
    # 异步数据库连接管理器 (单例模式)
    _instance = None

    def __new__(cls, settings: Optional[DatabaseSettings] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._settings = settings or DatabaseSettings()
            try:
                cls._engine = create_async_engine(
                    cls._settings.DB_URL,
                    pool_pre_ping=True,
                    pool_size=cls._settings.DB_POOL_SIZE,
                    max_overflow=cls._settings.DB_MAX_OVERFLOW,
                    pool_recycle=cls._settings.DB_POOL_RECYCLE,
                    echo=cls._settings.DB_DEBUG,
                    connect_args={
                        "connect_timeout": 10,
                        "charset": "utf8mb4",
                    }
                )
                cls._session_factory = async_sessionmaker(
                    bind=cls._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False
                )
                cls.Base = declarative_base()
            except Exception as e:
                trace_id = str(uuid4())
                logger.error(f"Failed to initialize database engine. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"Database initialization failed. Trace ID: {trace_id}") from e
        return cls._instance

    @property
    def engine(self):
        # 获取SQLAlchemy引擎
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                trace_id = str(uuid4())
                logger.error(f"Transaction failed: {e}. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"Database transaction failed. Trace ID: {trace_id}") from e

    async def health_check(self) -> bool:
        # 数据库连接健康检查
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            trace_id = str(uuid4())
            logger.error(f"Health check failed: {e}. Trace ID: {trace_id}")
            return False
```

```
# models.py
from sqlalchemy import Column, Integer, String
from connect import DatabaseManager

# 获取数据库管理器实例
db_manager = DatabaseManager()
Base = db_manager.Base

# 以下代码仅为示例，实际使用时请根据具体需求定义模型
# 定义用户模型类
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    email = Column(String(100))

# 可根据需要添加更多模型类，例如：
# class Calculator(Base):
#     __tablename__ = 'calculators'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     # 其他字段...

# db_operations.py
import logging
from connect import DatabaseManager
from sqlalchemy.orm import declarative_base

Base = declarative_base()

# 以下代码仅为示例，实际使用时请根据具体需求插入数据
async def insert_default_data(session, models_and_data):

    # 插入默认数据的通用函数。
    # :param session: 数据库会话
    # :param models_and_data: 包含模型类和对应数据列表的元组列表，例如 [(ModelClass, [data1, data2])]

    try:
        for model, data_list in models_and_data:
            for data in data_list:
                instance = model(**data)
                session.add(instance)
        await session.commit()
        logging.info("Default data inserted successfully.")
    except Exception as e:
        logging.error(f"Failed to insert default data: {e}")
        await session.rollback()

async def initialize_models(drop_existing: bool = False, models_and_data=None):

    # 初始化数据库表结构的通用函数。
    # :param drop_existing: 是否删除已存在的表
    # :param models_and_data: 包含模型类和对应数据列表的元组列表，例如 [(ModelClass, [data1, data2])]

    db_manager = DatabaseManager()
    if not await db_manager.health_check():
        raise ConnectionError("Database connection failed")

    async with db_manager.engine.begin() as conn:
        if drop_existing:
            logging.warning("Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)

        logging.info("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)

        if models_and_data:
            async with db_manager.session() as session:
                await insert_default_data(session, models_and_data)
```
"""

eslintrc_code = """
```
// .eslintrc.js
// @ts-check
const { defineConfig } = require('eslint-define-config')

module.exports = defineConfig({
  root: true,
  env: {
    browser: true,
    node: true,
    es6: true
  },
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 2020,
    sourceType: 'module',
    jsxPragma: 'React',
    ecmaFeatures: {
      jsx: true
    }
  },
  extends: [
    'plugin:vue/vue3-recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier',
    'plugin:prettier/recommended'
  ],
  rules: {
    'vue/no-setup-props-destructure': 'off',
    'vue/script-setup-uses-vars': 'error',
    'vue/no-reserved-component-names': 'off',
    '@typescript-eslint/ban-ts-ignore': 'off',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-var-requires': 'off',
    '@typescript-eslint/no-empty-function': 'off',
    'vue/custom-event-name-casing': 'off',
    'no-use-before-define': 'off',
    '@typescript-eslint/no-use-before-define': 'off',
    '@typescript-eslint/ban-ts-comment': 'off',
    '@typescript-eslint/ban-types': 'off',
    '@typescript-eslint/no-non-null-assertion': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-unused-vars': 'off',
    'no-unused-vars': 'off',
    'space-before-function-paren': 'off',

    'vue/attributes-order': 'off',
    'vue/one-component-per-file': 'off',
    'vue/html-closing-bracket-newline': 'off',
    'vue/max-attributes-per-line': 'off',
    'vue/multiline-html-element-content-newline': 'off',
    'vue/singleline-html-element-content-newline': 'off',
    'vue/attribute-hyphenation': 'off',
    'vue/require-default-prop': 'off',
    'vue/require-explicit-emits': 'off',
    'vue/html-self-closing': [
      'error',
      {
        html: {
          void: 'always',
          normal: 'never',
          component: 'always'
        },
        svg: 'always',
        math: 'always'
      }
    ],
    'vue/multi-word-component-names': 'off',
    'vue/no-v-html': 'off',
    'vue/require-toggle-inside-transition': 'off'
  }
})

```
"""

playwright_example_code = """
```python  
from playwright.sync_api import sync_playwright
import os
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('test.log')  # 输出到日志文件
    ]
)
logger = logging.getLogger('playwright')

# Environment configuration
APP_PORT = os.getenv("APP_PORT", 3000)
BASE_URL = f"http://localhost:{APP_PORT}"

def sanitize_html(content):

    # Remove <style> and <script> tags from HTML content and clean up empty lines.

    import re
    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    return '\n'.join(line for line in content.split('\n') if line.strip())

def log_response(response):

    # Log response information including status, method, URL, headers, and response time.

    req = response.request
    logger.info(f"Response [{response.status} {req.method} {req.url}]")
    logger.debug(f"Request headers: {dict(req.headers)}")
    logger.debug(f"Response headers: {dict(response.headers)}")
    logger.info(f"Response time: {response.request.timing['responseEnd'] - response.request.timing['requestStart']:.2f}ms")

def setup_console_listeners(page):

    # Set up listeners for console logs, errors, and failed network requests.

    def handle_console_message(msg):
        if msg.type == "error":
            logger.error(f"Console Error: {msg.text}")
        elif msg.type == "warning":
            logger.warning(f"Console Warning: {msg.text}")
        else:
            logger.info(f"Console Log: {msg.text}")

    page.on("console", handle_console_message)

    def handle_request_failed(request):
        logger.error(f"Network Request Failed: {request.url}")

    page.on("requestfailed", handle_request_failed)

def test_login_with_backend(page):

    # Test the login flow with backend interaction.

    login_url = f"{BASE_URL}/login"
    api_url = f"{BASE_URL}/api/login"
    logger.info(f"Starting test: Login flow with backend [URL: {login_url}]")

    try:
        # Navigate to login page
        page.goto(login_url)
        logger.info(f"Navigated to login page: {login_url}")

        # Verify page elements
        username_input = page.locator('input[name=username]')
        password_input = page.locator('input[name=password]')
        logger.info(f"Username input: {'Found' if username_input.count() else 'Missing'}")
        logger.info(f"Password input: {'Found' if password_input.count() else 'Missing'}")

        # Fill form fields
        username_input.fill("user1")
        password_input.fill("Password123!")

        # Listen for API response
        with page.expect_response(lambda res: res.url.startswith(api_url)) as resp_info:
            page.click("button[type=submit]")
        logger.info(f"Form submitted. Awaiting API response.")

        # Validate API response
        api_response = resp_info.value
        logger.info(f"API Response: {api_response.json() if api_response.ok else 'No response data'}")
        assert api_response.ok, f"API call failed: {api_response.status}"

        # Verify final navigation
        page.wait_for_url(f"{BASE_URL}/dashboard")
        logger.info(f"Login successful. Navigated to dashboard.")
    except AssertionError as e:
        logger.error(f"Login test failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during login test: {e}")

def test_generic_api_call(page, endpoint, method="GET", payload=None):

    # Generic test function for any API endpoint.
    # :param page: Playwright page object
    # :param endpoint: Full URL of the API endpoint
    # :param method: HTTP method (GET, POST, etc.)
    # :param payload: Optional payload for POST/PUT requests

    logger.info(f"Starting test: Generic API call [Endpoint: {endpoint}, Method: {method}]")

    try:
        # Listen for API response
        with page.expect_response(lambda res: res.url.startswith(endpoint)) as resp_info:
            if method.upper() == "GET":
                page.goto(endpoint)
            elif method.upper() == "POST":
                page.evaluate(f'''
                    async () => {{
                        await fetch("{endpoint}", {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({payload})
                        }});
                    }}
                ''')
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        logger.info(f"API request sent. Awaiting response.")

        # Validate API response
        api_response = resp_info.value
        logger.info(f"API Response: {api_response.json() if api_response.ok else 'No response data'}")
        assert api_response.ok, f"API call failed: {api_response.status}"
    except AssertionError as e:
        logger.error(f"API call test failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during API call test: {e}")

def setup_browser():
    # Set up the browser context and start tracing.

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Configure context
    context.set_extra_http_headers({
        'X-Test-Env': 'playwright'
    })

    # Enable tracing
    context.tracing.start(screenshots=True, snapshots=True)
    return context, browser, playwright

def teardown_browser(context, browser, playwright):
    # Close the browser context, browser, and stop Playwright.
    try:
        context.tracing.stop(path="trace.zip")
    except Exception as e:
        logger.error(f"Error stopping tracing: {e}")
    context.close()
    browser.close()
    playwright.stop()

from playwright.sync_api import sync_playwright
import os
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler('test.log')  # 输出到日志文件
    ]
)
logger = logging.getLogger('playwright')

# Environment configuration
APP_PORT = os.getenv("APP_PORT", 3000)
BASE_URL = f"http://localhost:{APP_PORT}"

def sanitize_html(content):

    # Remove <style> and <script> tags from HTML content and clean up empty lines.

    import re
    content = re.sub(r'<style.*?>.*?</style>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script.*?>.*?</script>', '', content, flags=re.DOTALL)
    return '\n'.join(line for line in content.split('\n') if line.strip())

def log_response(response):

    # Log response information including status, method, URL, headers, and response time.

    req = response.request
    logger.info(f"Response [{response.status} {req.method} {req.url}]")
    logger.debug(f"Request headers: {dict(req.headers)}")
    logger.debug(f"Response headers: {dict(response.headers)}")
    logger.info(f"Response time: {response.request.timing['responseEnd'] - response.request.timing['requestStart']:.2f}ms")

def setup_console_listeners(page):

    # Set up listeners for console logs, errors, and failed network requests.

    def handle_console_message(msg):
        if msg.type == "error":
            logger.error(f"Console Error: {msg.text}")
        elif msg.type == "warning":
            logger.warning(f"Console Warning: {msg.text}")
        else:
            logger.info(f"Console Log: {msg.text}")

    page.on("console", handle_console_message)

    def handle_request_failed(request):
        logger.error(f"Network Request Failed: {request.url}")

    page.on("requestfailed", handle_request_failed)

def test_login_with_backend(page):

    # Test the login flow with backend interaction.

    login_url = f"{BASE_URL}/login"
    api_url = f"{BASE_URL}/api/login"
    logger.info(f"Starting test: Login flow with backend [URL: {login_url}]")

    try:
        # Navigate to login page
        page.goto(login_url)
        logger.info(f"Navigated to login page: {login_url}")

        # Verify page elements
        username_input = page.locator('input[name=username]')
        password_input = page.locator('input[name=password]')
        logger.info(f"Username input: {'Found' if username_input.count() else 'Missing'}")
        logger.info(f"Password input: {'Found' if password_input.count() else 'Missing'}")

        # Fill form fields
        username_input.fill("user1")
        password_input.fill("Password123!")

        # Listen for API response
        with page.expect_response(lambda res: res.url.startswith(api_url)) as resp_info:
            page.click("button[type=submit]")
        logger.info(f"Form submitted. Awaiting API response.")

        # Validate API response
        api_response = resp_info.value
        logger.info(f"API Response: {api_response.json() if api_response.ok else 'No response data'}")
        assert api_response.ok, f"API call failed: {api_response.status}"

        # Verify final navigation
        page.wait_for_url(f"{BASE_URL}/dashboard")
        logger.info(f"Login successful. Navigated to dashboard.")
    except AssertionError as e:
        logger.error(f"Login test failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during login test: {e}")

def test_generic_api_call(page, endpoint, method="GET", payload=None):

    # Generic test function for any API endpoint.
    # :param page: Playwright page object
    # :param endpoint: Full URL of the API endpoint
    # :param method: HTTP method (GET, POST, etc.)
    # :param payload: Optional payload for POST/PUT requests

    logger.info(f"Starting test: Generic API call [Endpoint: {endpoint}, Method: {method}]")

    try:
        # Listen for API response
        with page.expect_response(lambda res: res.url.startswith(endpoint)) as resp_info:
            if method.upper() == "GET":
                page.goto(endpoint)
            elif method.upper() == "POST":
                page.evaluate(f'''
                    async () => {{
                        await fetch("{endpoint}", {{
                            method: "POST",
                            headers: {{ "Content-Type": "application/json" }},
                            body: JSON.stringify({payload})
                        }});
                    }}
                ''')
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        logger.info(f"API request sent. Awaiting response.")

        # Validate API response
        api_response = resp_info.value
        logger.info(f"API Response: {api_response.json() if api_response.ok else 'No response data'}")
        assert api_response.ok, f"API call failed: {api_response.status}"
    except AssertionError as e:
        logger.error(f"API call test failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during API call test: {e}")

def setup_browser():
    # Set up the browser context and start tracing.

    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()

    # Configure context
    context.set_extra_http_headers({
        'X-Test-Env': 'playwright'
    })

    # Enable tracing
    context.tracing.start(screenshots=True, snapshots=True)
    return context, browser, playwright

def teardown_browser(context, browser, playwright):
    # Close the browser context, browser, and stop Playwright.
    try:
        context.tracing.stop(path="trace.zip")
    except Exception as e:
        logger.error(f"Error stopping tracing: {e}")
    context.close()
    browser.close()
    playwright.stop()

if __name__ == "__main__":
    context, browser, playwright = setup_browser()
    page = context.new_page()
    setup_console_listeners(page)

    try:
        # Run tests
        test_login_with_backend(page)
        test_generic_api_call(
            page,
            endpoint=f"{BASE_URL}/api/sample",
            method="POST",
            payload={"key": "value"}
        )
    finally:
        teardown_browser(context, browser, playwright)
  """


database_settings_code = """
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from urllib.parse import quote_plus 

class DatabaseSettings(BaseSettings):
    mysql_host: str = os.getenv('mysql_host', 'localhost')
    mysql_port: int = int(os.getenv('mysql_port', '3306'))
    mysql_database: str = os.getenv('mysql_database', 'default_db')
    mysql_user: str = os.getenv('mysql_user', 'root')
    mysql_password: str = os.getenv('mysql_password', '123456')

    DB_POOL_SIZE: int = int(os.getenv('DB_POOL_SIZE', '5'))
    DB_MAX_OVERFLOW: int = int(os.getenv('DB_MAX_OVERFLOW', '10'))
    DB_POOL_RECYCLE: int = int(os.getenv('DB_POOL_RECYCLE', '3600'))
    DB_DEBUG: bool = os.getenv('DB_DEBUG', 'False').lower() == 'true'

    @property
    def DB_URL(self) -> str:
        escaped_user = quote_plus(self.mysql_user)
        escaped_password = quote_plus(self.mysql_password)
        escaped_host = quote_plus(self.mysql_host)
        escaped_database = quote_plus(self.mysql_database)
        return (
            f"mysql+asyncmy://{escaped_user}:{escaped_password}"
            f"@{escaped_host}:{self.mysql_port}/{escaped_database}"
            f"?charset=utf8mb4"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
"""

database_connect_code = """
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional, List, Tuple, Type
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import text
from fastapi import HTTPException
from backend.database.settings import DatabaseSettings
from backend.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None

    def __new__(cls, settings: Optional[DatabaseSettings] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._settings = settings or DatabaseSettings()
            try:
                cls._engine = create_async_engine(
                    cls._settings.DB_URL,
                    pool_pre_ping=True,
                    pool_size=cls._settings.DB_POOL_SIZE,
                    max_overflow=cls._settings.DB_MAX_OVERFLOW,
                    pool_recycle=cls._settings.DB_POOL_RECYCLE,
                    echo=cls._settings.DB_DEBUG,
                    connect_args={
                        "connect_timeout": 10,
                        "charset": "utf8mb4",
                    }
                )
                cls._session_factory = async_sessionmaker(
                    bind=cls._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                    autoflush=False
                )
                cls.Base = Base
            except Exception as e:
                trace_id = str(uuid4())
                logger.error(f"Failed to initialize database engine. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"Database initialization failed. Trace ID: {trace_id}") from e
        return cls._instance

    @property
    def engine(self):
        return self._engine

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                trace_id = str(uuid4())
                logger.error(f"Transaction failed: {e}. Trace ID: {trace_id}")
                raise HTTPException(status_code=500, detail=f"Database transaction failed. Trace ID: {trace_id}") from e

    async def health_check(self) -> bool:
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            trace_id = str(uuid4())
            logger.error(f"Health check failed: {e}. Trace ID: {trace_id}")
            return False

    async def initialize_database(self, drop_existing: bool = False, models_and_data: List[Tuple[Type[Base], List[dict]]] = None):
        if not await self.health_check():
            raise ConnectionError("Database connection failed")

        async with self.engine.begin() as conn:
            if drop_existing:
                logging.warning("Dropping existing tables...")
                await conn.run_sync(self.Base.metadata.drop_all)

            logging.info("Creating tables...")
            await conn.run_sync(self.Base.metadata.create_all)

            if models_and_data:
                async with self.session() as session:
                    try:
                        for model, data_list in models_and_data:
                            for data in data_list:
                                instance = model(**data)
                                session.add(instance)
                        await session.commit()
                        logging.info("Default data inserted successfully.")
                    except Exception as e:
                        logging.error(f"Failed to insert default data: {e}")
                        await session.rollback()
"""


database_model_code = """
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    email = Column(String(100))
"""


frontend_dockerfile_code = """
FROM harbor.eazytec-building.com/eazytec/node:22.12.0

# 设置工作目录
WORKDIR /workdir/project/project/frontend

# 复制依赖文件并安装依赖（层缓存优化）
COPY package*.json ./
RUN npm install --registry=http://2.2.0.23:45923/repository/group-npm/

# 复制应用代码
COPY . .

# 设置环境变量：前端服务端口（默认3000，可通过容器环境变量覆盖）
ENV APP_PORT_1=3000
ENV NODE_ENV=development

# 暴露前端服务端口（使用环境变量APP_PORT_1）
EXPOSE ${APP_PORT_1}

# 定义启动命令（使用npm run dev，框架会自动读取APP_PORT_1环境变量）
CMD ["npm", "run", "dev"]
"""

backend_dockerfile_code = """
# 使用提供的Python基础镜像
FROM hb.eazytec-cloud.com/eazydevelop/python:3.12.3-slim-amd64

# 清空原有源配置
RUN rm -f /etc/apt/sources.list.d/*

# 配置完整清华源
RUN echo "deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware\n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware\n\
deb http://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" > /etc/apt/sources.list

# 安装 Python 3.11 和虚拟环境支持
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 创建并激活 Python 3.11 虚拟环境
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装编译工具链
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libbz2-dev \
    libncurses-dev \
    libgdbm-dev \
    liblzma-dev \
    libsqlite3-dev \
    zlib1g-dev \
    libreadline-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

# 复制应用代码
COPY . .

# 环境变量与启动命令
ENV APP_PORT_2=8000 HOST=0.0.0.0
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""