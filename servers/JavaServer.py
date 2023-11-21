import asyncio
import base64
import logging
from time import time
from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
from mcstatus.status_response import JavaStatusPlayer
from database.DbQueries import JavaQueries

from servers.Server import ServerSv

from database.DbUtils import ServerType, DbUtils
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.Errors import ERRORS, ErrorHandler
from vars.Frontend import FRONTEND_UPDATE_THREAD
from vars.Timings import Timings

class JavaServerSv(ServerSv):
    server: JavaServer
    table_name: str
    insert_query: str

    async def __init__(self, table_name: str, ip: str, port: int = 25565) -> None:
        # inheriting
        await super().__init__(table_name, ip, port)
        # get non changing values
        self.table_name = table_name
        self.server = await JavaServer.async_lookup(ip, port)
        self.insert_query = JavaQueries.get_insert_query(table_name)
        # create db if not present
        DBQUEUES.db_queue_java.add_important_instruction(
            JavaQueries.get_create_table_query(table_name)
        )

        # load last values from db (if any)
        self.values = DbUtils.get_previous_values_from_db(
            DBINSTANCES.java_instance.cursor, table_name, ServerType.JAVA
        )

    async def save_status(self):
        # logging.debug(f"Starting to grab {self.ip}.")
        try:
            async with asyncio.timeout(Timings.server_timeout):
                # version = mc version for the ping.
                # Default is 47 (1.8 -> 1.8.9)
                # Set it to 764 (1.20.2, currently latest)
                # Should still be able to ping old clients, 
                # While showing new fancy hex colors on servers that support it
                status = await self.server.async_status(version=764) 
                # TODO: EXPERIMENT & IMPLEMENT W QUERY LOOKUP.
                # CAN GET SERVER PLUGINS, BRAND & SOME OTHER DATA.
                # query = await self.server.async_query()
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

        data = self.get_values_dict(status)
        data = self.update_values(data)  # only keep changed ones
        FRONTEND_UPDATE_THREAD.add_update(self.table_name, data)

        data_list = DbUtils.get_args_in_order_from_dict(data, ServerType.JAVA)
        DBQUEUES.db_queue_java.add_instuction(self.insert_query, data_list)
        logging.getLogger("root").debug(f"Done grabbing {self.ip} !")

    def get_values_dict(self, status: PingResponse) -> dict:
        return {
            "save_time": int(time()),
            "players_on": status.players.online,
            "players_max": status.players.max,
            "ping": int(status.latency),
            "players_sample": self._get_player_sample(status.players.sample),
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "motd": self._parse_motd(status),
            "favicon": self._get_favicon(status.favicon)
        }

    @staticmethod
    def _parse_motd(status: PingResponse) -> dict | str:
        raw = status.motd.raw

        # Normal legacy ping
        if isinstance(raw, str):
            return raw
        
        # New ping
        elif isinstance(raw, dict):
            rawStr = str(raw)
            # Extra = new format, so if extra return the new format
            if "extra" in raw.keys():
                return rawStr

            # Text = the old format with §s
            text = raw.get("text")
            # Just in case there's no text for some reason?

            if text == None:
                return ""
            
            # Return the text, should be equal to status.description (or almost),
            # eg Syuu has an additional '§r' on status.description (parsing error?)
            return text
        
        else:
            exit_code = ErrorHandler.add_error("motd_parse_type", {"raw": raw, "type": type(raw)})
            if exit_code > 0: exit(exit_code)
        return "?"

    @staticmethod
    def _get_favicon(favicon: str | None) -> bytes | str:
        if favicon:
            # TODO (maybe?): Switch to storing images externally as files,
            # & only storing the MD5s here
            # -> requires altering the db (column favicon BLOB -> TEXT)
            # -> less practical
            # -> only useful for the few servers changing favicons often
            # ---> 8b8t.me (rotating favicons)
            # ---> craftplay.pl (for some reason same favicon but a bit different???)
            return base64.decodebytes(bytes(favicon.split(',')[-1], "ascii"))
        return "None"

    @staticmethod
    def _get_player_sample(sample: list[JavaStatusPlayer] | None) -> str:
        if sample == None:
            return "None"
        if len(sample) == 0:
            return "[]"

        players = []
        for player in sample:
            players.append({
                "name": player.name,
                "id": player.id
            })

        return str(players)

