#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/12 22:24
@Author  : alexanderwu
@File    : design_api_an.py
"""
from typing import List, Optional, Union

from metagpt.actions.action_node import ActionNode
from metagpt.utils.mermaid import MMC1, MMC2, MMC3

IMPLEMENTATION_APPROACH = ActionNode(
    key="Implementation approach",
    expected_type=str,
    instruction="Analyze technical challenges and architectural requirements based on Project Settings (type, stack, configurations), then select compatible open-source frameworks that adhere to the defined stack constraints and dependency specifications.",
    example="We will ...",
)

REFINED_IMPLEMENTATION_APPROACH = ActionNode(
    key="Refined Implementation Approach",
    expected_type=str,
    instruction="Update and extend the original implementation approach to reflect the evolving challenges and "
    "requirements due to incremental development. Outline the steps involved in the implementation process with the "
    "detailed strategies.",
    example="We will refine ...",
)

PROJECT_NAME = ActionNode(
    key="Project name", expected_type=str, instruction="The project name with underline", example="game_2048"
)


# FILE_LIST = ActionNode(
#     key="Project File Structure",
#     expected_type=list[str],
#     instruction="Based on 'Project Setting', List relative file paths following modern project structure conventions. "
#                 "There Must shuold be only one main execution file with a name commonly used for the main entry point (such as 'main.py' for Python, 'main.js' for Node.js etc.) and it must be at the project root for easy execution. "
#                 "For frontend projects, there must be a dedicated directory for frontend code, and the `index.html`, `package.json` file should be located at the root of this frontend directory as the entry point. "
#                 "Configuration files should be at root level. "
#                 "Static assets go under static/ with subdirectories by type. "
#                 "Not include test files. "
#                 "For backend code of any type, organize non-main execution files in relevant sub-directories, but ensure no other file with the main execution file name exists within backend directories.",
#     example=[
#         # 根目录文件
#         "main.py",              # 主入口文件
#         "requirements.txt",     # Python依赖
#         "README.md",            # 项目文档

#         # 前端文件
#         "frontend/index.js",    # 前端主入口
#         "frontend/App.jsx",     # 主组件
#         "frontend/assets/main.css",  # 样式文件
#         "frontend/index.html",  # Frontend entry (required, in frontend directory)
#         "frontend/package.json",         # Node.js依赖(如适用)"

#         # 后端文件
#         "api/__init__.py",      # Python包初始化
#         "api/routes.py",        # 路由定义
#         "api/models.py",        # 数据模型

#         # 模板和静态文件
#         "templates/base.html",  # 基础模板
#         "static/js/bundle.js",  # 打包后的JS
#         "static/css/styles.css" # 编译后的CSS
#     ],
# )


FILE_LIST = ActionNode(
    key="Project File Structure",
    expected_type=List[List[str]],
    instruction="Based on 'Project Setting', generate file paths that must satisfy: "
                "1. Root Level: Include a single main entry file (main.py for Python backend or app.js for JavaScript backend), README.md for project documentation, and config files like .env for environment variables or requirements.txt for dependencies. "
                "2. Backend: "
                "- Have a database configuration file (such as database.py or database/__init__.py) to handle database connections and setups. "
                "- Contain model files (models.py or within a models/ directory) to define database schemas and data structures. "
                "- Include business logic files (in services/ or core/ directories) to implement application - specific operations. "
                "- Have API endpoint files (routes.py or in an api/ directory) to define the API routes and handle requests. "
                "3. Frontend: Include index.html as the main HTML entry point, package.json for managing project metadata and dependencies, vite.config.ts for build configuration, and an src/ directory for source code. Also, include router (for routing), store (for state management), app.vue (the root component), and global.less (for global styles).\n"
                "4. Validation: Ensure all imports resolve to existing files and there are no duplicate entry points. Each returned element should be a list where the first item is the file path and the second item is a brief description of the file's role in the project.",
    example=[
        ["main.py", "The main entry point of the backend application, responsible for initializing the application and starting the server."],
        ["requirements.txt", "Lists all the Python dependencies required for the backend project to run."],
        ["backend/database.py", "Contains the configuration and connection setup code for the database used by the backend."],
        ["backend/models/user.py", "Defines the data model for user entities, including database table schema and related operations."],
        ["backend/api/users.py", "Defines the API endpoints related to user management, handling user - related requests and responses."],
        ["frontend/index.html", "The main HTML file that serves as the entry point for the frontend application, providing the basic structure for the web page."],
        ["frontend/src/App.jsx", "The root component of the frontend application, where the overall application layout and initial rendering logic are defined."]
    ]
)

REFINED_FILE_LIST = ActionNode(
    key="Refined File list",
    expected_type=List[str],
    instruction="Update and expand the original file list including only relative paths. Up to 2 files can be added."
    "Ensure that the refined file list reflects the evolving structure of the project.",
    example=["main.py", "game.py", "new_feature.py"],
)

# optional,because low success reproduction of class diagram in non py project.
DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Data structures and interfaces",
    expected_type=Optional[str],
    instruction="Use mermaid classDiagram to create a software system class diagram covering front - end, back - end, or both."
                "### Class & Method"
                "- Define classes with constructors (__init__) and other methods. Add clear type annotations to parameters and return values."
                "### Relationships"
                "- Mark class associations like inheritance, composition, and aggregation."
                "- Show invocation relationships: specify HTTP requests for front - end to back - end calls, and indicate peer - to - peer or hierarchical internal calls."
                "### Data & API"
                "- Detail class data structures with well - defined property types."
                "- Design comprehensive APIs for relevant classes. Include backend CRUD operations and define input/output data models."
                "### Naming"
                "- Follow PEP8: use PascalCase for classes, lowercase with underscores for methods/properties.",
    example=MMC3,
)

REFINED_DATA_STRUCTURES_AND_INTERFACES = ActionNode(
    key="Refined Data structures and interfaces",
    expected_type=str,
    instruction="Update and extend the existing mermaid classDiagram code syntax to incorporate new classes, "
    "methods (including __init__), and functions with precise type annotations. Delineate additional "
    "relationships between classes, ensuring clarity and adherence to PEP8 standards."
    "Retain content that is not related to incremental development but important for consistency and clarity.",
    example=MMC1,
)

PROGRAM_CALL_FLOW = ActionNode(
    key="Program call flow",
    expected_type=Optional[str],
    instruction="Use sequenceDiagram code syntax, COMPLETE and VERY DETAILED, using CLASSES AND API DEFINED ABOVE "
    "accurately, covering the CRUD AND INIT of each object, SYNTAX MUST BE CORRECT.",
    example=MMC2,
)

REFINED_PROGRAM_CALL_FLOW = ActionNode(
    key="Refined Program call flow",
    expected_type=str,
    instruction="Extend the existing sequenceDiagram code syntax with detailed information, accurately covering the"
    "CRUD and initialization of each object. Ensure correct syntax usage and reflect the incremental changes introduced"
    "in the classes and API defined above. "
    "Retain content that is not related to incremental development but important for consistency and clarity.",
    example=MMC2,
)

ANYTHING_UNCLEAR = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention unclear project aspects, then try to clarify it.",
    example="Clarification needed on third-party API integration, ...",
)

PROJECT_SETTINGS = ActionNode(
    key="Project Settings",
    expected_type=str,
    instruction="Extract Project Settings information, Must should include Dependencies Requirements(Do Not omit information), File Structure.",
    example="""

