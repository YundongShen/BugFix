from metagpt.roles import Role
from metagpt.schema import Document, Message, SystemTestingContext, SystemTestingPlayWrightCodeContext, LaunchProjectTestingContext,ProjectIntegrationTestingContext
from metagpt.actions.write_testcase import WriteTestCase
from metagpt.actions.write_prd import WritePRD

class TestEngineer(Role):
    name: str = "TestEdward"
    profile: str = "TestEngineer"
    goal: str = "Create the test case based on PRD and frontend html files to test the functions of all software, and execute the test case after code change"
    constraints: str = (
        ""
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.set_actions([WriteTestCase])
        self._watch([WritePRD])
        