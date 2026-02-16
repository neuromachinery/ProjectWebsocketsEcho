import asyncio
import threading
import websockets
import queue
from json import dumps, loads
from os import path
from time import time
LOGFILE = "log.log"
HOST_RELATIONAL_DICTIONARY = {}
HOST_REGISTRATION_DICTIONARY = {}
CLIENT_RELATIONAL_DICTIONARY = {}
CLIENT_REGISTRATION_DICTIONARY = {}
DICTIONARIES = (HOST_RELATIONAL_DICTIONARY,HOST_REGISTRATION_DICTIONARY,CLIENT_REGISTRATION_DICTIONARY,CLIENT_RELATIONAL_DICTIONARY)
#MESSAGE_QUEUE defined in main()
LOG_LEVEL = 2
def log(*args,**kwargs):
    try:
        if LOG_LEVEL!=0:
            with open(LOGFILE,"a",encoding="utf-8") as file:
                file.write(f"[{time()}] args-({str(args)})\nkwargs-({str(kwargs)})\n{'' if LOG_LEVEL<2 else DICTIONARIES}\n\n")
            print(*args,**kwargs)
    except Exception as E:
        print(str(E))
def host_reg(websocket,info=None):
    'message -> info in format {key:val,key:val,...}; not necessary; will fail if already registered.'
    log("host_reg")
    host_id = str(websocket.id)
    res = HOST_RELATIONAL_DICTIONARY.get(host_id,None)
    if not res:
        HOST_REGISTRATION_DICTIONARY[host_id] = {"websocket":websocket,**info}
        HOST_RELATIONAL_DICTIONARY[host_id]=dict()
        log(HOST_REGISTRATION_DICTIONARY[host_id])
        return True

    return False
def client_reg(websocket, host_id=None):
    'TODO'
    log("client_reg")
    res = HOST_RELATIONAL_DICTIONARY.get(host_id,None)
    log(f"host id:{host_id},\nhost_rel:{HOST_RELATIONAL_DICTIONARY},\nhost_dict:{HOST_REGISTRATION_DICTIONARY},\nres:{res}")
    if res!=None:
        client_id = str(websocket.id)
        if CLIENT_RELATIONAL_DICTIONARY.get(client_id,None) != None:return False
        HOST_RELATIONAL_DICTIONARY[host_id][client_id] = websocket
        CLIENT_RELATIONAL_DICTIONARY[client_id] = {host_id:HOST_REGISTRATION_DICTIONARY[host_id]["websocket"]}
        CLIENT_REGISTRATION_DICTIONARY[client_id] = {"websocket":websocket,}
        return True

    return False
def send(websocket, message=None):
    'TODO'
    log("send")
    user_id = str(websocket.id)
    res = next(item for item in (HOST_RELATIONAL_DICTIONARY.get(user_id,None),CLIENT_RELATIONAL_DICTIONARY.get(user_id,None),False) if item is not None)
    log(f"user_id:{user_id},\nmessage{message},\nhost_rel:{HOST_RELATIONAL_DICTIONARY},\ncli_rel:{CLIENT_RELATIONAL_DICTIONARY},\nres:{res}")
    if res:
        for sub_id,sub_ws in res.items():
            log(f"sending to {sub_id}")
            echo(sub_ws,dumps({"type":"message","message":message},ensure_ascii=False))
        log("yey")
        return True

    return False
def get_hosts(websocket,_=None):
    'TODO'
    try:
        log("get_host")
        result = {"type":"hosts","message":dict()}
        for key1,val1 in HOST_REGISTRATION_DICTIONARY.items():
            val = {}
            for key2,val2 in val1.items():
                if key2=="websocket": continue
                val[key2] = val2
            result["message"] = {key1:val}
        log(result)
        echo(websocket,dumps(result,ensure_ascii=False))
    except Exception as E:
        log(str(E))
        return False
    return True
def get_clients(websocket,_=None):
    'TODO'
    try:
        log("get_clients")
        host_id = str(websocket.id)
        result = {"type":"clients","message":",".join(HOST_RELATIONAL_DICTIONARY[host_id].keys())}
        log(result)
        echo(websocket,dumps(result,ensure_ascii=False))
        return True
    except Exception as E:
        log(str(E))
        return False
def info_change(websocket,info=None):
    'TODO'
    try:
        host_id = str(websocket.id)
        host_info = HOST_REGISTRATION_DICTIONARY.get(host_id,None)
        if not host_info:return False
        HOST_REGISTRATION_DICTIONARY[host_id] = {"websocket":websocket,**info}
        log(HOST_REGISTRATION_DICTIONARY[host_id])

    except Exception as E:
        log(str(E))
        return False
    return True
