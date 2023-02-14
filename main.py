#!/bin/python3
import asyncio
from servers.bedrock import BedrockServerManager
from servers.java import JavaServerManager
import json

#for some weird reason need to first instantiate and then lookup
#TODO: redo that shitty af multithreading kinda
#bc its not even multithreading rn
#if i just give up: just run like 1/2 server per thread and thats all


def load_json():
    list_java: list[JavaServerManager] = []
    list_pe: list[BedrockServerManager] = []
    with open("servers.json", "r") as file:
        dico = json.load(file)
    
    for value in dico["java"]:
        list_java.append(JavaServerManager(value, dico["java"][value]))
    for value in dico["bugrock"]:
        list_pe.append(BedrockServerManager(value, dico["bugrock"][value]))

    return list_java, list_pe


def chunks(lst, n = 2):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
    


async def run_multiple(server_groups: list):
    while True:
        tasks = []
        for group in server_groups:
            tasks.append(asyncio.create_task(save_all(group)))
        
        await asyncio.sleep(30)
        print("===done waiting 30s===")
        for task in tasks:
            await task
        print("===done awaiting for tasks leftover===")
        

async def save_all(servers: list[JavaServerManager | BedrockServerManager]):
    tasks = []
    for server in servers:
        tasks.append(asyncio.create_task(server.add_data_db()))
        
    # in case some tasks are still unfinished after the 10s
    # for task in tasks:
    #     await task 

java_servers, pe_servers = load_json()
full = java_servers + pe_servers
# thread_lists_java = list(chunks(java_servers))
# thread_lists_pe = list(chunks(pe_servers))

full_list = list(chunks(full))

asyncio.run(run_multiple(full_list))

# asyncio.run(java_servers[0].add_data_db())

# async def main():
#     for key in java_servers:
#         await key.add_data_db()

# asyncio.run(main())


# HOW THIS WORKS:
# - the script grabs every info about the server & saves it to db
# - next time the save runs, if all previous long standing info (motd, version, etc) 
# --- are the same, just fill those w NULLs (note that playercount still updates)
# --- However, if just 1 value is different, the whole row update (for easier queries)

#TODO: more flexibility.
#eg, when a motd is changed, sometimes avoid changing everything
#tbh will prolly make an option to change it either all or one at a time
