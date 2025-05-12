import os
import time
import logging
import json
import asyncio
import redis
from eazytec_util import get_stable_machine_id
from metagpt.software_company import generate_repo
from metagpt.product_roles import generate_product
from metagpt.code_roles import generate_codes
from eazytec_send import ConnectionState, get_connection_state, connection_states

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


redis_host = os.environ.get("REDIS_HOST", "2.2.0.23")
redis_port = os.environ.get("REDIS_PORT", 47921)
redis_db = os.environ.get("REDIS_DB", 0)
redis_password = os.environ.get("REDIS_PASSWORD", "eazy")
redis_channel_meta_to_oh = os.environ.get("REDIS_CHANNEL_META_TO_OH", "metagpt_session:meta_to_oh")
redis_channel_oh_to_meta = os.environ.get("REDIS_CHANNEL_OH_TO_META", "metagpt_session:oh_to_meta")

logger.info(f"使用redis: {redis_host}:{redis_port}/{redis_db}")

machine_id = get_stable_machine_id() 
logger.info(f"机器ID: {machine_id}")

# 创建 Redis 客户端
redis_client = redis.Redis(
    host=redis_host,
    port=int(redis_port),
    db=int(redis_db),
    password=redis_password,
    socket_keepalive=True,  # 启用TCP keepalive
    socket_timeout=300,     # 设置socket超时时间
    health_check_interval=30  # 定期进行健康检查
)

# 用于存储每个 conversation_id 对应的 MetaGPTWrite 实例
conversation_instances = {}

class MockSio:
    def __init__(self, sid):
        self.sid = sid

class MetaGPTWrite:
    def __init__(self, conversation_id, user_intend, llm_config=None):
        self.conversation_id = conversation_id
        self.user_intend = user_intend
        self.llm_config = llm_config

    def write(self, message):
        if message is not None and len(message) > 0 and message.find("<OH_ACTION>") != -1:
            if message.find("json_data") !=-1:
                json_data = json.loads(message.split("json_data:")[1].strip())

                if 'conversation_id' in json_data:
                    print(f"########### json data conv id:{json_data['conversation_id']}, sid:{self.conversation_id}")
                    if json_data['conversation_id'] == self.conversation_id:
                        # 使用 Redis 发布消息
                        response_data = {
                            'conversation_id': self.conversation_id,
                            'message': message,
                            'type': 'action'
                        }
                        redis_client.publish(redis_channel_meta_to_oh, json.dumps(response_data))

async def handle_message(data):
    """处理接收到的消息
    data = {
        'type': 'task',
        'content': content,
        'conversation_id': conversation_id
    }
    """
    logger.info(f"收到消息: {data}")

    try:
        conversation_id = data.get('conversation_id')
        sio = MockSio(conversation_id)
        state = get_connection_state(sio, conversation_id)
        logger.info(f"Processing {data['type']} for conversation {conversation_id}")

        if data['type'] == 'task':
            content = data['content']
            print(content)

            # 检查该 conversation_id 是否已经有对应的实例
            if conversation_id not in conversation_instances:
                # 如果没有，创建一个新的 MetaGPTWrite 实例
                stream_object = MetaGPTWrite(conversation_id, content)
                conversation_instances[conversation_id] = stream_object
            else:
                # 如果有，获取已有的实例
                stream_object = conversation_instances[conversation_id]

            if(content == "RE_GENERATE"): # or (content == "REQ_CONFIRM")):
                await asyncio.to_thread(generate_product, idea=stream_object.user_intend, logger_stream_obj=stream_object, project_name="project", sid=conversation_id, sio=sio, local=False, llm_config=stream_object.llm_config)

            elif(content == "DESIGN_CONFIRM"):
                await asyncio.to_thread(generate_codes, idea=stream_object.user_intend, logger_stream_obj=stream_object, project_name="project", sid=conversation_id, sio=sio, local=False, llm_config=stream_object.llm_config)

            else:
                stream_object.user_intend = content
                await asyncio.to_thread(generate_product, idea=stream_object.user_intend, logger_stream_obj=stream_object, project_name="project", sid=conversation_id, sio=sio, local=False, llm_config=stream_object.llm_config)

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

        if data['type'] == 'config':
            '''
            data = {
            'type': 'config',
            'content': {"llm_config": {"model": "openai/qwen-max-2025-01-25", "api_key": "", "base_url": ""}}
            'conversation_id': None
            }
            '''
            
            content = data['content']
            content = json.loads(content)
            llm_config = content['llm_config']
            conversation_id = data['conversation_id']

            if conversation_id not in conversation_instances:
                # 如果没有，创建一个新的 MetaGPTWrite 实例
                stream_object = MetaGPTWrite(conversation_id, content, llm_config)
                conversation_instances[conversation_id] = stream_object
            else:
                # 如果有，获取已有的实例
                stream_object = conversation_instances[conversation_id]
                stream_object.llm_config = llm_config

    except Exception as e:
        logger.error(f"处理消息失败: {e}")

