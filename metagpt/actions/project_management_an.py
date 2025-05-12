#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/12/14 15:28
@Author  : alexanderwu
@File    : project_management_an.py
"""
from typing import List, Optional, Tuple

from metagpt.actions.action_node import ActionNode

REQUIRED_PACKAGES = ActionNode(
    key="Required packages",
    expected_type=Optional[List[str]],
    instruction="Provide required third-party packages in requirements.txt format.",
    example=["flask==1.1.2", "bcrypt==3.2.0"],
)

REQUIRED_OTHER_LANGUAGE_PACKAGES = ActionNode(
    key="Required Other language third-party packages",
    expected_type=List,
    instruction="Provide a comprehensive list of dependency management configurations for multi-language projects, like package.json for node.js, and write configurations file."
                "Which can based on Project Settings.",
    example=[
                {
                    "dependencies": {
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0",
                    "react-router-dom": "^6.14.2"
                    },
                    "devDependencies": {
                    "vite": "^4.3.9",
                    "@types/react": "^18.2.15"
                    }
                }
    ],
)

LOGIC_ANALYSIS = ActionNode(
    key="Logic Analysis",
    expected_type=List[List[str]],
    instruction="Based on the provided 'Project File Structure', Provide a list of each files with the classes/methods/functions to be implemented, "
    "including dependency analysis and imports."
    "Ensure the list of files matches the 'Project File Structure' files.",
    example=[
        ["game.py", "Contains Game class and ... functions"],
        ["main.py", "Contains main function, from game import Game"],
    ],
)

BACKEND_FILES = ActionNode(
    key="Backend Files",
    expected_type=list,
    instruction="Based on the provided 'Project File Structure', identify all the files related to the backend. "
                "The backend files are typically identified by their file extensions (e.g., .py, .java, .php) "
                "or their functionality within the project. The result should be a list containing the paths of "
                "all backend - related files.",
    example=["src/api/routes.py", "app/controllers/user_controller.java", "server.php"]
)


FRONTEND_FILES = ActionNode(
    key="Frontend Files",
    expected_type=list,
    instruction="Based on the provided 'Project File Structure', identify all the files related to the frontend. "
                "The frontend files are usually recognized by their file extensions (e.g., .html, .js, .css) "
                "or their role in presenting the user interface. The result should be a list containing the paths of "
                "all frontend - related files.",
    example=["public/index.html", "src/components/header.js", "styles/main.css", "static/css/styles.css"]
)


REFINED_LOGIC_ANALYSIS = ActionNode(
    key="Refined Logic Analysis",
    expected_type=List[List[str]],
    instruction="Review and refine the logic analysis by merging the Legacy Content and Incremental Content. "
    "Provide a comprehensive list of files with classes/methods/functions to be implemented or modified incrementally. "
    "Include dependency analysis, consider potential impacts on existing code, and document necessary imports."
    "Make sure: "
                "1.Enforces explicit interface definitions between callers/callees, "
                "2.Adds validation mechanisms for interface compliance."
                "3.Requires dependency tracking at function/method level."
                "4.Mandates structural separation of interface vs implementation"
                "5.Provides verification artifacts for technical review",
    example=[
        ["game.py", "Contains Game class and ... functions"],
        ["main.py", "Contains main function, from game import Game"],
        ["new_feature.py", "Introduces NewFeature class and related functions"],
        ["utils.py", "Modifies existing utility functions to support incremental changes"],
    ],
)

TASK_LIST = ActionNode(
    key="Task List",
    expected_type=List[str],
    instruction="Break down the tasks into a list of filenames, prioritized by dependency order. "
                "Prioritize frontend files (HTML, CSS, JavaScript) first, followed by backend files (Python, API, database). "
                "Ensure the list of files matches the 'Project File Structure' files.",
    example=["index.html", "styles.css", "script.js", "main.py", "api.py"],
)

FILE_RELATION = ActionNode(
    key="File Dependency Mapper",
    expected_type=List[Tuple[str, List[str]]],
    instruction="""Generate complete dependency graph following these rules:
                1. ​**Full Project Coverage**:
                - Process ALL files from Project File Structure
                - Include both backend and frontend files
                - Never omit any project files (except third-party)

                2. ​**Architecture Rules**:
                - Backend: 
                    ```
                    configs/ → models/ → schemas/ → services/ → apis/ → main.py
                    ```
                - Frontend:
                    ```
                    stores/ → composables/ → components/ → views/ → App.vue
                    ```
                - Config files (main.py, vite.config.ts) depend on everything else

                3. ​**Dependency Logic**:
                - Each file must declare ALL its internal dependencies
                - Config files automatically depend on all module entry points
                - `__init__.py`/`index.ts` depends on sibling files

                4. ​**Validation**:
                - No circular dependencies
                - No missing files from project structure
                - Config files must be last in order"

                DO NOT modify the file names.
            """,
    example=[
        ("backend/app/config.py", []),
        ("backend/app/models/base.py", ["config.py"]),
        ("backend/app/services/core.py", ["models/base.py"]),
        ("backend/app/api/main.py", ["services/core.py"]),
        ("frontend/src/stores/core.ts", []),
        ("frontend/src/App.vue", ["stores/core.ts"]),
        ("backend/main.py", ["app/api/main.py"]),
        ("frontend/vite.config.ts", ["src/main.ts"])
    ]
)
REFINED_TASK_LIST = ActionNode(
    key="Refined Task list",
    expected_type=List[str],
    instruction="Review and refine the combined task list after the merger of Legacy Content and Incremental Content, "
    "and consistent with Refined File List. Ensure that tasks are organized in a logical and prioritized order, "
    "considering dependencies for a streamlined and efficient development process. ",
    example=["new_feature.py", "utils", "game.py", "main.py"],
)

FULL_API_SPEC = ActionNode(
    key="Full API spec",
    expected_type=str,
    instruction="Based on the 'Data structures and interfaces' and 'Program call flow' sections, create an OpenAPI 3.0 spec for all APIs used by both frontend and backend. " \
    "If there's no frontend-to-backend communication, leave it blank. Define endpoints, HTTP methods, and request/response models accordingly. Group related endpoints with tags.",
    example="""
