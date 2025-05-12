
from metagpt.schema import Document
from time import sleep

# Dictionary to maintain conversation state per connection
connection_states = {}

def get_connection_state(sio, sid):
    """Get or create state for a connection"""
    key = (sio.sid, sid)
    if key not in connection_states:
        connection_states[key] = ConnectionState(sio)
        print(f"#########connect state of key: {key}, sio.sid:{sio.sid},session id{sid}")
    return connection_states[key]

class ConnectionState:
    def __init__(self, sio):
        self.sio = sio
        self.sid_stream_obj = {}
        self.doc_recv = None
        self.msg_recv = ""
        self.continue_flag = False
        self.msg_continue_flag = False

def set_doc_for_recv(sio, sid, doc:Document):
    state = get_connection_state(sio, sid)

    #print(f"######### continue wait for sig sio: {sio}, sid:{sid}")
    while not state.continue_flag:
        sleep(0.2)
    state.continue_flag = False
    doc.content = state.doc_recv
    print(f"######### continue wait get doc: {doc.content}")


def get_msg_for_recv(sio, sid):
    state = get_connection_state(sio, sid)

    #print(f"######### continue wait for sig sio: {sio}, sid:{sid}")
    while not state.msg_continue_flag:
        sleep(0.2)
    state.msg_continue_flag = False
    content = state.msg_recv
    print(f"######### continue wait get msg: {content}")
    return content
