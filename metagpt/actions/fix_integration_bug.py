from typing import Optional, List
from tenacity import retry, stop_after_attempt, wait_random_exponential
import json
from pydantic import Field
from metagpt.logs import logger
from metagpt.actions import Action
from metagpt.utils.common import CodeParser
from metagpt.schema import CodingContext, Document, RunCodeResult
from metagpt.utils.project_setting import get_project_setting, merge_json_string
from metagpt.actions.launch_project_test_an import SUGGESTION, CONSOLE_OUTPUT, ERROR_MESSAGE, REQUIRES_FILES, ERROR_PRONE_FILES, BUG_FIX_PLAN
from metagpt.actions.design_api_an import PROGRAM_CALL_FLOW, PROJECT_SETTINGS, DATA_STRUCTURES_AND_INTERFACES, ARCHITECTURAL_OVERVIEW, SYSTEM_COMPONENTS
from metagpt.actions.project_management_an import FILE_RELATION, REQUIRED_PACKAGES, REQUIRED_OTHER_LANGUAGE_PACKAGES, LOGIC_ANALYSIS, SHARED_KNOWLEDGE, FULL_API_SPEC, TASK_LIST, BACKEND_FILES,FRONTEND_FILES
from metagpt.utils.project_repo import ProjectRepo
from metagpt.utils.action_utils import get_values

# ## Dependency Code
# ```Code
# {dependency_code}
# ```
BUG_FIX_REFINED_TEMPLATE = """
NOTICE
Role: You are a professional full - stack engineer responsible for fixing bugs in a web application. Your core task is to ensure that the updated code resolves the identified bugs in the frontend, backend, and Playwright test code, enabling the tests to run successfully.

# Key Information

## Product Documentation
For a comprehensive understanding of the project's overall functions, features, and constraints, the product documentation provides essential information:
{product_documentation}


## Dependency Code
This field lists files related to the current one. When fixing issues in the current file, refer to these related files, especially for reference relationships and interfaces. Incorrect references or interface issues between them are common problem sources.
The relevant files are:
{dependency_code}


## Code of the Problematic File
This field displays the original code of the file needing modification. If console output logs confirm no issues with this code, you may skip modifying it. However, always cross-check with Dependency Code (related files) for hidden relational issues or interface mismatches, even when the current file appears problem-free.
```Code
{error_code}
```

## API Compliance Notice
{api_desc}
Both the frontend and backend components of the project are required to strictly comply with the above Full API spec when making requests. This is crucial for maintaining consistent communication and ensuring the stable operation of the entire system.


# Supplementary Information

## Console Output logs
```text
{console_output}
```
## Fix File description
{fix_file_desc}

## File List
Your project may have a directory structure similar to the following:
{file_list}

## Fixing Suggestions
```text
{bugfix_plan}
```

# Instruction: Fix the bug in the specified file {filename} by following these guidelines:
1. Exclusive File Focus: Solely modify or rewrite {filename}. Do not make any changes to other files.
2. Code Completeness: Ensure the code is complete, reliable, and reusable within the project.
3. Bug Fixing Priority: Only address the bug; avoid adding new features.
4. Default Values and Typing: Use default values and strong typing; avoid circular imports.
5. Design Adherence: Follow the existing design and avoid modifying public interfaces.
6. Code Review and Modification: Carefully review the error code and its dependencies; ensure the fix maintains system integrity.
7. Function and Class Check: Ensure all necessary functions and classes in {filename} are implemented.
8. Import Management: Correctly import external modules in {filename} to avoid runtime errors. If you encounter an import - related error (e.g., ModuleNotFoundError), refer to the provided file list. Check if the required module is among the listed files and ensure the import statement is correctly formatted according to the project's directory structure.
9. Code Detail Elaboration: Write explicit code details in {filename}; avoid placeholders like "TODO".
10. Playwright Best Practices:
    - In {filename} (if it's a Playwright - related file), use appropriate selectors (e.g., `input[name=username]` instead of `input#username`).
    - Add explicit waits (e.g., `page.wait_for_selector`) for dynamic content in {filename} (if applicable).
    - Capture console logs and network requests in {filename} (if relevant) for debugging.
    - Use assertions (`expect`) to verify test results in {filename} (if it contains test code).
11. Error Handling: Add error handling for unexpected scenarios (e.g., element not found, network errors) in {filename}.
12. Dynamic URL Handling: In {filename}, avoid hardcoding URLs; use environment variables or configuration files.
13. Frontend - Backend Integration: If {filename} is related to frontend - backend interaction, ensure proper integration; verify backend responses in Playwright tests (if relevant to {filename}).
14. Do Not have any Explanation.
15.Backend Entry Point Constraint: When writing backend code, all backend-related imports and file references should start with the provided backend root directory {backend_root}. Ensure that the backend entry point is correctly configured and all subsequent backend code adheres to this root directory structure.
16.Frontend Entry Point Constraint: When writing frontend code, all frontend-related imports and file references should start with the provided frontend root directory {front_root}. Ensure that the frontend entry point is correctly configured and all subsequent frontend code adheres to this root directory structure.
17. Interface Mounting and Route Prefix Constraints: 
    - Mounting Order: In the backend entry file (e.g., main.py), always mount backend interfaces first. Organize the mounting sequence to ensure a clear and logical flow of API endpoints.
    - Prefix Consistency and API Compliance:
        All route prefixes and URL structures must strictly adhere to the specifications defined in 'API Compliance Notice'. This includes both the global prefixes set in the main entry file (e.g., app.include_router(router, prefix="/api")) and the local prefixes within individual routers (e.g., APIRouter(prefix="/subpath")). Avoid creating nested or redundant prefixes (e.g., /api/api/xxx) that deviate from the API spec.
        When combining route definitions across different files, ensure that the concatenated URL (e.g., global prefix + router prefix + route path) matches the 'API Compliance Notice' exactly. For example, if a main router sets a prefix /api and a sub-router defines /resource, the final URL /api/resource must align with the API documentation. Regularly cross-check all route configurations against 'API Compliance Notice' to prevent integration issues and ensure seamless communication between frontend and backend components.
    - For Frontend:     
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
Please provide only the fixed code for {filename} in the following format:
18. Retrieve database configuration from environment variables:
        mysql_host: Use os.getenv('mysql_host', 'localhost')
        mysql_port: Use int(os.getenv('mysql_port', 3306))
        mysql_database: Use os.getenv('mysql_database', 'default_db')
        mysql_user: Use os.getenv('mysql_user', 'root')
        mysql_password: Use os.getenv('mysql_password', '123456')
19. Database Operations: Use SQLAlchemy (or a suitable alternative) for database connection management. Configure the engine with standard pooling and logging options based on environment variables. For example, set connection - checking, recycling, pool sizing, and overflow limits. Enable SQL logging (echo) based on the DEBUG environment variable.
    - Model Definition with Declarative Base: When employing SQLAlchemy, define database models using the declarative base approach. This provides a structured and Pythonic way to represent database tables and their relationships.
    - Table Existence Check and Creation: Prior to executing any database operations, thoroughly verify if the necessary tables exist. In the event that a table is missing, automatically create it according to the defined models. Alongside table creation, insert default data into the newly created table during the initialization phase. This ensures that the database is in a ready state with pre-populated relevant data.
    - Field Integrity Assurance: Guarantee that all fields in the database tables are defined accurately in accordance with the design requirements. This includes setting the correct data types, lengths, and constraints for each field to maintain data integrity and consistency.
20. Front-End Integration:
    - API and Data Sync: Ensure front-end code (HTML, JavaScript etc.) precisely matches backend API endpoints and data structures. Correctly handle API requests, methods, and received data according to the defined structures.
    - View Accuracy: Implement front-end views that display data accurately in the right format. Interactive components should function as expected, gracefully handling errors, loading, and empty states with appropriate feedback.
    - Responsive Layout: Create responsive views adapting well to various screen sizes and devices, maintaining consistent and user-friendly layouts.
    - UX Enhancement: Prioritize user experience with intuitive navigation, clear visual hierarchy, and easy-to-use interfaces for efficient task execution.   
# Format example

## Code: {filename}
```code
## {filename}
...
```

"""


