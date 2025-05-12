
from metagpt.schema import Document
from time import sleep

g_doc_recv :Document
g_continue : bool = False
g_msg_continue : bool = False

g_msg_recv: str = ""

def set_doc_for_recv(doc:Document):
    global g_doc_recv
    g_doc_recv = doc

def get_doc_for_recv():
    global g_doc_recv
    return g_doc_recv

def notify_continue(doc: Document):
    global g_doc_recv
    global g_continue
    if doc is g_doc_recv:
      g_continue = True  

def wait_for_continue(doc: Document):
    global g_doc_recv
    global g_continue
    if doc is g_doc_recv:
        while True:
            if g_continue == True:
                g_continue = False
                break
            else:
                sleep(0.5)
    
def set_msg_for_recv(msg:str):
    global g_msg_recv
    g_msg_recv = msg

def get_msg_for_recv():
    global g_msg_recv
    return g_msg_recv

def notify_msg_continue():
    #global g_msg_recv
    global g_msg_continue
    #if msg is g_msg_recv:
    #print("\n-----------notify_msg_continue-----------------\n")
    #print(g_msg_recv)
    g_msg_continue = True

def wait_for_msg_continue():
    global g_msg_continue
    #global g_msg_recv
    #if msg is g_msg_recv:
    while True:
        if g_msg_continue == True:
            g_msg_continue = False
            break
        else:
            sleep(0.5)
