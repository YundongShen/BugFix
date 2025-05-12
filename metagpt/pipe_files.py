
import os
import base64

pipe_metagpt_to_openhands_file = ""
pipe_openhands_to_metagpt_file = ""

data_block_size = (1024*20)

gpipein = None
gpipeout = None

def set_metagpt_to_openhands_file_pipe(pipe_file):
    global pipe_metagpt_to_openhands_file
    pipe_metagpt_to_openhands_file = pipe_file

def set_openhands_to_metagpt_file_pipe(pipe_file):
    global pipe_openhands_to_metagpt_file
    pipe_openhands_to_metagpt_file = pipe_file

def get_metagpt_to_openhands_file_pipe():
    return pipe_metagpt_to_openhands_file

def get_openhands_to_metagpt_file_pipe():
    return pipe_openhands_to_metagpt_file   

def init_pipe_files():
    if os.path.exists(pipe_metagpt_to_openhands_file):
        os.unlink(pipe_metagpt_to_openhands_file)

    if os.path.exists(pipe_openhands_to_metagpt_file):
        os.unlink(pipe_openhands_to_metagpt_file)

    os.mkfifo(pipe_metagpt_to_openhands_file)
    global gpipeout
    gpipeout = os.open(pipe_metagpt_to_openhands_file, os.O_RDWR)

    return gpipeout

def get_pipes():
    return gpipeout, gpipein

def get_pipeout():
    return gpipeout

def set_pipein(pipein):
    global gpipein
    gpipein = pipein

def get_pipein():
    return gpipein

def set_pipes(pipeout, pipein):
    global gpipeout
    global gpipein
    pipeout = pipeout
    pipein = pipein 


def write_pipe_message_with_len(pipeout, message):
    encoded_bytes = message.encode('utf-8')
    encoded_text = base64.b64encode(encoded_bytes)
    
    #dataLen = len(encoded_text)
    #dataLenStr = str(dataLen).rjust(32,' ').encode()
    #dataWrite = os.write(pipeout, dataLenStr)
    #while dataWrite < 32:
    #    dataWrite += os.write(pipeout, dataLenStr[dataWrite:])
    
    encoded_text = encoded_text.rjust(data_block_size,b'\x00')
    dataWrite = os.write(pipeout, encoded_text)
    while dataWrite < data_block_size:
        dataWrite += os.write(pipeout, encoded_text[dataWrite:]) 

def read_pipe_message_with_len(pipein):
    #dataLenBytes = os.read(pipein, 32)
    #while len(dataLenBytes) < 32:
    #    dataLenBytes += os.read(pipein, 32 - len(dataLenBytes))
        
    #dataLenStr = dataLenBytes.decode().strip()
    #dataLen = int(dataLenStr)
    dataCmd = os.read(pipein, data_block_size)

    print("Received command in read_pipe_message_with_len: " + base64.b64decode(dataCmd).decode('utf-8'))
    while len(dataCmd) < data_block_size:
        dataCmd += os.read(pipein, data_block_size - len(dataCmd))
    return base64.b64decode(dataCmd).decode('utf-8')
