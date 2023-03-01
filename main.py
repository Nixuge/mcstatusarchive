#!/bin/python3.11

import asyncio
from time import time
from servers.ServersLoader import ServersLoader
from vars.DbQueues import DBQUEUES
from vars.Timings import Timings


async def main():
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_bedrock.start()

    servers = await ServersLoader("z_servers/servers.json").parse()
    print(f"{len(servers)} servers loaded.")

    await save_every_x_secs(servers)


async def save_every_x_secs(servers: list):
    every = Timings.save_every
    while True:
        start_time = int(time())
        await run_batch(servers)
        
        print("[Waiting for timer to finish...]")
        while start_time + every > int(time()):
            await asyncio.sleep(.01)

async def run_batch(servers: list):
    print("== Starting batch ==")
    tasks = []
    for server in servers:
        tasks.append(server.save_status())

    await asyncio.gather(*tasks)
    print("== Done with batch ==")


if __name__ == "__main__":
    asyncio.run(main())
