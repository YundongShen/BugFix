
import os
import time
import logging
import os
from metagpt.software_company import generate_repo
import socketio
from eazytec_send import ConnectionState, get_connection_state,connection_states
import json
import asyncio

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 从环境变量读取URL，如果不存在则使用默认值
url = os.environ.get("EAZYTEC_SERVER_URL", "http://127.0.0.1:8080/socket.io/")
logger.info(f"使用服务器URL: {url}")

# 创建 Socket.IO 客户端
sio = socketio.Client()



class MetaGPTWrite:
    def __init__(self, conversation_id):
        self.conversation_id = conversation_id

    def write(self, message):
        if message is not None and len(message) > 0 and message.find("<OH_ACTION>") != -1:
            if message.find("json_data") !=-1:
                json_data = json.loads(message.split("json_data:")[1].strip())
                #print(f"################metagpt, json data:{json_data}")

                if 'conversation_id' in json_data:
                    print(f"########### json data conv id:{json_data['conversation_id']}, sid:{self.conversation_id}")
                    if json_data['conversation_id'] == self.conversation_id:
                        sio.emit('eazytec_response', {
                            'conversation_id': self.conversation_id,
                            'message': message,
                            'type': 'action'
                        })

@sio.event
def connect():
    """连接成功时的回调"""
    logger.info("已连接到服务器")

@sio.event
def disconnect():
    """断开连接时的回调"""
    logger.info("已断开连接")

@sio.event
def eazytec_request(data):
    """接收消息的回调
    data = {
        'type': 'task',
        'content': content,
        'conversation_id': conversation_id
    }
    """
    logger.info(f"收到消息: {data}")
    try:
        state = get_connection_state(sio, data.get('conversation_id', sio.sid))
        logger.info(f"Processing {data['type']} for conversation {data.get('conversation_id')}")

        loop = asyncio.new_event_loop() #for local test
        asyncio.set_event_loop(loop) #for local test

        if data['type'] == 'task':
            content = data['content']
            conversation_id = data['conversation_id']
            stream_object = MetaGPTWrite(conversation_id)
            print(content)
            generate_repo(content, logger_stream_obj = stream_object, sid = conversation_id, sio=sio, local = False)

            """
            loop.run_until_complete(
                generate_repo(
                    content,
                    logger_stream_obj=stream_object,
                    sid = conversation_id,
                    sio = sio,
                )
            )
            """

        if data['type'] == 'file':
            content = data['content']
            state.doc_recv = content.strip()
            state.continue_flag = True
            print(f"##########state in data type file:{state}, content:{state.doc_recv}")

        if data['type'] == 'message':
            content = data['content']
            state.msg_recv = content.strip()
            state.msg_continue_flag = True
            print(f"##########state in data type message:{state}, content:{state.msg_recv}")

    except Exception as e:
        logger.error(f"处理消息失败: {e}")


def main():
    try:
        # 从 WebSocket URL 提取服务器地址
        server_url = f"{url}?client_name=meta"
        logger.info(f"正在连接到服务器: {server_url}")

        # 连接到服务器 - 修改这里
        # 正确的方式是使用 params 参数而不是 query
        sio.connect(
            server_url,
            transports=['websocket']
        )
        # 保持程序运行
        try:
            while True:
                time.sleep(30)  # 每30秒检查一次
        except KeyboardInterrupt:
            logger.info("程序被用户中断")

    except Exception as e:
        logger.error(f"连接错误: {e}")

    finally:
        # 断开连接
        if sio.connected:
            sio.disconnect()

if __name__ == "__main__":
    main()

