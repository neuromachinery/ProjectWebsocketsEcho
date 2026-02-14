import asyncio
import threading
import websockets
import queue
from json import dumps, loads
HOST_REL_DICT = {}
HOST_DICT = {}
CLIENT_REL_DICT = {}
CLIENT_DICT = {}
MESSAGE_QUEUE = queue.Queue()
LOG_LEVEL = 0
def log(*args):
    if LOG_LEVEL==1:
        print(args)
def host_reg(websocket,info=None):
    log("host_reg")
    host_id = str(websocket.id)
    res = HOST_REL_DICT.get(host_id,None)
    if not res:
        HOST_DICT[host_id] = {"websocket":websocket,**info}
        HOST_REL_DICT[host_id]=dict()
        log(HOST_DICT[host_id])
        return True
    log("fuck",end="")
    return False
def client_reg(websocket, host_id=None):
    log("client_reg")
    res = HOST_REL_DICT.get(host_id,None)
    log(f"host id:{host_id},\nhost_rel:{HOST_REL_DICT},\nhost_dict:{HOST_DICT},\nres:{res}")
    if res!=None:
        client_id = str(websocket.id)
        HOST_REL_DICT[host_id][client_id] = websocket
        CLIENT_REL_DICT[client_id] = {host_id:HOST_DICT[host_id]["websocket"]}
        CLIENT_DICT[client_id] = {"websocket":websocket,}
        return True
    log("fuck",end="")
    return False
def send(websocket, message=None):
    log("send")
    user_id = str(websocket.id)
    res = next(item for item in (HOST_REL_DICT.get(user_id,None),CLIENT_REL_DICT.get(user_id,None),False) if item is not None)
    log(f"user_id:{user_id},\nmessage{message},\nhost_rel:{HOST_REL_DICT},\ncli_rel:{CLIENT_REL_DICT},\nres:{res}")
    if res:
        for sub_id,sub_ws in res.items():
            log(f"sending to {sub_id}")
            MESSAGE_QUEUE.put_nowait(sub_ws.send(dumps({"type":"message","message":message},ensure_ascii=False)))
        log("yey")
        return True
    log("fuck",end="")
    return False
def get_hosts(websocket,_=None):
    log("get_host")
    if (len(HOST_DICT.keys())==0): return False
    result = {}
    for key1,val1 in HOST_DICT.items():
        val = {}
        for key2,val2 in val1.items():
            if key2=="websocket": continue
            val[key2] = val2
        result[key1]=val 
    log(result)
    MESSAGE_QUEUE.put_nowait(websocket.send(dumps(result,ensure_ascii=False)))
    return True
def handle_messages(queue:queue):
    async def handle():
        log("message handler started")
        while True:
            log("waiting for message")
            await queue.get()
            log("sent message")
    asyncio.run(handle())
    
        
async def handle_connection(websocket):
    try:
        log()
        async for message in websocket:
            log(f"{str(websocket.id)} -> {message}")
            message = loads(message)
            if not COMMANDS[message["type"]](websocket,message.get("message",None)):
                log("off")
                await websocket.send(dumps({"type":"fuck_off","message":"wtf do you want"},ensure_ascii=False))
    finally:
        del_id = str(websocket.id)
        if res:=CLIENT_DICT.get(del_id,None):HOST_REL_DICT[res].pop(del_id,None)
        if res:=HOST_DICT.get(del_id,None):
            for client,server in CLIENT_REL_DICT.copy().items():
                if server==del_id:CLIENT_REL_DICT.pop(client)
        for dict_for_del in (HOST_DICT,HOST_REL_DICT,CLIENT_DICT,CLIENT_REL_DICT):
            dict_for_del.pop(del_id,None)
        await websocket.close()

COMMANDS = {
    "HOST_REG":host_reg,
    "CLI_REG":client_reg,
    "SEND":send,
    "GET_HOSTS":get_hosts
    }
message_handler = threading.Thread(target=handle_messages,args=(MESSAGE_QUEUE,),daemon=True)
async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 8766):
        await asyncio.Future()
        

if __name__ == "__main__":
    message_handler.start()
    asyncio.run(main())
