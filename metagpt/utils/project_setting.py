import json

# def get_project_setting(project_config):
       
#     project_type_map = {
#         "frontend": "Frontend Project",
#         "backend": "Backend Project",
#         "fullstack": "Fullstack Project"
#     }

#     # Core project info
#     project_desc = f"Project Type: {project_type_map.get(project_config.project_type, 'Unknown Project Type')}"

#     components = [project_desc]
#     file_requirements = []

#     # Database config (conditional)
#     def has_database_config():
#         return any([
#             project_config.database_url,
#             project_config.database_type,
#             project_config.database_port,
#             project_config.database_username,
#             project_config.database_password
#         ])

#     if project_config.project_type in ["backend", "fullstack"] or (
#             project_config.project_type == "frontend" and has_database_config()
#     ):
#         db_password = f"{project_config.database_password}" if project_config.database_password else "[Not Set]"
#         database_desc = (
#             "Database Configuration:\n"
#             f"- Url: {project_config.database_url or 'Not specified'}\n"
#             f"- Type: {project_config.database_type.upper() if project_config.database_type else 'Not specified'}\n"
#             f"- Port: {project_config.database_port or 'Not specified'}\n"
#             f"- Table: {project_config.database_table or 'Not specified'}\n"
#             f"- Username: {project_config.database_username or 'Not specified'}\n"
#             f"- Password: {db_password}"
#         )
#         components.append(database_desc)

#     # Frontend configuration
#     if project_config.project_type in ["frontend", "fullstack"] and project_config.frontend_framework:
#         frontend_desc = f"Frontend Framework: {project_config.frontend_framework.capitalize()}"
#         components.append(frontend_desc)

#         # Frontend file structure
#         if project_config.frontend_framework.lower() == "react":
#             file_requirements.append(
#                 # "Frontend File Structure and Dependencies:\n"
#                 # "package.json         # Manages project dependencies and scripts\n"
#                 # "vite.config.js       # Configuration for Vite build tool\n"
#                 # "index.html           # Main application entry point\n"
#                 # "src/ the source code direction, include       \n"
#                 # "src/main.jsx         # Root component rendering\n"
#                 # "src/App.jsx          # Main application component\n"
#                 # "src/router           # Routing related directories"
#                 # "src/router/index.jsx # Routing configuration files"   
#                 # "src/components/\n  #the components direction\n"
#                 # "src/components/Button.jsx   # Example component module\n"

#                 # "Dependencies Requirements:\n"
#                 # "[\n"
#                 # "react==18.2.0,\n"
#                 # "react-dom==18.2.0,\n"
#                 # "react-router-dom==6.21.1\n"
#                 # "@vitejs/plugin-react==4.2.1,\n"
#                 # "@types/react==18.2.45,\n"
#                 # "@types/react-dom==18.2.18,\n"
#                 # "vite==5.1.4\n"
#                 # "]\n"
#                 ""
#             )
#         elif project_config.frontend_framework.lower() == "vue":
#             file_requirements.append(
#                 # "Frontend File Structure and Dependencies:\n"
#                 # "package.json  # Manages project dependencies and scripts\n"
#                 # "vite.config.js       # Configuration for Vite build tool\n"
#                 # "index.html           # Main application entry point\n"
#                 # "src/ the source code direction, include       \n"
#                 # "src/main.js          # Vue application entry point\n"
#                 # "src/App.vue          # Root Vue component\n"
#                 # "src/router           # Routing related directories"
#                 # "src/router/index.js  # Routing configuration files"   
#                 # "src/components/  #the components direction\n"
#                 # "src/components/HelloWorld.vue # Example component module\n"

#                 # "Dependencies Requirements:\n"
#                 # "[\n"
#                 # "vue==3.4.21,\n"
#                 # " vue-router==4.3.0,\n"
#                 # " pinia==2.1.7\n"
#                 # " @vitejs/plugin-vue==5.0.4,\n"
#                 # " @vue/eslint-config-typescript==12.0.0,\n"
#                 # " eslint-plugin-vue==9.25.0,\n"
#                 # " vite==5.1.4\n"
#                 # "]\n"
#                 ""
#             )

