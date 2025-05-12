#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code.py
@Modified By: mashenquan, 2023-11-1. In accordance with Chapter 2.1.3 of RFC 116, modify the data type of the `cause_by`
            value of the `Message` object.
@Modified By: mashenquan, 2023-11-27.
        1. Mark the location of Design, Tasks, Legacy Code and Debug logs in the PROMPT_TEMPLATE with markdown
        code-block formatting to enhance the understanding for the LLM.
        2. Following the think-act principle, solidify the task parameters when creating the WriteCode object, rather
        than passing them in when calling the run function.
        3. Encapsulate the input of RunCode into RunCodeContext and encapsulate the output of RunCode into
        RunCodeResult to standardize and unify parameter passing between WriteCode, RunCode, and DebugError.
"""

import json
import os
from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions.action import Action
from metagpt.actions.project_management_an import FILE_RELATION, REQUIRED_PACKAGES, REQUIRED_OTHER_LANGUAGE_PACKAGES, LOGIC_ANALYSIS, SHARED_KNOWLEDGE, FULL_API_SPEC, TASK_LIST, BACKEND_FILES, FRONTEND_FILES
from metagpt.actions.design_api_an import PROGRAM_CALL_FLOW, PROJECT_SETTINGS, DATA_STRUCTURES_AND_INTERFACES, DTATBASE_SETTINGS
from metagpt.actions.write_code_plan_and_change_an import REFINED_TEMPLATE
from metagpt.const import BUGFIX_FILENAME, REQUIREMENT_FILENAME, SIMULATE_ROOT
from metagpt.logs import logger
from metagpt.schema import CodingContext, Document, RunCodeResult
from metagpt.utils.common import CodeParser
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.action_utils import get_values
from metagpt.utils.example_code import vite_example_code, database_example_code, eslintrc_code,package_example_code, database_settings_code, database_connect_code, database_model_code

PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional engineer; the main goal is to write google-style, elegant, modular, easy to read and maintain code
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context

## Product Documentation
For a comprehensive understanding of the project's overall functions, features, and constraints, the product documentation provides essential information:
{product_documentation}

## Design
{design}

## Task
{task}

## Dependency Code
{code}

## Project Directory Reference
The following files are confirmed to exist in the project. Use these paths as the canonical reference for all imports:

## API Compliance Notice
{api_desc}
Both the frontend and backend components of the project are required to strictly comply with the above Full API spec when making requests. This is crucial for maintaining consistent communication and ensuring the stable operation of the entire system.


### Frontend Files
{frontend_files}

### Backend Files
{backend_files}
## Import Guidelines

### 1. Frontend Code Imports
- When writing frontend code, use relative imports based on the location of the current file.
- Relative paths are based on the directory where the current file resides. Use ./ to represent the current directory and ../ to represent the parent directory when constructing paths
- Format of import: `import `module` from root - directory/path/to/module`
- Import format: import module from './path/to/module' or import module from '../path/to/module', etc., depending on the relative position of the module to the current file
- Logging for Debugging: Initialization Logging: In each Vue component's created or mounted lifecycle hook, add a console.log statement to indicate that the component has been initialized.
- Example: 
    - Suppose the current file is {frontend_root}/views/Home.vue and you want to import the {frontend_root}/components/Calculator.vue component. Since the components directory is at the same level as the views directory, you need to go back one level to the parent directory (src) and then enter the components directory from Home.vue. So the import statement should be written as import Calculator from '../components/Calculator.vue'.
    - If the current file is {frontend_root}/components/SubComponent.vue and you want to import AnotherComponent.vue in the same directory, the import statement would be import AnotherComponent from './AnotherComponent.vue'.

### 2. Backend Code Imports
- For backend code, use absolute imports based on the root of the backend project structure. All backend-related imports must start with '{backend_root}'.
- Locate the top - level directory or entry point of the backend part of the project. It might be `{backend_root}.
- Format of import: `from {backend_root}.path.to.module import module_name`
- Example: If the backend root is `{backend_root}`, and you have a model in `{backend_root}/modules/calculator/models.py`, you would write `from {backend_root}.modules.calculator.models import Calculation`

### 3. Relative Imports Prohibition
- Import Order: In both frontend and backend, order imports as follows: external libraries first, then internal project - wide modules, and finally local functional modules. Separate groups with a blank line.
- Version Adherence: Use the exact versions of external libraries specified in the project's package.json (frontend) or requirements.txt (backend) to prevent version - related issues.

## File description
{file_desc}

In such a structure, if you are using a framework like FastAPI for the backend in the `main.py` file.

# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context, follow "Format example", write code.

## Code: {filename}. Write code with triple quoto, based on the following attentions and context.
1.Single File Implementation: Implement only this file, ensuring completeness and reusability.Just write {filename}, not write other file.
2.Complete Code: Ensure the code is reliable and can be integrated into the larger project.
3.Default Values: Always set default values based on project settings. Use strong typing and explicit variables. Avoid circular imports.
4.Follow Design: Strictly adhere to the provided design and interfaces. Do not introduce public member functions that are not part of the design.
5.Dependency Management: Before using external variables or modules, ensure proper imports. Verify that dependency code exists and is used correctly.
6.Database Operations: Use SQLAlchemy (or a suitable alternative) for database connection management. Configure the engine with standard pooling and logging options based on environment variables. For example, set connection - checking, recycling, pool sizing, and overflow limits. Enable SQL logging (echo) based on the DEBUG environment variable.
    - Model Definition with Declarative Base: When employing SQLAlchemy, define database models using the declarative base approach. This provides a structured and Pythonic way to represent database tables and their relationships.
    - Table Existence Check and Creation: Prior to executing any database operations, thoroughly verify if the necessary tables exist. In the event that a table is missing, automatically create it according to the defined models. Alongside table creation, insert default data into the newly created table during the initialization phase. This ensures that the database is in a ready state with pre-populated relevant data.
    - Field Integrity Assurance: Guarantee that all fields in the database tables are defined accurately in accordance with the design requirements. This includes setting the correct data types, lengths, and constraints for each field to maintain data integrity and consistency.
    ```
    {database_example_code}
    ```
7.API Design: If the task involves API implementation, use Pydantic for input/output data structures(like 'from pydantic_settings import BaseSettings, SettingsConfigDict'). Ensure the API design is well-structured and matches front-end requirements.
8.Logging: Add logs for every function and critical code block to facilitate debugging.
9.CORS Configuration: 
    - When implementing a backend API, use fastapi.middleware.cors.CORSMiddleware to configure CORS. Set allow_origins, allow_credentials, allow_methods, and allow_headers appropriately according to project needs. For example, add the front - end domain to allow_origins if they are on different domains, and set allow_credentials to True if credentials like cookies need to be carried.
10 Front-End Integration:
    - API and Data Sync: Ensure front-end code (HTML, JavaScript etc.) precisely matches backend API endpoints and data structures. Correctly handle API requests, methods, and received data according to the defined structures.
    - View Accuracy: Implement front-end views that display data accurately in the right format. Interactive components should function as expected, gracefully handling errors, loading, and empty states with appropriate feedback.
    - Responsive Layout: Create responsive views adapting well to various screen sizes and devices, maintaining consistent and user-friendly layouts.
    - UX Enhancement: Prioritize user experience with intuitive navigation, clear visual hierarchy, and easy-to-use interfaces for efficient task execution.
11.Avoid using relative imports like 'from .module import something in this file. Instead, use absolute imports to prevent.
12.Method Call Restriction: When dealing with classes that encapsulate business logic or database operations (such as ORM model classes), the methods of these classes should only be called from the appropriate service layer or a higher-level module specifically designed for orchestrating these operations. Direct calls to these class methods from other parts of the codebase, especially from unrelated modules or lower-level utility modules, are prohibited. This helps in maintaining a clear separation of concerns and a well-structured codebase.
13.Do Not have any Explanation of the Code.Please use the correct comment method.
14.Vite-Specific Path Configuration in Frontend: In the vite.config.ts file within the frontend project (assuming the frontend root path is {frontend_root}), all file references must be set as relative paths. First, set root: path.resolve(__dirname) to establish the base directory for Vite's build process. Then, when configuring path aliases or other path - related settings, calculate the paths relative to the {frontend_root} directory.
    - For example, to set an alias for the components directory:
    ```
    {example_code}
    ```
15. Environment Dependency Management:All projects must adhere to the following rules regarding environment dependencies based on the ## PACKAGES LIMIT references (such as package.json for Node.js projects or requirements.txt for Python projects)
16. Retrieve database configuration from environment variables:
        mysql_host: Use os.getenv('mysql_host', 'localhost')
        mysql_port: Use int(os.getenv('mysql_port', 3306))
        mysql_database: Use os.getenv('mysql_database', 'default_db')
        mysql_user: Use os.getenv('mysql_user', 'root')
        mysql_password: Use os.getenv('mysql_password', '123456')
17. Interface Mounting and Route Prefix Constraints: 
    - Mounting Order: In the backend entry file (e.g., main.py), mount backend interfaces first
    - Prefix Consistency: 
        - Backend:  Establish a single, project - wide prefix for backend interfaces (e.g., /api). When mounting routes, coordinate prefixes between the main entry file and router files to form correct, non - redundant URLs. For instance, if the main file sets a prefix /api and a router has a relative route xxx, the resulting URL should be /api/xxx. Avoid situations where duplicate prefixes accumulate, such as /api/api/xxx.
        - Frontend: In vite.config.ts, if server URL has a prefix (e.g., /api), frontend requests use relative paths (e.g., /xx/xx). If requests use full paths (e.g., /api/xx/xx), set baseURL to /. Ensure consistent prefix usage to avoid access issues and meet project design.
18. .eslintrc.js File Generation: You can refer to the following code when generating the .eslintrc.js file:
        {eslintrc_code}
19 .Ensure all route dependencies and response models use Pydantic-serializable types, avoiding direct injection of non-model classes like database connections.
    1. Strict separation between:
        - Pydantic models (response/request shapes)
        - Service layer (business logic)
        - Route handlers (API interface)
    2. Route parameters must only accept:
        - Basic Python types (str, int, etc.)
        - Pydantic models
        - FastAPI dependencies that ultimately resolve to Pydantic-serializable types
    3. Prohibited in routes:
        - Direct database objects (Session, Connection, etc.)
        - ORM models
        - Complex non-Pydantic types
    4. Service layer acts as the bridge between:
        - Database operations (using SQLAlchemy models)
        - API layer (returning Pydantic models)

    """