def listen_to_redis():
    """监听 Redis 通道"""
    pubsub = redis_client.pubsub()
    pubsub.subscribe(redis_channel_oh_to_meta)
    
    logger.info(f"开始监听Redis通道: {redis_channel_oh_to_meta}")
    
    # 创建事件循环
    loop = asyncio.new_event_loop()
    
    # 创建一个线程来运行事件循环
    def run_event_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    import threading
    loop_thread = threading.Thread(target=run_event_loop, args=(loop,), daemon=True)
    loop_thread.start()
    
    while True:
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'].decode('utf-8'))
                        conversation_id = data.get('conversation_id')
                        if conversation_id is None:
                            logger.warning(f"收到消息，但conversation_id为空，忽略")
                            continue

                        # 检查该会话是否属于当前机器
                        conversation_machine_key = f"meta-server:{conversation_id}"
                        stored_machine_id = redis_client.get(conversation_machine_key)
                        
                        # 如果会话ID尚未分配给任何机器，则分配给当前机器
                        if not stored_machine_id:
                            # 使用 setnx 确保在并发情况下只有一台服务器能成功设置
                            is_set = redis_client.setnx(conversation_machine_key, machine_id)
                            if is_set:
                                # 设置成功，表示当前服务器获得了该会话的管理权
                                # 设置1小时过期时间（3600秒）
                                redis_client.expire(conversation_machine_key, 36000)
                                logger.info(f"会话 {conversation_id} 已分配给当前机器 {machine_id}，1小时后过期")
                                stored_machine_id = machine_id
                            else:
                                # 设置失败，说明其他服务器已经抢先设置了
                                stored_machine_id = redis_client.get(conversation_machine_key).decode('utf-8')
                                logger.info(f"会话 {conversation_id} 已被机器 {stored_machine_id} 抢先分配")
                        else:
                            stored_machine_id = stored_machine_id.decode('utf-8')
                            # 刷新过期时间
                            redis_client.expire(conversation_machine_key, 36000)
                        
                        # 如果会话不属于当前机器，则忽略该消息
                        if stored_machine_id != machine_id:
                            logger.info(f"会话 {conversation_id} 属于机器 {stored_machine_id}，当前机器 {machine_id} 忽略此消息")
                            continue
                    
                        future = asyncio.run_coroutine_threadsafe(handle_message(data), loop)
                    except json.JSONDecodeError:
                        logger.error(f"JSON解析错误: {message['data']}")
                    except Exception as e:
                        logger.error(f"处理消息异常: {e}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            logger.warning(f"Redis监听器发生错误: {str(e)}...")

def main():
    try:
        logger.info("正在启动Redis监听服务...")
        
        # 启动Redis监听
        listen_to_redis()
        
    except Exception as e:
        logger.error(f"Redis连接错误: {e}")

if __name__ == "__main__":
    main()