class FixIntegrationBug(Action):
    """Fix bug action without any implementation details"""

    name: str = "FixIntegrationBug"
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
        bugfix_plan, error_message, console_output, error_files, require_files = await self.get_values_from_json(bugfix_doc.content, 
                                                                                                                [BUG_FIX_PLAN, ERROR_MESSAGE, CONSOLE_OUTPUT, ERROR_PRONE_FILES, REQUIRES_FILES], 
                                                                                                                ["", "", "", [], []])
        file_relation = await self.get_json_value(task_doc.content, FILE_RELATION, [])
        backend_root = await self.get_json_value(task_doc.content, BACKEND_FILES, "")
        front_root = await self.get_json_value(task_doc.content, FRONTEND_FILES, "")
        front_end_files, back_end_files, playwright_files = await self.sort_error_prone_files(file_list)
        bugfile_list = coding_context.bugfile_list
        fix_file_desc=coding_context.fix_file_desc
        design_desc = await self.parse_design(coding_context.design_doc.content)
        task_desc = await self.parse_task(coding_context.task_doc.content, self.i_context.filename)

        # if filename in require_files:
        #     file_relation.append([filename, error_files])
        # if filename in error_files:
        #     file_relation.append([filename, require_files])
        dependency_code = await self.get_dependency_error_codes(current_filename=filename, bugfile_list=bugfile_list, project_repo=self.repo)
        error_code = await self.repo.srcs.get(filename=filename)
        api_desc = get_values(task_doc.content, FULL_API_SPEC)
        prompt = BUG_FIX_REFINED_TEMPLATE.format(
            # design=design_desc,
            product_documentation=coding_context.prd_doc.content,
            # task=task_desc,
            # error_message=error_message,
            # playwright_test_code=await self.get_legacy_code(playwright_files),
            console_output=console_output,
            dependency_code=dependency_code,
            error_code=error_code,
            file_list=file_list,
            bugfix_plan=bugfix_plan,
            filename=filename,
            backend_root=backend_root,
            front_root=front_root,
            fix_file_desc=await self.get_bugfix_desc(file_name=filename, file_list=file_list, file_desc=fix_file_desc),
            api_desc=api_desc
            )  
        logger.info(f"Integration Bug fixing {coding_context.filename}..")

        self.config.current_role = f"ENGINEER"
        self.config.role_task = f"3/3 Fix integration bug"

        oh_action_data = {}
        content_info = {
            "sub_content": f"Integration Bug fixing {coding_context.filename}",
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

            oh_action_data = {}
            content_info = {
                "sub_content": f"Writing system_test_playwright_code.py to {root_path}",
                "role_task": self.config.role_task,
                "agent_role": self.config.current_role,
                "mission": self.config.user_intend
            }
            oh_action_data['action_type'] = "MESSAGE"
            oh_action_data['content'] = content_info
            oh_action_data['conversation_id'] = self.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
            #print(f"!!!!!workspace: {oh_action_data}")

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
    
    async def get_legacy_code(self, file_list):
        codes = []
        src_file_repo = self.repo.srcs
        for filename in file_list:
            code_str = await src_file_repo.get(filename=filename)
            if not code_str:
                continue
            codes.append(f"\n{filename}\n```code\n{code_str.content}```")
        return "\n".join(codes)
    

    async def get_dependency_codes(self, file_relation: list, current_filename: str, project_repo: ProjectRepo) -> str:

        file_relation_dict = {item[0]: item[1] for item in file_relation}
        code_filenames= file_relation_dict.get(current_filename, [])

        codes = []
        files = []
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
        implementation_desc = "### ARCHITECTURAL_OVERVIEW\n " + m.get(ARCHITECTURAL_OVERVIEW.key, "").strip() + "\n"
        system_desc = "### SYSTEM_COMPONENTS\n " + m.get(SYSTEM_COMPONENTS.key, "").strip() + "\n"
        data_structures_and_interfaces_des = "### DATA_STRUCTURES_AND_INTERFACES\n " + m.get(DATA_STRUCTURES_AND_INTERFACES.key, "").strip() + "\n"
        program_call_flow_desc = "### PROGRAM_CALL_FLOW\n " + m.get(PROGRAM_CALL_FLOW.key, "").strip() + "\n"
        project_settings_desc = "### PROJECT SETTINGS\n " + m.get(PROJECT_SETTINGS.key, "").strip() + "\n"
        return implementation_desc + system_desc + data_structures_and_interfaces_des + program_call_flow_desc + project_settings_desc


    async def sort_error_prone_files(self, error_prone_files: List[str]) -> List[str]:
            """
            对错误易发生文件列表进行排序，顺序为：前端相关文件、后端相关文件、Playwright 相关文件
            """
            front_end_files = []
            back_end_files = []
            playwright_files = []

            for file in error_prone_files:
                if file.endswith(('.html', '.css', '.js', '.ts', '.vue')):
                    front_end_files.append(file)
                elif file.endswith(('.py')):
                    if 'playwright' in file.lower():
                        playwright_files.append(file)
                    else:
                        back_end_files.append(file)

            # 将 main 文件移动到 back_end_files 末尾
            main_files_in_backend = [file for file in back_end_files if file.lower().endswith('main.py')]
            other_backend_files = [file for file in back_end_files if not file.lower().endswith('main.py')]
            back_end_files = other_backend_files + main_files_in_backend
        
            return front_end_files, back_end_files, playwright_files
    
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
    
    @staticmethod
    async def parse_task(task_doc, current_filename):
        if not task_doc:
            return ""
        m = json.loads(task_doc)
        packages_desc = "### PACKAGES LIMIT\n " + "\n ".join(m.get(REQUIRED_PACKAGES.key, []))+ "\n " +  ''.join([
                            f"{dep_type}:\n" +
                            ''.join([f"  {package_name}: {version}\n" for package_name, version in deps.items()]) +
                            "\n"
                            for item in m.get(REQUIRED_OTHER_LANGUAGE_PACKAGES.key, [{}])
                            for dep_type, deps in item.items()
                        ]) + "\n "
        # logic_analysis = {item[0]: item[1] for item in  m.get(LOGIC_ANALYSIS.key, [])}
        # file_logic = "### FILE LOGIC\n " + current_filename + "\n " + logic_analysis.get(current_filename,"") + "\n " if logic_analysis.get(current_filename, None) is not None else ""
        full_api_desc = "### FULL API SPEC\n " + m.get(FULL_API_SPEC.key, "") + "\n" if m.get(FULL_API_SPEC.key, "") != "" else ""
        shared_knowledge_desc = "### SHARED KNOWLEDGE\n " + m.get(SHARED_KNOWLEDGE.key, "").strip() + "\n "
        return packages_desc  + shared_knowledge_desc + full_api_desc
