import asyncio
import logging
from time import time
from mcstatus import BedrockServer
from mcstatus.responses import BedrockStatusResponse

from servers.base import ServerSv, PollResult, PollStatus
from db.database import Database
from config import Timings
from utils.errors import ErrorHandler, ErrorKey

class BedrockServerSv(ServerSv):
    server: BedrockServer

    def __init__(self, server_id: int, ip: str, db: Database, port: int = 19132) -> None:
        super().__init__(server_id, ip, db, port)

    async def async_init(self):
        self.server = BedrockServer.lookup(self.ip, self.port)

    async def save_status(self) -> PollResult:
        if not self.server:
            return PollResult(status=PollStatus.OTHER_FAIL)

        status = await self._perform_status()
        if status is None:
            self.rater.report_down()
            return PollResult(status=PollStatus.FAIL)

        try:
            data = self.get_values_dict(status)
            changed = self.diff_values(data)

            self.rater.report_success(status.players.online)

            timestamp = int(time())
            text_dedups, saved = self.save_changes(timestamp, changed)
            return PollResult(
                status=PollStatus.SUCCESS,
                text_dedups=text_dedups,
                player_dedups=[],
                updated_properties=list(saved.keys()),
            )
        except Exception as e:
            ErrorHandler.add_error(ErrorKey.SAVE_EXCEPTION, {"type": "bedrock", "ip": self.ip, "exception": str(e)})
            return PollResult(status=PollStatus.SAVE_FAIL)

    async def _perform_status(self) -> BedrockStatusResponse | None:
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                return await self.server.async_status()
        except TimeoutError:
            logging.warning(f"ERRORSPLIT{self.ip}: Timeout")
            return None
        except Exception as e:
            e_str = str(e)
            if "[Errno 111]" in e_str:
                logging.warning(f"ERRORSPLIT{self.ip}: ConnectCallFailed")
            else:
                logging.warning(f"ERRORSPLIT{self.ip}: Unknown error happened {e_str}")
            return None

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
