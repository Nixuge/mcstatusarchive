import asyncio
import base64
import json
import logging
from time import time
from typing import Any
import dns.resolver
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusResponse, JavaStatusPlayer

from servers.base import ServerSv
from db.database import Database
from utils.errors import ErrorHandler, ErrorKey
from config import Timings, LoggingConfig, McConfig

class JavaServerSv(ServerSv):
    server: JavaServer = None # pyright: ignore[reportAssignmentType]

    def __init__(self, server_id: int, ip: str, db: Database, port: int = 25565) -> None:
        super().__init__(server_id, ip, db, port)

    async def async_init(self):
        tries = 1
        success = False
        while tries <= 3 and not success:
            try:
                async with asyncio.timeout(Timings.DNS_TIMEOUT):
                    self.server = await JavaServer.async_lookup(self.ip, self.port)
                    success = True
            except TimeoutError:
                if LoggingConfig.LOG_DNS_TIMEOUT:
                    logging.error(f"DNS lookup timeout for {self.ip} (try n°{tries})")
            except dns.resolver.NoNameservers:
                if LoggingConfig.LOG_DNS_ERROR:
                    logging.error(f"DNS lookup failed for {self.ip} (try n°{tries})")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Error happened looking up {self.ip}: {e} (try n°{tries})")
            tries += 1

        if not success:
            ErrorHandler.add_error(ErrorKey.DNS_LOOKUP, {"server": self.ip, "port": self.port})

    async def save_status(self):
        if not self.server:
            return

        status = await self._perform_status()
        if status is None:
            self.rater.report_down()
            return

        data = self.get_values_dict(status)
        changed = self.update_values(data)

        self.rater.report_success(status.players.online)

        timestamp = int(time())
        self.save_changes(timestamp, changed)

    async def _perform_status(self) -> JavaStatusResponse | None:
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                status = await self.server.async_status(version=McConfig.JAVA_VERSION)
        except Exception as e:
            if type(e) == TimeoutError:
                logging.warning(f"ERRORSPLIT{self.ip}: Timeout")
                return None
            e_str = str(e)
            if "[Errno 111]" in e_str or "[Errno 113]" in e_str:
                logging.warning(f"ERRORSPLIT{self.ip}: ConnectCallFailed")
            else:
                logging.warning(f"ERRORSPLIT{self.ip}: Unknown error happened {e_str}")
            return None

        return status

    def get_values_dict(self, status: JavaStatusResponse) -> dict[str, Any]:
        # TODO:
        # - status.enforces_secure_chat
        # - status.forge_data, which itself has:
        # --- status.forge_data.fml_network_version
        # --- status.forge_data.channels
        # --- status.forge_data.mods
        # --- status.forge_data.truncated
        return {
            "players_on": status.players.online,
            "players_max": status.players.max,
            "ping": int(status.latency),
            "players_sample": self._get_player_sample(status.players.sample),
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "motd": self._parse_motd(status),
            "favicon": self._get_favicon(status.icon)
        }

    @staticmethod
    def _get_favicon(favicon: str | None) -> bytes:
        if favicon:
            return base64.decodebytes(bytes(favicon.split(',')[-1], "ascii"))
        return b"" # The db format doesnt handle nulls, this is fine tbh.

    def _get_player_sample(self, sample: list[JavaStatusPlayer] | None) -> str:
        if sample is None:
            return "-1" # db doesn't handle nulls, so using a unique value for this case.
        if len(sample) == 0:
            return ""

        player_ids: list[int] = []
        for player in sample:
            p_id = self.db.player_dedup.get_or_create(player.name, player.id)
            player_ids.append(p_id)

        # Player order can vary so just in case sort so that it's always the same order
        player_ids.sort()
        return ",".join(str(p_id) for p_id in player_ids)
