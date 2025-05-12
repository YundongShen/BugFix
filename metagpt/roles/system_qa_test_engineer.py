#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2025/2/25 14:43
@Author  : huakunyang
@File    : system_qa_test_engineer.py
"""

import os
import json
from metagpt.actions import WritePlayWrightSystemTestCode,LaunchProjectTest, LaunchIntegrationTest
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.const import MESSAGE_ROUTE_TO_NONE
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Document, Message, SystemTestingContext, SystemTestingPlayWrightCodeContext, LaunchProjectTestingContext,ProjectIntegrationTestingContext, DockerfileContext
from metagpt.utils.common import any_to_str_set, parse_recipient
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.fix_integration_bug import FixIntegrationBug
from metagpt.actions.launch_project_test_an import REQUIRES_FILES, ERROR_PRONE_FILES
from metagpt.actions import Action
from metagpt.actions.write_dockerfile import WriteDockerfile
from metagpt.const import (
    BUGFIX_FILENAME,
    LAUNCH_RESULT,
    PACKAGE_REQUIREMENTS_FILENAME,
    PRDS_FILE_REPO,
    REQUIREMENT_FILENAME,
    TESTCASE_FILENAME,
    PRD_FILENAME,
    CODEDESIGN_FILENAME,
    DOCKERFILE_FILENAME
)
from pathlib import Path

class SystemQaTester(Role):
    name: str = "SysEdward"
    profile: str = "SystemQaTester"
    goal: str = "Create the test case based on PRD and frontend html files to test the functions of all software, and execute the test case after code change"
    constraints: str = (
        ""
    )
    test_round_allowed: int = 5
    test_round: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # FIXME: a bit hack here, only init one action to circumvent _think() logic,
        #  will overwrite _think() in future updates
        #self.set_actions([WriteSystemTestCase, RunSystemTestCase])
        self.set_actions([WritePlayWrightSystemTestCode])
        self._watch([SummarizeCode, FixBug, LaunchProjectTest, FixIntegrationBug, WritePlayWrightSystemTestCode, LaunchIntegrationTest])
        self.test_round = 0
        self.integration_test_started = False
        self.launch_backend_file=""
        self.launch_front_file=""
        self.config.current_role = "System QA Tester"
        self.config.role_task = "Create the testcase baseon PRD and execute the test case."

    async def _write_playwright_system_test_code(self, message: Message) -> None:

        logger.info(f"SystemQaTester _write_playwright_system_test_code Invoked.")
        testcase = await self.project_repo.docs.testcase.get(filename=TESTCASE_FILENAME)
        prd = await self.project_repo.docs.prd.get(filename=PRD_FILENAME)
        
        design = await self.project_repo.docs.code_design.get(filename=CODEDESIGN_FILENAME)
        dep_list = []
        
        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs

        file_list = await self.filter_files(src_file_repo.all_files)
        frontend_extensions = ['.vue', '.js', '.ts', '.css', '.html','.less']
        for file in file_list:
            for ext in frontend_extensions:
                if file.endswith(ext) and "dist" not in file:
                    dep_list.append(file)
            # if code_filename.endswith(".html"):
            #    depList.append(code_filename)
            #    html_contents = html_contents +"html_file: " + code_filename + "\n-----begin-------\n"
            #    code_doc = await src_file_repo.get(code_filename)
            #    html_contents = html_contents + code_doc.content
            #    html_contents = html_contents + "\n-----end-------\n"

            # if code_filename.endswith(".js"):
            #    depList.append(code_filename)
            #    js_contents = js_contents +"javascript_file: " + code_filename + "\n-----begin-------\n"
            #    code_doc = await src_file_repo.get(code_filename)
            #    js_contents = js_contents + code_doc.content
            #    js_contents = js_contents + "\n-----end-------\n"
        code_content = ""
        for filename in dep_list:
            code_str = await src_file_repo.get(filename)
            code_content += f"# Code: {filename}\n ```code\n{code_str.content}```\n"
        system_test_playwright_code = await self.project_repo.tests.get("system_test_playwright_code.py")
        if not system_test_playwright_code:
                system_test_playwright_code = Document(
                    root_path=str(self.project_repo.tests.root_path), filename="system_test_playwright_code.py" , content=""
                )

        context = SystemTestingPlayWrightCodeContext(filename=system_test_playwright_code.filename, 
                                                     prd = prd.content,
                                                     design=design.content,
                                                     frontend_code=code_content,
                                                     sys_test_doc=testcase.content,
                                                     sys_test_playwright_code=system_test_playwright_code)
        
        context = await WritePlayWrightSystemTestCode(i_context=context, context=self.context, llm=self.llm).run()
        await self.project_repo.tests.save_doc(
                doc=context.sys_test_playwright_code, current_role=self.config.current_role, role_task=self.config.role_task,sid = self.config.sid, user_intend=self.config.user_intend)

        self.publish_message(
                Message(
                    content=context.filename,
                    role=self.profile,
                    cause_by=WritePlayWrightSystemTestCode,
                    sent_from=self,
                    send_to=self,
                )
            )

        logger.info(f"Done Playwright system test code generating.")


    async def _do_integration_test(self, message: Message) -> ProjectIntegrationTestingContext:

        logger.info(f"SystemQaTester _do_integration_test Invoked.")

        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs
        
        file_list = await self.filter_files(src_file_repo.all_files)
        integration_test_info = await self.project_repo.tests.get("integration_test_info")
        if not integration_test_info:
                integration_test_info = Document(
                    root_path=str(self.project_repo.tests.root_path), filename="project_integration_test_result" , content=""
                )
        

        logger.info(f"Writing {integration_test_info.filename}..")

        launch_backend_file=str(src_file_repo.workdir)+"/"+ "main.py"
        launch_front_file=str(src_file_repo.workdir) + "/" + "package.json"
        file_list = await self.filter_files(src_file_repo.all_files)
        if not os.path.exists(launch_backend_file):
            launch_backend_file=""
            for code_filename in file_list:
                if "main.py" in code_filename:
                    launch_backend_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break

        if not os.path.exists(launch_front_file):
            launch_front_file = ""
            for code_filename in file_list:
                if "package.json" in code_filename:
                    launch_front_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break 
        context = ProjectIntegrationTestingContext(filename=integration_test_info.filename,
                                                   project_path=str(self.project_repo.workdir), 
                                                   project_src_path=str(src_file_repo.workdir), 
                                                   integration_test_case_file_path = str(self.project_repo.tests.workdir)+"/system_test_playwright_code.py", 
                                                   test_success = False, 
                                                   file_list=file_list,
                                                   launch_backend_file=launch_backend_file,
                                                   launch_front_file=launch_front_file,
                                                   integration_test_result=integration_test_info)

        logger.info(f"Prepare to do LaunchIntegrationTest..")

        context = await LaunchIntegrationTest(i_context=context, context=self.context, llm=self.llm).run()
        if self.config.simulate:
            context.test_success = True

        if context.test_success ==False:
            await self.project_repo.docs.save(filename=BUGFIX_FILENAME, content=context.integration_test_result.content, current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
            logger.info(f"Integartion test failed, send mesaage to Alex for fixing it.")
            await self.project_repo.tests.save_doc(
                doc=context.integration_test_result,
                current_role=self.config.current_role,
                role_task=self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend
            )

        logger.info(f"Done integration test report generating.")

        return context

    async def _launch_project_test(self, message: Message) -> LaunchProjectTestingContext:
        logger.info(f"SystemQaTester _launch_project_test Invoked.")
        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs
        
        launch_backend_file=str(src_file_repo.workdir)+"/"+ "main.py"
        launch_front_file=str(src_file_repo.workdir) + "/" + "package.json"
        launch_requirements_file = str(src_file_repo.workdir.parent) + "/" + "requirements.txt"
        file_list = await self.filter_files(src_file_repo.all_files)
        if not os.path.exists(launch_backend_file):
            launch_backend_file=""
            for code_filename in file_list:
                if "main.py" in code_filename:
                    launch_backend_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break

        if not os.path.exists(launch_front_file):
            launch_front_file = ""
            for code_filename in file_list:
                if "package.json" in code_filename:
                    launch_front_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break 
        
        if not os.path.exists(launch_requirements_file):
            launch_requirements_file = ""
            for code_filename in file_list:
                if "requirements.txt" in code_filename:
                    launch_requirements_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break 
        
        # 赋值后给Intergation测试使用，无需重复检查启动文件
        self.launch_backend_file = launch_backend_file
        self.launch_front_file = launch_front_file

        logger.info(f"Found Front Launching {self.launch_front_file}..")
        logger.info(f"Found Backend Launching {self.launch_backend_file}..")
        project_launch_info = await self.project_repo.tests.get("project_launch_info")
        if not project_launch_info:
                project_launch_info = Document(
                    root_path=str(self.project_repo.tests.root_path), filename="project_launch_analysis" , content=""
                )
        
        logger.info(f"Writing {project_launch_info.filename}..")
        launch_result = await self.project_repo.docs.get(LAUNCH_RESULT)
        bugfix = await self.project_repo.docs.get(BUGFIX_FILENAME)
        context = LaunchProjectTestingContext(filename=project_launch_info.filename,
                                              project_path=str(self.project_repo.workdir), 
                                              project_src_path=str(src_file_repo.workdir), 
                                              launch_front_file=launch_front_file,
                                              launch_backend_file=launch_backend_file, 
                                              launch_requirements_file=launch_requirements_file,
                                              launch_success=False,
                                              launch_front_success=False,
                                              build_front_success=False,
                                              front_dependency=False,
                                              backend_dependency=False, 
                                              file_list=file_list,
                                              launch_result_analysis=project_launch_info)
        if launch_result is not None:
            m = json.loads(launch_result.content)
            context.front_dependency=m.get("front_dependency", False)
            context.backend_dependency=m.get("backend_dependency", False)
            context.launch_front_success = m.get("launch_front_success", False)
            context.build_front_success = m.get("build_front_success", False)

        if bugfix is not None:
            m = json.loads(bugfix.content)
            error_list = m.get(ERROR_PRONE_FILES.key, [])
            require_list = m.get(REQUIRES_FILES.key, [])
            merge_list = error_list+require_list
            for file, desc in merge_list:
                if "requirements.txt" in file:
                    context.backend_dependency = False
                    break
            for file, desc in merge_list:
                if "package.json" in file:
                    context.front_dependency = False
                    context.launch_front_success = False
                    context.build_front_success = False
                    break
            frontend_extensions = ['.vue', '.js', '.ts', '.css', '.html']
            for file, desc in merge_list:
                for ext in frontend_extensions:
                    if file.endswith(ext):
                        context.launch_front_success = False
                        context.build_front_success = False
                        break


        if launch_front_file=="":
            launch_result_analysis_template = {
                "Launch Result": "FAILED",
                "Error Message": "Critical dependency missing: No package.json found in frontend directory. This file is required to define project dependencies and scripts for Node.js applications.",
                "Bugfix Plan": "1. Create a package.json file by running `npm init -y` in the frontend directory\n2. Install required dependencies with `npm install`\n3. Ensure the file contains at least a 'start' script (e.g., \"scripts\": {\"start\": \"vite\"})",
                "Error-Prone Files": [],
                "Requires Files": ["package.json"],
                "Console Output": "[ERROR] Failed to execute command: npm run start"
            }
            context.launch_result_analysis.content = json.dumps(launch_result_analysis_template, ensure_ascii=False)
            logger.info(f"Not find package.json to launch backend, send mesaage to Alex for fixing it.")
            await self.project_repo.docs.save(filename=BUGFIX_FILENAME, content=context.launch_result_analysis.content, current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
            return context

        if launch_backend_file == "":
            launch_result_analysis_template = {
                "Launch Result": "FAILED",
                "Error Message": "Critical application entry point missing: No main.py found in project directory. This file is required as the default FastAPI/uvicorn entry point.",
                "Bugfix Plan": " 1. Create a main.py file with minimal FastAPI content\n2. Verify the file exists in the correct directory\n3. If using a non-standard entry point, specify it explicitly: uvicorn module:app",
                "Error-Prone Files": [],
                "Requires Files": ["main.py"],
                "Console Output": "[Errno 2] No such file or directory: 'main.py, ASGI application 'main:app' could not be found"
            }
            context.launch_result_analysis.content = json.dumps(launch_result_analysis_template, ensure_ascii=False)
            logger.info(f"Not find main.py to launch backend, send mesaage to Alex for fixing it.")
            await self.project_repo.docs.save(filename=BUGFIX_FILENAME, content=context.launch_result_analysis.content, current_role=self.config.current_role,  role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
            return context
        
        logger.info(f"Prepare to do LaunchProjectTest..")
        context = await LaunchProjectTest(i_context=context, context=self.context, llm=self.llm).run()
        if context.launch_success ==False:
            await self.project_repo.docs.save(filename=BUGFIX_FILENAME, content=context.launch_result_analysis.content, current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
            logger.info(f"Project launch failed, send mesaage to Alex for fixing it.")
            await self.project_repo.tests.save_doc(
                doc=context.launch_result_analysis, dependencies=[context.launch_backend_file, context.launch_front_file], current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend
            )

        logger.info(f"Done Launching {launch_backend_file} report generating.")
        await self.project_repo.docs.save(filename=LAUNCH_RESULT, content=context.model_dump_json(),current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        return context

    async def _write_dockerfile(self, message: Message):
        logger.info(f"SystemQaTester _launch_project_test Invoked.")
        src_file_repo = self.project_repo.with_src_path(self.context.src_workspace).srcs
        
        file_list = await self.filter_files(src_file_repo.all_files)
        integration_test_info = await self.project_repo.tests.get("integration_test_info")
        if not integration_test_info:
                integration_test_info = Document(
                    root_path=str(self.project_repo.tests.root_path), filename="project_integration_test_result" , content=""
                )
        

        logger.info(f"Writing {integration_test_info.filename}..")

        launch_backend_file=str(src_file_repo.workdir)+"/"+ "main.py"
        launch_frontend_file=str(src_file_repo.workdir) + "/" + "package.json"
        launch_requirements_file = str(src_file_repo.workdir.parent) + "/" + "requirements.txt"
        file_list = await self.filter_files(src_file_repo.all_files)
        if not os.path.exists(launch_backend_file):
            launch_backend_file=""
            for code_filename in file_list:
                if "main.py" in code_filename:
                    launch_backend_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break

        if not os.path.exists(launch_frontend_file):
            launch_frontend_file = ""
            for code_filename in file_list:
                if "package.json" in code_filename:
                    launch_frontend_file = str(src_file_repo.workdir)+"/"+ code_filename
                    break 
        
        context = DockerfileContext(
            launch_backend_file=launch_backend_file,
            launch_frontend_file=launch_frontend_file,
            launch_requirements_file=launch_requirements_file
        )
        

        frontend_content, backend_content, docker_entrypoint, default_conf = await WriteDockerfile(i_context=context, context=self.context, llm=self.llm).run()
        frontend_dockerfile_path = launch_frontend_file.replace("package.json", "Dockerfile")
        backend_dockerfile_path = launch_backend_file.replace("main.py", "Dockerfile")
        docker_entrypoint_path = launch_frontend_file.replace("package.json", "docker-entrypoint.sh")
        default_conf_path = launch_frontend_file.replace("package.json", "default.conf")
        await self.project_repo.srcs.save(Path(frontend_dockerfile_path).relative_to(src_file_repo.workdir),dependencies=file_list[:2], content=frontend_content,current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        await self.project_repo.srcs.save(Path(backend_dockerfile_path).relative_to(src_file_repo.workdir),dependencies=file_list[:2], content=backend_content,current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        await self.project_repo.srcs.save(Path(docker_entrypoint_path).relative_to(src_file_repo.workdir),dependencies=file_list[:2], content=docker_entrypoint,current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        await self.project_repo.srcs.save(Path(default_conf_path).relative_to(src_file_repo.workdir),dependencies=file_list[:2], content=default_conf,current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
   
        # await self.project_repo.docs.frontend_dockerfile_repo.save(DOCKERFILE_FILENAME, content=frontend_content, current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        # await self.project_repo.docs.backend_dockerfile_repo.save(DOCKERFILE_FILENAME, content=backend_content,current_role=self.config.current_role, role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)

    async def _act(self) -> Message:
        # if self.test_round > self.test_round_allowed:
        #     result_msg = Message(
        #         content=f"Exceeding {self.test_round_allowed} rounds of system tests, skip remains system testing",
        #         role=self.profile,
        #         cause_by=WritePlayWrightSystemTestCode,
        #         sent_from=self.profile,
        #         send_to=MESSAGE_ROUTE_TO_NONE,
        #     )
        #     return result_msg

        code_filters = any_to_str_set({SummarizeCode, FixBug, FixIntegrationBug})
        launch_result_filters = any_to_str_set({LaunchProjectTest})
        playwright_test_filters = any_to_str_set({WritePlayWrightSystemTestCode})
        dockerfile_filters = any_to_str_set({LaunchIntegrationTest})

        for msg in self.rc.news:
            # 如果代码写完了即SummarizeCode，或Bug修复完成FixBug
            if msg.cause_by in code_filters:
                #启动测试
                context:LaunchProjectTestingContext = await self._launch_project_test(msg)

                # 启动测试成功（python环境安装， python后台启动）
                if context.launch_success ==True:
                    
                    # 如果没写过测试用例，此时开始写
                    if self.integration_test_started ==False:
                        await self._write_playwright_system_test_code(msg)
                        self.integration_test_started = True
                    
                    # 发送启动成功消息
                    return Message(
                        content="LAUNCH_SUCCESS",
                        role=self.profile,
                        cause_by=WritePlayWrightSystemTestCode,
                        sent_from=self,
                        send_to=self,
                    )
                # 如果启动失败，发过去FixBug
                else:
                    logger.info(f"Project launch failed, send mesaage to Alex for fixing it.")
                    self.config.inc = True
                    return Message(
                            content=context.launch_result_analysis.content,
                            role=self.profile,
                            cause_by=LaunchProjectTest,
                            sent_from=self,
                            send_to="Alex",
                        )
            elif msg.cause_by in launch_result_filters:
                # project launch result, time to analyze it
                if msg.content == "LAUNCH_SUCCESS":
                    if self.integration_test_started ==False:
                        await self._write_playwright_system_test_code(msg)
                        self.integration_test_started = True
                    if self.integration_test_started:
                        context = await self._do_integration_test(msg)

                        if context.test_success ==False:
                            return Message(
                                content=context.integration_test_result.content,
                                role=self.profile,
                                cause_by=LaunchIntegrationTest,
                                sent_from=self,
                            )
                else:
                    # 这种情况一般是restore，因为engineer那边需要判断是不是发给他的才做fix_action。这边watch这个消息重新做一遍launch_project_test
                    # 在正常流程内，是不会收到这个消息的。
                    context:LaunchProjectTestingContext = await self._launch_project_test(msg)
                    if context.launch_success ==True:
                        if self.integration_test_started ==False:
                            await self._write_playwright_system_test_code(msg)
                            self.integration_test_started = True
                        return Message(
                                content="Do integration test",
                                role=self.profile,
                                cause_by=WritePlayWrightSystemTestCode,
                                sent_from=self,
                                send_to=self,
                            )
                    else:
                        return Message(
                                    content=context.launch_result_analysis.content,
                                    role=self.profile,
                                    cause_by=LaunchProjectTest,
                                    sent_from=self,
                                    send_to="Alex",
                                )
    
            elif msg.cause_by in playwright_test_filters:
                context = await self._do_integration_test(msg)
                if context.test_success:
                    return Message(
                        content=context.integration_test_result.content,
                        role=self.profile,
                        cause_by=LaunchIntegrationTest,
                        sent_from=self,
                        send_to=self
                        )
                else:
                    return Message(
                        content=context.integration_test_result.content,
                        role=self.profile,
                        cause_by=LaunchIntegrationTest,
                        sent_from=self,
                        send_to="Alex"
                        )

            elif msg.cause_by in dockerfile_filters:
                await self._write_dockerfile(msg)

        # # self.test_round += 1
                return Message(
                    content="",
                    role=self.profile,
                    cause_by=DockerfileContext,
                    sent_from=self.profile,
                    send_to=MESSAGE_ROUTE_TO_NONE,
                )

    async def filter_files(self, file_list, exclude_keywords=["node_modules", "lock.json"]):
        """
        过滤掉文件名中包含特定关键词的文件路径
        
        :param file_list: 原始文件路径列表
        :param exclude_keywords: 需要排除的关键词列表
        :return: 过滤后的文件路径列表
        """
        filtered_list = []
        for file_path in file_list:
            # 检查文件路径中是否包含任何排除关键词
            if not any(keyword.lower() in file_path.lower() for keyword in exclude_keywords):
                filtered_list.append(file_path)
        return filtered_list
        

    async def _observe(self, ignore_memory=False) -> int:
        # This role has events that trigger and execute themselves based on conditions, and cannot rely on the
        # content of memory to activate.
        return await super()._observe(ignore_memory=True)