FRONTEND_PROMPT_TEMPLATE = """
NOTICE
Role: You are a professional frontend engineer; the main goal is to write google-style, elegant, modular, and maintainable frontend code.
Language: Please use the same language as the user requirement, but the title and code should still be in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context

## Product Documentation
{product_documentation}

## Design
{design}
## Task
{task}

## Dependency Code
{code}


## Project Directory Reference
### Frontend Files
{frontend_files}

## API Compliance Notice
{api_desc}

Frontend components must strictly comply with the above Full API spec when making requests.
## Import Guidelines
- Use relative imports based on the location of the current file.
- Relative paths are based on directory structure starting from the current file.
- Format of import: `import module from './path/to/module'` or `import module from '../path/to/module'`
- Example:
    - From `{frontend_root}/views/Home.vue`, to import `{frontend_root}/components/Calculator.vue`: `import Calculator from '../components/Calculator.vue'`
    - From `{frontend_root}/components/SubComponent.vue`, to import AnotherComponent in the same folder: `import AnotherComponent from './AnotherComponent.vue'`
- Initialization Logging: In each Vue component's created or mounted lifecycle hook, add a console.log statement to indicate that the component has been initialized.
## Interface Mounting and Route Prefix Constraints:
    1. Prefix Consistency Rule
    Global request prefixes (e.g., baseURL in axios) must align with the API spec’s base path (e.g., /api).
    Never repeat the global prefix in specific request paths (e.g., use /inventory/items instead of /api/inventory/items if baseURL is /api).
    2. Configuration Guidelines
    Centralized Prefix Setup: Define the global request prefix once in a shared config file (e.g., axios instance) to avoid conflicts.
    Path Clarity: Write specific request paths (e.g., in service files) as relative to the global prefix, using only the endpoint’s module/resource path (e.g., /users for an API endpoint at /api/users).
    3. Validation Steps
    Path Concatenation Check: Ensure Global Prefix + Specific Path matches the API spec exactly (e.g., /api + /users = /api/users).
    Cross-Reference: Verify all requests against the API doc to catch unintended prefix duplication (e.g., check for /api in both config and request path).
    4. Prohibited Patterns
    Avoid nested prefixes like /api/api/xxx—they break API compliance.
    Keep prefixes consistent across environments (dev/prod) to prevent routing errors.

## Vite-Specific Path Configuration
In vite.config.ts:
- Set root: `path.resolve(__dirname)`
- Configure aliases using paths relative to {frontend_root}
Example:
{vite_example_code}

## ESlint configuration (if needed):
When generating the .eslintrc.js file, refer to the following configuration content:
{eslintrc_code}

## package.json exmaple code
When creating the project's package.json file, you can refer to the following example. It includes scripts for development, build, preview, and linting, as well as dependencies related to Vue 3 and TypeScript projects. Adjust as needed:
{package_example_code}


## File description
{file_desc}

# Format example
## Code: {filename}
```javascript
...
```

# Instruction: Based on the context, follow "Format example", write code.
## Code: {filename}. Write code with triple quote, based on the following attentions and context.
2. Single File Implementation: Implement only this file, ensuring completeness and reusability.
3. Complete Code: Ensure the code can be integrated into the larger project.
4. Default Values: Always set default values with strong typing and explicit variables.
5. Follow Design: Strictly adhere to UI/UX design and component specifications.
6. Dependency Management: Ensure all required modules are imported correctly.
7. Front-End Integration:
    - API and Data Sync: Match backend API endpoints and data structures.
    - View Accuracy: Display data accurately and handle errors, loading, empty states.
    - Responsive Layout: Create responsive views adapting to various screen sizes.
    - UX Enhancement: Prioritize intuitive navigation and visual clarity.
8. Do Not have any Explanation of the Code. Please use the correct comment method.
9. Environment Dependency Management: Adhere to dependencies defined in package.json.
"""


