from time import time
from mcstatus import BedrockServer
from mcstatus.bedrock_status import BedrockStatusResponse
from database.DbQueries import BedrockQueries

from servers.Server import ServerSv

from database.DbUtils import ServerType, DbUtils
from vars.DbManagers import DBMANAGERS
from vars.DbQueues import DBQUEUES


class BedrockServerSv(ServerSv):
    server: BedrockServer
    insert_query: str

    def __init__(self, table_name: str, ip: str, port: int = 19132) -> None:
        # inheriting
        super().__init__(table_name, ip, port)
        # get non changing values
        self.server = BedrockServer.lookup(ip, port)
        self.insert_query = BedrockQueries.get_insert_query(table_name)
        # create db if not present
        DBQUEUES.db_queue_bedrock.add_instuction(
            BedrockQueries.get_create_table_query(table_name), None
        )
        # load last values from db (if any)
        self.values = DbUtils.get_previous_values_from_db(
            DBMANAGERS.bedrock_connection.cursor, table_name, ServerType.BEDROCK
        )

    async def save_status(self):
        try:
            status = await self.server.async_status()
        except Exception as e:
            print(f"Failed to grab {self.ip}! {e}")
            return # just continue another time if fail

        data = self.get_values_dict(status)
        data = self.update_values(data)  # only keep changed ones
        data_list = DbUtils.get_args_in_order_from_dict(data, ServerType.JAVA)
        DBQUEUES.db_queue_java.add_instuction(self.insert_query, data_list)


    def get_values_dict(self, status: BedrockStatusResponse) -> dict:
        return {
            "save_time": int(time()), 
            "players_on": status.players_online, 
            "players_max": status.players_max, 
            "ping": int(status.latency),
            "version_protocol": status.version.protocol, 
            "version_name": status.version.version, 
            "version_brand": status.version.brand, 
            "motd": status.motd, 
            "gamemode": status.gamemode, 
            "map": status.map
        }
