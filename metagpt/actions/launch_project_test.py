#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/2/25 18:09
@Author  : huakunyang
@File    : launch_project_test.py
"""

from typing import Optional
import json
from metagpt.actions.action import Action
from metagpt.actions.launch_project_test_an import LAUNCH_TEST_NODE, LAUNCH_RESULT,  DATABASE_ERROR_RESULT, ERROR_MESSAGE, SUGGESTION,ERROR_PRONE_FILES, CONSOLE_OUTPUT, BUGFIX_NODE, BUG_FIX_PLAN
from metagpt.const import TEST_CODES_FILE_REPO
from metagpt.logs import logger
from metagpt.schema import LaunchProjectTestingContext
from metagpt.utils.common import CodeParser
import subprocess
from subprocess import Popen, PIPE, STDOUT
from pathlib import Path
import os
from eazytec_send import get_msg_for_recv
from metagpt.utils.file_repository import extract_file_path
from time import sleep

# PROMPT_TEMPLATE = """
# NOTICE
# 1. Role: You are a System QA engineer; Now you are trying to check the errors during lauching the project, the project is composed of front-end and back-end files.
# 2. Requirement: you need carefully read the information printed in the console when the project launches, you need provide the following information:
# - The project is launched successfully or not ?
# - If the project is not launched successfully, please analyze the error message and provide the suggestion to fix the error. For example, missing the dependency package, wrong configurations, code errors, etc.
# 3. Attention1: As the command is launched with timeout 10 commands, so the finnal console message "Finished server process" is not error message, please ignore it. 
# 4. Attention2: If the console message contains "INFO:uvicorn.error:Finished server process", it means the project is launched successfully, please ignore the other message below it.
# 5. Attention3: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD WRITE BEFORE the content of each section. Please state the launch result, the error messages, and suggestions separately in each section.
# 6. Attention4: Please use the following template to provide the information launch result, if success, just say "SUCCESS", if not, just SAY "FAILED", this information shall be put in the first line of the output.
# <lauch result>

# 7. Attention3: Please use the following template to provide the information of each error message and suggestion:
# ERROR: <error message>  
# SUGGESTION: <suggestion>  

# -----
# ## Given the following information printed in the console when the project launches, work out the report required above:

# console output::
# {console_output}

# file list::
# {file_list}

# """

DATABASE_CHECK_PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a System QA engineer; Now you are trying to check the errors during launching the project, the project is composed of front - end and back - end files.
2. Requirement: 
    - You need to carefully read the information printed in the console when the project launches and the provided file list.
    - Determine whether the project is launched with database - relevant issues or not.
    - If the project has database - relevant issues, analyze the error message and provide suggestions to fix the error, such as missing dependency packages, wrong configurations, code errors, etc.
    - If the error information contains file names that are also in the provided file list, list these error - prone files in the report.
3. Attention1: As the command is launched with timeout 10 commands, the final console message "Finished server process" is not an error message, please ignore it. 
4. Attention2: Use '##' to split sections, not '#', and '## <SECTION_NAME>' SHOULD BE WRITTEN BEFORE the content of each section. Please state the launch result, the error messages, suggestions, and error - prone files separately in each section.
5. Attention3: Please use the following template to provide the information of error analysis. If there is no database error, just say "NOERR"; if there is, just say "ERR". This information shall be put in the first line of the output.
<err result>
6. Attention4: Please use the following template to provide the information of each error message and suggestion. If the error information contains file names that are in the provided file list, list all such file names in the `FILENAME` section, separated by commas. If no relevant file names are found, leave the `FILENAME` section empty.
ERROR: <error message>  
SUGGESTION: <suggestion>  
FILENAME: <file1.py, file2.js>
-----
## Given the following information printed in the console when the project launches and the file list, work out the report required above:

console output::
{console_output}

file list::
{file_list}

"""

PROMPT_TEMPLATE = """
NOTICE
1. Role: You are a System QA engineer; your task is to check errors during the launch of a project.
2. Requirement:
   - Analyze the console output and the provided file list (if any) to determine if the project launched successfully or encountered errors.
   - If errors are found, analyze them and provide suggestions to fix them (e.g., missing dependencies, wrong configurations, code errors, etc.).
   - If the error messages reference files in the provided file list, list those files in the report.