BACKEND_PROMPT_TEMPLATE = """
Role: You are a professional backend engineer; the main goal is to write google-style, elegant, modular, and maintainable backend code.
Language: Please use the same language as the user requirement, but the title and code should still be in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context

## Product Documentation
{product_documentation}

## Design
{design}

## Task
{task}

## Dependency Code
{code}


## Project Directory Reference
### Backend Files
{backend_files}

## API Compliance Notice
{api_desc}
Backend components must strictly comply with the above Full API spec when handling requests.

## Import Guidelines
    - Use absolute imports based on the root of the backend project structure.
    - All imports start with '{backend_root}'.
    - Format: from {backend_root}.path.to.module import module_name
    - Example:
        - Model in {backend_root}/modules/calculator/models.py: from {backend_root}.modules.calculator.models import Calculation

## File description
{file_desc}
In such a structure, if you are using a framework like FastAPI for the backend in the main.py file.

## Database Operations:
 - Use SQLAlchemy for database connection management, configured via environment variables for pooling, logging, and connection settings.
    ### Database Configuration
    - Define connection parameters and pool settings using environment variables (via Pydantic):
    {database_settings_code}
    - Requirements:
        - Use DB_DEBUG to enable SQL logging (echo=True in the engine).
        - Configure connection pooling (size, overflow, recycle) via environment variables

    ### Database Connection Management
    - Implement a singleton manager for database connections and sessions:
    {database_connect_code} 
    - Requirements:
        - Enable pool_pre_ping for connection validation.
        - Centralize session handling with auto-commit/rollback.
    ### Model Definition with Declarative Base (models.py)
        - Define database models using SQLAlchemy’s declarative base, ensuring field integrity:
    {database_model_code}
    - Requirements:
        - Use declarative base for table-model mapping.
        - Enforce data types (e.g., String(50)) and constraints (e.g., nullable=False).
        - Table Initialization & Default Data
        - Auto-create tables and insert default data during setup:
        - Check for missing tables using Base.metadata.create_all().
        - Seed initial data (e.g., admin users) after table creation.
    ### Key Constraints
        - Configuration: All settings (connection URL, pool size, debug mode) must be environment-driven.
        - Connection Pooling: Use pool_size, max_overflow, and pool_recycle for efficient connection reuse.
        - Model Integrity: Define fields with exact data types, lengths, and constraints (nullability, uniqueness).
        - Bootstrap: Ensure tables exist and default data is present before application startup.


# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context, follow "Format example", write code.
# Code: {filename}. Write code with triple quote, based on the following attentions and context.
1. Single File Implementation: Implement only this file, ensuring completeness and reusability.
2. Complete Code: Ensure the code is reliable and can be integrated into the larger project.
3. Default Values: Always set default values based on project settings. Use strong typing.
4. Follow Design: Strictly adhere to provided interfaces and models.
5. Dependency Management: Before using external variables or modules, ensure proper imports.
6. API Design:
    - Use Pydantic for input/output data structures.
    - Route parameters must only accept basic types or Pydantic models.
    - Prohibited in routes: ORM models, database objects, non-Pydantic types.
7. Logging: Add logs for every function and critical code block.
8. CORS Configuration:
    - Use fastapi.middleware.cors.CORSMiddleware.
    - Set allow_origins, allow_credentials, allow_methods, allow_headers properly.
9. Interface Mounting and Route Prefix Constraints:
    - Mounting Order: In the backend entry file (e.g., main.py), always mount backend interfaces first. Organize the mounting sequence to ensure a clear and logical flow of API endpoints.
    - Prefix Consistency and API Compliance:
        All route prefixes and URL structures must strictly adhere to the specifications defined in 'API Compliance Notice'. This includes both the global prefixes set in the main entry file (e.g., app.include_router(router, prefix="/api")) and the local prefixes within individual routers (e.g., APIRouter(prefix="/subpath")). Avoid creating nested or redundant prefixes (e.g., /api/api/xxx) that deviate from the API spec.
        When combining route definitions across different files, ensure that the concatenated URL (e.g., global prefix + router prefix + route path) matches the 'API Compliance Notice' exactly. For example, if a main router sets a prefix /api and a sub-router defines /resource, the final URL /api/resource must align with the API documentation. Regularly cross-check all route configurations against 'API Compliance Notice' to prevent integration issues and ensure seamless communication between frontend and backend components.
10. Retrieve database configuration from environment variables:
    mysql_host: os.getenv('mysql_host', 'localhost')
    mysql_port: int(os.getenv('mysql_port', 3306))
    mysql_database: os.getenv('mysql_database', 'default_db')
    mysql_user: os.getenv('mysql_user', 'root')
    mysql_password: os.getenv('mysql_password', '123456')
11. Method Call Restriction: Business logic methods must be called from service layer only.
12. Do Not have any Explanation of the Code. Please use the correct comment method.
13. Environment Dependency Management: Adhere to dependencies defined in requirements.txt.
14. Ensure all route dependencies and response models use Pydantic-serializable types.
"""

