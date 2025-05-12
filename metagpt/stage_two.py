import asyncio
from metagpt.team2 import Team2
from metagpt.config2 import config
from metagpt.roles import ProductManager, TestEngineer, Architect, CodeArchitect, ProjectManager, SystemQaTester, Engineer
from metagpt.context import Context
from pathlib import Path
from metagpt.utils.common import read_json_file
from metagpt.schema import Message

def find_role_with_true_use_flag(data):
    if "env" in data and "roles" in data["env"]:
        roles = data["env"]["roles"]
        for role_key, role_value in roles.items():
            if role_value.get("use_flag", False):
                cause_by = role_value.get("cause_action", "")
                return role_key, cause_by
    return None, None


def generate_stage_one(idea, sid):
    serialized_data = read_json_file(json_file=Path("/Users/yangxiaodong/workspace/metagpt-eazytec/workspace/storage/team/team.json").as_posix())
    role_name, cause_by = find_role_with_true_use_flag(serialized_data)
    ctx = Context(config=config)
    ctx.lite_deserialize(serialized_data)
    company = Team2(context=ctx)
    message = Message(cause_by=cause_by, send_from=role_name)
    company.hire(
    [
                ProductManager(),
                TestEngineer(),
                Architect(),
                CodeArchitect(),
                ProjectManager(),
                SystemQaTester(),
            ]
    )
    asyncio.run(company.run(with_message=message))


if __name__=="__main__":
    generate_stage_one()