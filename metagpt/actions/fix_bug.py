from typing import Optional
from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
import os
from pydantic import Field
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.utils.common import CodeParser
from metagpt.schema import CodingContext, Document, RunCodeResult
from metagpt.utils.project_setting import get_project_setting, merge_json_string
from metagpt.actions.launch_project_test_an import SUGGESTION, CONSOLE_OUTPUT, ERROR_MESSAGE, REQUIRES_FILES, ERROR_PRONE_FILES, BUG_FIX_PLAN
from metagpt.actions.design_api_an import PROGRAM_CALL_FLOW, DTATBASE_SETTINGS, DATA_STRUCTURES_AND_INTERFACES, ARCHITECTURAL_OVERVIEW, SYSTEM_COMPONENTS
from metagpt.actions.project_management_an import FILE_RELATION, BACKEND_FILES, FRONTEND_FILES, REQUIRED_OTHER_LANGUAGE_PACKAGES, REQUIRED_PACKAGES, LOGIC_ANALYSIS, FULL_API_SPEC, SHARED_KNOWLEDGE
from metagpt.const import BUGFIX_FILENAME, REQUIREMENT_FILENAME
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.example_code import vite_example_code, database_example_code, eslintrc_code, database_model_code, database_connect_code, database_settings_code
from metagpt.utils.action_utils import get_values

"""
## Design
This field describes the design plan and architecture of the entire code, including design information such as data structures, interface definitions, and module divisions. It provides an overall framework and design principles for code fixing, ensuring that the fixed code conforms to the original design concept.
{design}

## Bug Feedback logs
The log information output by the console, which includes detailed records of the code's operation, such as the function call process and the changes in variable values. By analyzing these logs, you can deeply understand the running state of the code when the problem occurs and assist in finding the cause of the bug.
```text
{bug_feedback}
```

## Fixing Suggestions
Provides some modification suggestions for the current bug. These suggestions are based on the analysis of error information, code dependencies, and the overall design, providing directions and ideas for code fixing.
```text
{modification_suggestions}
```
## Backend Root Directory
Specifies the root directory of the backend code. When writing backend code, all backend-related imports and file references should start with this directory to ensure the consistency and maintainability of the backend code's directory structure.
{backend_root}

## Frontend Root Directory
Specifies the root directory of the frontend code. When writing frontend code, all frontend-related imports and file references should be based on this directory, which helps to standardize the directory structure of the frontend code and avoid path errors. 
{front_root}

"""

