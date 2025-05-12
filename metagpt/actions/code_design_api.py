from pathlib import Path
from typing import Optional
import json

from metagpt.actions import Action, ActionOutput
from metagpt.schema import Document, Documents, Message
from metagpt.logs import logger
from metagpt.const import DATA_API_DESIGN_FILE_REPO, SEQ_FLOW_FILE_REPO, DESIGN_FILENAME, PRD_FILENAME, CODEDESIGN_FILENAME, SIMULATE_ROOT
from metagpt.utils.mermaid import mermaid_to_file
from metagpt.utils.json_to_markdown import json_to_markdown
from metagpt.actions.design_api_an import (
    DATA_STRUCTURES_AND_INTERFACES,
    DESIGN_API_NODE,
    PROGRAM_CALL_FLOW,
    REFINED_DATA_STRUCTURES_AND_INTERFACES,
    REFINED_DESIGN_NODE,
    REFINED_PROGRAM_CALL_FLOW,
    CODE_DESIGN_NODE, 
    FILE_LIST
)
from metagpt.utils.project_setting import get_project_setting
from metagpt.utils.action_utils import check_frontend_files, check_backend_files

CODE_DESIGN_TEMPLATE = """
## PRD
{prd}

## System Design
{system_design}

## Project Setting
{project_setting}
"""

class WriteCodeDesignAPI(Action):
    name: str = ""
    i_context: Optional[str] = None
    desc: str = (
        "Based on the PRD, System Design, Project Setting think about the code design, and design the corresponding APIs, "
        "data structures, library tables, processes, and paths. Please provide your design, feedback "
        "clearly and in detail."
    )

    async def run(self, with_messages: Message, schema: str = None):

        self.config.current_role = f"ARCHITECT"
        self.config.role_task = f"2/2 Write code design"

        changed_files = Documents()
        filename = CODEDESIGN_FILENAME

        oh_action_data = {}
        content_info = {
            "sub_content": f"Start writing {filename}",
            "role_task": self.config.role_task,
            "agent_role": self.config.current_role,
            "mission": self.config.user_intend
        }
        oh_action_data['action_type'] = "MESSAGE"
        oh_action_data['content'] = content_info
        oh_action_data['conversation_id'] = self.config.sid
        logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data, ensure_ascii=False)}")
        #print(f"!!!!!workspace: {oh_action_data}")

        doc = await self._update_code_desgin(filename=filename)
        changed_files.docs[filename] = doc
        if not changed_files.docs:
            logger.info("Nothing has changed.")
        # Wait until all files under `docs/system_designs/` are processed before sending the publish message,
        # leaving room for global optimization in subsequent steps.
        return ActionOutput(content=changed_files.model_dump_json(), instruct_content=changed_files)


    async def _update_code_desgin(self, filename) -> Document:
        prd = await self.repo.docs.prd.get(PRD_FILENAME)
        system_design = await self.repo.docs.system_design.get(DESIGN_FILENAME)
        prd_md = await  self._convert_to_markdown(prd.content)
        system_design_md = await self._convert_to_markdown(system_design.content)
        project_setting = get_project_setting()
        project_setting_md = await self._convert_to_markdown(project_setting)

        context = CODE_DESIGN_TEMPLATE.format(prd=prd_md, system_design=system_design_md, project_setting=project_setting_md)
        code_desgin = await self._new_code_design(context=context)

        code_desgin_dict = code_desgin.instruct_content.model_dump()
        file_list = code_desgin_dict.get(FILE_LIST.key, [])
        file_list = check_frontend_files(file_list=file_list)
        file_list = check_backend_files(file_list=file_list)
        code_desgin_dict[FILE_LIST.key] = file_list
        logger.info(f"new filter file_list : {str(file_list)}")
        if self.config.simulate:
            file_path = SIMULATE_ROOT / filename
            with open(file_path, "r") as f:
                content = f.read()
            doc = await self.repo.docs.code_design.save(
                    filename=filename,
                    content=content,
                    dependencies={prd.root_relative_path},
                    current_role = self.config.current_role,
                    role_task = self.config.role_task,
                    sid = self.config.sid,
                    user_intend=self.config.user_intend,
                )
        else:
            doc = await self.repo.docs.code_design.save(
                    filename=filename,
                    content=json.dumps(code_desgin_dict, ensure_ascii=False),
                    dependencies={prd.root_relative_path},
                    current_role = self.config.current_role,
                    role_task = self.config.role_task,
                    sid = self.config.sid,
                    user_intend=self.config.user_intend,
                )
            await self._save_data_api_design(doc)
            await self._save_seq_flow(doc)
            await self.repo.resources.system_design.save_pdf(doc=doc, current_role = self.config.current_role,role_task = self.config.role_task,sid=self.config.sid, user_intend=self.config.user_intend)
        return doc


    async def _new_code_design(self, context):
        node = await CODE_DESIGN_NODE.fill(context=context, llm=self.llm)
        return node

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

    async def _convert_to_markdown(self, content):
        try:
            content = json.loads(content)
            content = json_to_markdown(content, depth=3)
            return content
        except:
            return content
