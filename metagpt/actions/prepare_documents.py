#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/11/20
@Author  : mashenquan
@File    : prepare_documents.py
@Desc: PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt.
        RFC 135 2.2.3.5.1.
"""
import shutil
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.const import REQUIREMENT_FILENAME
from metagpt.utils.file_repository import FileRepository
from metagpt.utils.git_repository import GitRepository
from metagpt.utils.project_repo import ProjectRepo
import json
from metagpt.logs import logger


class PrepareDocuments(Action):
    """PrepareDocuments Action: initialize project folder and add new requirements to docs/requirements.txt."""

    name: str = "PrepareDocuments"
    i_context: Optional[str] = None

    @property
    def config(self):
        return self.context.config

    def _init_repo(self):
        """Initialize the Git environment."""
        if not self.config.project_path:
            name = self.config.project_name or FileRepository.new_filename()
            self.config.workspace.path = Path(self.config.workspace.path) / self.config.sid
            path = Path(self.config.workspace.path)
            path = path /name
        else:
            path = Path(self.config.project_path)
        if path.exists() and not self.config.inc:
            shutil.rmtree(path)
        self.config.project_path = path

        self.context.git_repo = GitRepository(local_path=path, auto_init=True, sid=self.config.sid, local=self.config.local,
                                               sio = self.context.config.sio, current_role =self.config.current_role, 
                                               role_task = self.config.role_task, user_intend=self.config.user_intend)
        self.context.repo = ProjectRepo(self.context.git_repo, local=self.config.local)


    async def run(self, with_messages, **kwargs):

        self.config.current_role = f"PRODUCT_MANAGER"
        self.config.role_task = f"1/2 Prepare documents"

        """Create and initialize the workspace folder, initialize the Git environment."""
        self._init_repo()

        oh_action_data = {}
        content_info = {
            "sub_content": f"Start writing {REQUIREMENT_FILENAME}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        # Write the newly added requirements from the main parameter idea to `docs/requirement.txt`.
        doc = await self.repo.docs.save(filename=REQUIREMENT_FILENAME, content=with_messages[0].content, current_role = self.config.current_role, role_task = self.config.role_task, sid =self.config.sid, user_intend=self.config.user_intend)
        # Send a Message notification to the WritePRD action, instructing it to process requirements using
        # `docs/requirement.txt` and `docs/prd/`.
        return ActionOutput(content=doc.content, instruct_content=doc)
