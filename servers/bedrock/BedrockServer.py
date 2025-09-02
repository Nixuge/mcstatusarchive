import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
from time import time
from typing import Any, Optional
from mcstatus import BedrockServer
from mcstatus.responses import BedrockStatusResponse
from database.DbQueries import BedrockQueries

from servers.Server import ServerSv

from database.DbUtils import ServerType, DbUtils
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.Errors import ERRORS
from vars.config import Timings

class BEDROCK_FIELD(Enum):
    save_time = 1
    players_on = 2
    players_max = 3
    ping = 4
    version_protocol = 5
    version_name = 6
    version_brand = 7
    motd = 8
    gamemode = 9
    map = 10

@dataclass
class BedrockValues:
    save_time: int
    players_on: int
    players_max: int
    ping: int
    version_protocol: int
    version_name: str
    version_brand: str
    motd: Any
    gamemode: Optional[str]
    map: Optional[str]
    
    def update_using_response_get_changed(self, status: BedrockStatusResponse) -> list[BEDROCK_FIELD]:
        changed: list[BEDROCK_FIELD] = []

        rn = int(time())
        if self.save_time != rn: # Pretty sure this is always true for obv reasons but just in case
            changed.append(BEDROCK_FIELD.save_time)
            self.save_time = rn

        if self.players_on != status.players.online:
            changed.append(BEDROCK_FIELD.players_on)
            self.players_on = status.players.online
        if self.players_max != status.players.max:
            changed.append(BEDROCK_FIELD.players_max)
            self.players_max = status.players.max

        self.ping = int(status.latency) # Always update ping to serve as a reference point.
        changed.append(BEDROCK_FIELD.ping)

        if self.version_protocol != status.version.protocol:
            changed.append(BEDROCK_FIELD.version_protocol)
            self.version_protocol = status.version.protocol
        if self.version_name != status.version.name:
            changed.append(BEDROCK_FIELD.version_name)
            self.version_name = status.version.name
        if self.version_brand != status.version.brand:
            changed.append(BEDROCK_FIELD.version_brand)
            self.version_brand = status.version.brand

        if self.motd != status.motd.raw:
            changed.append(BEDROCK_FIELD.motd)
            self.motd = status.motd.raw
        if self.gamemode != status.gamemode:
            changed.append(BEDROCK_FIELD.gamemode)
            self.gamemode = status.gamemode
        if self.map != status.map_name:
            changed.append(BEDROCK_FIELD.map)
            self.map = status.map_name
        
        return changed

class BedrockDbHandler:
    pass

class BedrockServerSv(ServerSv):
    server: BedrockServer
    insert_query: str

    values: BedrockValues

    async def __init__(self, table_name: str, ip: str, port: int = 19132) -> None:
        # inheriting
        await super().__init__(table_name, ip, port)
        # get non changing values
        self.server = BedrockServer.lookup(ip, port) #bedrock doesn't need/have async lookup
        self.insert_query = BedrockQueries.get_insert_query(table_name)
        # create db if not present TODO
        # DBQUEUES.db_queue_bedrock.add_important_instruction(
        #     BedrockQueries.get_create_table_query(table_name)
        # )
        # load last values from db (if any)
        # self.values = DbUtils.get_previous_values_from_db(
        #     DBINSTANCES.bedrock_instance.cursor, table_name, ServerType.BEDROCK, LAST_BEDROCK_VALUES
        # )

    async def save_status(self):
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                status = await self.server.async_status()
        except TimeoutError:
            logging.warn(f"ERRORSPLIT{self.ip}: {ERRORS.get('Timeout')}")
            return
        except Exception as e:
            e = str(e)
            if "[Errno 111]" in e:
                formated_error = ERRORS.get("ConnectCallFailed")
            else:
                formated_error = ERRORS.get(e, 'Unknown error happened ' + e)

            logging.warn(f"ERRORSPLIT{self.ip}: {formated_error}")
            return

        changed_fields = self.values.update_using_response_get_changed(status)

        # TODO: USE NEW SYSTEM
        DBQUEUES.db_queue_bedrock.add_instuction(self.insert_query, data_list)