def read_first_line(string):
    lines = string.splitlines()
    first_line = lines[0]
    return first_line

class WriteCode(Action):
    name: str = "WriteCode"
    i_context: Document = Field(default_factory=Document)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code(self, prompt) -> str:
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code

    async def run(self, *args, **kwargs) -> CodingContext:
        coding_context = CodingContext.loads(self.i_context.content)
        self.config.current_role = f'ENGINEER'
        self.config.role_task = f'1/3 Write code'

        code_context = await self.get_codes(
            coding_context.task_doc,
            exclude=self.i_context.filename,
            project_repo=self.repo.with_src_path(self.context.src_workspace),
        )
        product_documentation= json_to_markdown(json.loads(coding_context.prd_doc.content), depth=3)
        design_desc = await self.parse_design(coding_context.design_doc.content)
        testcase = coding_context.testcase_doc.content
        m = json.loads(coding_context.task_doc.content)
        backend_list =m.get(BACKEND_FILES.key, "")
        backend_root = await self.find_root(backend_list)
        front_list = m.get(FRONTEND_FILES.key, "")
        front_root = await self.find_root(front_list)
        api_desc = m.get(FULL_API_SPEC.key, "")
        filename = self.i_context.filename
        code_type = ""
        file_ext = filename.split(".")[-1]
        if filename in backend_list or file_ext in ["py", "txt"]:
            code_type = "backend"
        elif filename in front_list or file_ext in ["json", "vue", "js", "ts", "less", "html"]:
            code_type = "frontend"
        
        if code_type == "frontend":
            prompt = FRONTEND_PROMPT_TEMPLATE.format(
                product_documentation=product_documentation,
                design=design_desc,
                task=await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                code=code_context,
                frontend_files=front_list,
                api_desc=api_desc,
                frontend_root=front_root,
                vite_example_code=vite_example_code,
                eslintrc_code=eslintrc_code,
                file_desc=await self.get_file_desc(self.i_context.filename, file_list=coding_context.file_list,file_desc=coding_context.fix_file_desc),
                filename=self.i_context.filename,
                package_example_code=package_example_code
            )
        elif code_type == "backend":
            prompt = BACKEND_PROMPT_TEMPLATE.format(
                product_documentation=product_documentation,
                design=design_desc,
                task=await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                code=code_context,
                backend_files=backend_list,
                api_desc=api_desc,
                backend_root=backend_root,
                database_settings_code=database_settings_code,
                database_connect_code=database_connect_code,
                database_model_code=database_model_code,
                file_desc=await self.get_file_desc(self.i_context.filename, file_list=coding_context.file_list,file_desc=coding_context.fix_file_desc),
                filename=self.i_context.filename
            )
        else:
            prompt = PROMPT_TEMPLATE.format(
                design=design_desc,
                product_documentation=product_documentation,
                task=await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                code=code_context,
                filename=self.i_context.filename,
                frontend_files=front_list,
                backend_files=backend_list,
                frontend_root=front_root,
                backend_root=backend_root,
                example_code=vite_example_code,
                database_example_code=database_example_code,
                eslintrc_code=eslintrc_code,
                file_desc=await self.get_file_desc(self.i_context.filename, file_list=coding_context.file_list,file_desc=coding_context.fix_file_desc),
                api_desc=api_desc
                # template_code=template_code
            )
        logger.info(f"Writing {coding_context.filename}..")
        oh_action_data = {}
        content_info = {
            "sub_content": f"Writing {coding_context.filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        code = await self.write_code(prompt)
        if self.config.simulate:
            file_path = SIMULATE_ROOT / "project" / filename
            assert file_path.exists()
            with open(file_path, "r") as f:
                code = f.read()
        if not coding_context.code_doc:
            # avoid root_path pydantic ValidationError if use WriteCode alone
            root_path = self.context.src_workspace if self.context.src_workspace else ""
            coding_context.code_doc = Document(filename=coding_context.filename, root_path=str(root_path))
        
        # if coding_context.filename == "requirements.txt":
        #     root_path = self.repo.workdir
        #     coding_context.code_doc = Document(filename=coding_context.filename, root_path=str(root_path))
        #     logger.info(f"Writing requirements.txt to {root_path}..")

        if coding_context.filename == "system_test_playwright_code.py":
            root_path = self.repo.tests.workdir
            coding_context.code_doc = Document(filename=coding_context.filename, root_path=str(root_path))
            logger.info(f"Writing system_test_playwright_code.py to {root_path}..")

        coding_context.code_doc.content = code
        return coding_context

    @staticmethod
    async def get_codes(task_doc: Document, exclude: str, project_repo: ProjectRepo, use_inc: bool = False) -> str:
        """
        Get codes for generating the exclude file in various scenarios.

        Attributes:
            task_doc (Document): Document object of the task file.
            exclude (str): The file to be generated. Specifies the filename to be excluded from the code snippets.
            project_repo (ProjectRepo): ProjectRepo object of the project.
            use_inc (bool): Indicates whether the scenario involves incremental development. Defaults to False.

        Returns:
            str: Codes for generating the exclude file.
        """

        def _expand_filenames(file_relation_dict, initial_filenames):
            # 初始化结果列表，用于存储所有找到的文件名
            result = []
            # 初始化队列，将初始文件名列表放入队列中
            queue = initial_filenames[:]

            while queue:
                # 从队列中取出一个文件名
                filename = queue.pop(0)
                # 如果该文件名还未处理过
                if filename not in result:
                    # 将该文件名添加到结果列表中
                    result.append(filename)
                    # 获取该文件名对应的关联文件名列表
                    related_filenames = file_relation_dict.get(filename, [])
                    # 将关联文件名列表中不在结果列表中的文件名添加到队列中
                    for related_filename in related_filenames:
                        if related_filename not in result:
                            queue.append(related_filename)

            return result

        if not task_doc:
            return ""
        if not task_doc.content:
            task_doc = project_repo.docs.task.get(filename=task_doc.filename)
        m = json.loads(task_doc.content)
        # code_filenames = m.get(TASK_LIST.key, []) if not use_inc else m.get(REFINED_TASK_LIST.key, [])
        file_relation = m.get(FILE_RELATION.key, []) if not use_inc else m.get(FILE_RELATION.key, [])
        file_relation_dict = {item[0]: item[1] for item in file_relation}
        code_filenames_tmp = file_relation_dict.get(exclude, [])
        code_filenames = _expand_filenames(file_relation_dict, code_filenames_tmp)
        logger.info(f"{exclude} related filenames: {code_filenames}")

        codes = []
        files = []
        src_file_repo = project_repo.srcs

        for filename in code_filenames:
            # Exclude the current file to get the code snippets for generating the current file
            if filename == exclude:
                continue
            doc = await src_file_repo.get(filename=filename)
            if not doc:
                continue
            files.append(filename)
            codes.append(f"\n{filename}\n```code\n{doc.content}```")

        return str(files) + "\n".join(codes)

    @staticmethod
    async def parse_design(design_doc):
        if not design_doc:
            return ""
        m = json.loads(design_doc)
        # implementation_desc = "### ARCHITECTURAL_OVERVIEW\n " + m.get(ARCHITECTURAL_OVERVIEW.key, "").strip() + "\n"
        # system_desc = "### SYSTEM_COMPONENTS\n " + m.get(SYSTEM_COMPONENTS.key, "").strip() + "\n"
        data_structures_and_interfaces_des = "### DATA_STRUCTURES_AND_INTERFACES\n " + m.get(DATA_STRUCTURES_AND_INTERFACES.key, "").strip() + "\n"
        program_call_flow_desc = "### PROGRAM_CALL_FLOW\n " + m.get(PROGRAM_CALL_FLOW.key, "").strip() + "\n"
        database_setting = m.get(DTATBASE_SETTINGS.key, "")
        if isinstance(database_setting, str):
            database_setting_desc =  "### DATABASE SETTING\n" + database_setting + "\n"
        else:
            database_setting_desc = "### DATABASE SETTING\n" + json.dumps(database_setting, ensure_ascii=False) + "\n"

        return data_structures_and_interfaces_des + program_call_flow_desc + database_setting_desc

    @staticmethod
    async def parse_task(task_doc, code_type):
        if not task_doc:
            return ""
        m = json.loads(task_doc)
        if code_type == "frontend":
            packages_desc = "### PACKAGES LIMIT\n" + ''.join([
                                                f"{dep_type}:\n" +
                                                ''.join([f"  {package_name}: {version}\n" for package_name, version in deps.items()]) +
                                                "\n"
                                                for item in m.get(REQUIRED_OTHER_LANGUAGE_PACKAGES.key, [{}])
                                                for dep_type, deps in item.items()
                                            ])
        elif code_type == "backend":
            packages_desc = "### PACKAGES LIMIT\n " + "\n ".join(m.get(REQUIRED_PACKAGES.key, [])) + "\n"
        else:
            packages_desc = "### PACKAGES LIMIT\n " + "\n ".join(m.get(REQUIRED_PACKAGES.key, []))+ "\n " +  ''.join([
                                f"{dep_type}:\n" +
                                ''.join([f"  {package_name}: {version}\n" for package_name, version in deps.items()]) +
                                "\n"
                                for item in m.get(REQUIRED_OTHER_LANGUAGE_PACKAGES.key, [{}])
                                for dep_type, deps in item.items()
                            ]) + "\n "
        # logic_analysis = {item[0]: item[1] for item in  m.get(LOGIC_ANALYSIS.key, [])}
        # file_logic = "### FILE LOGIC\n " + current_filename + "\n " + logic_analysis.get(current_filename,"") + "\n " if logic_analysis.get(current_filename, None) is not None else ""
        # full_api_desc = "### FULL API SPEC\n " + m.get(FULL_API_SPEC.key, "") + "\n" if m.get(FULL_API_SPEC.key, "") != "" else ""
        shared_knowledge_desc = "### SHARED KNOWLEDGE\n " + m.get(SHARED_KNOWLEDGE.key, "").strip() + "\n "
        return packages_desc  + shared_knowledge_desc


    async def get_file_type(self, filename: str, extensions, case_sensitive=True) -> str:
        target = filename if case_sensitive else filename.lower()
        
        for ext in extensions:
            check_ext = ext if case_sensitive else ext.lower()
            if target.endswith(check_ext):
                return ext
            
        return None



    async def find_root(self, file_list):
        if not file_list:
            return None
        # 收集所有可能的根目录候选
        candidates = []
        for file in file_list:
            parts = file.split(os.sep)
            if parts:
                candidates.append(parts[0])

        # 统计每个候选根目录的出现次数
        count_dict = {}
        for candidate in candidates:
            count_dict[candidate] = count_dict.get(candidate, 0) + 1

        # 选择出现次数最多的候选作为根目录
        root = max(count_dict, key=count_dict.get)
        return root




    async def get_file_desc(self, file_name, file_list, file_desc):
        # 提取目标文件所在的文件夹路径
        parts = file_name.split('/')
        if len(parts) > 1:
            target_dir = '/'.join(parts[:-1])
        else:
            target_dir = ''

        siblings = set()
        for file in file_list:
            if file == file_name:
                continue
            if target_dir:
                if file.startswith(target_dir + '/'):
                    next_part = file[len(target_dir) + 1:].split('/')[0]
                    siblings.add(next_part)
            else:
                file_parts = file.split('/')
                if len(file_parts) == 1:
                    siblings.add(file)
                else:
                    siblings.add(file_parts[0])
        desc = f"{file_name}, situated in the {target_dir} folder, serves the purpose of {file_desc}. Meanwhile, the current directory includes the following files and directories: {siblings}"
        return desc