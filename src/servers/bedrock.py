import asyncio
import logging
from time import time
from mcstatus import BedrockServer
from mcstatus.responses import BedrockStatusResponse

from servers.base import ServerSv
from db.database import Database
from config import Timings

class BedrockServerSv(ServerSv):
    server: BedrockServer

    def __init__(self, server_id: int, ip: str, db: Database, port: int = 19132) -> None:
        super().__init__(server_id, ip, db, port)

    async def async_init(self):
        self.server = BedrockServer.lookup(self.ip, self.port)

    async def save_status(self):
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                status = await self.server.async_status()
        except TimeoutError:
            logging.warning(f"ERRORSPLIT{self.ip}: Timeout")
            self.rater.report_down()
            return
        except Exception as e:
            e_str = str(e)
            if "[Errno 111]" in e_str:
                logging.warning(f"ERRORSPLIT{self.ip}: ConnectCallFailed")
            else:
                logging.warning(f"ERRORSPLIT{self.ip}: Unknown error happened {e_str}")
            self.rater.report_down()
            return

        data = self.get_values_dict(status)
        changed = self.update_values(data)

        self.rater.report_success(status.players.online)

        timestamp = int(time())
        self.save_changes(timestamp, changed)

    def get_values_dict(self, status: BedrockStatusResponse) -> dict:
        # Note: pretty sure the _parse_motd for bedrock isn't required
        # as it always returns a raw string, but just in case it evolves in the future or smth
        # logging.info(f"Bedrock motd: {status.motd.raw}")
        return {
            "players_on": status.players.online,
            "players_max": status.players.max,
            "ping": int(status.latency),
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "version_brand": status.version.brand,
            "motd": self._parse_motd(status),
            "gamemode": status.gamemode,
            "map": status.map_name
        }