def disconnect(websocket,message):
    'TODO'
    try:
        del_id = str(websocket.id)
        if CLIENT_REGISTRATION_DICTIONARY.get(del_id,None):
            host_id = next(iter(CLIENT_RELATIONAL_DICTIONARY[del_id]))
            print("########################################")
            print(HOST_REGISTRATION_DICTIONARY)
            print(HOST_REGISTRATION_DICTIONARY[host_id])
            print(HOST_REGISTRATION_DICTIONARY[host_id]["websocket"])
            print("########################################")
            host_websocket = HOST_REGISTRATION_DICTIONARY[host_id]["websocket"]
            echo(host_websocket,message)
            HOST_RELATIONAL_DICTIONARY[host_id].pop(del_id,None)
        if HOST_REGISTRATION_DICTIONARY.get(del_id,None):
            for client_id,client_socket in HOST_REGISTRATION_DICTIONARY.copy()[del_id].items():
                echo(client_socket,message)
                CLIENT_RELATIONAL_DICTIONARY.pop(client_id)
        for dict_for_del in DICTIONARIES:
            dict_for_del.pop(del_id,None)
    except Exception as E:
        log("CRASH",str(E),type(E))
        return False
    return True
def echo(websocket,message=None):
    'TODO'
    MESSAGE_QUEUE.put_nowait(websocket.send(message))
    return True
def log_upload(websocket,message=None):
    'TODO'
    seek,read = map(int,message.split(",")) if message else 0,-1
    with open(LOGFILE,"r",encoding="utf-8") as log_file:
        log_file.seek(seek)
        logs = log_file.read(read)
    echo(websocket,logs)
    return True
def info_upload(websocket,_=None):
    'TODO'
    res = {
        "HOST_RELATIONAL":HOST_RELATIONAL_DICTIONARY,
        "HOST_REGISTRATION":HOST_REGISTRATION_DICTIONARY,
        "CLIENT_RELATIONAL":CLIENT_RELATIONAL_DICTIONARY,
        "CLIENT_REGISTRATION":CLIENT_REGISTRATION_DICTIONARY
        }
    echo(websocket,dumps(res))
    return True
def man(websocket,_=None):
    'TODO'
    result = ""
    for command,func in COMMANDS.items():
        result+=f"'{command}'->'{func.__doc__}'\n"
    echo(websocket,result)
    return True
def handle_messages(queue:queue.Queue):
    while True:
        try:
            async def handle():
                log("message handler started")
                while True:
                    log("waiting for message")
                    try:
                        await queue.get()
                    except websockets.exceptions.ConnectionClosedError:pass
                    except websockets.exceptions.ConnectionClosedOK:pass
                    except websockets.exceptions.ConnectionClosed:pass
                    finally:
                        queue.task_done()
                    log("sent message")
            asyncio.run(handle())
        except Exception as E:
            log("CRASH",str(E),type(E))
        
    

async def handle_connection(websocket):
    while True:
        try:
            async for message in websocket:
                log(f"{str(websocket.id)} -> {message}")
                message = loads(message)
                if not COMMANDS[message["type"]](websocket,message.get("message",None)):
                    log("fuck off")
                    await websocket.send(dumps('{"type":"error","message":"oops somethings gone wrong vwv"}'))
        except websockets.exceptions.ConnectionClosedError:pass
        except Exception as E:
            log("CRASH",str(E),type(E))
        finally:
            try:
                disconnect(websocket,dumps({"type":"disconnect","message":str(websocket.id)}))
                await websocket.close()
            except TypeError:
                del_id = str(websocket.id)
                log(del_id,CLIENT_REGISTRATION_DICTIONARY,HOST_RELATIONAL_DICTIONARY,CLIENT_REGISTRATION_DICTIONARY.get(del_id,None))
            except Exception as E:
                log("CRASH",str(E),type(E))

COMMANDS = {
    "HOST_REG":host_reg,
    "CLI_REG":client_reg,
    "SEND":send,
    "GET_HOSTS":get_hosts,
    "GET_CLIENTS":get_clients,
    "DISCONNECT":disconnect,
    "ECHO":echo,
    "INFO_CHANGE":info_change,
    "GIMME_LOGS":log_upload,
    "GIMME_INFO":info_upload,
    "MAN":man,
    #"GLOBAL_BROADCAST":global_broadcast,
    #"LOCAL_BROADCAST":local_broadcast,
    }

async def main():
    global MESSAGE_QUEUE
    MESSAGE_QUEUE = queue.Queue()
    threading.Thread(target=handle_messages,args=(MESSAGE_QUEUE,),daemon=True).start()
    while True:
        try:
            async with websockets.serve(handle_connection, "0.0.0.0", 8766):
                await asyncio.Future()
        except Exception as E:
            log("CRASH",str(E),type(E))
        

if __name__ == "__main__":
    
    asyncio.run(main())
