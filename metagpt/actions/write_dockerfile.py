from metagpt.actions import Action
from metagpt.schema import DockerfileContext
from metagpt.schema import Document, Documents, Message
from metagpt.utils.common import CodeParser
from typing import Optional
from pathlib import Path
from metagpt.utils.example_code import backend_dockerfile_code, frontend_dockerfile_code
from metagpt.const import SIMULATE_ROOT

PROMPT_TEMPLATE = """
NOTICE
Role: You are a DevOps engineer; your main goal is to generate a Dockerfile based on provided project details. The Dockerfile should follow best practices for containerization, including dependency management, file organization, and runtime configuration.
Language: Use the same language as the user requirement, but keep the title and code in English. For example, if the user speaks Chinese, the specific text of your answer should also be in Chinese.
ATTENTION: Use '##' to split sections, not '#'. Output format should carefully follow the "Format example" provided.

# Context
## Project Details

### Base Image
{base_image}

### WORK_DIR
{work_dir}

### Dependecies Command
{dependencies_command}

### Startup Command
{startup_command}

### EXPOSE PORT VARIABLE
{export_variable}
# Format example

### EXAMPLE CODE
{example_code}

## Code
```dockerfile
## Dockerfile
...
```

# Instruction: Based on the context, follow "Format example", write dockerfile.Based on the provided Project Details, generate a Dockerfile following these guidelines:
Base Image: Use the provided {base_image} (e.g., node:20-alpine).
Working Directory: Set to {work_dir} (e.g., /app).
Dependencies: Run {dependencies_command} (e.g., npm ci --production).
Environment: Define {export_variable} with a default port (e.g., 3000).
Port Exposure: Use ${export_variable} in EXPOSE for dynamic port configuration.
Startup: Use CMD with {startup_command} (e.g., ["sh", "start.sh"]).
Layer Optimization: Copy dependencies first to leverage Docker caching.
DONOT EXPLAIN ANYTHING.
"""

class WriteDockerfile(Action):
    name: str = "WriteDockerfile"
    i_context: Optional[DockerfileContext] = None
    async def run(self):
        frontend_prompt = PROMPT_TEMPLATE.format(
            base_image=self.i_context.frontend_image,
            work_dir=self.extract_path(Path(self.i_context.launch_frontend_file).parent.as_posix()),
            dependencies_command=self.i_context.install_frontend_command,
            startup_command=self.i_context.launch_frontend_command,
            export_variable="APP_PORT_1",
            example_code=frontend_dockerfile_code
        )
        backend_prompt = PROMPT_TEMPLATE.format(
            base_image=self.i_context.backend_image,
            work_dir=self.extract_path(Path(self.i_context.launch_backend_file).parent.as_posix()),
            dependencies_command=self.i_context.install_backend_command,
            startup_command=self.i_context.launch_backend_command,
            export_variable="APP_PORT_2",
            example_code=backend_dockerfile_code
        )
        frontend_dockerfile = await self._aask(frontend_prompt)
        backend_dockerfile = await self._aask(backend_prompt)
        frontend_code = CodeParser.parse_code(block="", text=frontend_dockerfile)
        if self.config.simulate:
            file_path = SIMULATE_ROOT / "frontend_dockerfile.txt"
            assert file_path.exists()
            with open(file_path, "r") as f:
                frontend_code = f.read()
        
        backend_code = CodeParser.parse_code(block="", text=backend_dockerfile)
        if self.config.simulate:
            file_path = SIMULATE_ROOT / "backend_dockerfile.txt"
            assert file_path.exists()
            with open(file_path, "r") as f:
                backend_code = f.read()

        if self.config.simulate:
            file_path = SIMULATE_ROOT / "docker-entrypoint.sh"
            assert file_path.exists()
            with open(file_path, "r") as f:
                docker_entrypoint = f.read()


        if self.config.simulate:
            file_path = SIMULATE_ROOT / "default.conf"
            assert file_path.exists()
            with open(file_path, "r") as f:
                default_conf = f.read()

        return frontend_code, backend_code, docker_entrypoint, default_conf


    def extract_path(self, full_path):
        """
        从完整路径中提取所需的部分路径
        :param full_path: 完整的路径字符串
        :return: 提取后的路径字符串
        """
        target = "/workspace/"
        first_index = full_path.find(target)
        if first_index != -1:
            # 查找第二个 /workspace 的位置
            second_index = full_path.find(target, first_index + len(target))
            if second_index != -1:
                return full_path[second_index:]
        return None