""",
)

DTATBASE_SETTINGS = ActionNode(
    key="Database Setting",
    expected_type=Optional[Union[str, dict]],
    instruction="""Extract database configuration from 'Project Settings and return as structured dict. 
                    Required fields: engine, host, port, username, password(must show), database, url. 
                    Parse connection URLs if available (format: engine+driver://user:pass@host:port/db). 
                    Handle multiple databases under 'default'/'redis'/'mongodb' keys. 
                    Return empty dict if no config found.""",
    example= """mysql": "mysql+asyncmy://root:123456@127.0.0.1:3306/eazydevelop
            redis": "redis://:123456@127.0.0.1:6379/1
            mongodb": "mongodb://mongoadmin:123456@127.0.0.1:27017/mydb?authSource=admin&retryWrites=true&w=majority"""
)
ARCHITECTURAL_OVERVIEW = ActionNode(
    key="Architectural Overview",
    expected_type=str,
    instruction="Describe the architectural pattern (such as layered architecture) and principles adopted by the project. Explain the way of separating the front - end and back - end (if any). Elaborate on how the architecture ensures the maintainability, scalability, and testability of the system, as well as its contribution to the flexibility of services and the improvement of user experience.",
    example=""
)

SYSTEM_COMPONENTS = ActionNode(
    key="System Components",
    expected_type=str,
    instruction="This instruction is designed to guide the creation of a comprehensive description of a software system's architecture. Data Layer: Justify DBMS choice, state stored data types, detail data modeling and ORM (if applicable), and note query optimization. Service Layer: Elaborate on service module functions per project needs, and explain interface exposure and support for different logics. Presentation Layer: Explain front - end framework usage, related tech (routing, state mgmt), describe UI design (page comp, responsive), and user experience optimization.",
    example=""
)

TECHNICAL_STACK = ActionNode(
    key="Technical Stack",
    expected_type=str,
    instruction="Based on 'Project Settings', summarize the usage of front - end, back - end, database, security - related, and other key technologies (such as containerization technology).",
    example=""
)


NODES = [
    IMPLEMENTATION_APPROACH,
    # PROJECT_NAME,
    FILE_LIST,
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
    PROJECT_SETTINGS
]

NEW_NODES = [
    ARCHITECTURAL_OVERVIEW,
    SYSTEM_COMPONENTS,
    TECHNICAL_STACK
]

CODE_DESIGN_NODES = [
    DATA_STRUCTURES_AND_INTERFACES,
    PROGRAM_CALL_FLOW,
    FILE_LIST,
    PROJECT_SETTINGS,
    DTATBASE_SETTINGS,
]


REFINED_NODES = [
    REFINED_IMPLEMENTATION_APPROACH,
    REFINED_FILE_LIST,
    REFINED_DATA_STRUCTURES_AND_INTERFACES,
    REFINED_PROGRAM_CALL_FLOW,
    ANYTHING_UNCLEAR,
]

DESIGN_API_NODE = ActionNode.from_children("SystemDesign", NEW_NODES)
REFINED_DESIGN_NODE = ActionNode.from_children("RefinedDesignAPI", REFINED_NODES)
CODE_DESIGN_NODE = ActionNode.from_children("CodeDesign", CODE_DESIGN_NODES)