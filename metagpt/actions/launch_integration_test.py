#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/3/05 15:47
@Author  : huakunyang
@File    : lauch_integration_test.py
"""

from typing import Optional
import json
from pathlib import Path
from metagpt.actions.action import Action
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import ProjectIntegrationTestingContext
import subprocess
from subprocess import Popen, PIPE, STDOUT
import threading
from threading import Thread
from time import sleep
from metagpt.actions.launch_integration_test_an import BUGFIX_NODE,BUG_FIX_PLAN, ERROR_MESSAGE, SUGGESTION,ERROR_PRONE_FILES, INTEGRATION_RESULT, INTEGRATION_TEST_NODE
from eazytec_send import get_msg_for_recv
from metagpt.utils.file_repository import extract_file_path
import os
import signal


PROMPT_TEMPLATE_BAK = """
NOTICE
# Role: You are a System QA engineer; Now you are trying to check the error information from the playwright framework logs and backend server,you need provide the suggestion to fix the error.
# Requirement: you need carefully read the information from the playwright framework and backend server, you need provide the following information:
- The testing with the playwright framework logs and backend server pass or not?
- If the testing does not pass, please analyze the error message and provide the suggestion to fix the error. For example, database connection error, database schema error, wrong configurations, API interface mismatches, frontend and backend interface mismatches, etc.    
3. Attention1: Please carefully analysize the followng information to get the conclusion of above question.
-  playwright test code.
-  the console output in client
-  output of backend server for
4. Attention2: The server console message "Finished server process" is not error message, please ignore it. 
5. Attention3: Please ignore the error information 'GET /favicon.ico HTTP/1.1 404 Not Found', which does not need to be handled
6. Attention4: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the content of each section. Please state the test result, the error messages, and suggestions separately in each section.
7. Attention5: Please use the following template to provide the information of testing analysis result, if success, just say "SUCCESS", if not, just SAY "FAILED", this information shall be put in the first line of the output.
<Testing result>

8. Attention6: Please use the following template to provide the information of failed cases analysis and suggestion:
ERROR: <error message>  
SUGGESTION: <suggestion>  

-----
## Given the following testing information of the playwright framework and backend server, work out the report required above:

testing information::
{combined_test_result}


"""

PROMPT_TEMPLATE = """
NOTICE
# Role
    - You are a System QA engineer. Your task is to check for errors during project testing using the Playwright framework and backend server.
# Requirement
    - Analyze Playwright logs, client console output, and backend server output to determine if testing passed or failed.
    - Categorize detected errors as frontend - or backend - related. Frontend errors may involve Playwright actions, client - side JavaScript (e.g., incorrect function calls, DOM issues). Backend errors can include database connection failures (wrong strings, server unavailability), schema mismatches, and misconfigurations (env vars, routing, API interfaces).
    - For API errors, verify correct endpoints, request methods (e.g., using POST for data creation), and data formatting (e.g., valid JSON).
    - If common error codes like 422 occur repeatedly, review backend interface logic, data validation rules, and frontend data generation.
    - Provide detailed and actionable suggestions to fix errors. For database connection errors, suggest checking connection strings, server status, and driver config. For frontend JavaScript errors, suggest using browser dev tools for debugging.
    - If error messages reference files in the provided list, list those files in the report with context on how they are related to the error.
# Attention
    - Ignore the server console message "Finished server process" as it's not an error.
    - Ignore the 'GET /favicon.ico HTTP/1.1 404 Not Found' error as it's not relevant to core testing.
    - Use '##' to split sections, with '## <SECTION_NAME>' before each section's content for an organized report.
    - Clearly state "SUCCESS" if testing passed or "FAILED" if it failed on the first line of the output.
    - Ignore any messages in the error message that contain "INFO: " and end with " 307 Temporary Redirect", as they are considered successful and do not require further error analysis.


Given the following testing information from the Playwright framework and backend server (and the file list, if provided), work out the report required above:
testing information:
{combined_test_result}
file list: (optional)
{file_list}
"""

BUGFIX_TEMPLATE = """
NOTICE
1. Role: You are a System QA engineer; your task is to analyze errors based on the provided information.
2. Requirement:
   - Analyze the console output (error message) and the provided file list to determine which files are causing errors (error_files) and which files are required to fix the issues (require_files).
   - If the error messages reference files in the provided file list, list those files as error_files in the report.
   - Ignore any messages in the error message that contain "INFO: " and end with " 307 Temporary Redirect", as they are considered successful and do not require further error analysis.
3. Attention:
   - Ignore the final console message "Finished server process" as it is not an error message (due to a timeout command).
   - Use '##' to split sections, and ensure '## <SECTION_NAME>' is written before the content of each section.

-----
## Given the following information, work out the report required above:

error_message:
{error_message}

bugfix_plan:
{bugfix_plan}

file list: (optional)
{file_list}
"""


COMBINED_TEST_TEMPLATE = """
## FRONTEND SERVER CONSOLE OUT
{forntend_console_output}

## BACKEND SERVER CONSOLE OUT
{backend_console_output}