BUG_FIX_REFINED_TEMPLATE = """
NOTICE
Role: You are a professional engineer tasked with fixing bugs in legacy code. Your primary objective is to ensure that the updated code resolves the identified bugs.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".


# Context
## Product Documentation
For a comprehensive understanding of the project's overall functions, features, and constraints, the product documentation provides essential information:
{product_documentation}

## Design
{design}

## Task
This is a description of the functional objectives of the code, clarifying the functions and tasks that the code should achieve. When fixing bugs, it is necessary to ensure that the fixed code can complete these tasks.
{task}


## Error Message
Records the error prompt information that appears during the code execution. These messages directly point out the problems in the code and are the key clues for locating and solving bugs.
```text
{error_message}
```

## Dependency Code
This field lists files related to the current one. When fixing issues in the current file, refer to these related files, especially for reference relationships and interfaces. Incorrect references or interface issues between them are common problem sources.
The relevant files are:
{dependency_code}


## Legacy Code
The original code with bugs. Analyzing and modifying this code is the core work of bug fixing. It is necessary to combine the information provided by other fields, identify the problems, and make corrections.
The code is below:
{legacy_code}


## Bug Fix Plan
```text
{bugfix_plan}
```
## Planned Files for Modification or Addition
{bugfile_list}

## Fix File description
{fix_file_desc}


## File List
Lists the files that may be included in the project, helping developers understand the file structure of the project. When fixing the code, these files can be referred to ensure the correctness of imports and file references.
{file_list}

## API Compliance Notice
{api_desc}
Both the frontend and backend components of the project are required to strictly comply with the above Full API spec when making requests. This is crucial for maintaining consistent communication and ensuring the stable operation of the entire system.


# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context including the legacy code, its dependency code, and the error messages, modification_suggestions, follow the "Format example" to write or rewrite the code for bug fix.
## Write/Rewrite Code: Only focus on one file {filename}, write or rewrite the complete code using triple quotes by taking the following points and the context into consideration:
1. Single File Concentration: Devote all your efforts to implementing or modifying THIS SINGLE FILE.
2. Code Completeness: Your code should be an integral, reliable, and reusable part of the whole project. Ensure it is comprehensive enough to function properly within the project framework.
3. Bug Fixing Priority: The code you write must address and fix the bug. Avoid adding new features that are not related to resolving the identified bug.
4. Default Values and Typing: When there are settings involved, always assign default values. Use strong typing and clearly define variables. Make sure to avoid circular imports that could cause issues in the code's execution.
5. Design Adherence: You are required to strictly follow the existing "Data structures and interfaces" design. Do not make any changes to the design, and refrain from using public member functions that are not defined in the design specifications.
6. Code Review and Modification: Carefully examine the error code and its dependent code. Identify parts that need to be modified based on the error messages. Make sure to update the code in a way that it resolves the errors while maintaining the integrity of the overall system.
7. Thorough Function and Class Check: Double-check that you haven't missed any essential classes or functions within this file. Each component should be carefully reviewed and implemented as per the requirements.
8. Import Management: Correctly import external modules in {filename} to avoid runtime errors. If you encounter an import - related error (e.g., ModuleNotFoundError), refer to the provided file list. Check if the required module is among the listed files and ensure the import statement is correctly formatted according to the project's directory structure.
9. Code Detail Elaboration: Write out all the code details explicitly. Do not leave any "TODO" placeholders as they may lead to incomplete or incorrect code implementation.
10. Do Not have any Explanation.
11. Backend Import Convention: When writing backend code, all backend - related imports and file references should start with the provided backend root directory {backend_root}. For example, in Python: from {backend_root} import xx; in Java: import {backend_root}.xx;; in Node.js: const xx = require('{backend_root}/xx');. Ensure the backend entry point is correctly configured.
12. Frontend Import Convention: Given the frontend root path as {frontend_root}, all frontend - related imports and file references in the frontend code must be constructed as relative paths. The relative paths should be calculated based on the location of the current file within the {frontend_root} directory structure. For example, in JavaScript, if you are in a file at {frontend_root}/src/utils.js and want to import a file in the same directory, use `import someFunction from './helpers.js';`. In a Vue project, if you are in {frontend_root}/src/views/Home.vue and want to import a component at {frontend_root}/src/components/Button.vue, use `import Button from '../components/Button.vue';`. This approach ensures that the code remains portable across different deployment scenarios and makes it easier to understand the file - to - file dependencies.
13. Environment Dependency Management: All projects must adhere to the environment dependency rules based on the ## PACKAGES LIMIT references (e.g., package.json for Node.js projects or requirements.txt for Python projects).
14. Retrieve database configuration from environment variables:
        mysql_host: Use os.getenv('mysql_host', 'localhost')
        mysql_port: Use int(os.getenv('mysql_port', 3306))
        mysql_database: Use os.getenv('mysql_database', 'default_db')
        mysql_user: Use os.getenv('mysql_user', 'root')
        mysql_password: Use os.getenv('mysql_password', '123456')
15. Interface Mounting and Route Prefix Constraints: 
    - Mounting Order: In the backend entry file (e.g., main.py), always mount backend interfaces first. Organize the mounting sequence to ensure a clear and logical flow of API endpoints.
    - Prefix Consistency and API Compliance:
        All route prefixes and URL structures must strictly adhere to the specifications defined in api_desc. This includes both the global prefixes set in the main entry file (e.g., app.include_router(router, prefix="/api")) and the local prefixes within individual routers (e.g., APIRouter(prefix="/subpath")). Avoid creating nested or redundant prefixes (e.g., /api/api/xxx) that deviate from the API spec.
        When combining route definitions across different files, ensure that the concatenated URL (e.g., global prefix + router prefix + route path) matches the api_desc exactly. For example, if a main router sets a prefix /api and a sub-router defines /resource, the final URL /api/resource must align with the API documentation. Regularly cross-check all route configurations against api_desc to prevent integration issues and ensure seamless communication between frontend and backend components.
    - Frontend: In vite.config.ts, if server URL has a prefix (e.g., /api), frontend requests use relative paths (e.g., /xx/xx). If requests use full paths (e.g., /api/xx/xx), set baseURL to /. Ensure consistent prefix usage to avoid access issues and meet project design.
16. Ensure all route dependencies and response models use Pydantic-serializable types, avoiding direct injection of non-model classes like database connections.
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
17. Database Operations: Use SQLAlchemy (or a suitable alternative) for database connection management. Configure the engine with standard pooling and logging options based on environment variables. For example, set connection - checking, recycling, pool sizing, and overflow limits. Enable SQL logging (echo) based on the DEBUG environment variable.
    - Model Definition with Declarative Base: When employing SQLAlchemy, define database models using the declarative base approach. This provides a structured and Pythonic way to represent database tables and their relationships.
    - Table Existence Check and Creation: Prior to executing any database operations, thoroughly verify if the necessary tables exist. In the event that a table is missing, automatically create it according to the defined models. Alongside table creation, insert default data into the newly created table during the initialization phase. This ensures that the database is in a ready state with pre-populated relevant data.
    - Field Integrity Assurance: Guarantee that all fields in the database tables are defined accurately in accordance with the design requirements. This includes setting the correct data types, lengths, and constraints for each field to maintain data integrity and consistency.
18. Front-End Integration:
    - API and Data Sync: Ensure front-end code (HTML, JavaScript etc.) precisely matches backend API endpoints and data structures. Correctly handle API requests, methods, and received data according to the defined structures.
    - View Accuracy: Implement front-end views that display data accurately in the right format. Interactive components should function as expected, gracefully handling errors, loading, and empty states with appropriate feedback.
    - Responsive Layout: Create responsive views adapting well to various screen sizes and devices, maintaining consistent and user-friendly layouts.
    - UX Enhancement: Prioritize user experience with intuitive navigation, clear visual hierarchy, and easy-to-use interfaces for efficient task execution.
19. Vite-Specific Path Configuration in Frontend: In the vite.config.ts file within the frontend project (assuming the frontend root path is {frontend_root}), all file references must be set as relative paths. First, set root: path.resolve(__dirname) to establish the base directory for Vite's build process. Then, when configuring path aliases or other path - related settings, calculate the paths relative to the {frontend_root} directory.
    - For example, to set an alias for the components directory:
    ```
    {example_code}

               """

