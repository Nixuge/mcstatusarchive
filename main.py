#!/bin/python3.11

# Needs to be on top of everything for it to propagate to imports
import logging
import os
import signal
from utils.logger import get_proper_logger
from vars.Errors import ERROR_HAPPENED
DEBUG_LOG = False
logger = get_proper_logger(logging.getLogger("root"), DEBUG_LOG)

import asyncio
from asyncio import Task
from time import time
from typing import Coroutine
from servers.BedrockServer import BedrockServerSv
from servers.JavaServer import JavaServerSv
from servers.ServersLoader import ServersLoader
from vars.Timings import Timings
from vars.DbQueues import DBQUEUES

async def save_every_x_secs(servers: list):
    every = Timings.save_every
    while True:
        if ERROR_HAPPENED["db"]:
            logging.critical("KILLING THE APP DUE TO A DB ERROR.")
            os.kill(os.getpid(), signal.SIGUSR1)
        
        start_time = int(time())
        await run_batch_limit(servers)

        logging.info("[Waiting for timer to finish...]")
        while start_time + every > int(time()):
            await asyncio.sleep(.01)


async def run_batch_raw(servers: list[JavaServerSv | BedrockServerSv]):
    logging.info("== Starting batch ==")
    tasks: list[Coroutine] = []
    for server in servers:
        tasks.append(server.save_status())

    await asyncio.gather(*tasks)
    logging.info("== Done with batch ==")


async def run_batch_limit(servers: list[JavaServerSv | BedrockServerSv], task_limit: int = 30):
    logging.info("== Starting batch ==")

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
        # logging.info(f"Remaining tasks: {len(running_tasks)}, Remaining servers: {len(to_add)}")

    logging.info("== Done with batch ==")


async def main():
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_bedrock.start()

    servers = await ServersLoader("servers.json").parse()
    logging.info(f"{len(servers)} servers loaded.")

    await save_every_x_secs(servers)


if __name__ == "__main__":
    asyncio.run(main())
