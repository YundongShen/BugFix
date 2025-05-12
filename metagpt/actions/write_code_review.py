#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 17:45
@Author  : alexanderwu
@File    : write_code_review.py
@Modified By: mashenquan, 2023/11/27. Following the think-act principle, solidify the task parameters when creating the
        WriteCode object, rather than passing them in when calling the run function.
"""
import datetime
import shutil

from pydantic import Field
from tenacity import retry, stop_after_attempt, wait_random_exponential

from metagpt.actions import WriteCode
from metagpt.actions.action import Action
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.logs import logger
from metagpt.schema import CodingContext
from metagpt.utils.common import CodeParser
import re
PROMPT_TEMPLATE = """
# System
Role: You are a professional software engineer whose main task is to review and revise the provided code (in standard text format and written in a programming language), ensuring it conforms to Google - style standards, is elegantly designed and modularized, and is easy to read and maintain;if there are additional code files that the code to be reviewed depends on, please provide them as well for a full understanding of context and dependencies.
Language: Please use the same language as the user requirement, but the title and code should be still in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to SPLIT SECTIONS, not '#'. Output format carefully referenced "Format example".

# Context
{context}

-----

## Code to be Reviewed: {filename}
```Code
{code}
```

## Playwright Test Code
```Code
{playwright_test_code}
```

"""

EXAMPLE_AND_INSTRUCTION = """

{format_example}


# Instruction: Based on the actual code, follow the "Code Review Format example" to conduct a comprehensive review of the provided code.".
- Note that the code filename should be {filename}. Return the review results for the single file {filename}.

## Code Review: Ordered List. Provide clear, concise, and specific answers based on the "Code to be Reviewed". If any answer is negative, explain step - by - step how to fix the issue.
1. Is the code implemented as per the requirements? If not, how to achieve it? Analyse it step by step.
2. Is the code logic completely correct? If there are errors, please indicate how to correct them.
3. Does the existing code follow the "Data structures and interfaces"?
4. Are all functions implemented? If there is no implementation, please indicate how to achieve it step by step.
5. Have all necessary pre-dependencies been imported? If not, indicate which ones need to be imported
6. Are methods from other files being reused correctly?
7. Whether the imported self-written module appears in the 'Dependency Code Files'. If not, delete the import.
8. Do the url requests in front-end files match the routes set in back-end files ? 
9. Do the requests parameters in the front-end files match the corresponding one in back-end files ?
10. Please double check above 7th and 8th points to ensure the front-end could successfully access the severices provide in back-end part.
11. ATTENTION1: Please ensure the request URL in front-end matchs the ones in back-end, for example, the typical error like the following:
 - The request URL in front-end is 'http://localhost:8000/register' but the request URL in back-end is 'http://localhost:8000/api/register', please double check the request URL in front-end and back-end.
 - The request URL in front-end is 'http://localhost:8000/register' but the request URL in back-end is 'http://localhost:8000/register/sregister', please double check the request URL in front-end and back-end.
12. ATTENTION2: PLEASE double check the the front-end javascript code refer correct element id and class name in the html file, for example, the typical error shall be avoid like the id in html is 'student-id' but the id in javascript code is 'student_id' or vise versa, please double check the id and class name in front-end and javascript code.
13. ATTENTION3: For playwright test code, PLEASE double check the html element id and class name in front-end html file match the corresponding ones in playwright test code, for example, the typical error shall be avoid like the id in html is 'student-id' but the id in playwright test code is 'student_id' or vise versa, please double check the id and class name in front-end and playwright test code.
14. Attention4: PLEASE double check the playwright test code and front-end code to make sure the indication message follows the requirement and is consistent with the front-end code. 
   - If the front-end follows the requirements, the checking rules of the test code shall be consistent with the front-end requirements or code. 
   - For example, if the front-end code set the success message as "Login successful", the test code should check the success message is "Login successful".
   - If the front-end code does not contain the indication message exactly, the test code should not set asserion for it.
15. Attention5: PLEASE ONLY create the playwright test code of valid user input,do not create the test code for invalid user input, for example, the test code should not check the input field should not be empty for an empty input field.
16. ATTENTION6: PLEASE carefully check the log information of front-end code and server console log to find the root cause of the bug and make the bug fix plan accordingly. In some cases, the playwright test code shall be updated accordingly to fix the bug.
17. ATTENTION7: For the front-end code, PLEASE do add the log information for the case of input format error, for example, if the front-end code requires the input field should be a valid email address, the log information should be "Invalid email format" when the user input is not a valid email format, which could be helpful for debugging.


## Actions: Ordered List. Things that should be done after CR, such as implementing class A and function B

## Code Review Result: str. If the code doesn't have bugs, we don't need to rewrite it, so answer LGTM and stop. ONLY ANSWER LGTM/LBTM.
LGTM/LBTM

"""

FORMAT_EXAMPLE = """
-----

# Code Review Format example 1
## Code Review: {filename}
1. No, we should fix the logic of class A due to ...
2. ...
3. ...
4. No, function B is not implemented, ...
5. ...
6. ...

