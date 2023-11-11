#!/bin/python3.11

import asyncio
from asyncio import Task
import logging
from time import time
from typing import Coroutine
from servers.BedrockServer import BedrockServerSv
from servers.JavaServer import JavaServerSv
from servers.ServersLoader import ServersLoader
from vars.DbQueues import DBQUEUES
from vars.Timings import Timings


async def save_every_x_secs(servers: list):
    every = Timings.save_every
    while True:
        start_time = int(time())
        await run_batch_limit(servers)

        print("[Waiting for timer to finish...]")
        while start_time + every > int(time()):
            await asyncio.sleep(.01)


async def run_batch_raw(servers: list[JavaServerSv | BedrockServerSv]):
    print("== Starting batch ==")
    tasks: list[Coroutine] = []
    for server in servers:
        tasks.append(server.save_status())

    await asyncio.gather(*tasks)
    print("== Done with batch ==")


async def run_batch_limit(servers: list[JavaServerSv | BedrockServerSv], task_limit: int = 10):
    print("== Starting batch ==")

    running_tasks: list[Task] = []

    to_add = list(servers)

    while True:
        for server in to_add:
            if (len(running_tasks) > task_limit):
                break
            running_tasks.append(asyncio.create_task(server.save_status()))
            to_add.remove(server)

        for task in running_tasks:
            if task.done():
                running_tasks.remove(task)

        if len(running_tasks) == 0:
            break

        await asyncio.sleep(.2)
        # print(f"Remaining tasks: {len(running_tasks)}, Remaining servers: {len(to_add)}")

    print("== Done with batch ==")


logging.warning("TEST DEBUG MESSAGE")

async def main():
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_bedrock.start()

    servers = await ServersLoader("servers.json").parse()
    print(f"{len(servers)} servers loaded.")

    await save_every_x_secs(servers)


if __name__ == "__main__":
    asyncio.run(main())