BUGFIX_FRONTEND_TEMPLATE = """
NOTICE  
Role: You are a professional front-end engineer responsible for fixing UI/interaction defects. The core objective is to ensure that the functionality complies with the design specifications and there are no runtime errors. 
Language: Write the main text in the user's language, while keeping the code titles and code blocks in English.

# Context  
## Product Documentation  
{product_documentation}  

## Design  
{design}  

## Task  
{task}  

## API Compliance Notice
{api_desc}

## Error Message  
```text  
{error_message}  
```
## Dependency Code
{dependency_code}  

## Legacy Code
{legacy_code}  


# Format Example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: : Based on the context including the legacy code, its dependency code, and the error messages, modification_suggestions, follow the "Format example" to write or rewrite the code for bug fix.
1. Single File Concentration: 仅修改 {filename} 文件，禁止跨文件重构。
2. Frontend Import Convention:
    - All imports should be relative paths based on {frontend_root}.
    - Example: import Button from '../components/Button.vue'
3. Build Tool Compliance:
    - Adhere to the path rules in vite.config.ts or webpack.config.js.
    - API request paths must match the baseURL setting (refer to 'API Compliance Notice').
4. View Consistency:
    - Data binding should strictly correspond to the API response structure.
    - Display friendly prompts for error states (loading/error/empty states).
5. Responsive Design:
    - Must be adapted to mobile breakpoints (min-width: 768px / max-width: 1024px).
    - Use Flex/Grid layout to ensure container adaptability.
6. Accessibility: Add necessary ARIA attributes (role, label, status).
7. CSS Scope: Component styles must be isolated using the scoped or CSS-in-JS approach.
8. State Management:
    - Update states through the project-specified solution (Vuex/Pinia/React Context).
    - Add debounce/throttle protection for asynchronous operations.
9. Test Coverage: If there are unit test files, update the relevant assertions synchronously.
10. Environment Dependency: Follow the dependency versions declared in package.json.
11. Vite Path Configuration:
    - Set root: path.resolve(__dirname) in vite.config.ts.
    - Calculate path aliases based on the {frontend_root} directory.
12. DONOT EXPLAIN AYNTHING.
13. Interface Mounting and Route Prefix Constraints:
    - Prefix Consistency Rule
    Global request prefixes (e.g., baseURL in axios) must align with the API spec’s base path (e.g., /api).
    Never repeat the global prefix in specific request paths (e.g., use /inventory/items instead of /api/inventory/items if baseURL is /api).
    - Configuration Guidelines
    Centralized Prefix Setup: Define the global request prefix once in a shared config file (e.g., axios instance) to avoid conflicts.
    Path Clarity: Write specific request paths (e.g., in service files) as relative to the global prefix, using only the endpoint’s module/resource path (e.g., /users for an API endpoint at /api/users).
    - Validation Steps
    Path Concatenation Check: Ensure Global Prefix + Specific Path matches the API spec exactly (e.g., /api + /users = /api/users).
    Cross-Reference: Verify all requests against the API doc to catch unintended prefix duplication (e.g., check for /api in both config and request path).
    - Prohibited Patterns
    Avoid nested prefixes like /api/api/xxx—they break API compliance.
    Keep prefixes consistent across environments (dev/prod) to prevent routing errors.

"""