## Actions
1. Fix the `handle_events` method to update the game state only if a move is successful.
   ```python
   def handle_events(self):
       for event in pygame.event.get():
           if event.type == pygame.QUIT:
               return False
           if event.type == pygame.KEYDOWN:
               moved = False
               if event.key == pygame.K_UP:
                   moved = self.game.move('UP')
               elif event.key == pygame.K_DOWN:
                   moved = self.game.move('DOWN')
               elif event.key == pygame.K_LEFT:
                   moved = self.game.move('LEFT')
               elif event.key == pygame.K_RIGHT:
                   moved = self.game.move('RIGHT')
               if moved:
                   # Update the game state only if a move was successful
                   self.render()
       return True
   ```
2. Implement function B

## Code Review Result
LBTM

-----

# Code Review Format example 2
## Code Review: {filename}
1. Yes.
2. Yes.
3. Yes.
4. Yes.
5. Yes.
6. Yes.

## Actions
pass

## Code Review Result
LGTM

-----
"""

REWRITE_CODE_TEMPLATE = """
# Instruction: rewrite the `{filename}` based on the Code Review and Actions
## Rewrite Code: CodeBlock. If it still has some bugs, rewrite {filename} with triple quotes. Do your utmost to optimize THIS SINGLE FILE. Return all completed codes and prohibit the return of unfinished codes.
```Code
## {filename}
...
```
"""


class WriteCodeReview(Action):
    name: str = "WriteCodeReview"
    i_context: CodingContext = Field(default_factory=CodingContext)

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
    async def write_code_review_and_rewrite(self, context_prompt, cr_prompt, filename):
        cr_rsp = await self._aask(context_prompt + cr_prompt)
        result = CodeParser.parse_block("Code Review Result", cr_rsp)
        if "LGTM" in result:
            return result, None

        # if LBTM, rewrite code
        rewrite_prompt = f"{context_prompt}\n{cr_rsp}\n{REWRITE_CODE_TEMPLATE.format(filename=filename)}"
        code_rsp = await self._aask(rewrite_prompt)
        code = CodeParser.parse_code(block="", text=code_rsp)
        return result, code

    async def run(self, *args, **kwargs) -> CodingContext:
        iterative_code = self.i_context.code_doc.content
        k = self.context.config.code_review_k_times or 1

        playwright_test_code_content = ""
        if self.i_context.playwright_code_doc != None:
            playwright_test_code_content = self.i_context.playwright_code_doc.content

        for i in range(k):
            format_example = FORMAT_EXAMPLE.format(filename=self.i_context.code_doc.filename)
            task_content = self.i_context.task_doc.content if self.i_context.task_doc else ""
            task_desc = await  WriteCode.parse_task(task_content, self.i_context.filename)
            design_desc = await WriteCode.parse_design(self.i_context.design_doc.content)
            code_context = await WriteCode.get_codes(
                self.i_context.task_doc,
                exclude=self.i_context.filename,
                project_repo=self.repo.with_src_path(self.context.src_workspace),
                use_inc=self.config.inc
            )

            ctx_list = [
                "## System Design\n" + design_desc + "\n",
                "## Task\n" + task_desc + "\n",
                "## Dependency Code Files :" + code_context + "\n",
            ]
            if self.config.inc:
                requirement_doc = await self.repo.docs.get(filename=REQUIREMENT_FILENAME)
                insert_ctx_list = [
                    "## User New Requirements\n" + str(requirement_doc) + "\n",
                    "## Code Plan And Change\n" + str(self.i_context.code_plan_and_change_doc) + "\n",
                ]
                ctx_list = insert_ctx_list + ctx_list

            context_prompt = PROMPT_TEMPLATE.format(
                context="\n".join(ctx_list),
                code=iterative_code,
                playwright_test_code= playwright_test_code_content,
                filename=self.i_context.code_doc.filename,
            )
            cr_prompt = EXAMPLE_AND_INSTRUCTION.format(
                format_example=format_example,
                filename=self.i_context.code_doc.filename,
            )
            len1 = len(iterative_code) if iterative_code else 0
            len2 = len(self.i_context.code_doc.content) if self.i_context.code_doc.content else 0
            logger.info(
                f"Code review and rewrite {self.i_context.code_doc.filename}: {i + 1}/{k} | len(iterative_code)={len1}, "
                f"len(self.i_context.code_doc.content)={len2}"
            )
            result, rewrited_code = await self.write_code_review_and_rewrite(
                context_prompt, cr_prompt, self.i_context.code_doc.filename
            )
            if "LBTM" in result:
                iterative_code = rewrited_code
            elif "LGTM" in result: # 第一轮如果没有review成功，重新写并进行二次review
                self.i_context.code_doc.content = iterative_code
                return self.i_context
        # code_rsp = await self._aask_v1(prompt, "code_rsp", OUTPUT_MAPPING)
        # self._save(context, filename, code)
        # 如果rewrited_code是None（原code perfect），那么直接返回code
        self.i_context.code_doc.content = iterative_code

        if self.i_context.filename.endswith(".js") or self.i_context.filename.endswith(".html") or self.i_context.filename.endswith(".css"):
            lines = self.i_context.code_doc.content.splitlines()
            if lines[0].startswith("##"):
                logger.info(f"Code Review - Removing the first line as it begins with invalid syntax ##...")
                self.i_context.code_doc.content = "\n".join(lines[1:])


        return self.i_context
