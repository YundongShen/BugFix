#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/12 00:30
@Author  : alexanderwu
@File    : team.py
@Modified By: mashenquan, 2023/11/27. Add an archiving operation after completing the project, as specified in
        Section 2.2.3.3 of RFC 135.
"""

import warnings
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field
import json
from metagpt.actions import UserRequirement
from metagpt.const import MESSAGE_ROUTE_TO_ALL, SERDESER_PATH
from metagpt.context import Context
from metagpt.environment import Environment
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import (
    NoMoneyException,
    read_json_file,
    serialize_decorator,
    write_json_file,
)


class Team(BaseModel):
    """
    Team: Possesses one or more roles (agents), SOP (Standard Operating Procedures), and a env for instant messaging,
    dedicated to env any multi-agent activity, such as collaboratively writing executable code.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    env: Optional[Environment] = None
    investment: float = Field(default=10.0)
    idea: str = Field(default="")

    def __init__(self, context: Context = None, **data: Any):
        super(Team, self).__init__(**data)
        ctx = context or Context()
        if not self.env:
            self.env = Environment(context=ctx)
        else:
            self.env.context = ctx  # The `env` object is allocated by deserialization
        if "roles" in data:
            self.hire(data["roles"])
        if "env_desc" in data:
            self.env.desc = data["env_desc"]

    def serialize(self, stg_path: Path = None):
        stg_path = SERDESER_PATH.joinpath("team") if stg_path is None else stg_path
        save_path = stg_path.joinpath(self.env.context.config.sid)
        team_info_path = save_path.joinpath("team.json")
        serialized_data = self.model_dump()
        serialized_data["context"] = self.env.context.serialize()
        last_role = ""
        for role_name, role_value in serialized_data["env"]["roles"].items():
            if role_value.get("use_flag", False):
                last_role = role_name
        serialized_data["context"]["last_role"] = last_role
        write_json_file(team_info_path, serialized_data)

    @classmethod
    def deserialize(cls, team_info_path, context: Context = None) -> "Team":
        """stg_path = ./storage/team"""
        # recover team_info
        
        if not team_info_path.exists():
            raise FileNotFoundError(
                "recover storage meta file `team.json` not exist, " "not to recover and please start a new project."
            )

        team_info: dict = read_json_file(team_info_path)
        ctx = context or Context()
        ctx.lite_deserialize(team_info.pop("context", None))
        team = Team(**team_info, context=ctx)
        return team

    def hire(self, roles: list[Role]):
        """Hire roles to cooperate"""
        self.env.add_roles(roles)

    @property
    def cost_manager(self):
        """Get cost manager"""
        return self.env.context.cost_manager

    def invest(self, investment: float, sid):
        """Invest company. raise NoMoneyException when exceed max_budget."""
        self.investment = investment
        self.cost_manager.max_budget = investment
        logger.info(f"Investment: ${investment}.")

    def _check_balance(self):
        if self.cost_manager.total_cost >= self.cost_manager.max_budget:
            raise NoMoneyException(self.cost_manager.total_cost, f"Insufficient funds: {self.cost_manager.max_budget}")

    def run_project(self, idea, send_to: str = ""):
        """Run a project from publishing user requirement."""
        self.idea = idea

        # Human requirement.
        self.env.publish_message(
            Message(role="Human", content=idea, cause_by=UserRequirement, send_to=send_to or MESSAGE_ROUTE_TO_ALL),
            peekable=False,
        )

    def start_project(self, idea, send_to: str = ""):
        """
        Deprecated: This method will be removed in the future.
        Please use the `run_project` method instead.
        """
        warnings.warn(
            "The 'start_project' method is deprecated and will be removed in the future. "
            "Please use the 'run_project' method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.run_project(idea=idea, send_to=send_to)


    # async def run(self, n_round=3, idea="", send_to="", auto_archive=True, with_message=None):
    #     """Run company until target round or no money"""
    #     if idea:
    #         self.run_project(idea=idea, send_to=send_to)

    #     while n_round > 0:
    #         if not with_message:
    #             if self.env.is_idle:
    #                 logger.info("All roles are idle.")
    #                 break
    #         n_round -= 1
    #         await self.env.run(with_message=with_message)
    #         self.serialize()
    #         logger.info(f"max {n_round=} left.")
    #     self.env.archive(auto_archive)
    #     return self.env.history
    async def run(self, idea="",n_round=3, send_to="", auto_archive=True, with_message=None):
        """Run company until target round or no money"""
        if idea:
            self.run_project(idea=idea, send_to=send_to)
        while True:
            if not with_message:
                if self.env.is_idle:
                    logger.info("All roles are idle.")
                    break
            await self.env.run(with_message=with_message)
            with_message = None
            self.serialize()
        self.env.archive(auto_archive)
        return self.env.history
