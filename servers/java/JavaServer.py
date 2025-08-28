import asyncio
import base64
from dataclasses import dataclass
import json
import logging
from time import time
import dns.resolver
from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
from mcstatus.status_response import JavaStatusPlayer
from database.DbQueries import JavaQueries
from maintenance.checks import run_db_checks

from servers.Server import ServerSv

from database.DbUtils import ServerType, DbUtils
from servers.java.JavaDuplicatesHelper import JavaDuplicatesHelper
from servers.java.JavaServerFlags import JavaServerFlags
from utils.timer import CumulativeTimers
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.Errors import ERRORS, ErrorHandler
from vars.Frontend import FRONTEND_UPDATE_THREAD
from vars.InvalidServers import INVALID_JAVA_SERVERS
from vars.LastValueSavers import LAST_JAVA_VALUES
from vars.config import Logging, Startup, Timings
from vars.counters import SAVED_SERVERS

@dataclass
class LoadingSteps:
    dns: bool
    db_init: bool
    db_load_values: bool

    def all_done(self):
        if self.dns and self.db_init and self.db_load_values:
            return True
        if not self.dns:
            return "DNS"
        if not self.db_init:
            return "DB_INIT"
        if not self.db_load_values:
            return "DB_LOAD_VALUES"

    @classmethod
    def new(cls):
        return cls(False, False, False)
    

class JavaServerSv(ServerSv):
    server: JavaServer
    table_name: str
    insert_query: str
    flags: JavaServerFlags
    duplicates_helper: JavaDuplicatesHelper
    loading_steps: LoadingSteps

    # TODO: IF POSSIBLE MOVE THE LOADING STEPS TO ANOTHER CLASS 
    async def __init__(self, table_name: str, ip: str, port: int = 25565) -> None:
        # inheriting
        await super().__init__(table_name, ip, port)
        # steps done
        self.loading_steps = LoadingSteps.new()
        # get non changing values
        self.table_name = table_name

        # Trying without an errorhandler for now.
        CumulativeTimers.get_timer("Lookup").start_time(table_name)
        tries = 1
        success = False
        while tries <= 3 and not success:
            try:
                async with asyncio.timeout(Timings.DNS_TIMEOUT):
                    self.server = await JavaServer.async_lookup(ip, port)
                    success = True
            except TimeoutError:
                if Logging.LOG_DNS_TIMEOUT:
                    logging.error(f"DNS lookup timeout for {ip} (try n°{tries})")
            except dns.resolver.NoNameservers: 
                if Logging.LOG_DNS_ERROR:
                    logging.error(f"DNS lookup failed for {ip} (try n°{tries})")
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Error happened looking up {ip}: {e} (try n°{tries})")
            tries += 1
        if not success:
            exitcode = ErrorHandler.add_error("dnslookup", {"server": self.ip, "port": self.port})
            if exitcode > 0: exit(exitcode)
        CumulativeTimers.get_timer("Lookup").end_time(table_name)

        self.loading_steps.dns = True

    async def init_db(self):
        # db init
        self.insert_query = JavaQueries.get_insert_query(self.table_name)
        DBQUEUES.db_queue_java.add_important_instruction(JavaQueries.get_create_table_query(self.table_name))

        # flag dbs init
        self.flags = JavaServerFlags(self.table_name)
        self.duplicates_helper = JavaDuplicatesHelper(self.flags)

        self.loading_steps.db_init = True

    async def load_previous_values_db(self):
        # load last values from db (if any)
        # CumulativeTimers.get_timer("Previous value").start_time(self.table_name)
        # First try to load from the last values bson
        values_ids = LAST_JAVA_VALUES.get_values(self.table_name)
        good = True
        if values_ids == None: 
            good = False
        else:
            for key in ServerType.JAVA.value:
                if values_ids.get(key) == None: 
                    good = False
        
        # If that doesn't work, load using the conventional way from the db directly
        if not good:
            values_ids = DbUtils.get_previous_values_from_db(
                DBINSTANCES.java_instance.cursor, self.table_name, ServerType.JAVA, LAST_JAVA_VALUES
            )
        # vscode can't figure this out automatically (if none, values_ids will be grabbed conventionally automatically)
        self.values = self.duplicates_helper.get_latest_values(values_ids) #type: ignore
        # CumulativeTimers.get_timer("Previous value").end_time(self.table_name)

        self.loading_steps.db_load_values = True

    async def perform_startup_checks(self):
        if Startup.SHOULD_PERFORM_STARTUP_CHECKS:
            run_db_checks(self.table_name)

    async def save_status(self):
        done_results = self.loading_steps.all_done()
        if done_results != True:
            return exit(ErrorHandler.add_error("init_not_done", {"table": self.table_name, "missing": done_results}))
        try:
            await self._save_status()
        except:
            ErrorHandler.add_error("save_status", {"table": self.table_name})

    async def _save_status(self):
        status = await self._perform_status()
        if status == None: return

        data = self.get_values_dict(status)
        data = self.update_values(data)  # only keep changed ones
        FRONTEND_UPDATE_THREAD.add_update(self.table_name, data)

        data_duplicate_ids = {}
        for key, value in data.items():
            duplicate_processed_value = self.duplicates_helper.get_value_for_save(key, value)
            data_duplicate_ids[key] = duplicate_processed_value
            # Save to last values for easy reload
            LAST_JAVA_VALUES.set_value(self.table_name, key, duplicate_processed_value)

        DBQUEUES.db_queue_java.add_instuction(
            self.insert_query, 
            DbUtils.get_args_in_order_from_dict(data_duplicate_ids, ServerType.JAVA)
        )
        logging.getLogger("root").debug(f"Done grabbing {self.ip} !")

    async def _perform_status(self):
        # logging.debug(f"Starting to grab {self.ip}.")
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                # version = mc version for the ping.
                # Default is 47 (1.8 -> 1.8.9)
                # Set it to 764 (1.20.2, currently latest)
                # Should still be able to ping old clients, 
                # While showing new fancy hex colors on servers that support it
                status = await self.server.async_status(version=764) 
                INVALID_JAVA_SERVERS.mark_server_valid(self.ip)
                SAVED_SERVERS.value += 1
        except Exception as e:
            INVALID_JAVA_SERVERS.add_server_fail(self.ip)
            if not INVALID_JAVA_SERVERS.is_invalid(self.ip): # do not log failed servers
                if type(e) == TimeoutError:
                    return logging.warn(f"ERRORSPLIT{self.ip}: {ERRORS.get('Timeout')}")
                e = str(e)
                if "[Errno 111]" or "[Errno 113]"in e: # has dynamic data in it, can't catch w ERRORS.get()
                    formated_error = ERRORS.get("ConnectCallFailed") 
                else: 
                    formated_error = ERRORS.get(e, 'Unknown error happened ' + e)
                logging.warn(f"ERRORSPLIT{self.ip}: {formated_error}")
            return
        
        return status

    def get_values_dict(self, status: PingResponse) -> dict:
        # TODO (maybe, check ram usage): check to objects instead of dicts for values
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
            # Extra = new format, so if extra return the new format
            if "extra" in raw.keys():
                return json.dumps(raw)

            # Text = the old format with §s
            text = raw.get("text")

            # Just in case there's no text for some reason?
            if text == None: return ""
            
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

