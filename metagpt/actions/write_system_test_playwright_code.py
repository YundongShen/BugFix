#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/3/04 16:04
@Author  : huakunyang
@File    : write_system_test_playwright_code.py
"""

from typing import Optional

from metagpt.actions.action import Action
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Document, SystemTestingPlayWrightCodeContext
from metagpt.utils.common import CodeParser
from metagpt.utils.common import CodeParser
from metagpt.utils.example_code import playwright_example_code
import json


PROMPT_TEMPLATE = """
NOTICE
Role: You are a QA engineer proficient in creating test cases using Microsoft's Playwright framework.  
Goal: Write Python test code using the Playwright framework to test a web application based on provided prd_requirement,desgin and frontend source code.  

## Requirements  
### 1. ​**Inputs**  
   - Product Requirements Document (prd_requirement)  
   - Code Design(design)
   - Frontend Source Code
   - System Test Cases  

### 2. ​**Output**  
Python test code using the Playwright framework that covers all the provided test cases. Each test case must be executed, regardless of whether previous test cases pass or fail. The test code should ensure that no single test case failure prevents the execution of subsequent test cases.


### 3. ​**Constraints**  
   - The test code must follow Python syntax and import the Playwright package.  
   - The test code should only include test cases that can be executed using Playwright in a Chrome browser. Skip test cases that cannot be verified through Playwright (e.g., backend-only tests).  
   - The test code should use the correct web application URL, which can be obtained from:  
     - Environment variables (e.g., `BASE_URL`).  
     - Configuration files (e.g., `.env`, `config.json`).  
     - Hardcoded values in the frontend code (e.g., `window.location.origin`).  
   - Ensure the HTML element IDs, class names, and selectors in the test code match those in the frontend HTML and JavaScript code.  
   - Carefully analyze the frontend JavaScript code to ensure the test code aligns with any validation rules or logic (e.g., password complexity, input field constraints).  
   - Avoid duplicating test cases already handled by the frontend code (e.g., if the frontend validates that an input field is not empty, do not include a test case for it).  
   - Only include test cases for valid user input. Do not create test cases for invalid input unless explicitly required.  
   - Include test cases to verify frontend-backend communication, such as API calls and responses, if the frontend logic depends on backend interactions.  
   - PLEASE insert sleep(1) after each page.goto() or page.click() to make sure the page is fully loaded before the next action, this is to avoid the "element not found" error
   - PLEASE ADD logging to capture the url requested and html content received for each page.goto() or page.click() to capture the state of the page for furuating debugging.
### 4. ​**Additional Notes**  
   - Include console output capture during test execution to log any errors or messages.  
   - Ensure the test code verifies any success or error messages displayed on the frontend, if applicable.  
   - For frontend-backend communication tests, ensure the test code verifies the following:  
     - The frontend sends the correct request to the backend (e.g., API endpoint, payload).  
     - The frontend correctly handles the backend response (e.g., success, error, or timeout).  
     - The frontend displays the appropriate message or updates the UI based on the backend response.  
   - Use Playwright’s `expect_response` or `route` functionality to intercept and verify API requests and responses.  
   - ​**API Endpoints**: Replace the API endpoints in the test code with the actual backend API endpoints used in the project. These endpoints can be found in the backend API documentation, frontend code, or by consulting the development team.  
   - Follow best practices for Playwright test automation, such as using appropriate assertions and selectors.  

### 5. ​**Example Code**  
{playwright_example_code}

### 6. ​**Console Output Capture​**
    - Please also include console output captured during the test execution, you may refer the following example code for it
    ```python
    def setup_console_listeners(page):
    # Set up listeners for console logs, errors, and failed network requests.
    # Captures only essential information to avoid redundancy.
    # Listen for all console messages

        def handle_console_message(msg):
            if msg.type == "error":
                logger.error(f"Console Error")
            elif msg.type == "warning":
                logger.warning(f"Console Warning")
            else:
                logger.info(f"Console Log")

    page.on("console", handle_console_message)

    # Listen for failed network requests
    def handle_request_failed(request):
        logger.error(f"Network Request Failed")

    page.on("requestfailed", handle_request_failed)

    # Listen for web errors (if supported by the framework)
    def handle_web_error(web_error):
        logger.error(f"Web Error")

    page.on("weberror", handle_web_error)
    ```

    
## Given the following PRD requirement and frontend html code, please write appropriate test cases :
## PRD Requirements:
{prd_requirement}

## System Test Cases:
{system_test_cases}

## Frontend Source Code
{frontend_code}

"""


class WritePlayWrightSystemTestCode(Action):
    name: str = "WriteSystemTestPlaywrightCode"
    i_context: Optional[SystemTestingPlayWrightCodeContext] = None

    async def write_system_test_playwright_code(self, prompt):
        code_rsp = await self._aask(prompt)

        return code_rsp

    async def run(self, *args, **kwargs) -> SystemTestingPlayWrightCodeContext:
        self.config.current_role = f"TEST_ENGINEER"
        self.config.role_task = f"3/4 Write playwright system test code"

        oh_action_data = {}
        content_info = {
            "sub_content": f"Writing system test code in {self.i_context.sys_test_playwright_code.filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        prompt = PROMPT_TEMPLATE.format(
            prd_requirement=self.i_context.prd,
            # design=self.i_context.design,
            # front_end_html_code=self.i_context.html_contents,
            # front_end_javascript_code = self.i_context.js_contents,
            system_test_cases = self.i_context.sys_test_doc,
            frontend_code = self.i_context.frontend_code,
            playwright_example_code=playwright_example_code
        )
        self.i_context.sys_test_playwright_code.content = CodeParser.parse_code(block="",text = await self.write_system_test_playwright_code(prompt))
        return self.i_context