#     # Backend configuration
#     if project_config.project_type in ["backend", "fullstack"]:
#         if project_config.backend_framework and project_config.backend_language:
#             backend_desc = (
#                 "Backend Configuration:\n"
#                 f"- Language: {project_config.backend_language.capitalize()}\n"
#                 f"- Framework: {project_config.backend_framework.capitalize()}"
#             )
#             components.append(backend_desc)

#         # Backend file structure
#         file_requirements.append(
#             # "Backend File Structure and Dependencies:\n"
#             # "requirements.txt  # Records all Python dependency packages and their versions\n"
#             # "main.py  # The main application entry point (initializes the application instance and starts the service)\n"
#             # "config.py  # Centralized management of configurations such as database connections and secret keys\n"
#             # "models /  # Directory for data model definitions (ORM classes)\n"
#             # "routes /  # Directory for route modules (API endpoint definitions)\n"
#             # "utils /  # Directory for utility functions (optional)\n"
#             # "migrations /  # Directory for database migration scripts\n"
#             # "Dependencies Requirements:\n"
#             "[\n"
#             "fastapi==0.109.2\n"
#             "uvicorn==0.27.1\n"
#             "pydantic==2.10.6\n"
#             "pydantic_core==2.27.2\n"
#             "pydantic-settings==2.8.1\n"
#             "numpy==2.2.3\n"
#             "sqlalchemy==2.0.29\n"
#             "pymysql==1.1.0\n"
#             "]\n"
            
#         )

#     # Extra fields
#     if project_config.extra_fields:
#         extra_items = "\n".join([f"- {k}: {v}" for k, v in project_config.extra_fields.items()])
#         components.append(f"Additional Configurations:\n{extra_items}")

#     # Add file requirements if any
#     if file_requirements:
#         components.append("\n".join(file_requirements))

#     string = "\n".join(filter(None, [
#         *components
#     ]))
#     return json.dumps(project_setting, ensure_ascii=False, indent=4)



def merge_json_string(json_string1, json_string2):
    try:
        # 尝试将第一个 JSON 字符串解析为 Python 对象
        obj1 = json.loads(json_string1)
        # 尝试将第二个 JSON 字符串解析为 Python 对象
        obj2 = json.loads(json_string2)

        merged_obj = {**obj1, **obj2}
       
        # 将合并后的对象转换回 JSON 字符串
        return json.dumps(merged_obj, ensure_ascii=False, indent=4)
    except json.JSONDecodeError:
        # 如果 JSON 解析失败，直接返回拼接后的字符串
        return json_string1 + json_string2
    
def get_project_setting(config=None):
    return json.dumps(project_setting, ensure_ascii=False, indent=4)


