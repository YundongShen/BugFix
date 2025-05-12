#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
from pathlib import Path

import agentops
import typer

from metagpt.const import CONFIG_ROOT
from metagpt.utils.project_repo import ProjectRepo
from metagpt.logs import logger
import json
from metagpt.const import SERDESER_PATH
from metagpt.utils.common import read_json_file
from metagpt.utils.restore import find_role_with_true_use_flag
from metagpt.schema import Message

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

def OH_ACTION_log_filter(record):
    return "<OH_ACTION>" in record["message"]

def generate_repo(
    idea,
    investment=3.0,
    n_round=50,
    code_review=False,
    run_tests=False,
    implement=True,
    project_name="",
    inc=False,
    project_path="",
    reqa_file="",
    max_auto_summarize_code=0,
    recover_path=None,
    logger_stream_obj=None,
    sid :str = "",
    sio =None,
    local: bool = True,
    simulate: bool = False
) -> ProjectRepo:
    """Run the startup logic. Can be called from CLI or other Python scripts."""
    from metagpt.config2 import config
    from metagpt.context import Context
    from metagpt.roles import (
        Architect,
        Engineer,
        ProductManager,
        ProjectManager,
        QaEngineer,
        SystemQaTester,
        TestEngineer,
        CodeArchitect
    )

    if logger_stream_obj:
        logger.add(logger_stream_obj,filter=OH_ACTION_log_filter,level="ERROR")
    from metagpt.team import Team

    if config.agentops_api_key != "":
        agentops.init(config.agentops_api_key, tags=["software_company"])

    # if sid and sio:
    config = config.default(sid,sio, local, idea, simulate=simulate)

    config.update_via_cli(project_path, project_name, inc, reqa_file, max_auto_summarize_code)
    ctx = Context(config=config)
    stg_path = SERDESER_PATH.joinpath(f"team/{sid}")
    team_info_path = stg_path.joinpath("team.json")
    restore = False
    if stg_path.exists():
        company = Team.deserialize(team_info_path, context=ctx)
        serialized_data = read_json_file(team_info_path)
        role_name, cause_by = find_role_with_true_use_flag(serialized_data)
        message = Message(cause_by=cause_by, send_from=role_name)
        restore = True   
    else:
        company = Team(context=ctx)
   
        
    company.hire(
        [
            ProductManager(),
            TestEngineer(),
            Architect(),
            CodeArchitect(),
            ProjectManager(),
            SystemQaTester(),
            Engineer()
        ]
    )

    '''
    oh_action_data = {}
    oh_action_data['action_type'] = "MESSAGE"
    oh_action_data['content'] = f"There are a total of 7 roles, namely Product Manager, Test Engineer, Architect, CodeArchitect, Project Manager, System QA Tester, Engineer"
    oh_action_data['conversation_id'] = sid
    oh_action_data['agent_role'] = ""
    oh_action_data['role_task'] = f"Start executing the task."
    oh_action_data['mission'] = config.user_intend
    logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")
    print(f"!!!!!workspace: {oh_action_data}")
    '''

    if not restore:

        company.invest(investment,sid)
        company.run_project(idea)

        asyncio.run(company.run(n_round=n_round))

    else:
        message = Message(cause_by=cause_by, send_from=role_name)   
        asyncio.run(company.run(with_message=message))

    if config.agentops_api_key != "":
        agentops.end_session("Success")

    print(f"############company run finished")
    logger.info(f"finish action.")
    oh_action_data = {}
    oh_action_data['action_type'] = "ACTION_FINISH"
    oh_action_data['message'] = f"send finish action event."
    oh_action_data['conversation_id'] = sid
    logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data)}")

    oh_action_data = {}
    content_info = {
        "sub_content": f"Finish mission",
        "role_task": f"4/4 Launch Integrate test",
        "agent_role": f"TEST_ENGINEER",
        "mission": config.user_intend
    }
    oh_action_data['action_type'] = "MESSAGE"
    oh_action_data['content'] = content_info
    oh_action_data['conversation_id'] = sid
    logger.error(f"<OH_ACTION> json_data:{json.dumps(oh_action_data, ensure_ascii=False)}")
    #print(f"!!!!!workspace: {oh_action_data}")

    return ctx.repo


@app.command("", help="Start a new project.")
def startup(
    idea: str = typer.Argument(None, help="Your innovative idea, such as 'Create a 2048 game.'"),
    investment: float = typer.Option(default=3.0, help="Dollar amount to invest in the AI company."),
    n_round: int = typer.Option(default=5, help="Number of rounds for the simulation."),
    code_review: bool = typer.Option(default=True, help="Whether to use code review."),
    run_tests: bool = typer.Option(default=False, help="Whether to enable QA for adding & running tests."),
    implement: bool = typer.Option(default=True, help="Enable or disable code implementation."),
    project_name: str = typer.Option(default="", help="Unique project name, such as 'game_2048'."),
    inc: bool = typer.Option(default=False, help="Incremental mode. Use it to coop with existing repo."),
    project_path: str = typer.Option(
        default="",
        help="Specify the directory path of the old version project to fulfill the incremental requirements.",
    ),
    reqa_file: str = typer.Option(
        default="", help="Specify the source file name for rewriting the quality assurance code."
    ),
    max_auto_summarize_code: int = typer.Option(
        default=0,
        help="The maximum number of times the 'SummarizeCode' action is automatically invoked, with -1 indicating "
        "unlimited. This parameter is used for debugging the workflow.",
    ),
    recover_path: str = typer.Option(default=None, help="recover the project from existing serialized storage"),
    init_config: bool = typer.Option(default=False, help="Initialize the configuration file for MetaGPT."),
):
    """Run a startup. Be a boss."""
    if init_config:
        copy_config_to()
        return

    if idea is None:
        typer.echo("Missing argument 'IDEA'. Run 'metagpt --help' for more information.")
        raise typer.Exit()

    return generate_repo(
        idea,
        investment,
        n_round,
        code_review,
        run_tests,
        implement,
        project_name,
        inc,
        project_path,
        reqa_file,
        max_auto_summarize_code,
        recover_path,
    )


DEFAULT_CONFIG = """# Full Example: https://github.com/geekan/MetaGPT/blob/main/config/config2.example.yaml
# Reflected Code: https://github.com/geekan/MetaGPT/blob/main/metagpt/config2.py
# Config Docs: https://docs.deepwisdom.ai/main/en/guide/get_started/configuration.html
llm:
  api_type: "openai"  # or azure / ollama / groq etc.
  model: "gpt-4-turbo"  # or gpt-3.5-turbo
  base_url: "https://api.openai.com/v1"  # or forward url / other llm url
  api_key: "YOUR_API_KEY"
"""


def copy_config_to():
    """Initialize the configuration file for MetaGPT."""
    target_path = CONFIG_ROOT / "config2.yaml"

    # 创建目标目录（如果不存在）
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # 如果目标文件已经存在，则重命名为 .bak
    if target_path.exists():
        backup_path = target_path.with_suffix(".bak")
        target_path.rename(backup_path)
        print(f"Existing configuration file backed up at {backup_path}")

    # 复制文件
    target_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    print(f"Configuration file initialized at {target_path}")


if __name__ == "__main__":
    app()
