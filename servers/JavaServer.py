import asyncio
import base64
from time import time
from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
from database.DbQueries import JavaQueries

from servers.Server import ServerSv

from database.DbUtils import ServerType, DbUtils
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.Timings import Timings
Player = PingResponse.Players.Player


class JavaServerSv(ServerSv):
    server: JavaServer
    insert_query: str

    async def __init__(self, table_name: str, ip: str, port: int = 25565) -> None:
        # inheriting
        await super().__init__(table_name, ip, port)
        # get non changing values
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
        try:
            async with asyncio.timeout(Timings.server_timeout):
                status = await self.server.async_status()
        except TimeoutError:
            print(f"Failed to grab {self.ip} (TIMEOUT)")
            return
        except Exception as e:
            print(f"Failed to grab {self.ip}! {e}")
            return # just continue another time if fail

        data = self.get_values_dict(status)
        data = self.update_values(data)  # only keep changed ones
        data_list = DbUtils.get_args_in_order_from_dict(data, ServerType.JAVA)
        DBQUEUES.db_queue_java.add_instuction(self.insert_query, data_list)

    def get_values_dict(self, status: PingResponse) -> dict:
        return {
            "save_time": int(time()),
            "players_on": status.players.online,
            "players_max": status.players.max,
            "ping": int(status.latency),
            "players_sample": self._get_player_sample(status.players.sample),
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "motd": status.description,
            "favicon": self._get_favicon(status.favicon)
        }

    @staticmethod
    def _get_favicon(favicon: str | None) -> bytes | str:
        if favicon:
            # return "DISABLED FOR TESTING"
            return base64.decodebytes(bytes(favicon.split(',')[-1], "ascii"))
        return "None"

    @staticmethod
    def _get_player_sample(sample: list[Player] | None) -> str:
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

