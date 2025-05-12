from typing import List, Optional, Tuple
from metagpt.actions.action_node import ActionNode

INTEGRATION_RESULT = ActionNode(
    key="Integration Result",
    expected_type=str,
    instruction="Determine if the testing with the Playwright framework and backend server passed. If successful, say 'SUCCESS'; if failed, say 'FAILED'.",
    example="FAILED",
)

ERROR_MESSAGE = ActionNode(
    key="Error Message",
    expected_type=str,
    instruction="Extract the error message from the Playwright framework logs and backend server output. Ignore 'Finished server process' and 'GET /favicon.ico HTTP/1.1 404 Not Found'.",
    example="Page.fill: Timeout 30000ms exceeded.",
)

SUGGESTION = ActionNode(
    key="Suggestion",
    expected_type=str,
    instruction="Provide a suggestion to fix the error based on the error message. For example, database connection error, database schema error, wrong configurations, API interface mismatches, frontend and backend interface mismatches, etc.",
    example="Increase the timeout for the `page.fill` method to 60000ms.",
)

ERROR_PRONE_FILES = ActionNode(
    key="Error-Prone Files",
    expected_type=List[List[str]],
    instruction="List the files mentioned in the error message that are also in the provided file list."
                "Also include the files that are likely related to the startup process, "
                "such as main application entry points (e.g., main.py, app.py in Python projects) "
                "and any configuration files used during startup."
                "Not include frontend build file, like frontend/dist/index.html"
                "Once all relevant files are identified, sort the list of files based on the order in which they should be fixed. Files that need to be fixed first (as they may be dependencies for other files that need fixing) should be placed at the beginning of the list. If the fix order is not explicitly known based on the error message and dependencies, you can sort them alphabetically as a fallback." \
                "For each file path, provide a brief plan to check and potentially fix the issues based on the error message. If no relevant files are found, return an empty list.",
    example=[
        ["backend/app/core/utils.py", "Review import statements and correct any circular or incorrect imports"]
    ],
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

BUG_FIX_PLAN = ActionNode(
    key="Bugfix Plan",
    expected_type=str,
    instruction="Develop a step - by - step bugfix plan focusing on error issues while ignoring warnings. " \
    "Based on bug information, specify detailed changes for each step. " \
    "When a '405 Method Not Allowed' error occurs due to incorrect or incomplete frontend requests to the backend, check frontend build configuration files (e.g., vite.config.ts). " \
    "Look for and correct any path - mounting issues that cause duplicate API prefixes, such as changing '/api/api/x/x' to the correct '/api/x/x'.",
    example="Update requirements.txt for missing packages; " \
        "Fix syntax errors in the code; " \
        "Incorporate latest API changes; " \
        "Fix program crash bugs; " \
        "Add import statements for missing modules; Resolve input - output mismatches; Fix data type mismatches; " \
        "Correct calculation logic; Align frontend and backend data; " \
        "Add code comments for logic explanation; Update playwright test code to match PRD and frontend files; " \
        "If playwright test code is aligned, fix bugs reported by it to pass tests."
)

NODES = [
    INTEGRATION_RESULT, 
    ERROR_MESSAGE, 
    BUG_FIX_PLAN
    # SUGGESTION,
    # ERROR_PRONE_FILES,
    # REQUIRES_FILES
    ]

BUG_NODES = [
    # SUGGESTION,
    ERROR_PRONE_FILES,
    REQUIRES_FILES,
]

INTEGRATION_TEST_NODE = ActionNode.from_children("INTEGRATION_TEST_NODE", NODES)
BUGFIX_NODE= ActionNode.from_children("BUGFIX_NODE", BUG_NODES)