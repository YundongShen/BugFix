import asyncio
from pathlib import Path

import agentops
import typer

from metagpt.const import CONFIG_ROOT
from metagpt.utils.project_repo import ProjectRepo
from metagpt.logs import logger
import json

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

def OH_ACTION_log_filter(record):
    return "<OH_ACTION>" in record["message"]


def generate_product(
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
        ProductManager,
        TestEngineer,
        Architect
    )
    if logger_stream_obj:
        logger.add(logger_stream_obj,filter=OH_ACTION_log_filter,level="ERROR")
    from metagpt.team import Team
    
    config = config.default(sid,sio, local, idea, llm_config)

    config.update_project(project_name)

    ctx = Context(config=config)

    company = Team(context=ctx)
    company.hire(
        [
            ProductManager(),
            TestEngineer(),
            Architect()
        ]
    )
    company.run_project(idea)
    asyncio.run(company.run())

    oh_action_data = {}
    content_info = {
        "sub_content": f"Finish write design, wait for user confirm",
        "role_task": f"1/1 Write architect design",
        "agent_role": f"ARCHITECT",
        "mission": config.user_intend
    }
    oh_action_data['action_type'] = "MESSAGE"
    oh_action_data['content'] = content_info
    oh_action_data['conversation_id'] = sid
    logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data, ensure_ascii=False)}")

    return ctx.repo

if __name__ == "__main__":
    app()
