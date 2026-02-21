import asyncio
from websockets.asyncio.server import serve
from websockets.protocol import State
from websockets.exceptions import ConnectionClosedOK
from websockets.asyncio.server import ServerConnection
from json import dumps, loads
from os import path
from time import time
LOGFILE = "log.log"
HOST_RELATIONAL_DICTIONARY = {}
HOST_REGISTRATION_DICTIONARY = {}
CLIENT_RELATIONAL_DICTIONARY = {}
CLIENT_REGISTRATION_DICTIONARY = {}
DICTIONARIES = (HOST_RELATIONAL_DICTIONARY,HOST_REGISTRATION_DICTIONARY,CLIENT_REGISTRATION_DICTIONARY,CLIENT_RELATIONAL_DICTIONARY)
LOG_LEVEL = 2
def log(*args,**kwargs):
    if LOG_LEVEL!=0:
        with open(LOGFILE,"a",encoding="utf-8") as file:
            file.write(f"[{time()}] args-({str(args)})\nkwargs-({str(kwargs)})\n{'' if LOG_LEVEL<2 else DICTIONARIES}\n\n")
        print(*args,**kwargs)

async def host_reg(websocket,info=None):
    'message -> info in format {key:val,key:val,...}; not necessary; will fail if already registered.'
    log("host_reg")
    a = {"websocket":websocket,**info}
    host_id = str(websocket.id)
    res = HOST_RELATIONAL_DICTIONARY.get(host_id,None)
    if not res:
        HOST_REGISTRATION_DICTIONARY[host_id] = a
        HOST_RELATIONAL_DICTIONARY[host_id]=dict()
        log(HOST_REGISTRATION_DICTIONARY[host_id])
        return 7

    return 1
async def client_reg(websocket, host_id=None):
    'message -> host id string in format "25895680134601346"; absolutely necessary; will fail if already registered'
    log("client_reg")
    res = HOST_RELATIONAL_DICTIONARY.get(host_id,None)
    log(f"host id:{host_id},\nhost_rel:{HOST_RELATIONAL_DICTIONARY},\nhost_dict:{HOST_REGISTRATION_DICTIONARY},\nres:{res}")
    if res!=None:
        client_id = str(websocket.id)
        if CLIENT_RELATIONAL_DICTIONARY.get(client_id,None) != None:return 1
        HOST_RELATIONAL_DICTIONARY[host_id][client_id] = websocket
        CLIENT_RELATIONAL_DICTIONARY[client_id] = {host_id:HOST_REGISTRATION_DICTIONARY[host_id]["websocket"]}
        CLIENT_REGISTRATION_DICTIONARY[client_id] = {"websocket":websocket,}
        return 8

    return 2
async def direct(websocket, message=None):
    'message -> {"recipients":["152656136","563461346"],"message":"the message itself"}; sends message to selected recipients. Will not send to clients not subscribed to you; crashes if no message'
    log("direct")
    host_id = str(websocket.id)
    if not host_id in HOST_REGISTRATION_DICTIONARY or host_id in CLIENT_REGISTRATION_DICTIONARY:return 4
    for client_id, client_websocket in HOST_RELATIONAL_DICTIONARY[host_id]:
        if client_id in message["recipients"]:
            await echo(client_websocket,message["message"])
async def kick(websocket,client_id=None):
    'message -> 53415345616; tries to delete specified client from your relational dictionary; will fail if not host or no client specified or message isn\'t a string'
    if not client_id or type(client_id)==dict: return 6
    host_id = str(websocket.id)
    if not host_id in HOST_REGISTRATION_DICTIONARY: return 4
    HOST_RELATIONAL_DICTIONARY[host_id].pop(client_id,None)
    return 11

async def send(websocket, message=None):
    'message -> uhh, the message? in format fuck-all, to send to clients if you\'re host and vice reversa; strictly speaking not required but like why would you do that; will fail if you\'re crazy'
    log("send")
    user_id = str(websocket.id)
    res = next(item for item in (HOST_RELATIONAL_DICTIONARY.get(user_id,None),CLIENT_RELATIONAL_DICTIONARY.get(user_id,None),False) if item is not None)
    log(f"user_id:{user_id},\nmessage{message},\nhost_rel:{HOST_RELATIONAL_DICTIONARY},\ncli_rel:{CLIENT_RELATIONAL_DICTIONARY},\nres:{res}")
    if res:
        for sub_id,sub_ws in res.items():
            log(f"sending to {sub_id}")
            await echo(sub_ws,dumps({"type":"message","message":message},ensure_ascii=False))
        log("yey")
        return 10

    return 2
async def get_hosts(websocket,_=None):
    'message (of any size) -> "tl;dr. here\'s available hosts. whateverr"'
    log("get_host")
    result = {"type":"hosts","message":dict()}
    for key1,val1 in HOST_REGISTRATION_DICTIONARY.items():
        val = {}
        for key2,val2 in val1.items():
            if key2=="websocket": continue
            val[key2] = val2
        result["message"].update({key1:val})
    log(result)
    await echo(websocket,dumps(result,ensure_ascii=False))
    return 0
async def get_clients(websocket,_=None):
    'message (of any size) -> "tl;dr. here\'s available clients. whateverr"; format {"type":"clients","message":"15135252,65426756136,..."}; will fail if you aren\'t a host'
    log("get_clients")
    host_id = str(websocket.id)
    if host_id not in HOST_REGISTRATION_DICTIONARY:return 4
    result = {"type":"clients","message":'["'+'","'.join(HOST_RELATIONAL_DICTIONARY[host_id].keys())+'"]'}
    log(result)
    await echo(websocket,dumps(result,ensure_ascii=False))
    return 0

