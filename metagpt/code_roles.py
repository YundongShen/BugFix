import asyncio
from pathlib import Path

import agentops
import typer
from metagpt.const import MESSAGE_ROUTE_TO_ALL, SERDESER_PATH
from metagpt.const import CONFIG_ROOT
from metagpt.utils.project_repo import ProjectRepo
from metagpt.logs import logger
import json
from metagpt.utils.common import read_json_file
from metagpt.schema import Message

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

def find_role_with_true_use_flag(data):
    last_role = data["context"].get("last_role", "")
    if last_role != "":
        cause_by = data["env"]["roles"][last_role].get("cause_action", "")
        return last_role, cause_by
    else:
        return "Architect", "metagpt.actions.design_api.WriteDesign"


def OH_ACTION_log_filter(record):
    return "<OH_ACTION>" in record["message"]


def generate_codes(
        idea,
        project_name="",
        logger_stream_obj=None,
        sid: str = "",
        sio =None,
        local: bool = True,
        llm_config :dict=None,

) -> ProjectRepo:
    from metagpt.config2 import config
    from metagpt.context import Context
    from metagpt.roles import (
        CodeArchitect,
        Engineer,
        ProjectManager,
        SystemQaTester
    )
    #if logger_stream_obj:
        #logger.add(logger_stream_obj,filter=OH_ACTION_log_filter,level="ERROR")
    from metagpt.team import Team
    config = config.default(sid, sio, local, idea, llm_config)
    config.update_project(project_name)
    ctx = Context(config=config)
    stg_path = SERDESER_PATH.joinpath(f"team/{sid}")
    team_info_path = stg_path.joinpath("team.json")
    company = Team.deserialize(team_info_path, context=ctx)
    company.hire(
    [
                Engineer(),
                CodeArchitect(),
                SystemQaTester(),
                ProjectManager()
            ]
    )

    serialized_data = read_json_file(team_info_path)
    role_name, cause_by = find_role_with_true_use_flag(serialized_data)
    message = Message(cause_by=cause_by, send_from=role_name)
    asyncio.run(company.run(with_message=message))

    oh_action_data = {}
    content_info = {
        "sub_content": f"Finish mission",
        "role_task": f"4/4 Launch Integrate test",
        "agent_role": f"TEST_ENGINEER",
        "mission": ctx.config.user_intend
    }
    oh_action_data['action_type'] = "MESSAGE"
    oh_action_data['content'] = content_info
    oh_action_data['conversation_id'] = sid
    logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data, ensure_ascii=False)}")

if __name__=="__main__":
    generate_codes()