3. Attention:
   - Ignore the final console message "Finished server process" as it is not an error message (due to a timeout command).
   - Also ignore messages related to normal application shutdown such as "Shutting down", "Waiting for application shutdown.", "Application shutdown complete.", "Stopping reloader process" as these are expected during a normal termination of the server.
   - Use '##' to split sections, and ensure '## <SECTION_NAME>' is written before the content of each section.
   - If the project launched successfully, say "SUCCESS"; if failed, say "FAILED". Place this on the first line of the output.

-----
## Given the following information printed in the console when the project launches (and the file list, if provided), work out the report required above:

console output:
{console_output}

file list: (optional)
{file_list}

"""

BUGFIX_TEMPLATE = """
NOTICE
1. Role: You are a System QA engineer; your task is to analyze errors based on the provided information.
2. Requirement:
   - Analyze the console output (error message) and the provided file list to determine which files are causing errors (error_files) and which files are required to fix the issues (require_files).
   - If the error messages reference files in the provided file list, list those files as error_files in the report.
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

def run_subprocess_cmd(cmd):

    commands = (cmd)

    process = Popen(["/bin/bash"], shell=False, stdout=PIPE, stdin=PIPE, stderr=STDOUT)
    outs = process.communicate(commands.encode())[0]

    result = "\nCONSOLE OUTPUTS: \n\n"
    content = [z.strip() for z in outs.decode().split("\n") if z]
    outs_log = "\n".join(content)
    result = result + outs_log +"\n"

    return result


