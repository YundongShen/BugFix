#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/5/11 14:43
@Author  : alexanderwu
@File    : architect.py
"""


from metagpt.actions import WritePRD
from metagpt.actions.code_design_api import WriteCodeDesignAPI
from metagpt.actions.write_testcase import WriteTestCase
from metagpt.actions.design_api import WriteDesign
from metagpt.roles.role import Role



class Architect(Role):
    """
    Represents an Architect role in a software development process.

    Attributes:
        name (str): Name of the architect.
        profile (str): Role profile, default is 'Architect'.
        goal (str): Primary goal or responsibility of the architect.
        constraints (str): Constraints or guidelines for the architect.
    """

    name: str = "Bob"
    profile: str = "Architect"
    goal: str = "design a concise, usable, complete software system"
    constraints: str = (
        "make sure the architecture is simple enough and use  appropriate open source "
        "libraries. Use same language as user requirement"
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([WriteDesign])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WriteTestCase})

class CodeArchitect(Role):
    name: str = "CodeBob"
    profile: str = "CodeArchitect"
    goal: str = "design and develop software systems that meet the needs of the business"
    constraints: str = (
        "Ensure data consistency throughout the system.For relevant components, maintain interface consistency."
        "If applicable, develop the back-end first, then the front-end, with the front-end conforming to back-end interfaces"
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Initialize actions specific to the Architect role
        self.set_actions([WriteCodeDesignAPI])

        # Set events or actions the Architect should watch or be aware of
        self._watch({WriteDesign})