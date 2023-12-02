#!/bin/python3.11

# Needs to be on top of everything for it to propagate to imports
import logging
from utils.logger import get_proper_logger
from vars.InvalidServers import INVALID_JAVA_SERVERS, InvalidServers
DEBUG_LOG = False
logger = get_proper_logger(logging.getLogger("root"), DEBUG_LOG)

# Rudimentary check.
# Will see for smth more complicated later
import sys
if len(sys.argv) > 1:
    if sys.argv[1] == "maintenance":
        from maintenance.main import maintenance_main
        maintenance_main()
        exit(0)


import os
import signal
from utils.timer import Timer
from vars.Errors import ErrorHandler
from vars.Frontend import FRONTEND_UPDATE_THREAD


import asyncio
from asyncio import Task
from time import time
from typing import Coroutine
from servers.bedrock.BedrockServer import BedrockServerSv
from servers.java.JavaServer import JavaServerSv
from servers.ServersLoader import ServersLoader
from vars.config import Timings
from vars.DbQueues import DBQUEUES

async def save_every_x_secs(servers: list):
    i = 1
    while True:
        try_invalid = False
        if i >= InvalidServers.RETRY_INVALID_EVERY:
            try_invalid = True
            i = 0
        i += 1

        if ErrorHandler.should_stop:
            logging.critical("KILLING THE APP.")
            os.kill(os.getpid(), signal.SIGUSR1)
        
        start_time = int(time())
        await run_batch_limit(servers, try_invalid)

        logging.info("[Waiting for timer to finish...]")
        while start_time + Timings.SAVE_EVERY > int(time()):
            await asyncio.sleep(.01)


async def run_batch_raw(servers: list[JavaServerSv | BedrockServerSv]):
    logging.info("== Starting batch ==")
    tasks: list[Coroutine] = []
    for server in servers:
        tasks.append(server.save_status())

    await asyncio.gather(*tasks)
    logging.info("== Done with batch ==")


async def run_batch_limit(servers: list[JavaServerSv | BedrockServerSv], try_invalid: bool = False, task_limit: int = 75):
    logging.info("== Starting batch ==")
    timer = Timer()

    running_tasks: list[Task] = []

    to_add = []
    for server in servers:
        if type(server) == JavaServerSv:
            if not INVALID_JAVA_SERVERS.is_invalid(server.ip):
                to_add.append(server)
            elif try_invalid: 
                to_add.append(server)
            # else:
                # print(f"Skipped server: {server.ip}")
        elif type(server) == BedrockServerSv:
            to_add.append(server)
    invalid_str = " (Trying invalid servers)" if try_invalid else ""
    logging.info(f"Grabbing {len(to_add)}/{len(servers)} servers.{invalid_str}")

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

    logging.info(f"== Done with batch == ({timer.end()})")


async def main():
    logging.info("Starting.")

    FRONTEND_UPDATE_THREAD.start()

    timer = Timer()
    
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_duplicates_java.start()
    DBQUEUES.db_queue_bedrock.start()

    logging.info(f"Databases loaded. ({timer.step()})")

    servers = await ServersLoader("servers.json").parse()
    logging.info(f"{len(servers)} servers loaded. ({timer.end()})")

    await save_every_x_secs(servers)


if __name__ == "__main__":
    asyncio.run(main())

# IMPORTANT:
# SWITCH FAVICONS FROM A BLOB TO A MD5 AND SAVE THE ICONS LOCALLY, 
# AS SOME SERVERS (8B8T) ARE BLOATING THE DB BY CHANGING FAVICONS QUICKLY