class LaunchProjectTest(Action):
    name: str = "LaunchProjectTest"
    i_context: Optional[LaunchProjectTestingContext] = None

    async def check_failed_cases(self,failed_cases)-> LaunchProjectTestingContext:
        context = PROMPT_TEMPLATE.format(
            console_output=failed_cases,
            file_list = str(self.i_context.file_list)
        )
        node = await LAUNCH_TEST_NODE.fill(context=context, llm=self.llm)
        launch_result = node.instruct_content
        launch_result_dict = launch_result.model_dump()
        if launch_result_dict.get(LAUNCH_RESULT.key) == "SUCCESS":
            self.i_context.launch_success = True
            self.i_context.launch_result_analysis.content = launch_result.model_dump_json()
        else:
            bugfix_prompt = BUGFIX_TEMPLATE.format(
                file_list=str(self.i_context.file_list),
                error_message=launch_result_dict.get(ERROR_MESSAGE.key, ""),
                bugfix_plan=launch_result_dict.get(BUG_FIX_PLAN.key, "")
            )
            bug_node = await BUGFIX_NODE.fill(context=bugfix_prompt, llm=self.llm)
            bugfixt_dict = bug_node.instruct_content.model_dump()
            self.i_context.launch_success = False
            bugfixt_dict.update({"Console Output": failed_cases})
            bugfixt_dict.update({ERROR_MESSAGE.key: launch_result_dict.get(ERROR_MESSAGE.key, "")})
            bugfixt_dict.update({BUG_FIX_PLAN.key: launch_result_dict.get(BUG_FIX_PLAN.key, "")})
            self.i_context.launch_result_analysis.content = json.dumps(bugfixt_dict, ensure_ascii=False)
        return self.i_context

    async def run(self, *args, **kwargs) -> LaunchProjectTestingContext:
        project_src_dir =self.i_context.project_src_path
        project_path = self.i_context.project_path
        self.config.current_role = f"TEST_ENGINEER"
        self.config.role_task = f"2/4 Launch project test"

        # 建立python虚拟环境
        if not os.path.exists(os.path.join(project_path, "venv_test")):
            run_subprocess_cmd('cd '+  project_path + '\n'+ "virtualenv venv_test --python=python3.11")

            print(f"path: {extract_file_path(self.context.config.sid, project_path)}")

            oh_action_data = {}
            oh_action_data['message'] = f"create venv_test"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = "cd " + extract_file_path(self.context.config.sid, project_path) + " ; " + 'virtualenv venv_test --python=python3.11'
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

        launch_backend_path = Path(self.i_context.launch_backend_file)
        launch_front_path = Path(self.i_context.launch_front_file)
        launch_requirements_path = Path(self.i_context.launch_requirements_file)

        
        # logger.info("\n======LAUHCH COMMAND=============\n:"
        #                             + 'cd '+  project_path + ';'  \
        #                             + 'pip install -r requirements.txt; ' \
        #                             + 'cd '+ project_src_dir + '; ' \
        #                             + 'uvicorn main:app --reload --port 8002')

        # npm install --registry=https://registry.npmmirror.com
        # 安装前端依赖
        if self.i_context.front_dependency == False:
            logger.info("\n======FRONTEND  ----> INSTALL DEPENDENCIES=============\n")
            #result = run_subprocess_cmd('cd '+  launch_front_path.parent.as_posix() + '\n'+ 'npm install --registry=https://registry.npmmirror.com')

            oh_action_data = {}
            content_info = {
                "sub_content": f"Install frontend dependencies.",
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
            oh_action_data['message'] = f"frontend install dependencies"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = 'cd ' + extract_file_path(self.context.config.sid, launch_front_path.parent.as_posix()) + " ; " + 'npm install --registry=http://2.2.0.23:45923/repository/group-npm/' # add vue@3.4.20
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
            print(f"##### front install depends data: {oh_action_data}")

            if not self.config.local:
                result = get_msg_for_recv(self.context.config.sio, self.context.config.sid)
                print("\n=====================frontend install dependencies===============\n:",result)
            else:
                result = run_subprocess_cmd('cd '+  launch_front_path.parent.as_posix() + '\n'+ 'npm install --registry=https://registry.npmmirror.com')

            context = await self.check_failed_cases(result)
            if context.launch_success == False:
                return context
            self.i_context.front_dependency = True
        
        # 启动前端服务器
        if self.i_context.launch_front_success == False:
            logger.info("\n======FRONTEND  ----> LAUNCH SERVER=============\n")
            if self.config.local:
                frontend_launch_result = run_subprocess_cmd(f'cd {launch_front_path.parent.as_posix()} && ' 'BROWSER=none timeout 15 npm run dev -- --debug 2>&1')
            else:
                content_info = {
                    "sub_content": f"Frontend run server",
                    "role_task": self.config.role_task,
                    "agent_role": self.config.current_role,
                    "mission": self.config.user_intend
                }
                oh_action_data['action_type'] = "MESSAGE"
                oh_action_data['content'] = content_info
                oh_action_data['conversation_id'] = self.context.config.sid
                logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")

                oh_action_data = {}
                oh_action_data['message'] = f"frontend run server"
                oh_action_data['action_type'] = "CMD_RUN"
                oh_action_data['cmd'] = 'cd ' + extract_file_path(self.context.config.sid, launch_front_path.parent.as_posix()) + " ; " + 'BROWSER=none timeout 10 npm run dev -- --port $APP_PORT_1' # add vue@3.4.20
                oh_action_data['handle_output'] = True
                oh_action_data['conversation_id'] = self.context.config.sid
                logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
                print(f"##### front run server data: {oh_action_data}")
                frontend_launch_result = get_msg_for_recv(self.context.config.sio, self.context.config.sid)
                print("\n=====================frontend install dependencies===============\n:",result)
            context = await self.check_failed_cases(frontend_launch_result)
            if context.launch_success == False:
                return context
            self.i_context.launch_front_success = True

        # # build前端文件
        # if self.i_context.build_front_success == False:
        #     logger.info("\n======FRONTEND  ----> BUILD SERVER=============\n")
        #     #frontend_build_result = run_subprocess_cmd(f'cd {launch_front_path.parent.as_posix()} && ' 'npm run build')
        #     oh_action_data = {}
        #     content_info = {
        #         "sub_content": f"Frontend build server",
        #         "role_task": self.config.role_task,
        #         "agent_role": self.config.current_role,
        #         "mission": self.config.user_intend
        #     }
        #     oh_action_data['action_type'] = "MESSAGE"
        #     oh_action_data['content'] = content_info
        #     oh_action_data['conversation_id'] = self.context.config.sid
        #     logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #     #print(f"!!!!!workspace: {oh_action_data}")

        #     oh_action_data = {}
        #     oh_action_data['message'] = f"frontend build server"
        #     oh_action_data['action_type'] = "CMD_RUN"
        #     oh_action_data['cmd'] = 'cd ' + extract_file_path(self.context.config.sid, launch_front_path.parent.as_posix()) + ' && ' + ' npm run build'
        #     oh_action_data['handle_output'] = True
        #     oh_action_data['conversation_id'] = self.context.config.sid
        #     logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

        #     if not self.config.local:
        #         frontend_build_result = get_msg_for_recv(self.context.config.sio, self.context.config.sid)
        #         print("\n=====================frontend build server===============\n:",frontend_build_result)
        #     else:
        #         frontend_build_result = run_subprocess_cmd(f'cd {launch_front_path.parent.as_posix()} && ' 'npm run build')

        #     context = await self.check_failed_cases(frontend_build_result)
        #     if context.launch_success == False:
        #         return context
        #     self.i_context.build_front_success = True

        # 安装python环境依赖
        if self.i_context.backend_dependency == False:
            logger.info("\n======INSTALL BACKEND DEPENDENCIES=============\n")
            #result = run_subprocess_cmd('cd ' + project_path + '\n' +
            #    'source ./venv_test/bin/activate\n'+ 'cd '+ launch_requirements_path.parent.as_posix() + '\n'+ 'pip install -r requirements.txt\n'
            #    + 'pip install playwright\n' + 'playwright install\n')
            oh_action_data = {}
            content_info = {
                "sub_content": f"Install backend dependencies",
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
            oh_action_data['message'] = f"install backend dependencies"
            oh_action_data['action_type'] = "CMD_RUN"
            oh_action_data['cmd'] = 'cd ' + extract_file_path(self.context.config.sid, project_path) + " ; " + '. ./venv_test/bin/activate' + " ; "+ 'cd '+ extract_file_path(self.context.config.sid, launch_requirements_path.parent.as_posix()) + " ; " + 'pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple' + " ; "  + 'pip install playwright -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple'
            oh_action_data['handle_output'] = True
            oh_action_data['conversation_id'] = self.context.config.sid
            logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
 
            if not self.config.local:
                result = get_msg_for_recv(self.context.config.sio, self.context.config.sid)
                print("\n=====================install backend dependencies===============\n:",result)
            else:
                result = run_subprocess_cmd('cd ' + project_path + '\n' +
                'source ./venv_test/bin/activate\n'+ 'cd '+ launch_requirements_path.parent.as_posix() + '\n'+ 'pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple\n'
                + 'pip install playwright -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple\n')
            
            context = await self.check_failed_cases(result)
            if context.launch_success == False:
                return context
            self.i_context.backend_dependency = True

        # 运行python后端程序
        logger.info("\n======LAUNCH BACKEND SERVER=============\n")
        ##result = run_subprocess_cmd('cd ' + project_path + '\n' + 'source ./venv_test/bin/activate\n'+ 'cd '+  launch_backend_path.parent.as_posix() + '\n'+'timeout 10 uvicorn main:app --reload --port 8002 --log-level trace\n')
        #result = run_subprocess_cmd('source ./venv_test/bin/activate\n'+ 'cd '+  project_src_dir + '\n'+'timeout 10 uvicorn main:app --reload --port 8002 --log-level trace\n')
        oh_action_data = {}
        content_info = {
            "sub_content": f"Launch backend server",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.context.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data, ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        oh_action_data = {}
        oh_action_data['message'] = f"launch backend server"
        oh_action_data['action_type'] = "CMD_RUN"
        oh_action_data['cmd'] = 'cd '+ extract_file_path(self.context.config.sid, project_path)  + " ; " + '. ./venv_test/bin/activate' + " ; " + 'cd '+  extract_file_path(self.context.config.sid, launch_backend_path.parent.as_posix())  + " ; " +'timeout 10 uvicorn main:app --reload --port $APP_PORT_2 --log-level trace\n'
        oh_action_data['handle_output'] = True
        oh_action_data['conversation_id'] = self.context.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

        sleep(5)

        #wait_for_msg_continue()
        if not self.config.local:
            result = get_msg_for_recv(self.context.config.sio, self.context.config.sid) #get_msg_for_recv()
        else:
            result = run_subprocess_cmd('cd ' + project_path + '\n' + 'source ./venv_test/bin/activate\n'+ 'cd '+  launch_backend_path.parent.as_posix() + '\n'+'timeout 10 uvicorn main:app --reload --port 8002 --log-level trace\n')

        print("\n=====================Launch result===============\n:",result)
        context = await self.check_failed_cases(result)
        return context
