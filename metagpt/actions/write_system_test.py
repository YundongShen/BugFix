#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/2/25 18:09
@Author  : huakunyang
@File    : write_system_test.py
"""

from typing import Optional

from metagpt.actions.action import Action
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import Document, SystemTestingContext
from metagpt.utils.common import CodeParser

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a System QA engineer; the main goal is to design, develop, and execute testing for the whole project, the testing shall cover the whole procedure from frontend to backend.
2. Requirement: Based on the context of PRD requirement document and frontend html code, develop a comprehensive test suite that adequately covers all features of the project, you need read carefully about the PRD documents and html code, work out the test case that could verify whether the features in the PRD document are satisified by the operation contained in the test case, which include the operation from the UI elements in the frontend html, and also you need list the expected results of the operation in the test cases. 
2. Attention1: PLEASE ONLY create the test case if valid user input, DO NOT create the test case of invalid user input, such as empty input, invalid input, etc.
3. Attention2: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the test case or script.
-----
## Given the following PRD requirement and frontend html code, please write appropriate test cases :

PRD Requirements:
{prd_requirement}

Frontend html source code:
{front_end_html_code}

"""


class WriteSystemTest(Action):
    name: str = "WriteSystemTest"
    i_context: Optional[SystemTestingContext] = None

    async def write_code(self, prompt):
        code_rsp = await self._aask(prompt)

        return code_rsp

    async def run(self, *args, **kwargs) -> SystemTestingContext:

        fake_root = "/data"
        prompt = PROMPT_TEMPLATE.format(
            prd_requirement=self.i_context.prd,
            front_end_html_code=self.i_context.html_contents,
        )
        self.i_context.sys_test_doc.content = await self.write_code(prompt)
        return self.i_context
