#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 19:26
@Author  : alexanderwu
@File    : design_api.py
@Modified By: mashenquan, 2023/11/27.
            1. According to Section 2.2.3.1 of RFC 135, replace file data in the message with the file name.
            2. According to the design in Section 2.2.3.5.3 of RFC 135, add incremental iteration functionality.
@Modified By: mashenquan, 2023/12/5. Move the generation logic of the project name to WritePRD.
"""
import json
from pathlib import Path
from typing import Optional

from metagpt.actions import Action, ActionOutput
from metagpt.actions.design_api_an import (
    DATA_STRUCTURES_AND_INTERFACES,
    DESIGN_API_NODE,
    PROGRAM_CALL_FLOW,
    REFINED_DATA_STRUCTURES_AND_INTERFACES,
    REFINED_DESIGN_NODE,
    REFINED_PROGRAM_CALL_FLOW,
)
from metagpt.const import DATA_API_DESIGN_FILE_REPO, SEQ_FLOW_FILE_REPO, DESIGN_FILENAME, PRD_FILENAME, SIMULATE_ROOT
from metagpt.logs import logger
from metagpt.schema import Document, Documents, Message
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.project_setting import get_project_setting, merge_json_string

NEW_REQ_TEMPLATE = """
### Legacy Content
{old_design}

### New Requirements
{context}
"""


class WriteDesign(Action):
    name: str = ""
    i_context: Optional[str] = None
    desc: str = (
        "Based on the PRD, think about the system design, and design the corresponding APIs, "
        "data structures, library tables, processes, and paths. Please provide your design, feedback "
        "clearly and in detail."
    )

    async def run(self, with_messages: Message, schema: str = None):
        # Use `git status` to identify which PRD documents have been modified in the `docs/prd` directory.
        filename = DESIGN_FILENAME
        # Use `git status` to identify which design documents in the `docs/system_designs` directory have undergone
        # changes.

        self.config.current_role = f'ARCHITECT'
        self.config.role_task = f'1/1 Write architect design'

        # For those PRDs and design documents that have undergone changes, regenerate the design content.
        changed_files = Documents()
        oh_action_data = {}
        content_info = {
            "sub_content": f"Update system design in {filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        doc = await self._update_system_design(filename=filename)
        changed_files.docs[filename] = doc

        # for filename in changed_system_designs:
        #     if filename in changed_files.docs:
        #         continue

        #     oh_action_data = {}
        #     content_info = {
        #         "sub_content": f"Update system design in {filename}",
        #         "role_task": self.config.role_task,
        #         "agent_role": self.config.current_role,
        #         "mission": self.config.user_intend
        #     }
        #     oh_action_data['action_type'] = "MESSAGE"
        #     oh_action_data['content'] = content_info
        #     oh_action_data['conversation_id'] = self.config.sid
        #     logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data,ensure_ascii=False)}")
        #     #print(f"!!!!!workspace: {oh_action_data}")

        #     doc = await self._update_system_design(filename=filename)
        #     changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        return ActionOutput(content=changed_files.model_dump_json(), instruct_content=changed_files)

    async def _new_system_design(self, context):
        node = await DESIGN_API_NODE.fill(context=context, llm=self.llm)
        return node

    async def _merge(self, prd_doc, system_design_doc, project_setting):
        prd_project_setting = merge_json_string(prd_doc.content, project_setting)
        context = NEW_REQ_TEMPLATE.format(old_design=system_design_doc.content, context=prd_project_setting)
        node = await REFINED_DESIGN_NODE.fill(context=context, llm=self.llm)
        system_design_doc.content = node.instruct_content.model_dump_json()
        return system_design_doc

    async def _update_system_design(self, filename) -> Document:
        prd = await self.repo.docs.prd.get(PRD_FILENAME)
        project_setting = get_project_setting()
        old_system_design_doc = await self.repo.docs.system_design.get(filename)
        if not old_system_design_doc:
            if self.config.simulate:
                design_path = SIMULATE_ROOT / filename
                with open(design_path, "r") as f:
                    content = f.read()
                doc = await self.repo.docs.system_design.save(
                filename=filename,
                content=content,
                dependencies={prd.root_relative_path},
                current_role=self.config.current_role,
                role_task = self.config.role_task,
                sid = self.config.sid,
                user_intend=self.config.user_intend,
            )
            else:
                content = merge_json_string(prd.content, project_setting)
                system_design = await self._new_system_design(context=content)
                doc = await self.repo.docs.system_design.save(
                    filename=filename,
                    content=system_design.instruct_content.model_dump_json(),
                    dependencies={prd.root_relative_path},
                    current_role=self.config.current_role,
                    role_task = self.config.role_task,
                    sid = self.config.sid,
                    user_intend=self.config.user_intend,
                )
        else:
            doc = await self._merge(prd_doc=prd, system_design_doc=old_system_design_doc, project_setting=project_setting)
            await self.repo.docs.system_design.save_doc(doc=doc, dependencies={prd.root_relative_path}, current_role=self.config.current_role,
                                        role_task=self.config.role_task, sid = self.config.sid, user_intend=self.config.user_intend)
        return doc

    async def _save_data_api_design(self, design_doc):
        m = json.loads(design_doc.content)
        data_api_design = m.get(DATA_STRUCTURES_AND_INTERFACES.key) or m.get(REFINED_DATA_STRUCTURES_AND_INTERFACES.key)
        if not data_api_design:
            return
        pathname = self.repo.workdir / DATA_API_DESIGN_FILE_REPO / Path(design_doc.filename).with_suffix("")
        await self._save_mermaid_file(data_api_design, pathname)
        logger.info(f"Save class view to {str(pathname)}")

    async def _save_seq_flow(self, design_doc):
        m = json.loads(design_doc.content)
        seq_flow = m.get(PROGRAM_CALL_FLOW.key) or m.get(REFINED_PROGRAM_CALL_FLOW.key)
        if not seq_flow:
            return
        pathname = self.repo.workdir / Path(SEQ_FLOW_FILE_REPO) / Path(design_doc.filename).with_suffix("")
        await self._save_mermaid_file(seq_flow, pathname)
        logger.info(f"Saving sequence flow to {str(pathname)}")

    async def _save_mermaid_file(self, data: str, pathname: Path):
        pathname.parent.mkdir(parents=True, exist_ok=True)
        await mermaid_to_file(self.config.mermaid.engine, data, pathname)
