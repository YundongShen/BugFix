from typing import Literal

from metagpt.utils.yaml_model import YamlModel

class ProjectConfig(YamlModel):
    """Config for Project"""

    project_type: str
    database_url: str
    database_type: str
    database_port: int
    database_username: str
    database_password: str
    database_table: str
    frontend_framework: str
    backend_framework: str
    backend_language: str