BUGFIX_BACKEND_TEMPLATE = """

NOTICE  
Role: You are a professional backend engineer responsible for fixing defects in the service layer/data layer. The core objective is to ensure the reliability of the interfaces and the stability of the system.
Language: Write the main text in the user's language, while keeping the code titles and code blocks in English.

# Context  
## Product Documentation  
{product_documentation}  

## Design  
{design}  

## Task  
{task}  

## API Compliance Notice
{api_desc}

## Error Message  
```text  
{error_message}  
```

## Dependency Code
{dependency_code}  

## Legacy Code
{legacy_code}  

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
        - Define database models using SQLAlchemy's declarative base, ensuring field integrity:
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

# Instruction: Based on the context including the legacy code, its dependency code, and the error messages, modification_suggestions, follow the "Format example" to write or rewrite the code for bug fix.
## Write/Rewrite Code: Only focus on one file {filename}, write or rewrite the complete code using triple quotes by taking the following points and the context into consideration:
1. Single File Focus: Only modify the specified {filename} file. Avoid module - level refactoring.
2. Import Convention: All imports should start with the backend root directory {backend_root}.
    - Example: from {backend_root}.utils import helper_function
3. Database Configuration:
    - Get database connection parameters using os.getenv (mysql_host, mysql_port, mysql_database, mysql_user, mysql_password).
    - ORM models should inherit from the SQLAlchemy declarative base.
4. API Compliance:
    - Use Pydantic models for request and response data.
    - Route prefixes must strictly follow the 'API Compliance Notice' to avoid redundant nesting.
5. Error Handling:
    - Raise FastAPI HTTPException with trace_id in logs.
6. Transaction Safety:
    - Explicitly commit write operations and handle rollbacks.
    - Set pool_pre_ping=True for connection pool timeout.
7. Security Requirements:
    - Validate the length and type of input parameters (using Pydantic validator).
    - Sanitize file upload paths.
8. Environment Variables: Default values are allowed in development, but in production, required=True must be marked.
9. Route Mounting Constraints:
    - Mount interfaces first in the backend entry file with a clear logical order.
    - Ensure the final URL structure matches 'API Compliance Notice' exactly.
    - Route prefixes must strictly match 'API Compliance Notice' to avoid redundant nesting (e.g., /api/api/xxx).
    - All route prefixes and URL structures must strictly adhere to the specifications defined in 'API Compliance Notice' This includes both the global prefixes set in the main entry file (e.g., app.include_router(router, prefix="/api")) and the local prefixes within individual routers (e.g., APIRouter(prefix="/subpath")). Avoid creating nested or redundant prefixes (e.g., /api/api/xxx) that deviate from the API spec.
        When combining route definitions across different files, ensure that the concatenated URL (e.g., global prefix + router prefix + route path) matches the 'API Compliance Notice' exactly. For example, if a main router sets a prefix /api and a sub-router defines /resource, the final URL /api/resource must align with the API documentation. Regularly cross-check all route configurations against 'API Compliance Notice' to prevent integration issues and ensure seamless communication between frontend and backend components.
10. DONOT EXPLAIN AYNTHING.
        """





