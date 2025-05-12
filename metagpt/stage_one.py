import asyncio
from metagpt.team2 import Team2
from metagpt.config2 import config
from metagpt.roles import ProductManager, TestEngineer, Architect
from metagpt.context import Context

def generate_stage_one(idea, sid):
    ctx = Context(config=config)
    company = Team2()
    company.hire(
        [                
            ProductManager(),
            TestEngineer(),
            Architect()]
    )
    company.run_project(idea)
    asyncio.run(company.run())


if __name__=="__main__":
    generate_stage_one()