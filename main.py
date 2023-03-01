#!/bin/python3.11

import asyncio
from servers.JavaServer import JavaServerSv
from servers.ServersLoader import ServersLoader
from vars.DbQueues import DBQUEUES




async def main():
    servers = await ServersLoader("z_servers/servers.json").parse()
    print(len(servers))
    # DBQUEUES.db_queue_java.start()
    # # serv = JavaServerSv("pickle", "hypixel.net")
    # for i in range(5):
    #     await asyncio.sleep(1)
    #     await serv.save_status()
    print("done")

asyncio.run(main())


