import asyncio
import threading
from servers.bedrock import BedrockServerManager
from servers.java import JavaServerManager
import time

#for some weird reason need to first instantiate and then lookup

pe_servers: list[BedrockServerManager] = [
    # BedrockServerManager("mineplex", "pe.mineplex.com")
]

java_servers: list[JavaServerManager] = [
    JavaServerManager("Hypickle", "hypixel.net"),
    JavaServerManager("Nixuge", "play.nixuge.me"),
    JavaServerManager("Mineplex", "mineplex.com"),
    JavaServerManager("Cubecraft", "cubecraft.net"),
    JavaServerManager("cubekrowd", "cubekrowd.net"),
]

def chunks(lst, n = 4):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
    
thread_lists_java = list(chunks(java_servers))
thread_lists_pe = list(chunks(pe_servers))


async def save_all(servers: list):
    while True:
        tasks = []
        for server in java_servers:
            tasks.append(asyncio.create_task(server.add_data_db()))

        await asyncio.sleep(4)
        
        # in case some tasks are still unfinished after the 10s
        for task in tasks:
            await task 
     
for java_thread in thread_lists_java:
    asyncio.run(save_all(java_thread))


for pe_thread in thread_lists_pe:
    asyncio.run(save_all(pe_thread))


# HOW THIS WORKS:
# - the script grabs every info about the server & saves it to db
# - next time the save runs, if all previous long standing info (motd, version, etc) 
# --- are the same, just fill those w NULLs (note that playercount still updates)
# --- However, if just 1 value is different, the whole row update (for easier queries)

#TODO: more flexibility.
#eg, when a motd is changed, sometimes avoid changing everything
#tbh will prolly make an option to change it either all or one at a time