openapi: 3.0.0
info:
  title: Simple API
  version: 1.0.0
paths:
  /api/data:
    get:
      summary: Fetch data
      tags:
        - Data Retrieval
      responses:
        '200':
          description: Data fetched successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: array
    post:
      summary: Add new data
      tags:
        - Data Manipulation
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                new_data:
                  type: string
      responses:
        '201':
          description: Data added successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
  /api/items:
    delete:
      summary: Delete an item
      tags:
        - Item Management
      parameters:
        - name: item_id
          in: query
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: Item deleted successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
"""
)

SHARED_KNOWLEDGE = ActionNode(
    key="Shared Knowledge",
    expected_type=str,
    instruction="Detail any shared knowledge, like common utility functions or configuration variables.",
    example="`game.py` contains functions shared across the project.",
)

REFINED_SHARED_KNOWLEDGE = ActionNode(
    key="Refined Shared Knowledge",
    expected_type=str,
    instruction="Update and expand shared knowledge to reflect any new elements introduced. This includes common "
    "utility functions, configuration variables for team collaboration. Retain content that is not related to "
    "incremental development but important for consistency and clarity.",
    example="`new_module.py` enhances shared utility functions for improved code reusability and collaboration.",
)


ANYTHING_UNCLEAR_PM = ActionNode(
    key="Anything UNCLEAR",
    expected_type=str,
    instruction="Mention any unclear aspects in the project management context and try to clarify them.",
    example="Clarification needed on how to start and initialize third-party libraries.",
)

NODES = [
    REQUIRED_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    # LOGIC_ANALYSIS,
    # TASK_LIST,
    FILE_RELATION,
    FULL_API_SPEC,
    SHARED_KNOWLEDGE,
    BACKEND_FILES,
    FRONTEND_FILES,
    ANYTHING_UNCLEAR_PM,
]

REFINED_NODES = [
    REQUIRED_PACKAGES,
    REQUIRED_OTHER_LANGUAGE_PACKAGES,
    REFINED_LOGIC_ANALYSIS,
    REFINED_TASK_LIST,
    FULL_API_SPEC,
    REFINED_SHARED_KNOWLEDGE,
    ANYTHING_UNCLEAR_PM,
]

PM_NODE = ActionNode.from_children("PM_NODE", NODES)
REFINED_PM_NODE = ActionNode.from_children("REFINED_PM_NODE", REFINED_NODES)