async def info_change(websocket,info=None):
    'message -> info json dictionary for yo info in format {"key":"val","key":"val",...};required;will fail if- who tf are you?'
    host_id = str(websocket.id)
    host_info = HOST_REGISTRATION_DICTIONARY.get(host_id,None)
    if not host_info:return 3
    HOST_REGISTRATION_DICTIONARY[host_id] = {"websocket":websocket,**info}
    log(HOST_REGISTRATION_DICTIONARY[host_id])
    return 9
async def disconnect(websocket,message):
    'message -> message to broadcast to everyone who knows you;not required;will not fail no matter what'
    del_id = str(websocket.id)
    if CLIENT_REGISTRATION_DICTIONARY.get(del_id,None):
        host_id = next(iter(CLIENT_RELATIONAL_DICTIONARY[del_id]))
        host_websocket = HOST_REGISTRATION_DICTIONARY[host_id]["websocket"]
        await echo(host_websocket,message)
        HOST_RELATIONAL_DICTIONARY[host_id].pop(del_id,None)
    elif HOST_REGISTRATION_DICTIONARY.get(del_id,None):
        for client_id,client_socket in HOST_RELATIONAL_DICTIONARY.copy()[del_id].items():
            await echo(client_socket,message)
            CLIENT_RELATIONAL_DICTIONARY.pop(client_id,None)
    for dict_for_del in DICTIONARIES:
        dict_for_del.pop(del_id,None)
    return 0
async def echo(websocket:ServerConnection, message=None):
    'message -> <- message '
    #print(f"###{websocket} [{type(websocket)}] ({message}) <{type(message)}>")
    if message == None:return 0
    if websocket.state != State.OPEN:
        return  # Skip dead connections
    if type(message)==dict:
        message=dumps(message)
    await websocket.send(message)
    log(f"({str(websocket.id)}) <- [{message}]")

    return 0
async def whoami(websocket,_=None):
    'message -> idc; returns YOUR id'
    await echo(websocket,dumps({"type":"id","message":str(websocket.id)}))
    return 0
async def log_upload(websocket,message=None):
    'lemme see those logs'
    seek,read = map(int,message.split(",")) if message else 0,-1
    with open(LOGFILE,"r",encoding="utf-8") as log_file:
        log_file.seek(seek)
        logs = log_file.read(read)
    await echo(websocket,logs)
    return 0
async def info_upload(websocket,_=None):
    'lemme see thiss data'
    res = {
        "HOST_RELATIONAL":HOST_RELATIONAL_DICTIONARY,
        "HOST_REGISTRATION":HOST_REGISTRATION_DICTIONARY,
        "CLIENT_RELATIONAL":CLIENT_RELATIONAL_DICTIONARY,
        "CLIENT_REGISTRATION":CLIENT_REGISTRATION_DICTIONARY
        }
    await echo(websocket,dumps(res))
    return 0
async def man(websocket,_=None):
    'The Manual. You\'re reading one.'
    result = ""
    for command,func in COMMANDS.items():
        result+=f"'{command}'->'{func.__doc__}'\n"
    await echo(websocket,result)
    return 0

# Global connections set to cleanup dead sockets
connected_websockets = set()

async def handle_connection(websocket:ServerConnection):
    connected_websockets.add(websocket)
    try:
        async for message in websocket:
            log(f"{str(websocket.id)} -> {message}")
            message = loads(message)
            res = await COMMANDS[message["type"]](websocket, message.get("message", None))
            if res != 0:
                await echo(websocket,dumps({"type": "error", "message": ERROR_CODES.get(res, "whar?")}))
    except Exception as e:
        log(f"WS processor ended for {websocket.id}: {e}")


COMMANDS = {
    "HOST_REG":host_reg,
    "CLI_REG":client_reg,
    "SEND":send,
    "DIRECT":direct,
    "KICK":kick,
    "GET_HOSTS":get_hosts,
    "GET_CLIENTS":get_clients,
    "DISCONNECT":disconnect,
    "ECHO": echo,
    "INFO_CHANGE":info_change,
    "GIMME_LOGS":log_upload,
    "GIMME_INFO":info_upload,
    "WHOAMI":whoami,
    "MAN":man,
    
    #"GLOBAL_BROADCAST":global_broadcast,
    #"LOCAL_BROADCAST":local_broadcast,
    }
ERROR_CODES = {
    0:"okay :3",
    1:"you already did that",
    2:"there's no one there",
    3:"who are you again?",
    4:"you are a client, not a host",
    5:"you are a host, not a client",
    6:"parameter issue",
    7:"host_reg_success",
    8:"client_reg_success",
    9:"info_changed_success",
    10:"message_sent_success",
    11:"kick_success",
}
async def main():
    global MESSAGE_QUEUE
    MESSAGE_QUEUE = asyncio.Queue()
    asyncio.create_task(cleanup_dead_connections())
    while True:
        async with serve(handler=handle_connection, host="0.0.0.0", port=10000):
            await asyncio.Future()


async def cleanup_dead_connections():
    while True:
        await asyncio.sleep(10)
        global connected_websockets
        dead = [ws for ws in connected_websockets if ws.state in (State.CLOSED,State.CLOSING)]
        for ws in dead:
            await disconnect(ws,dumps({"type":"disconnect","message":str(ws.id)}))
            connected_websockets.discard(ws)        
        

if __name__ == "__main__":
    print("started")
    asyncio.run(main())
