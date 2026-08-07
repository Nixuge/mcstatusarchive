import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from asyncio import Task
from time import time
import logging

try:
    from utils.logger import get_proper_logger
    logger = get_proper_logger(logging.getLogger("root"), False)
except ImportError:
    logging.basicConfig(level=logging.INFO)

from db.database import Database
from db.schema import SERVER_TYPE_JAVA, SERVER_TYPE_BEDROCK
from config import Paths, Timings
from utils.errors import ErrorHandler
from servers.loader import ServersLoader


async def run_batch_limit(servers: list, task_limit: int = 100):
    logging.info("== Starting batch ==")
    running_tasks: list[Task] = []
    to_add = list(servers)

    while True:
        for server in to_add:
            if (len(running_tasks) > task_limit):
                break
            running_tasks.append(asyncio.create_task(server.poll_and_save()))
            to_add.remove(server)

        for task in running_tasks:
            if task.done():
                running_tasks.remove(task)

        if len(running_tasks) == 0:
            break

        await asyncio.sleep(.2)

    logging.info(f"== Done with batch ==")

async def save_every_x_secs(servers: list):
    while True:
        if ErrorHandler.should_stop:
            logging.critical("Stop instruction found. Now stopping the app.")
            return

        start_time = int(time())
        await run_batch_limit(servers)

        logging.info("[Waiting for timer to finish...]")
        while start_time + Timings.SAVE_EVERY > int(time()):
            await asyncio.sleep(.01)


async def main():
    logging.info("Starting.")

    should_stop = lambda: ErrorHandler.should_stop
    db_java = Database(Paths.DB_PATH_JAVA, SERVER_TYPE_JAVA, should_stop)
    db_bedrock = Database(Paths.DB_PATH_BEDROCK, SERVER_TYPE_BEDROCK, should_stop)
    db_java.start_writer()
    db_bedrock.start_writer()

    servers = await ServersLoader(Paths.SERVERS_JSON, db_java, db_bedrock).parse()
    logging.info(f"{len(servers)} servers loaded.")

    try:
        await save_every_x_secs(servers)
    except asyncio.CancelledError:
        ErrorHandler.should_stop = True
        logging.info("Excepting a graceful stop soon.")

if __name__ == "__main__":
    asyncio.run(main())
