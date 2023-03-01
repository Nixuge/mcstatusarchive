#!/bin/python3.11

import asyncio
from time import time
from typing import Coroutine
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
    tasks: list[Coroutine] = []
    for server in servers:
        tasks.append(server.save_status())
    # to_add = list(servers)
    # while True:
    #     # only run 30 at once to avoid overloading the poor cpu
    #     # doesn't work w how i made things rn, to fix when possible
    #     left_to_add = len(to_add)
    #     if len(tasks) < 30:
    #         diff = 30 - len(tasks)
    #         if diff > left_to_add:
    #             diff = left_to_add
            
    #         for _ in range(diff):
    #             tasks.append(to_add[0].save_status())
    #             to_add.pop(0)

    #         for task in list(tasks):
    #             if not task.cr_running:
    #                 tasks.remove(task)

    await asyncio.gather(*tasks)
    print("== Done with batch ==")


if __name__ == "__main__":
    asyncio.run(main())
