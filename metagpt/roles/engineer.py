from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Optional, Set, List
import re
from collections import deque
from metagpt.actions import Action, WriteCode, WriteCodeReview, WriteTasks
from metagpt.actions.fix_bug import FixBug
from metagpt.actions.fix_integration_bug import FixIntegrationBug
from metagpt.actions.project_management_an import REFINED_TASK_LIST, TASK_LIST, FILE_RELATION, FRONTEND_FILES
from metagpt.actions.design_api_an import FILE_LIST
from metagpt.actions.summarize_code import SummarizeCode
from metagpt.actions.write_code_plan_and_change_an import WriteCodePlanAndChange
from metagpt.actions.write_bug_fix_plan_and_change import WriteBugFixPlanAndChange
from metagpt.actions import  LaunchProjectTest
from metagpt.actions import  LaunchIntegrationTest
from metagpt.actions.launch_project_test_an import REQUIRES_FILES, ERROR_PRONE_FILES
from metagpt.utils.action_utils import check_frontend_files, check_backend_files, check_files

from metagpt.const import (
    BUGFIX_FILENAME,
    CODE_PLAN_AND_CHANGE_FILE_REPO,
    REQUIREMENT_FILENAME,
    SYSTEM_DESIGN_FILE_REPO,
    TASK_FILE_REPO,
    PRD_FILENAME,
    CODEDESIGN_FILENAME,
    TASK_FILENAME,
    DESIGN_FILENAME,
    CODE_PLAN_FILENAME,
    TESTCASE_FILENAME
)
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import (
    CodePlanAndChangeContext,
    CodeSummarizeContext,
    CodingContext,
    Document,
    Documents,
    Message,

)
from metagpt.utils.common import any_to_name, any_to_str, any_to_str_set
from metagpt.utils.project_setting import merge_json_string, get_project_setting
from pathspec import PathSpec

IS_PASS_PROMPT = """
{context}

----
Does the above log indicate anything that needs to be done?
If there are any tasks to be completed, please answer 'NO' along with the to-do list in JSON format;
otherwise, answer 'YES' in JSON format.
"""


