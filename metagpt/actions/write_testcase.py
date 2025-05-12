from typing import Optional
import json
from metagpt.logs import logger
from metagpt.actions import Action, ActionOutput
from metagpt.schema import Document, Documents, Message
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.utils.common import OutputParser
from metagpt.const import TESTCASE_FILENAME, PRD_FILENAME, SIMULATE_ROOT


PROMPT_TEMPLATE = """
NOTICE
Role: You are a System QA engineer; your main goal is to design, develop, and execute testing for the entire project. The testing should cover the whole procedure from frontend to backend.
Language: Use the same language as the user requirement, but keep the title and code in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to split sections, not '#'. Output format should carefully follow the "Format example" provided.

# Context
## PRD Requirements
{prd}

# Format example
```text
Test Case ID: unique_id
Description: brief_description_of_test_case
Steps:
1. step_1
2. step_2
3. step_3
...
Expected Result: expected_result

```
# Instruction: Based on the PRD requirements, follow the "Format example" and write test cases.Write test cases with the following attentions and context:
1.Valid Input Only: Create test cases only for valid user inputs. Do not include test cases for invalid inputs such as empty or invalid data.
2.Comprehensive Coverage: Ensure the test suite adequately covers all features described in the PRD.
3.Expected Results: Clearly define the expected result for each test case.
4.Modularity: Write test cases in a modular and reusable way.
5.Clarity: Use clear and concise language for steps and expected results.
This revised prompt is more concise and focuses solely on the PRD requirements, eliminating the need to reference frontend HTML code. It ensures that the test cases are derived directly from the PRD, making the process more streamlined.
"""


class WriteTestCase(Action):
    name: str =""
    i_context: Optional[str] = None
    desc: str = (
        "Based on the PRD, write test case"
    )

    async def run(self, with_messages: Message, schema: str = None):
        all_prds = self.repo.docs.prd.all_files
        self.config.current_role = f"TEST_ENGINEER"
        self.config.role_task = f"1/1 Write test case"

        changed_files = Documents()
        filename = TESTCASE_FILENAME

        oh_action_data = {}
        content_info = {
            "sub_content": f"Writing test case in: {filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        doc = await self.write_testcase(filename=filename)
        changed_files.docs[filename] = doc
        return ActionOutput(content=changed_files.model_dump_json(), instruct_content=changed_files)
    
    async def write_testcase(self, filename):
        prd = await self.repo.docs.prd.get(PRD_FILENAME)
        prd_md = await self._convert_to_markdown(prd.content)
        context = PROMPT_TEMPLATE.format(prd=prd_md)
        testcase_rsp = await self._aask(context)
        if self.config.simulate:
            testcase_path = SIMULATE_ROOT / TESTCASE_FILENAME
            with open(testcase_path, "r") as f:
                content = f.read()
            doc = await self.repo.docs.testcase.save(
                filename=filename,
                content=content,
                dependencies={prd.root_relative_path},
                current_role = self.config.current_role,
                role_task = self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend
            )
        else:
            doc = await self.repo.docs.testcase.save(
                filename=filename,
                content=testcase_rsp,
                dependencies={prd.root_relative_path},
                current_role = self.config.current_role,
                role_task = self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend
            )
        return doc
    
    async def _convert_to_markdown(self, content):
        try:
            content = json.loads(content)
            content = json_to_markdown(content, depth=3)
            return content
        except:
            return content
