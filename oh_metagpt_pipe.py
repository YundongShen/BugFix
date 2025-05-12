
from metagpt.software_company import generate_repo
from metagpt.utils.project_repo import ProjectRepo
import os
from time import sleep
import base64

from metagpt.pipe_files import get_pipes, set_pipes, write_pipe_message_with_len, read_pipe_message_with_len,init_pipe_files,get_pipeout,set_pipein
from metagpt.pipe_files import get_metagpt_to_openhands_file_pipe,get_openhands_to_metagpt_file_pipe,set_metagpt_to_openhands_file_pipe,set_openhands_to_metagpt_file_pipe

set_metagpt_to_openhands_file_pipe("/tmp/metagpt_to_openhands_pipe")
set_openhands_to_metagpt_file_pipe("/tmp/openhands_to_metagpt_pipe")
init_pipe_files()
#pipeout = get_pipeout()

class MetaGPTWrite:
    def write(self, message):
        if message is not None and len(message) > 0 and message.find("<OH_ACTION>") != -1:
            write_pipe_message_with_len(get_pipeout(),message)

stream_object = MetaGPTWrite()

def cleanup_pipe_file():
    """清理管道文件并处理异常"""
    pipe_path = get_openhands_to_metagpt_file_pipe()
    try:
        if os.path.exists(pipe_path):
            os.remove(pipe_path)
            print(f"Deleted pipe file: {pipe_path}")
        else:
            print(f"Pipe file {pipe_path} does not exist")
    except Exception as e:
        print(f"Error deleting pipe file: {str(e)}")

print("Enter While Loop")
while True:    
    if os.path.exists(get_openhands_to_metagpt_file_pipe()):
        pipein = os.open(get_openhands_to_metagpt_file_pipe(), os.O_RDWR)
        set_pipein(pipein)
        print("Pipe file "+get_openhands_to_metagpt_file_pipe() + " exists!")
        while True:
            cmd_str = read_pipe_message_with_len(pipein)
            cmd_str = cmd_str.strip()
            print("Received command: " + cmd_str)
            idx_for_launch = cmd_str.find("LaunchProject: ")
            if idx_for_launch != -1:
                project_name = cmd_str[idx_for_launch+len("LaunchProject: "):]
                print("Launching project: " + project_name)
                try:
                    generate_repo(project_name, logger_stream_obj = stream_object)    
                finally:
                    cleanup_pipe_file()
            else:
                print("Command not recognized: " + cmd_str)
    else:
        print("Pipe file "+get_openhands_to_metagpt_file_pipe() + " does not exist!")

    sleep(5)


os.close(get_pipeout())
os.close(pipein)