class Engineer(Role):
    """
    Represents an Engineer role responsible for writing and possibly reviewing code.

    Attributes:
        name (str): Name of the engineer.
        profile (str): Role profile, default is 'Engineer'.
        goal (str): Goal of the engineer.
        constraints (str): Constraints for the engineer.
        n_borg (int): Number of borgs.
        use_code_review (bool): Whether to use code review.
    """

    name: str = "Alex"
    profile: str = "Engineer"
    goal: str = "write elegant, readable, extensible, efficient code"
    constraints: str = (
        "the code should conform to standards like google-style and be modular and maintainable. "
        "Use same language as user requirement"
    )
    n_borg: int = 1
    use_code_review: bool = False
    code_todos: list = []
    summarize_todos: list = []
    next_todo_action: str = ""
    n_summarize: int = 0

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.set_actions([WriteCode])
        self._watch([WriteTasks, WriteCode, WriteCodeReview, WriteCodePlanAndChange,WriteBugFixPlanAndChange,LaunchIntegrationTest])
        self.code_todos = []
        self.summarize_todos = []
        self.next_todo_action = any_to_name(WriteCode)

    async def _think(self) -> Action | None:
        if not self.src_workspace:
            self.src_workspace = self.git_repo.workdir / self.git_repo.workdir.name
        logger.info("Alex Engineer _think invoked")
        write_code_filters = any_to_str_set([WriteTasks, WriteCodePlanAndChange])
        write_bugfix_code_filters = any_to_str_set([WriteBugFixPlanAndChange])
        summarize_code_filters = any_to_str_set([WriteCode, WriteCodeReview])
        launch_bug_fix_filters = any_to_str_set([LaunchProjectTest])
        launch_integration_test_filters = any_to_str_set([LaunchIntegrationTest])
        if not self.rc.news:
            return None
        
        logger.info("Alex Engineer {self.rc.news}")
        msg = self.rc.news[0]
        if msg.cause_by in write_code_filters:
            await self._new_code_actions()
            return self.rc.todo
        if msg.cause_by in summarize_code_filters and msg.sent_from == any_to_str(self):
            await self._new_summarize_actions()
            return self.rc.todo
        if msg.cause_by in write_bugfix_code_filters:
            await self._bugfix_code_actions()
            return self.rc.todo
        if msg.cause_by in launch_bug_fix_filters and msg.send_to.pop() == self.name:
            await self._bugfix_code_actions()
            return self.rc.todo
        if msg.cause_by in launch_integration_test_filters and msg.send_to.pop() == self.name:
            await self._bugfix_integration_code_actions()
            return self.rc.todo
        return None
    

    async def _act(self) -> Message | None:
        """Determines the mode of action based on whether code review is used."""
        if self.rc.todo is None:
            return None
        if isinstance(self.rc.todo, WriteCode):
            return await self._act_write_code()
        if isinstance(self.rc.todo, SummarizeCode):
            return await self._act_summarize()
        if isinstance(self.rc.todo, FixBug):
            return await self._act_fixbug()
        if isinstance(self.todo, FixIntegrationBug):
            return await self._act_fix_integration_bug()
        return None
    
    async def _act_sp_with_cr(self, review=False) -> Set[str]:
        changed_files = set()
        for todo in self.code_todos:
            """
            # Select essential information from the historical data to reduce the length of the prompt (summarized from human experience):
            1. All from Architect
            2. All from ProjectManager
            3. Do we need other codes (currently needed)?
            TODO: The goal is not to need it. After clear task decomposition, based on the design idea, you should be able to write a single file without needing other codes. If you can't, it means you need a clearer definition. This is the key to writing longer code.
            """
            coding_context = await todo.run()
            if review:
                coding_context.playwright_code_doc = await self.project_repo.tests.get(filename=f"system_test_playwright_code.py")
                action = WriteCodeReview(i_context=coding_context, context=self.context, llm=self.llm)
                self._init_action(action)
                coding_context = await action.run()
            
            dependencies = {coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path}
            if self.config.inc:
                dependencies.add(coding_context.code_plan_and_change_doc.root_relative_path)

            await self._save_coding_context(coding_context, dependencies)
            logger.info(f"The tagget file to be written is {coding_context.filename}")
            msg = Message(
                content=coding_context.model_dump_json(),
                instruct_content=coding_context,
                role=self.profile,
                cause_by=WriteCode,
            )
            self.rc.memory.add(msg)

            changed_files.add(coding_context.code_doc.filename)
        if not changed_files:
            logger.info("Nothing has changed.")
        return changed_files

    async def _act_write_code(self):
        changed_files = await self._act_sp_with_cr(review=self.use_code_review)
        return Message(
            content="\n".join(changed_files),
            role=self.profile,
            cause_by=WriteCodeReview if self.use_code_review else WriteCode,
            send_to=self,
            sent_from=self,
        )

    async def _act_summarize(self):

        return Message(
                content="",
                role=self.profile,
                cause_by=SummarizeCode,
                sent_from=self,
                #send_to="Edward",  # The name of QaEngineer
                send_to="SysEdward",  # The name of QaEngineer
                #SysEdward
        )



        # tasks = []
        # for todo in self.summarize_todos:
        #     summary = await todo.run()
        #     summary_filename = Path(todo.i_context.design_filename).with_suffix(".md").name
        #     dependencies = {todo.i_context.design_filename, todo.i_context.task_filename}
        #     for filename in todo.i_context.codes_filenames:
        #         rpath = self.project_repo.src_relative_path / filename
        #         dependencies.add(str(rpath))
        #     await self.project_repo.resources.code_summary.save(
        #         filename=summary_filename, content=summary, dependencies=dependencies
        #     )
        #     is_pass, reason = await self._is_pass(summary)
        #     if not is_pass:
        #         todo.i_context.reason = reason
        #         tasks.append(todo.i_context.model_dump())

        #         await self.project_repo.docs.code_summary.save(
        #             filename=Path(todo.i_context.design_filename).name,
        #             content=todo.i_context.model_dump_json(),
        #             dependencies=dependencies,
        #         )
        #     else:
        #         await self.project_repo.docs.code_summary.delete(filename=Path(todo.i_context.design_filename).name)

        # logger.info(f"--max-auto-summarize-code={self.config.max_auto_summarize_code}")
        # if not tasks or self.config.max_auto_summarize_code == 0:
        #     return Message(
        #         content="",
        #         role=self.profile,
        #         cause_by=SummarizeCode,
        #         sent_from=self,
        #         #send_to="Edward",  # The name of QaEngineer
        #         send_to="SysEdward",  # The name of QaEngineer
        #         #SysEdward
        #     )
        # # The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating unlimited.
        # # This parameter is used for debugging the workflow.
        # self.n_summarize += 1 if self.config.max_auto_summarize_code > self.n_summarize else 0
        # return Message(
        #     content=json.dumps(tasks), role=self.profile, cause_by=SummarizeCode, send_to=self, sent_from=self
        # )

    async def _act_fixbug(self):
        changed_files = set()
        for todo in self.fixbug_todos:
            coding_context = await todo.run()
            dependencies = {coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path}
            await self._save_coding_context(coding_context=coding_context, dependencies=dependencies)
            msg = Message(
                    content=coding_context.model_dump_json(),
                    instruct_content=coding_context,
                    role=self.profile,
                    cause_by=FixIntegrationBug,
                )
            self.rc.memory.add(msg)
            changed_files.add(coding_context.code_doc.filename)
            await self.project_repo.srcs.save(
                filename=coding_context.filename,
                dependencies=list(dependencies),
                content=coding_context.code_doc.content,
                current_role=self.config.current_role,
                role_task=self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend
                )
            msg = Message(
                    content=coding_context.model_dump_json(),
                    instruct_content=coding_context,
                    role=self.profile,
                    cause_by=FixBug,
                )
            self.rc.memory.add(msg)
            changed_files.add(coding_context.code_doc.filename)
        return Message(
            content="\n".join(changed_files),
            role=self.profile,
            cause_by=FixBug,
            send_to="SysEdward",
            sent_from=self,
        )
    async def _act_fix_integration_bug(self):
        changed_files = set()
        for todo in self.fixbug_todos:
            coding_context = await todo.run()
            dependencies = {coding_context.design_doc.root_relative_path, coding_context.task_doc.root_relative_path}
            await self._save_coding_context(coding_context=coding_context, dependencies=dependencies)
            msg = Message(
                    content=coding_context.model_dump_json(),
                    instruct_content=coding_context,
                    role=self.profile,
                    cause_by=FixIntegrationBug,
                )
            self.rc.memory.add(msg)
            changed_files.add(coding_context.code_doc.filename)
        return Message(
            content="\n".join(changed_files),
            role=self.profile,
            cause_by=FixIntegrationBug,
            send_to="SysEdward",
            sent_from=self,
        )
    
    async def _is_pass(self, summary):
        rsp = await self.llm.aask(msg=IS_PASS_PROMPT.format(context=summary), stream=False)
        logger.info(rsp)
        if "YES" in rsp:
            return True, rsp
        return False, rsp



    async def _new_coding_context(self, filename, dependency) -> CodingContext:
        old_code_doc = await self.project_repo.srcs.get(filename)
        if not old_code_doc:
            old_code_doc = Document(root_path=str(self.project_repo.src_relative_path), filename=filename, content="")
        dependencies = {Path(i) for i in await dependency.get(old_code_doc.root_relative_path)}
        task_doc = None
        design_doc = None
        code_plan_and_change_doc = await self._get_any_code_plan_and_change() if await self._is_fixbug() else None
        for i in dependencies:
            if str(i.parent.as_posix()) == TASK_FILE_REPO:
                task_doc = await self.project_repo.docs.task.get(i.name)
            elif str(i.parent.as_posix()) == SYSTEM_DESIGN_FILE_REPO:
                design_doc = await self.project_repo.docs.system_design.get(i.name)
            elif str(i.parent.as_posix()) == CODE_PLAN_AND_CHANGE_FILE_REPO:
                code_plan_and_change_doc = await self.project_repo.docs.code_plan_and_change.get(i.name)
        if not task_doc or not design_doc:
            logger.error(f'Detected source code "{filename}" from an unknown origin.')
            raise ValueError(f'Detected source code "{filename}" from an unknown origin.')
        context = CodingContext(
            filename=filename,
            design_doc=design_doc,
            task_doc=task_doc,
            code_doc=old_code_doc,
            code_plan_and_change_doc=code_plan_and_change_doc,
        )
        return context

    async def _new_coding_doc(self, filename, dependency):
        context = await self._new_coding_context(filename, dependency)
        coding_doc = Document(
            root_path=str(self.project_repo.src_relative_path), filename=filename, content=context.model_dump_json()
        )
        return coding_doc

    async def _bugfix_code_actions(self):
        changed_task_files = self.project_repo.docs.task.all_files
        bugfix_doc = await self.project_repo.docs.get(BUGFIX_FILENAME)
        code_design = await self.project_repo.docs.code_design.get(CODEDESIGN_FILENAME)
        system_desgin = await self.project_repo.docs.system_design.get(DESIGN_FILENAME)
    
        design_doc = Document(content=merge_json_string(code_design.content, system_desgin.content), filename=DESIGN_FILENAME, root_path=code_design.root_path) 
        # project_setting = get_project_setting(self.config.project)
        # design_project_setting_doc = Document(content=merge_json_string(design_doc, project_setting), filename=filename, root_path=code_design.root_path) 
        task_doc = await self.project_repo.docs.task.get(TASK_FILENAME)
        error_files = await self.get_json_value(bugfix_doc.content, ERROR_PRONE_FILES, [])
        prd_doc = await self.project_repo.docs.prd.get(PRD_FILENAME)
        # error_files = await self.sort_error_prone_files(error_files)
        require_files = await self.get_json_value(bugfix_doc.content, REQUIRES_FILES, [])
        file_list = self.list_files_and_filter(self.context.repo.srcs.workdir)

        # file_list = self._parse_files(code_design)
        # bug_files = await self.merge_bug_list(error_files, require_files, file_list)
        # merge_lists = lambda a, b: list(dict.fromkeys(a + [x for x in b if x not in a]))
        bug_files = await self.merge_lists(require_files, error_files)
        bug_files = check_files(bug_files)

        changed_files = Documents()
        for filename, desc in bug_files:
            if "." not in os.path.basename(filename):
                continue
            context = CodingContext(filename=filename,
                                    design_doc=design_doc,
                                    prd_doc=prd_doc,
                                    task_doc=task_doc,
                                    bugfix_doc=bugfix_doc,
                                    file_list=file_list,
                                    bugfile_list=bug_files,
                                    fix_file_desc=desc)
            coding_doc = Document(
                    root_path=str(self.project_repo.src_relative_path),
                    filename=filename,
                    content=context.model_dump_json(),
                )
            changed_files.docs[filename] = coding_doc

        self.fixbug_todos = [
            FixBug(i_context=i, context=self.context, llm=self.llm) for i in changed_files.docs.values()
        ]

        if self.fixbug_todos:
            self.set_todo(self.fixbug_todos[0])

    async def _bugfix_integration_code_actions(self):
        
        bugfix_doc = await self.project_repo.docs.get(BUGFIX_FILENAME)
        code_design = await self.project_repo.docs.code_design.get(CODEDESIGN_FILENAME)
        system_desgin = await self.project_repo.docs.system_design.get(DESIGN_FILENAME)
        design_doc = Document(content=merge_json_string(code_design.content, system_desgin.content), filename=CODE_PLAN_FILENAME, root_path=code_design.root_path) 
        # project_setting = get_project_setting(self.config.project)
        # design_project_setting_doc = Document(content=merge_json_string(design_doc, project_setting), filename=filename, root_path=code_design.root_path) 
        task_doc = await self.project_repo.docs.task.get(TASK_FILENAME)
        error_files = await self.get_json_value(bugfix_doc.content, ERROR_PRONE_FILES, [])
        prd_doc = await self.project_repo.docs.prd.get(PRD_FILENAME)
        # error_files = await self.sort_error_prone_files(error_files)
        require_files = await self.get_json_value(bugfix_doc.content, REQUIRES_FILES, [])
        file_list = self.list_files_and_filter(self.context.repo.srcs.workdir)
        # bug_files = await self.merge_bug_list(error_files, require_files, file_list)
        # merge_lists = lambda a, b: list(dict.fromkeys(a + [x for x in b if x not in a]))
        bug_files = await self.merge_lists(require_files, error_files)
        bug_files = check_files(bug_files)
        # bug_files = list(set(bug_files))
        
        changed_files = Documents()
        for filename, desc in bug_files:
            if "." not in os.path.basename(filename):
                continue
            if "dist/" in filename:
                continue
            context = CodingContext(filename=filename,
                                    design_doc=design_doc,
                                    task_doc=task_doc,
                                    prd_doc=prd_doc,
                                    bugfix_doc=bugfix_doc,
                                    file_list=file_list,
                                    bugfile_list=bug_files,
                                    fix_file_desc=desc
                                    )
            coding_doc = Document(
                    root_path=str(self.project_repo.src_relative_path),
                    filename=filename,
                    content=context.model_dump_json(),
                )
            changed_files.docs[filename] = coding_doc

        self.fixbug_todos = [
            FixIntegrationBug(i_context=i, context=self.context, llm=self.llm) for i in changed_files.docs.values()
        ]

        if self.fixbug_todos:
            self.set_todo(self.fixbug_todos[0])

    async def _new_code_actions(self):
        bug_fix = await self._is_fixbug()
        # Prepare file repos
        changed_files = Documents()
        # Recode caused by upstream changes.
        code_design = await self.project_repo.docs.code_design.get(CODEDESIGN_FILENAME)
        system_desgin = await self.project_repo.docs.system_design.get(DESIGN_FILENAME)
        design_doc = Document(content=merge_json_string(code_design.content, system_desgin.content), filename=DESIGN_FILENAME, root_path=code_design.root_path) 
        # project_setting = get_project_setting(self.config.project)
        # design_project_setting_doc = Document(content=merge_json_string(design_doc, project_setting), filename=filename, root_path=code_design.root_path) 
        task_doc = await self.project_repo.docs.task.get(TASK_FILENAME)
        prd_doc = await self.project_repo.docs.prd.get(PRD_FILENAME)
        code_plan_and_change_doc = await self.project_repo.docs.code_plan_and_change.get(CODE_PLAN_FILENAME)
        testcase_doc = await self.project_repo.docs.testcase.get(TESTCASE_FILENAME)
        file_relation = self._parse_relation(task_doc)
        file_list = self._parse_files(code_design)
        # task_list = self._parse_tasks(task_doc)
        sorted_task_list = self._sort_tasks(file_list, file_relation)
        logger.info(f"Will write file..: {str(sorted_task_list)}")
        for task_filename, desc in sorted_task_list:
            _, file_extension = os.path.splitext(task_filename)
            if not file_extension:
                continue
            # old_code_doc = await self.project_repo.srcs.get(task_filename)
            # if not old_code_doc:
            old_code_doc = Document(
                root_path=str(self.project_repo.src_relative_path), filename=task_filename, content=""
            )
            # if not code_plan_and_change_doc:
            #     context = CodingContext(
            #         filename=task_filename, design_doc=design_doc, task_doc=task_doc, code_doc=old_code_doc
            #     )
            # else:
            context = CodingContext(
                filename=task_filename,
                prd_doc=prd_doc,
                design_doc=design_doc,
                testcase_doc=testcase_doc,
                task_doc=task_doc,
                code_doc=old_code_doc,
                code_plan_and_change_doc=code_plan_and_change_doc,
                fix_file_desc=desc,
                file_list=[x for x, y in file_list]
            )
            coding_doc = Document(
                root_path=str(self.project_repo.src_relative_path),
                filename=task_filename,
                content=context.model_dump_json(),
            )
            if task_filename in changed_files.docs:
                logger.warning(
                    f"Log to expose potential conflicts: {coding_doc.model_dump_json()} & "
                    f"{changed_files.docs[task_filename].model_dump_json()}"
                )
            changed_files.docs[task_filename] = coding_doc

        self.code_todos = [
            WriteCode(i_context=i, context=self.context, llm=self.llm) for i in changed_files.docs.values()
        ]

        if self.code_todos:
            self.set_todo(self.code_todos[0])

    async def _new_summarize_actions(self):
        src_files = self.project_repo.srcs.all_files
        # Generate a SummarizeCode action for each pair of (system_design_doc, task_doc).
        summarizations = defaultdict(list)
        for filename in src_files:
            dependencies = await self.project_repo.srcs.get_dependency(filename=filename)
            ctx = CodeSummarizeContext.loads(filenames=list(dependencies))
            summarizations[ctx].append(filename)
        for ctx, filenames in summarizations.items():
            ctx.codes_filenames = filenames
            new_summarize = SummarizeCode(i_context=ctx, context=self.context, llm=self.llm)
            for i, act in enumerate(self.summarize_todos):
                if act.i_context.task_filename == new_summarize.i_context.task_filename:
                    self.summarize_todos[i] = new_summarize
                    new_summarize = None
                    break
            if new_summarize:
                self.summarize_todos.append(new_summarize)
        if self.summarize_todos:
            self.set_todo(self.summarize_todos[0])
            self.summarize_todos.pop(0)

    @property
    def action_description(self) -> str:
        """AgentStore uses this attribute to display to the user what actions the current role should take."""
        return self.next_todo_action

    async def _is_fixbug(self) -> bool:
        fixbug_doc = await self.project_repo.docs.get(BUGFIX_FILENAME)
        return bool(fixbug_doc and fixbug_doc.content)

    async def get_json_value(self, json_str, key_desc, return_des = ""):
        data = json.loads(json_str)
        return data.get(key_desc.key, return_des)

    @staticmethod
    def _parse_tasks(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get(TASK_LIST.key) or m.get(REFINED_TASK_LIST.key)

    @staticmethod
    def _parse_relation(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get(FILE_RELATION.key) or m.get(FILE_RELATION.key)

    @staticmethod
    def _parse_files(task_msg: Document) -> list[str]:
        m = json.loads(task_msg.content)
        return m.get(FILE_LIST.key) or m.get(FILE_LIST.key)

    @staticmethod
    def _sort_tasks(task_list, file_dependencies):
        # 检查并补充a中存在但b中没有的文件
        file_desc_dict = {x: y for x, y in task_list}
        task_list = [x for x, y in task_list]
        all_files_in_a = set([f for sublist in file_dependencies for f in [sublist[0]] + sublist[1]])
        missing_files = all_files_in_a - set(task_list)
        task_list = task_list + list(missing_files)

        # 补充缺失的文件到 file_dependencies
        existing_files = set([file for file, _ in file_dependencies])
        for task in task_list:
            if task not in existing_files:
                file_dependencies.append((task, []))

        # 构建依赖图
        dependency_graph = {file: deps for file, deps in file_dependencies}

        # 函数用于递归查找所有依赖
        def find_all_dependencies(file, graph, visited=None):
            if visited is None:
                visited = set()
            if file in visited:
                return set()  # 检测到循环依赖，终止递归
            visited.add(file)
            all_deps = set()
            for dep in graph.get(file, []):
                all_deps.add(dep)
                all_deps.update(find_all_dependencies(dep, graph, visited))
            return all_deps

        # 扩充依赖关系
        expanded_dependency_graph = {}
        for file in dependency_graph:
            expanded_dependency_graph[file] = list(find_all_dependencies(file, dependency_graph))

        # 计算入度
        in_degree = {file: len(expanded_dependency_graph.get(file, [])) for file in task_list}  # 确保所有任务列表中的文件都有入度

        queue = [file for file, degree in in_degree.items() if degree == 0]
        sorted_files = []
        try:
            while queue:
                file = queue.pop(0)
                sorted_files.append([file, file_desc_dict.get(file, "")])
                for dependent, deps in expanded_dependency_graph.items():
                    if file in deps:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)
        except Exception as e:
            print(f"拓扑排序过程中发生错误: {e}")
            sorted_files = [[x, y] for x, y in file_desc_dict.items()]

        # 确保所有文件都在排序结果中
        for file in task_list:
            if file not in [x for x, y in sorted_files]:
                sorted_files.append([file, file_desc_dict.get(file, "")])
        sorted_files = check_frontend_files(sorted_files)
        sorted_files = check_backend_files(sorted_files)
        return sorted_files
            

    @staticmethod
    def _remove_comment(text):
        # 定义匹配 """xxx""" 格式注释的正则表达式
        pattern = r'""".*?"""'
        # 使用 re.DOTALL 标志使 . 可以匹配包括换行符在内的任意字符
        text = re.sub(pattern, '', text, flags=re.DOTALL).strip()
        return text
    
    async def _save_coding_context(self, coding_context, dependencies):
        if  "requirements.txt" in coding_context.filename:
                coding_context.filename = coding_context.filename.split("/")[-1]
                await self.project_repo.srcs.save(
                filename=coding_context.filename,
                dependencies=list(dependencies),
                content=self._remove_comment(coding_context.code_doc.content) if coding_context.code_doc.content.startswith('"""') else coding_context.code_doc.content,
                current_role = self.config.current_role,
                role_task=self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend                
                )
        elif coding_context.filename == "tests/system_test_playwright_code.py":
                await self.project_repo.tests.save(
                filename="system_test_playwright_code.py",
                dependencies=list(dependencies),
                content=coding_context.code_doc.content,
                current_role = self.config.current_role,
                role_task = self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend
                )                
        else:
            await self.project_repo.srcs.save(
            filename=coding_context.filename,
            dependencies=list(dependencies),
            content=coding_context.code_doc.content,
            current_role = self.config.current_role,
            role_task = self.config.role_task,
            sid = self.config.sid,
            user_intend=self.config.user_intend
            )
    async def sort_error_prone_files(self, error_prone_files: List[str]) -> List[str]:
        """
        对错误易发生文件列表进行排序，顺序为：前端相关文件、后端相关文件、Playwright 相关文件
        """
        front_end_files = []
        back_end_files = []
        playwright_files = []
        other_files = []

        for file, desc in error_prone_files:
            if file.endswith(('.html', '.css', '.js', '.ts', '.vue')):
                front_end_files.append(file)
            elif file.endswith(('.py')):
                if 'playwright' in file.lower():
                    playwright_files.append(file)
                else:
                    back_end_files.append(file)
            else:
                other_files.append(file)

        # 将 main 文件移动到 back_end_files 末尾
        main_files_in_backend = [file for file in back_end_files if file.lower().endswith('main.py')]
        other_backend_files = [file for file in back_end_files if not file.lower().endswith('main.py')]
        back_end_files = other_backend_files + main_files_in_backend
        
        return other_files + front_end_files + back_end_files + playwright_files
    
    async def merge_bug_list(self, error_pron_files, require_files, file_list):
        def _is_path_dependent(path1, path2):
            """
            判断两个路径是否存在依赖关系（一个路径是另一个路径的子路径）
            :param path1: 第一个文件路径
            :param path2: 第二个文件路径
            :return: 如果存在依赖关系返回True，否则返回False
            """
            # 对路径进行简单的标准化处理，去除首尾的斜杠
            path1 = path1.rstrip('/')
            path2 = path2.rstrip('/')
            return path1 in path2 or path2 in path1

        error_list = []
        for file in error_pron_files:
            if file not in error_list:
                error_list.append(file)

        require_list = []
        for file in require_files:
            # 如果文件在 file_list 中，添加到 error_list 中
            if file in file_list:
                if file not in error_list:
                    error_list.append(file)
                continue

            # 检查是否与现有文件有依赖关系
            is_dependent = False
            for existing_file in file_list + error_list + require_list:
                if _is_path_dependent(file, existing_file):
                    is_dependent = True
                    break

            # 如果没有依赖关系，添加到 require_list 中
            if not is_dependent:
                require_list.append(file)

        # 再次检查 require_list 中是否有与 file_list 和 error_list 依赖的文件
        final_require_list = []
        for file in require_list:
            is_dependent = False
            for existing_file in file_list + error_list:
                if _is_path_dependent(file, existing_file):
                    is_dependent = True
                    break
            if not is_dependent:
                final_require_list.append(file)

        return error_list+final_require_list



    async def merge_lists(self, list1, list2):
        result = []
        # 用于存储已经处理过的文件路径
        processed_files = {}
        for sub_list in list1 + list2:
            file_path = sub_list[0]
            description = sub_list[1]
            if file_path in processed_files:
                # 如果文件路径已存在，合并描述
                existing_index = processed_files[file_path]
                result[existing_index][1] += "; " + description
            else:
                # 如果文件路径不存在，添加到结果列表
                result.append(sub_list)
                processed_files[file_path] = len(result) - 1
        return result
    
    @staticmethod
    def list_files_and_filter(directory, filter_patterns = ['.git', 'node_modules', '__pycache__','package-lock.json']):
        # 定义要过滤的目录模式
        # 创建PathSpec对象
        spec = PathSpec.from_lines('gitwildmatch', filter_patterns)
        file_list = []
        # 将PosixPath对象转换为字符串
        directory_str = str(directory)
        root_len = len(directory_str) + len(os.path.sep)  # 计算根目录的长度加上路径分隔符的长度
        # 遍历目录及其子目录下的所有文件
        for root, dirs, files in os.walk(directory_str):
            # 过滤子目录
            dirs[:] = [d for d in dirs if not spec.match_file(os.path.join(root, d))]
            for file in files:
                file_path = os.path.join(root, file)
                if not spec.match_file(file_path):
                    relative_path = file_path[root_len:]  # 提取相对路径
                    file_list.append(relative_path)

        return file_list