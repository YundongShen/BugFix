#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/03/01
@Author  : huakunyang
@File    : write_bug_fix_plan_and_change.py
"""
import os
from typing import List

from pydantic import Field
import json
from metagpt.actions.action import Action
from metagpt.actions.action_node import ActionNode
from metagpt.logs import logger
from metagpt.schema import CodePlanAndChangeContext
from metagpt.utils.project_setting import get_project_setting, merge_json_string
from metagpt.actions.write_code import WriteCode
from metagpt.actions.launch_project_test_an import ERROR_PRONE_FILES
from metagpt.actions.project_management_an import FILE_RELATION

BUG_FIX_PLAN = ActionNode(
    key="Bugfix Plan",
    expected_type=List[str],
    instruction="Develop a comprehensive and step-by-step incremental bugfix plan, providing the detail "
    "changes to be implemented at each step based on the bug information",
    example=[
        "Update the requirements.txt for the missing packages, ...",
        "Fix the syntax error in the code, ...",
        "Update the code to incorporate the latest API changes, ...",
        "Fix the bug that causes the program to crash, ...",
        "Add import statements to the code for missing modules, ...",
        "Fix the mismatch between the expected input and output, ...",
        "Fix the mismatched data types, ...",
        "Fix the incorrect calculation logic, ...",
        "Fix the mismatch between frontend and backend data, ...",
        "Add comments to the code to explain the logic, ...",
        "Update the playwright test code to align with PRD requirements and front end html,js files",
        "If the playwright tese code is correctly aligned with PRD requirements and html,js files, updated the code to fix the bug reported by the playwright test code, pass the testing in the playwright test code",

    ],
)

BUG_FIX_INCREMENTAL_CHANGE = ActionNode(
    key="Bugfix Incremental Change",
    expected_type=List[List[str]],
    instruction="Write Incremental Change by making a code draft that how to implement incremental bugfix "
    "including detailed steps based on the bug information. Note: Track incremental changes using the marks `+` and `-` to "
    "indicate additions and deletions, and ensure compliance with the output format of `git diff`,"
    "put the names of the file to be changed in the first list, and detail change information for each file in the second list,"
    "if the file is not new file, please ensure the changes should be done in the original file, avoid incorrectly creating extra redundant file, especially for wrongly createing the same file with different path in the project folder to lead to confusion,"
    "If the playwright test code is not aligned with PRD requirements document and front html,js code, please update the playwright test code to align with PRD and html, js files,otherwise, if the playwright tese code is correctly aligned with PRD requirements and html,js files, updated the code to fix the bug and pass the testing in the playwright test code"
    "ATTENTION1: Please carefully analysis the call stack information in the server console log to find the root cause of the bug and make the bug fix plan accordingly"
    "ATTENTION2: For the issue reports in the server console about '404 Not Found', Please carefully check the request URL in front-end source files match with the corresponding route path in server back-end code"
    "ATTENTION3: Please double check the request parameters in fron-end match the corresponding ones in back-end interface,ensure the front-end could access the back-end serverice successfully"
    "ATTENTION4: PLEASE double check the playwright test code aligns with the front-end code and PRD document, update the playwright test code if it is not aligned with them"
    "ATTENTION5: PLEASE double check the html element id and class name in front-end html file match the corresponding ones in playwright test code, for example, the typical error shall be avoid like the id in html is 'student-id' but the id in playwright test code is 'student_id' or vise versa, please double check the id and class name in front-end and playwright test code"
    "Attention6: PLEASE carefully read the frontend html and javascript code to create the test code that match some special criteria, for example:"
        "- The javascript code set 'Password must be at least 8 characters long and include uppercase, lowercase, digits, and special characters.', the test code should check the password input field should have the same criteria."
        "- The javascript code set 'Student ID must be alphanumeric and exactly 8 characters long.', the test code should follow it to create the test code."
        "- The javascript code set 'The input field should not be empty.', the test code should check the input field should not be empty."
    "ATTENTION7: PLEASE double check the test code and front-end code to make sure the indication message follows the requirement and to be consistent:." 
     "- If the front-end follows the requirements, the checking rules of the test code shall be consistent with the front-end requirements or code. "
     "- For example, if the front-end code set the success message as 'Login successful', the test code should check the success message is 'Login successful'. "
     "- If the front-end code does not contain the indication message exactly, the test code should not set asserion for it."

    "ATTENTION8: PLEASE double check the the front-end javascript code refer correct element id and class name in the html file, for example, the typical error shall be avoid like the id in html is 'student-id' but the id in javascript code is 'student_id' or vise versa, please double check the id and class name in front-end and javascript code."
    "ATTENTION9: For the front-end code, PLEASE do add the log information for the case of input format error, for example, if the front-end code requires the input field should be a valid email address, the log information should be 'Invalid email format' when the user input is not a valid email format, which could be helpful for debugging."
    "Attention10: PLEASE ONLY create the playwright test code of valid user input,do not create the test code for invalid user input, for example, the test code should not check the input field should not be empty for an empty input field."
    "ATTENTION11: PLEASE carefully check the log information of front-end code and server console log to find the root cause of the bug and make the bug fix plan accordingly. In some cases, the playwright test code shall be updated accordingly to fix the bug."
    "ATTENTION12: PLEASE ALWAYS PUT the package requirements file 'requirements.txt' in the project root directory, PLEASE DO NOT PUT IT IN THE 'OLD' FOLDER, PLEASE DO NOT create a new one in the source folder!",
    example=[
        ['calculator.py',
         'main.py'],
         [
        '''```diff
--- Old/calculator.py
+++ New/calculator.py

class Calculator:
         self.result = number1 + number2
         return self.result

-    def sub(self, number1, number2) -> float:
+    def subtract(self, number1: float, number2: float) -> float:
+        """
+        Subtracts the second number from the first and returns the result.
+
+        Args:
+            number1 (float): The number to be subtracted from.
+            number2 (float): The number to subtract.
+
+        Returns:
+            float: The difference of number1 and number2.
+        """
+        self.result = number1 - number2
+        return self.result
+
    def multiply(self, number1: float, number2: float) -> float:
-        pass
+        """
+        Multiplies two numbers and returns the result.
+
+        Args:
+            number1 (float): The first number to multiply.
+            number2 (float): The second number to multiply.
+
+        Returns:
+            float: The product of number1 and number2.
+        """
+        self.result = number1 * number2
+        return self.result
+
    def divide(self, number1: float, number2: float) -> float:
-        pass
+        """
+            ValueError: If the second number is zero.
+        """
+        if number2 == 0:
+            raise ValueError('Cannot divide by zero')
+        self.result = number1 / number2
+        return self.result
+
-    def reset_result(self):
+    def clear(self):
+        if self.result != 0.0:
+            print("Result is not zero, clearing...")
+        else:
+            print("Result is already zero, no need to clear.")
+
         self.result = 0.0
```''',
        """```diff
--- Old/main.py
+++ New/main.py

def add_numbers():
     result = calculator.add_numbers(num1, num2)
     return jsonify({'result': result}), 200

-# TODO: Implement subtraction, multiplication, and division operations
+@app.route('/subtract_numbers', methods=['POST'])
+def subtract_numbers():
+    data = request.get_json()
+    num1 = data.get('num1', 0)
+    num2 = data.get('num2', 0)
+    result = calculator.subtract_numbers(num1, num2)
+    return jsonify({'result': result}), 200
+
+@app.route('/multiply_numbers', methods=['POST'])
+def multiply_numbers():
+    data = request.get_json()
+    num1 = data.get('num1', 0)
+    num2 = data.get('num2', 0)
+    try:
+        result = calculator.divide_numbers(num1, num2)
+    except ValueError as e:
+        return jsonify({'error': str(e)}), 400
+    return jsonify({'result': result}), 200
+
 if __name__ == '__main__':
     app.run()
```""",
    ]],
)

BUG_FIX_CODE_PLAN_AND_CHANGE_CONTEXT = """
## User New Requirements
{requirement}