project_setting = {
    "Project Settings": {
        "metadata": {
            "version": "1.1.0",
            "description": "Standardized Full-Stack Project Configuration Template",
        },
        "backend": {
            "description": "## Backend Configuration\n\n### Core Technology Stack\n- Programming Language: Python 3.10+\n- Web Framework: FastAPI\n- ORM: SQLAlchemy 2.0+\n- Database Migrations: Alembic",
            "structure": "### Standard Directory Structure with Functional Descriptions\n```bash\nbackend/\n├── app/                   # Main application package\n│   ├── core/              # Core application logic and utilities\n│   ├── modules/           # Business feature modules\n│   │   └── module_name/   # Example feature module\n│   │       ├── models/    # Database models and schemas\n│   │       ├── schemas/   # Pydantic validation models\n│   │       ├── api/       # API endpoint definitions\n│   │       └── services/  # Business logic implementation\n│   ├── database/          # Database configuration\n│   │   ├── connection.py  # DB connection setup\n│   │   ├── models.py      # Base model definitions\n│   │   └── session.py     # Session management\n│   └── main.py           # FastAPI application entry point\n└── requirements.txt       # Python dependencies```",
            "dependencies": "aiohttp==3.8.6,alembic==1.13.1,anyio==3.7.1,asgiref==3.7.2,asyncmy==0.2.9,fastapi==0.110.0,pydantic==2.11.2,pydantic_core==2.33.1,pydantic-settings==2.8.1,SQLAlchemy==2.0.25,typer==0.9.0,uvicorn==0.25.0,httpx==0.26.0,python-dotenv==1.0.0,passlib==1.7.4,bcrypt==4.0.1,PyMySQL==1.1.0,greenlet==3.1.1,cryptography==42.0.5",
            "configuration": "### Essential Configuration\n- Environment variables for all sensitive data\n- Separate settings for development/production\n- API versioning in endpoint paths\n- Structured logging configuration"
        },
        "frontend": {
            "description": "## Frontend Configuration\n\n### Core Technology Stack\n- Framework: Vue 3 Composition API\n- Build Tool: Vite\n- UI Library: Element Plus\n- State Management: Pinia\n- Language: TypeScript",
            "structure": "### Standard Directory Structure with Functional Descriptions\n```bash\nfrontend/\n├── src/                   # Source code directory\n│   ├── assets/            # Static assets (images/fonts)\n│   ├── components/        # Reusable Vue components\n│   ├── composables/       # Composition API utilities\n│   ├── router/            # Vue router configuration\n│   ├── stores/            # Pinia state management\n│   ├── views/             # Page-level components\n│   ├── App.vue            # Root application component\n│   └── main.ts            # Application entry point\n├── package.json          # Project metadata and dependencies\n├── index.html            # Main HTML entry point\n├── .eslintrc.js          # ESLint configuration\n└── vite.config.ts        # Vite build configuration```",
            "dependencies": "@iconify/vue@4.1.1,@vueuse/core@10.9.0,axios@1.6.7,dayjs@1.11.10,element-plus@2.5.6,lodash-es@4.17.21,mitt@3.0.1,nprogress@0.2.0,pinia@2.1.7,pinia-plugin-persistedstate@3.2.1,vue@3.4.20,vue-router@4.3.0,vue-i18n@9.9.1",
            "devDependencies": "@intlify/unplugin-vue-i18n@2.0.0,@types/node@20.11.21,@typescript-eslint/eslint-plugin@7.1.0,@typescript-eslint/parser@7.1.0,@vitejs/plugin-vue@5.0.4,eslint@8.57.0,eslint-config-prettier@9.1.0,eslint-plugin-prettier@5.1.3,eslint-plugin-vue@9.22.0,less@4.2.0,prettier@3.2.5,typescript@5.3.3,vite@5.1.4,vite-plugin-ejs@1.7.0,vite-plugin-eslint@1.8.1,vite-plugin-progress@0.0.7,vite-plugin-purge-icons@0.10.0,vite-plugin-style-import@2.0.0,vite-plugin-svg-icons@2.0.1,consola@3.2.2,terser@5.26.0",
            "features": "### Standard Features\n- Theme customization system\n- Internationalization support\n- Authentication integration\n- Responsive layout system\n- Performance optimization setup"
        },
        "quality_standards": {
            "testing": "### Testing Requirements\n- Minimum 80% unit test coverage\n- API contract validation tests\n- Critical path end-to-end tests\n- Automated visual regression testing",
            "documentation": "### Documentation Requirements\n- API specification (OpenAPI format)\n- Component documentation\n- Development environment setup guide\n- Deployment procedures"
        },
        "environment_management": {
            "frontend": {
                "development": {
                    "base_url": "http://localhost:${APP_PORT_1}",
                    "api_proxy": "/api -> http://localhost:${APP_PORT_2}"
                }
            },
            "backend": {
                "development": {
                    "server_url": "http://localhost:${APP_PORT_2}"
                }
            }
        },
        "databases": {
            "configuration": "### Database Connection Specifications\n\n1. MySQL (Primary DB):\n- Connection URL: mysql+asyncmy://{user}:{password}@{host}:{port}/{database}\n- Min/Max connections: 5/20 in dev, 10/100 in production\n- Connection timeout: 30s\n\n4. Connection Pool Settings:\n| Parameter       | Development | Production |\n|-----------------|-------------|------------|\n| Pool Size       | 5           | 20         |\n| Max Overflow    | 10          | 50         |\n| Timeout         | 30s         | 10s        |",
            "urls": {
                "mysql": "mysql+asyncmy://root:123456@127.0.0.1:3306/eazydevelop",
            }
        }
    }
}