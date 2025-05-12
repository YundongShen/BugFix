from typing import List, Optional, Tuple
from metagpt.actions.action_node import ActionNode

LAUNCH_RESULT = ActionNode(
    key="Launch Result",
    expected_type=str,
    instruction="Determine if the project launched successfully. If successful, say 'SUCCESS'; if failed, say 'FAILED'.",
    example="SUCCESS",
)

DATABASE_ERROR_RESULT = ActionNode(
    key="Database Error Result",
    expected_type=str,
    instruction="Determine if there are database-related errors. If no errors, say 'NOERR'; if errors, say 'ERR'.",
    example="NOERR",
)

ERROR_MESSAGE = ActionNode(
    key="Error Message",
    expected_type=str,
    instruction="Extract the error message from the console output.",
    example="ModuleNotFoundError: No module named 'flask'",
)

SUGGESTION = ActionNode(
    key="Suggestion",
    expected_type=str,
    instruction="Provide a suggestion to fix the error based on the error message.",
    example="Install the missing package using: pip install flask",
)


ERROR_PRONE_FILES = ActionNode(
    key="Error-Prone Files",
    expected_type=List[List[str]],
    instruction="""
        Analyze the 'Error Message' to identify relevant files using these rules:
        1. Direct Error Files: If the error mentions specific filenames (e.g., `TagManagement.vue` for frontend or `main.py` for backend), add them to the list.
        2. Frontend Dependency Issues:
            - When a frontend error indicates a missing dependency (e.g., `axios`), check for relevant dependency config files in the file list, such as `package.json`, `package-lock.json`, `yarn.lock`. Include these files in the list if they exist.
        3. Backend Dependency and Import Issues:
            - Missing Dependency Errors: When the backend error indicates a missing dependency (e.g., "No module named 'greenlet'"), check for relevant dependency config files in the file list. Files like `requirements.txt`, `pyproject.toml`, or `setup.py` should be added to the list if they exist. 
            - Import-Related Errors: If the error is about an import problem (e.g., circular imports, incorrect import paths), add the files involved in the import statements to the list.
        4. Build/Config Files: If the error suggests build or config issues (e.g., related to webpack or vite), add relevant config files (e.g., `vite.config.ts`, `webpack.config.js`) to the list.
        For each file path, provide a brief plan to check and potentially fix the issues based on the error message. If no relevant files are found, return an empty list.
    """,
    example=[
        ["frontend/src/views/TaskList.vue", "Check for incorrect component imports and fix if necessary"],
        ["package.json", "Verify the version and presence of the required frontend dependencies"],
        ["backend/requirements.txt", "Check for the correct version and installation of the missing backend dependency"],
        ["backend/app/core/utils.py", "Review import statements and correct any circular or incorrect imports"]
    ]
)

BUG_FIX_PLAN = ActionNode(
    key="Bugfix Plan",
    expected_type=str,
    instruction="Develop a comprehensive and step-by-step incremental bugfix plan, focusing only on error issues and ignoring warning messages. " \
    "Provide the detailed changes to be implemented at each step based on the bug information changes to be implemented at each step based on the bug information",
    example="Update the requirements.txt for the missing packages, ..."
        "Fix the syntax error in the code, ..."
        "Update the code to incorporate the latest API changes, ..."
        "Fix the bug that causes the program to crash, ..."
        "Add import statements to the code for missing modules, ..."
        "Fix the mismatch between the expected input and output, ..."
        "Fix the mismatched data types, ..."
        "Fix the incorrect calculation logic, ..."
        "Fix the mismatch between frontend and backend data, ..."
        "Add comments to the code to explain the logic, ..."
        "Update the playwright test code to align with PRD requirements and front end html,js files"
        "If the playwright tese code is correctly aligned with PRD requirements and html,js files, updated the code to fix the bug reported by the playwright test code, pass the testing in the playwright test code",
)

CONSOLE_OUTPUT = ActionNode(
    key="Console Output",
    expected_type=str,
    instruction="The raw console output from the project launch.",
    example="INFO:uvicorn.error:Finished server process",
)

REQUIRES_FILES = ActionNode(
    key="Requires Files",
    expected_type=List[List[str]],
    instruction="Based on the 'Error Message' and 'Bugfix Plan', determine if new files need to be created. If so, list the relative file paths to be created, ensuring each path has a valid file extension (e.g.,.py,.js,.vue). "
                "For each file path, provide a brief plan for what the file will contribute to the bug - fixing process, such as implementing a new validation function or creating a component to handle a specific error case. "
                "If no new files are required, return an empty list.",
    example=[
        ["frontend/src/components/NewErrorHandler.vue", "Create a Vue component to handle errors thrown during form submissions"],
        ["backend/app/core/validation_utils.py", "Implement utility functions for input validation to fix data - related errors"]
    ]
)

NODES = [
    LAUNCH_RESULT, 
    ERROR_MESSAGE, 
    BUG_FIX_PLAN
    ]

BUG_NODES = [
    # SUGGESTION,
    ERROR_PRONE_FILES,
    REQUIRES_FILES,
]

LAUNCH_TEST_NODE = ActionNode.from_children("LAUNCH_TEST_NODE", NODES)
BUGFIX_NODE= ActionNode.from_children("BUGFIX_NODE", BUG_NODES)