## Issue
{issue}

## PRD
{prd}

## Design
{design}

## Task
{task}

## Legacy Code
{code}

## Playwright Test Code
{playwright_test_code}
"""

BUG_FIX_REFINED_TEMPLATE = """
NOTICE
Role: You are a professional engineer; The main goal is to complete bug fix of legacy code, ensuring the bug is fixed in the updated code.

# Context
## Code Plan And Change
{code_plan_and_change}

## Legacy Code
```Code
{code}
```

## Debug logs
```text
{logs}

{summary_log}
```

## Bug Feedback logs
```text
{feedback}
```

# Format example
## Code: {filename}
```python
## {filename}
...
```

# Instruction: Based on the context, follow "Format example", write or rewrite code for bug fix.
## Write/Rewrite Code: Only write one file {filename}, write or rewrite complete code using triple quotes based on the following attentions and context.
1. Only One file: do your best to implement THIS ONLY ONE FILE.
2. COMPLETE CODE: Your code will be part of the entire project, so please implement complete, reliable, reusable code snippets.
3. Fix the bug: Your code must fix the bug, not just add new features.
4. Set default value: If there is any setting, ALWAYS SET A DEFAULT VALUE, ALWAYS USE STRONG TYPE AND EXPLICIT VARIABLE. AVOID circular import.
5. Follow design: YOU MUST FOLLOW "Data structures and interfaces". DONT CHANGE ANY DESIGN. Do not use public member functions that do not exist in your design.
6. Follow Code Plan And Change: If there is any "Incremental Change" that is marked by the git diff format with '+' and '-' symbols, or Legacy Code files contain "{filename} to be rewritten", you must merge it into the code file according to the "Development Plan". 
7. CAREFULLY CHECK THAT YOU DONT MISS ANY NECESSARY CLASS/FUNCTION IN THIS FILE.
8. Before using a external variable/module, make sure you import it first.
9. Write out EVERY CODE DETAIL, DON'T LEAVE TODO.
"""

BUG_FIX_PLAN_AND_CHANGE = [BUG_FIX_PLAN, BUG_FIX_INCREMENTAL_CHANGE]

WRITE_BUG_PLAN_AND_CHANGE_NODE = ActionNode.from_children("WriteBugFixPlanAndChange", BUG_FIX_PLAN_AND_CHANGE)


class WriteBugFixPlanAndChange(Action):
    name: str = "WriteBugFixPlanAndChange"
    i_context: CodePlanAndChangeContext = Field(default_factory=CodePlanAndChangeContext)

    async def run(self, *args, **kwargs):
        self.llm.system_prompt = "You are a professional software engineer, your primary responsibility is to "
        "analysize the error information of the project files and provide a bug fix plan and change."
        prd_doc = await self.repo.docs.prd.get(filename=self.i_context.prd_filename)
        system_design_doc = await self.repo.docs.system_design.get(filename=self.i_context.design_filename)
        code_design_doc = await self.repo.docs.code_design.get(filename=self.i_context.code_design_filename)
        desgin_doc = merge_json_string(system_design_doc.content, code_design_doc.content)
        task_doc = await self.repo.docs.task.get(filename=self.i_context.task_filename)
        project_setting = get_project_setting(self.config.project)
        desgin_setting_doc = merge_json_string(desgin_doc, project_setting)
        playwright_code = await self.repo.tests.get(filename="system_test_playwright_code.py")
        error_prone_files = await self.get_json_value(self.i_context.issue, ERROR_PRONE_FILES, [])
        file_relation = await self.get_json_value(task_doc.content, FILE_RELATION, [])
        legacy_code_files = await self.get_all_related_files(file_relation=file_relation, error_file=error_prone_files)
        legacy_code = await self.get_legacy_code(legacy_code_files)
        context = BUG_FIX_CODE_PLAN_AND_CHANGE_CONTEXT.format(
            requirement=f"```text\n{self.i_context.requirement}\n```",
            issue=f"```text\n{self.i_context.issue}\n```",
            prd=prd_doc.content,
            design=system_design_doc.content,
            task=task_doc.content,
            code=legacy_code,
            playwright_test_code = playwright_code
        )
        logger.info("Writing code plan and change..")
        return await WRITE_BUG_PLAN_AND_CHANGE_NODE.fill(context=context, llm=self.llm, schema="json")

    async def get_json_value(self, json_str, key_desc, return_des = ""):
        data = json.loads(json_str)
        return data.get(key_desc.key, return_des)

    async def get_old_codes(self) -> str:
        self.repo.old_workspace = self.repo.git_repo.workdir / os.path.basename(self.config.project_path)
        old_file_repo = self.repo.git_repo.new_file_repository(relative_path=self.repo.old_workspace)
        old_codes = await old_file_repo.get_all()
        codes = [f"----- {code.filename}\n```{code.content}```" for code in old_codes]
        return "\n".join(codes)
    
    async def get_legacy_code(self, file_list):
        codes = []
        src_file_repo = self.repo.srcs
        for filename in file_list:
            code_str = await src_file_repo.get(filename=filename)
            codes.append(f"\n{filename}\n```code\n{code_str.content}```")
        return "\n".join(codes)

    async def get_all_related_files(self, file_relation, error_file):
        related_files = set(error_file)
        # 创建一个字典，方便查找每个文件的依赖项
        relation_dict = {file[0]: file[1] for file in file_relation}
        # 用于存储待处理的文件
        to_process = list(error_file)

        while to_process:
            current_file = to_process.pop()
            dependencies = relation_dict.get(current_file, [])
            for dep in dependencies:
                if dep not in related_files:
                    related_files.add(dep)
                    to_process.append(dep)

        return list(related_files)
