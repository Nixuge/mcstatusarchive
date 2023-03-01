#!/bin/python3.11

import asyncio
from servers.JavaServer import JavaServerSv
from servers.ServersLoader import ServersLoader
from vars.DbQueues import DBQUEUES


async def main():
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_bedrock.start()

    servers = await ServersLoader("z_servers/servers.json").parse()
    print(f"{len(servers)} servers loaded.")
    
    input("start?")
    
    tasks = []
    for server in servers:
        tasks.append(server.save_status())

    await asyncio.gather(*tasks)
    
    print("done: " + str(len(tasks)))

asyncio.run(main())