## PLAYWRIGHT TEST RESULT
{playwright_console_output}
"""

class ThreadWithReturnValue(Thread):
    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        super().join()
        return self._return


def run_subprocess_cmd(cmd):

    commands = (cmd)

    process = Popen(["/bin/bash"], shell=False, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    outs = process.communicate(commands.encode())[0]

    result = "\nSERVER CONSOLE OUTPUTS: \n\n"
    print("---------------------Integration Test OUTS:----------------\n",outs)
    content = [z.strip() for z in outs.decode().split("\n") if z]
    outs_log = "\n".join(content)
    result = result + outs_log +"\n"

    return result

def run_playwright_subprocess_cmd(cmd):

    commands = (cmd)

    process = Popen(["/bin/bash"], shell=False, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    outs = process.communicate(commands.encode())[0]

    result = "\nPLAYWRIGHT TEST OUTPUTS: \n\n"
    print("---------------------PLAYWRIGHT Test OUTS:----------------\n",outs)
    content = [z.strip() for z in outs.decode().split("\n") if z]
    outs_log = "\n".join(content)
    result = result + outs_log +"\n"

    return result
def cmds_thread(cmd_str):
    server_console_out = run_subprocess_cmd(cmd_str)
    logger.info(f"Server console output in cmds_thread: {server_console_out}")
    return server_console_out

class LaunchIntegrationTest(Action):
    name: str = "LaunchIntegrationTest"
    i_context: Optional[ProjectIntegrationTestingContext] = None

    async def check_failed_cases(self,test_result)-> ProjectIntegrationTestingContext:
        
        prompt = PROMPT_TEMPLATE.format(
            combined_test_result=test_result,
            file_list = str(self.i_context.file_list)
        )

        node = await INTEGRATION_TEST_NODE.fill(context=prompt, llm=self.llm)
        test_analyze_result = node.instruct_content
        test_analyze_result_dict = test_analyze_result.model_dump()
        if test_analyze_result_dict.get(INTEGRATION_RESULT.key) == "SUCCESS":
            self.i_context.test_success = True
            self.i_context.integration_test_result.content = test_analyze_result.model_dump_json()
        else:
            bugfix_prompt = BUGFIX_TEMPLATE.format(
                file_list=str(self.i_context.file_list),
                error_message=test_analyze_result_dict.get(ERROR_MESSAGE.key, ""),
                bugfix_plan=test_analyze_result_dict.get(BUG_FIX_PLAN.key, "")
            )
            bug_node = await BUGFIX_NODE.fill(context=bugfix_prompt, llm=self.llm)
            bugfixt_dict = bug_node.instruct_content.model_dump()
            self.i_context.test_success = False
            bugfixt_dict.update({"Console Output": test_result})
            bugfixt_dict.update({ERROR_MESSAGE.key: test_analyze_result_dict.get(ERROR_MESSAGE.key, "")})
            bugfixt_dict.update({BUG_FIX_PLAN.key: test_analyze_result_dict.get(BUG_FIX_PLAN.key, "")})
            self.i_context.integration_test_result.content = json.dumps(bugfixt_dict, ensure_ascii=False)
        return self.i_context
        

    async def run(self, *args, **kwargs) -> ProjectIntegrationTestingContext:
        project_src_dir =self.i_context.project_src_path
        project_path = self.i_context.project_path
        launch_backend_path = Path(self.i_context.launch_backend_file)
        launch_front_path = Path(self.i_context.launch_front_file)
        integration_test_case_file_path = self.i_context.integration_test_case_file_path
        self.config.current_role = f"TEST_ENGINEER"
        self.config.role_task = f"4/4 Launch Integrate test"

        backend_cmd_str = 'cd ' + project_path + '\n'+ 'source ./venv_test/bin/activate\n'+ 'cd '+  launch_backend_path.parent.as_posix() + '\n'+'timeout 20 uvicorn main:app --reload --port $APP_PORT_2  --log-level trace\n'
        front_cmd_str = 'cd ' + launch_front_path.parent.as_posix() + '\n' + 'BROWSER=none timeout 15 npm run dev -- --port $APP_PORT_1\n'

        logger.info(f"fr path ------     {front_cmd_str}")
        #cmd_str = 'source ./venv_test/bin/activate\n'+ 'cd '+  project_src_dir + '\n'+'timeout 20 uvicorn main:app --reload --port 8000 --log-level trace\n'
        #thread = ThreadWithReturnValue(target=cmds_thread,args=(cmd_str,))
        #thread.start()
        if self.config.local:
            logger.info(f"start ")
            thread = ThreadWithReturnValue(target=cmds_thread, args=(backend_cmd_str,))
            # 启动前端进程
            front_process = subprocess.Popen(front_cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            thread.start()

            sleep(3)
            playwright_result = run_playwright_subprocess_cmd('cd ' + project_path + '\n'+ 'source ./venv_test/bin/activate\n'+'python '+  integration_test_case_file_path + '\n')
            # 测试完成后，发送终止信号给前端进程
            try:
                # 获取进程组 ID
                pgid = os.getpgid(front_process.pid)
                # 发送 SIGKILL 信号给进程组
                os.killpg(pgid, signal.SIGKILL)
                front_process.wait()
            except OSError as e:
                print(f"Error killing process group: {e}")
            front_output, front_error = front_process.communicate()
            if not isinstance(front_error, str):
                front_error = front_error.decode('utf-8')
                front_output = front_output.decode('utf-8')
            backend_console_out =thread.join()

        else:
            oh_action_data = {}
            content_info = {
                "sub_content": f"Launch integration test.",
                "role_task": self.config.role_task,
                "agent_role": self.config.current_role,
                "mission": self.config.user_intend
            }
            oh_action_data['action_type'] = "MESSAGE"
            oh_action_data['content'] = content_info
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
            #print(f"!!!!!workspace: {oh_action_data}")

            oh_action_data = {}
            oh_action_data['message'] = f"Launch integration test - Start Server"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = 'cd '+ extract_file_path(self.context.config.sid, project_path)  + " ; " + '. ./venv_test/bin/activate' + " ; " + 'cd '+  extract_file_path(self.context.config.sid, launch_backend_path.parent.as_posix()) + '\n'
            oh_action_data['handle_output'] = False
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

            sleep(5)

            oh_action_data = {}
            oh_action_data['message'] = f"Remove previous nohup.out"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = f"rm -rf ./nohup.out\n"
            oh_action_data['handle_output'] = False
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

            oh_action_data = {}
            oh_action_data['message'] = f"Launch Integration Test - Start Server"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = f"nohup timeout 20 uvicorn main:app --reload --port $APP_PORT_2 --log-level trace &"
            oh_action_data['handle_output'] = False
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

            oh_action_data = {}
            oh_action_data['message'] = f"Update Shell"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = f"cd ."
            oh_action_data['handle_output'] = False
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
            sleep(2)

            # 启动前端
            oh_action_data = {}
            content_info = {
                "sub_content": f"Launch Integration Test - Start Frontend Server",
                "role_task": self.config.role_task,
                "agent_role": self.config.current_role,
                "mission": self.config.user_intend
            }
            oh_action_data['action_type'] = "MESSAGE"
            oh_action_data['content'] = content_info
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")

            oh_action_data = {}
            oh_action_data['message'] = f"Launch Integration Test - Start Frontend Server"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = 'cd '+extract_file_path(self.context.config.sid, launch_front_path.parent.as_posix())  + " ; " + 'timeout 20 npm run dev -- --port $APP_PORT_1'
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
            front_output = get_msg_for_recv(self.context.config.sio, self.context.config.sid) #get_msg_for_recv()

            sleep(15)
            oh_action_data = {}
            oh_action_data['message'] = f"Update Shell"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = f"cd ."
            oh_action_data['handle_output'] = False
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
            sleep(2)

            # 启动playwright 测试
            oh_action_data = {}
            content_info = {
                "sub_content": f"Launch Integration Test - Run Test",
                "role_task": self.config.role_task,
                "agent_role": self.config.current_role,
                "mission": self.config.user_intend
            }
            oh_action_data['action_type'] = "MESSAGE"
            oh_action_data['content'] = content_info
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
            #print(f"!!!!!workspace: {oh_action_data}")

            oh_action_data = {}
            oh_action_data['message'] = f"Launch Integration Test - Run Test"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] =  'cd '+ extract_file_path(self.context.config.sid, project_path)  + " ; " + '. ./venv_test/bin/activate' + " ; " + "python "+  extract_file_path(self.context.config.sid, integration_test_case_file_path) + "\n"
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

            playwright_result = get_msg_for_recv(self.context.config.sio, self.context.config.sid) #get_msg_for_recv()
            sleep(15)
            #test_result = run_subprocess_cmd('source ./playwright_venv/bin/activate\n'+'python '+  integration_test_case_file_path + '\n')
            print("\n----------playwright_result Integration Test Result playwright:----------------\n",playwright_result)

            oh_action_data = {}
            oh_action_data['message'] = f"Show log of uvicorn"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = f"cat ./nohup.out"
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

            backend_console_out = get_msg_for_recv(self.context.config.sio, self.context.config.sid)
            print("\n----------playwright_result Integration Test Result backend_console_out:----------------\n",backend_console_out)
            

        # TODO,这里需要修改

        # with open(integration_test_case_file_path, 'r') as file:
        # # Read the entire file
        #     integrate_test_conent = file.read()

        # TODO, 这个地方可能有问题，前端在runtime里如何获得信息需要调试
        if self.config.local:
            combined_test_result = COMBINED_TEST_TEMPLATE.format(
                forntend_console_output=front_output + "\n"+front_error,
                backend_console_output=backend_console_out,
                playwright_console_output=playwright_result
            )
        else:
            combined_test_result = COMBINED_TEST_TEMPLATE.format(
                forntend_console_output=front_output,
                backend_console_output=backend_console_out,
                playwright_console_output=playwright_result
            )

        print("\n----------COMBINED TEST RESULT:\n", combined_test_result)
        
        self.i_context = await self.check_failed_cases(combined_test_result)
        return self.i_context