class FixBug(Action):
    """Fix bug action without any implementation details"""

    name: str = "FixBug"
    i_context: Document = Field(default_factory=Document)
    desc: str = (
        "Based on console error messages, analyze root causes and design bug - fixing for error - prone files. "
        "Present solutions clearly and in detail."
    )

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code(self, prompt) -> str:
        code_rsp = await self._aask(prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return code
    
    async def run(self, *args, **kwargs) -> CodingContext:

        coding_context = CodingContext.loads(self.i_context.content)
        filename = coding_context.filename
        design_doc = coding_context.design_doc
        task_doc = coding_context.task_doc
        bugfix_doc = coding_context.bugfix_doc
        file_list = coding_context.file_list
        fix_file_desc=coding_context.fix_file_desc
        bugfile_list = coding_context.bugfile_list
        product_documentation= json_to_markdown(json.loads(coding_context.prd_doc.content), depth=3)
        error_message, bugfix_plan = await self.get_values_from_json(bugfix_doc.content, [ERROR_MESSAGE, BUG_FIX_PLAN], ["", ""])
        backend_files, front_files = await self.get_values_from_json(task_doc.content, [BACKEND_FILES, FRONTEND_FILES], [[], []])
        backend_root = await self.find_root(backend_files)
        front_root = await self.find_root(front_files)
        api_desc = get_values(task_doc.content, FULL_API_SPEC)
        dependency_code = await self.get_dependency_error_codes(current_filename=filename, bugfile_list=bugfile_list, project_repo=self.repo)
        code_type = ""
        file_ext = filename.split(".")[-1]
        if filename in backend_files or file_ext in ["py", "txt"]:
            code_type = "backend"
        elif filename in front_files or file_ext in ["json", "vue", "js", "ts", "less", "html"]:
            code_type = "frontend"

        if code_type == "frontend":
            prompt = BUGFIX_FRONTEND_TEMPLATE.format(
                product_documentation=product_documentation,
                design = await self.parse_design(design_doc.content),
                task = await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                error_message=error_message,
                dependency_code=dependency_code,
                legacy_code=await self.get_legacy_code(filename=filename),
                filename=filename,
                frontend_root=front_root,
                api_desc=api_desc

            )
        elif code_type == "backend":
            prompt = BUGFIX_BACKEND_TEMPLATE.format(
                product_documentation=product_documentation,
                design = await self.parse_design(design_doc.content),
                task = await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                error_message=error_message,
                dependency_code=dependency_code,
                legacy_code=await self.get_legacy_code(filename=filename),
                filename=filename,
                backend_root=backend_root,
                api_desc=api_desc,
                database_settings_code=database_settings_code,
                database_connect_code=database_connect_code,
                database_model_code=database_model_code,
            )
        else:
            prompt = BUG_FIX_REFINED_TEMPLATE.format(
                design = await self.parse_design(design_doc.content),
                product_documentation=coding_context.prd_doc.content,
                task = await self.parse_task(coding_context.task_doc.content, code_type=code_type),
                error_message=error_message,
                # bug_feedback=console_output,
                dependency_code=dependency_code,
                legacy_code=await self.get_legacy_code(filename=filename),
                # modification_suggestions=suggestion,
                file_list=file_list,
                filename=filename,
                backend_root=backend_root,
                frontend_root=front_root,
                bugfix_plan=bugfix_plan,
                bugfile_list=bugfile_list,
                fix_file_desc=await self.get_bugfix_desc(file_name=filename, file_list=file_list, file_desc=fix_file_desc),
                api_desc=api_desc,
                example_code=vite_example_code,
                # database_example_code=database_example_code,
                # eslintrc_code=eslintrc_code
                )
        logger.info(f"Bug fixing {coding_context.filename}..")
        self.config.current_role = f"ENGINEER"
        self.config.role_task = f"2/3 Fix bug"

        oh_action_data = {}
        content_info = {
            "sub_content": f"Bug fixing {coding_context.filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")


        code = await self.write_code(prompt)
        if not coding_context.code_doc:
            # avoid root_path pydantic ValidationError if use WriteCode alone
            root_path = self.context.src_workspace if self.context.src_workspace else ""
            coding_context.code_doc = Document(filename=coding_context.filename, root_path=str(root_path))
        
        if coding_context.filename == "system_test_playwright_code.py":
            root_path = self.repo.tests.workdir
            coding_context.code_doc = Document(filename=coding_context.filename, root_path=str(root_path))
            logger.info(f"Writing system_test_playwright_code.py to {root_path}..")

        coding_context.code_doc.content = code
        return coding_context


    async def get_json_value(self, json_str, key_desc, return_des = ""):
        data = json.loads(json_str)
        return data.get(key_desc.key, return_des)


    async def get_values_from_json(self, json_str, keys: list, default_return: list):
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            print("JSON 解析出错，请检查输入的 JSON 字符串是否正确。")
            return default_return

        result = []
        for i, key_desc in enumerate(keys):
            # 获取对应索引的默认值
            current_default = default_return[i] if i < len(default_return) else None
            result.append(data.get(key_desc.key, current_default))
        return result
    
    async def get_legacy_code(self, filename):
        codes = []
        src_file_repo = self.repo.srcs
        code_str = ""
        code= await src_file_repo.get(filename=filename)
        if code:
            code_str = code.content
        codes.append(f"\n{filename}\n```code\n{code_str}```")
        return "\n".join(codes)
    

    async def get_dependency_codes(self, file_relation: list, current_filename: str, project_repo: ProjectRepo) -> str:

        file_relation_dict = {item[0]: item[1] for item in file_relation}
        code_filenames= file_relation_dict.get(current_filename, [])
        logger.info(f"Fix bug--> current file :{current_filename} is dependency file :{str(code_filenames)}")
        codes = []
        src_file_repo = project_repo.srcs

        
        for filename in code_filenames:
            # Exclude the current file to get the code snippets for generating the current file
            if filename == current_filename:
                continue
            doc = await src_file_repo.get(filename=filename)
            if not doc:
                continue
            codes.append(f"\n{filename}\n```code\n{doc.content}```")
        return "\n".join(codes)

    async def get_dependency_error_codes(self, current_filename, bugfile_list, project_repo):
        src_file_repo = project_repo.srcs
        codes = []
        for filename, desc in bugfile_list:
            # Exclude the current file to get the code snippets for generating the current file
            if filename == current_filename:
                continue
            doc = await src_file_repo.get(filename=filename)
            if not doc:
                continue
            codes.append(f"\n{filename}\n```code\n{doc.content}```")
        return "\n".join(codes)


    @staticmethod
    async def parse_design(design_doc):
        if not design_doc:
            return ""
        m = json.loads(design_doc)
        # implementation_desc = "### ARCHITECTURAL_OVERVIEW\n " + m.get(ARCHITECTURAL_OVERVIEW.key, "").strip() + "\n"
        # system_desc = "### SYSTEM_COMPONENTS\n " + m.get(SYSTEM_COMPONENTS.key, "").strip() + "\n"
        data_structures_and_interfaces_des = "### DATA_STRUCTURES_AND_INTERFACES\n " + m.get(DATA_STRUCTURES_AND_INTERFACES.key, "").strip() + "\n"
        program_call_flow_desc = "### PROGRAM_CALL_FLOW\n " + m.get(PROGRAM_CALL_FLOW.key, "").strip() + "\n"
        # database_setting =  "### DATABASE SETTING\n" + m.get(DTATBASE_SETTINGS.key, "")
        return data_structures_and_interfaces_des + program_call_flow_desc

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
    

    async def get_bugfix_desc(self, file_name, file_list, file_desc):
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