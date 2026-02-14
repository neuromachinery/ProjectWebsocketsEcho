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
def host_reg(websocket,info=None):
    print("host_reg")
    host_id = str(websocket.id)
    res = HOST_REL_DICT.get(host_id,None)
    if not res:
        HOST_DICT[host_id] = {"websocket":websocket,**info}
        HOST_REL_DICT[host_id]=dict()
        return True
    print("fuck",end="")
    return False
def client_reg(websocket, host_id=None):
    print("client_reg")
    res = HOST_REL_DICT.get(host_id,None)
    print(host_id,HOST_REL_DICT,res)
    if res:
        client_id = str(websocket.id)
        HOST_REL_DICT[host_id][client_id] = websocket
        CLIENT_REL_DICT[client_id] = host_id
        CLIENT_DICT[client_id] = {"websocket":websocket,}
        return True
    print("fuck",end="")
    return False
def send(websocket, message=None):
    print("send")
    user_id = str(websocket.id)
    res = next(item for item in (HOST_REL_DICT.get(user_id,False),CLIENT_REL_DICT.get(user_id,False)) if item is not None)
    print(message,HOST_REL_DICT,CLIENT_REL_DICT,res)
    if res:
        for subscriber in res:
            sub = next(item for item in (HOST_DICT.get(subscriber,False),CLIENT_DICT.get(subscriber,False)) if item is not None)
            MESSAGE_QUEUE.put_nowait(sub.websocket.send(dumps({"type":"message","message":message})))
        print("yey")
        return True
    print("fuck",end="")
    return False
def get_hosts(websocket,_=None):
    print("get_host")
    if (len(HOST_DICT.keys())==0): return False
    result = {}
    for key,val in HOST_DICT.items():
        val.pop("websocket")
        result[key]=val
    print(result)
    MESSAGE_QUEUE.put_nowait(websocket.send(dumps(result)))
    return True
def handle_messages(queue:queue):
    async def handle():
        print("message handler started")
        while True:
            print("waiting for message")
            await queue.get()
            print("sent message")
    asyncio.run(handle())
    
        
async def handle_connection(websocket):
    try:
        print()
        async for message in websocket:
            print(f"{str(websocket.id)} -> {message}")
            message = loads(message)
            if not COMMANDS[message["type"]](websocket,message.get("message",None)):
                print("off")
                await websocket.send(dumps({"type":"fuck_off","message":"wtf do you want"}))
    finally:
        del_id = str(websocket.id)
        if res:=CLIENT_DICT.get(del_id,None):HOST_REL_DICT[res].pop(del_id,None)
        if res:=HOST_DICT.get(del_id,None):
            for client,server in CLIENT_REL_DICT.items():
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
message_handler = threading.Thread(target=handle_messages,args=(MESSAGE_QUEUE,))
async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 8766):
        await asyncio.Future()
        

if __name__ == "__main__":
    message_handler.start()
    asyncio.run(main())
