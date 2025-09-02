import asyncio
import base64
from dataclasses import dataclass
from enum import Enum
import json
import logging
from time import time
from typing import Any, Callable, Optional, Self
import dns.resolver
from mcstatus import JavaServer
from mcstatus.responses import JavaStatusResponse
from mcstatus.status_response import JavaStatusPlayer

from servers.Server import DbUpdater, ServerSv

from database.DbUtils import DbUtils
from utils.impossible import AMPASSABLE
from utils.loading_steps import JavaLoadingSteps
from utils.timer import CumulativeTimers
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.Errors import ERRORS, ErrorHandler
from vars.Frontend import FRONTEND_UPDATE_THREAD
from vars.InvalidServers import INVALID_JAVA_SERVERS
from vars.config import Logging, Startup, Timings
from vars.counters import SAVED_SERVERS

import zstandard



class JAVA_FIELD(Enum):
    save_time = 1
    players_on = 2
    players_max = 3
    ping = 4
    players_sample = 5
    version_protocol = 6
    version_name = 7
    motd = 8
    favicon = 9

@dataclass
class JavaValues:
    zstd_compressor = zstandard.ZstdCompressor()

    save_time: int
    players_on: int
    players_max: int
    ping: int
    player_sample: bytes
    version_protocol: int
    version_name: str
    motd: Any # TODO: Type properly
    favicon: bytes

    @classmethod
    def from_status(cls, status: JavaStatusResponse) -> tuple[Self, list[JAVA_FIELD]]:
        # Note: kinda dirty trick,
        # basically we know the types of values (except the optionals bc yes dw about it)
        # and we already have a function to update the changes using a status.
        # What we can do is just make an object with values we know can never be there by normal means,
        # then get the changes done on it using the status (which are all of the fields.)
        # This then yields us a proper object with all the good values set as well as a list of JAVA_FIELDs, exactly what we need.
        values = cls(AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE, AMPASSABLE) #type: ignore
        changes = values.update_using_response_get_changed(status)
        return values, changes

    def __getitem__(self, key: JAVA_FIELD):
        # Note: could probably be done using:
        # return self.__getattribute__(str(key))
        # But still writing all that boilerplate just to be SURE everything is correct.
        if key == JAVA_FIELD.save_time:
            return self.save_time
        
        if key == JAVA_FIELD.players_on:
            return self.players_on
        if key == JAVA_FIELD.players_max:
            return self.players_max
        
        if key == JAVA_FIELD.ping:
            return self.ping
        
        if key == JAVA_FIELD.players_sample:
            return self.player_sample
        
        if key == JAVA_FIELD.version_protocol:
            return self.version_protocol
        if key == JAVA_FIELD.version_name:
            return self.version_name
        
        if key == JAVA_FIELD.motd:
            return self.motd
        
        if key == JAVA_FIELD.favicon:
            return self.favicon
        
        # TODO: Raise exception if ends up here with no value at the end
        # using errorhandler*

    def _parse_motd_legacy_shouldnt_use_anymore(self, status: JavaStatusResponse) -> str:
        # TODO: check on that again
        # TBH i think would be better if the raw motd was just saved as is.
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

    def _get_motd(self, status: JavaStatusResponse):
        # Note: when migrating to just saving all of the MOTD instead of just a portion of it, make sure to json.dumps the string INSTEAD OF STR()ING IT
        # Did that at one point and now on an old db there's a part where it has stringified python dicts instead of proper json
        # Basically just write 2 isinstances (str and dict otherwise err) and for the dict one USE JSON.DUMPS
        return self.zstd_compressor.compress(self._parse_motd_legacy_shouldnt_use_anymore(status).encode("utf-8"))

    def _get_favicon(self, favicon: str | None) -> bytes:
        if favicon:
            return base64.decodebytes(bytes(favicon.split(',')[-1], "ascii"))
        return b""

    def _get_players_sample(self, sample: list[JavaStatusPlayer] | None) -> bytes:
        if sample == None:
            return b""
        if len(sample) == 0:
            return b""
        
        players = []
        for player in sample:
            players.append({
                "name": player.name,
                "id": player.id
            })

        return self.zstd_compressor.compress(str(players).encode("utf-8"))

    def update_using_response_get_changed(self, status: JavaStatusResponse) -> list[JAVA_FIELD]:
        changed: list[JAVA_FIELD] = []

        rn = int(time())
        if self.save_time != rn: # Pretty sure this is always true for obv reasons but just in case
            changed.append(JAVA_FIELD.save_time)
            self.save_time = rn

        if self.players_on != status.players.online:
            changed.append(JAVA_FIELD.players_on)
            self.players_on = status.players.online
        if self.players_max != status.players.max:
            changed.append(JAVA_FIELD.players_max)
            self.players_max = status.players.max

        self.ping = int(status.latency) # Always update ping to serve as a reference point.
        changed.append(JAVA_FIELD.ping)

        players_sample = self._get_players_sample(status.players.sample)
        if self.player_sample != players_sample:
            changed.append(JAVA_FIELD.players_sample)
            self.player_sample = players_sample

        if self.version_protocol != status.version.protocol:
            changed.append(JAVA_FIELD.version_protocol)
            self.version_protocol = status.version.protocol
        if self.version_name != status.version.name:
            changed.append(JAVA_FIELD.version_name)
            self.version_name = status.version.name

        motd = self._get_motd(status)
        if self.motd != motd:
            changed.append(JAVA_FIELD.motd)
            self.motd = motd

        favicon = self._get_favicon(status.icon)
        if self.favicon != favicon:
            changed.append(JAVA_FIELD.favicon)
            self.fav = favicon

        return changed
    


class JavaDbUpdater(DbUpdater):
    zstd_decompressor = zstandard.ZstdDecompressor()

    func_per_field: dict[JAVA_FIELD, Callable[[JavaValues, Any], None]]
    def __init__(self, base_table_name: str) -> None:
        self.base_table_name = base_table_name

        self.func_per_field = {
            JAVA_FIELD.save_time: self.new_save,
            JAVA_FIELD.players_on: self.players_on_changed,
            JAVA_FIELD.players_max: self.players_max_changed,
            JAVA_FIELD.ping: lambda *args: None, # Do nothing as ping is already saved with the save_time
            JAVA_FIELD.players_sample: self.players_sample_changed,
            JAVA_FIELD.version_protocol: self.version_protocol_changed,
            JAVA_FIELD.version_name: self.version_name_changed,
            JAVA_FIELD.motd: self.motd_changed,
            JAVA_FIELD.favicon: self.favicon_changed
        }

    def dbs_exist(self):
        # Technically redundant as we "create table IF NOT EXISTS" anyways but still.
        return DbUtils.table_exists(DBINSTANCES.java_instance.cursor, f"{self.base_table_name}_saves")

    def create_dbs(self):
        DBQUEUES.db_queue_java.add_important_instruction(f"""
        CREATE TABLE IF NOT EXISTS {self.base_table_name}_saves (
            save_time INTEGER PRIMARY KEY,
            ping INTEGER
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_players_on (
            save_time INTEGER PRIMARY KEY,
            players_on INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_players_max (
            save_time INTEGER PRIMARY KEY,
            players_max INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_version_protocol (
            save_time INTEGER PRIMARY KEY,
            version_protocol INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_version_name (
            save_time INTEGER PRIMARY KEY,
            version_name TEXT,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_players_sample_values (
            sample_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_blob BLOB UNIQUE  -- Changed to BLOB for compressed data
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_players_sample_changes (
            save_time INTEGER PRIMARY KEY,
            sample_id INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time),
            FOREIGN KEY (sample_id) REFERENCES {self.base_table_name}_players_sample_values(sample_id)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_motd_values (
            motd_id INTEGER PRIMARY KEY AUTOINCREMENT,
            motd_blob BLOB UNIQUE  -- Changed to BLOB for compressed data
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_motd_changes (
            save_time INTEGER PRIMARY KEY,
            motd_id INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time),
            FOREIGN KEY (motd_id) REFERENCES {self.base_table_name}_motd_values(motd_id)
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_favicon_values (
            favicon_id INTEGER PRIMARY KEY AUTOINCREMENT,
            favicon_blob BLOB UNIQUE
        );

        CREATE TABLE IF NOT EXISTS {self.base_table_name}_favicon_changes (
            save_time INTEGER PRIMARY KEY,
            favicon_id INTEGER,
            FOREIGN KEY (save_time) REFERENCES {self.base_table_name}_saves(save_time),
            FOREIGN KEY (favicon_id) REFERENCES {self.base_table_name}_favicon_values(favicon_id)
        );
        """)
    
    def load_previous_values(self) -> Optional[JavaValues]:
        if not self.dbs_exist():
            return None
        
        cursor = DBINSTANCES.java_instance.cursor
        try:
            # Get the latest save_time (for the save_time and ping)
            cursor.execute(f"""
                SELECT save_time, ping
                FROM {self.base_table_name}_saves
                ORDER BY save_time DESC
                LIMIT 1
            """)
            saves_row = cursor.fetchone()
            if not saves_row:
                return None

            latest_save_time, ping = saves_row

            # Get the latest players_on (regardless of save_time)
            cursor.execute(f"""
                SELECT players_on
                FROM {self.base_table_name}_players_on
                ORDER BY save_time DESC
                LIMIT 1
            """)
            players_on_row = cursor.fetchone()
            players_on = players_on_row[0] if players_on_row else AMPASSABLE

            # Get the latest players_max (regardless of save_time)
            cursor.execute(f"""
                SELECT players_max
                FROM {self.base_table_name}_players_max
                ORDER BY save_time DESC
                LIMIT 1
            """)
            players_max_row = cursor.fetchone()
            players_max = players_max_row[0] if players_max_row else AMPASSABLE

            # Get the latest version_protocol (regardless of save_time)
            cursor.execute(f"""
                SELECT version_protocol
                FROM {self.base_table_name}_version_protocol
                ORDER BY save_time DESC
                LIMIT 1
            """)
            version_protocol_row = cursor.fetchone()
            version_protocol = version_protocol_row[0] if version_protocol_row else AMPASSABLE

            # Get the latest version_name (regardless of save_time)
            cursor.execute(f"""
                SELECT version_name
                FROM {self.base_table_name}_version_name
                ORDER BY save_time DESC
                LIMIT 1
            """)
            version_name_row = cursor.fetchone()
            version_name = version_name_row[0] if version_name_row else AMPASSABLE

            # Get the latest player_sample (regardless of save_time)
            cursor.execute(f"""
                SELECT ps.save_time, psv.sample_blob
                FROM {self.base_table_name}_players_sample_changes ps
                JOIN {self.base_table_name}_players_sample_values psv ON ps.sample_id = psv.sample_id
                ORDER BY ps.save_time DESC
                LIMIT 1
            """)
            player_sample_row = cursor.fetchone()
            player_sample_bytes = player_sample_row[1] if player_sample_row else AMPASSABLE

            # Get the latest motd (regardless of save_time)
            cursor.execute(f"""
                SELECT m.save_time, mv.motd_blob
                FROM {self.base_table_name}_motd_changes m
                JOIN {self.base_table_name}_motd_values mv ON m.motd_id = mv.motd_id
                ORDER BY m.save_time DESC
                LIMIT 1
            """)
            motd_row = cursor.fetchone()
            motd_blob = motd_row[1] if motd_row else AMPASSABLE

            # Get the latest favicon (regardless of save_time)
            cursor.execute(f"""
                SELECT f.save_time, fv.favicon_blob
                FROM {self.base_table_name}_favicon_changes f
                JOIN {self.base_table_name}_favicon_values fv ON f.favicon_id = fv.favicon_id
                ORDER BY f.save_time DESC
                LIMIT 1
            """)
            favicon_row = cursor.fetchone()
            favicon = favicon_row[1] if favicon_row else AMPASSABLE


            # Why are we ignoring types here?
            # If we haven't got a value from somewhere in the DB, that means that either there's a problem OR the line is just missing (eg server down).
            # In that case, we do NOT want to miss a possible value that might come at some point in the future.
            # If we respect the types and eg set the VERSION_PROTOCOL to None when there's no line in the DB for it, if in the future we actually get
            # a value for the VERSION_PROTOCOL that's None, it's just not going to update as it'll think it's already up to date, even tho we actually
            # have nothing in the db.
            # So we just assign an impossible value to all fields by default if they're not found in the db, so that if ANY value comes by
            # an update is triggered.
            # Note that tbh I could set "Impossible" as a type for all JavaValue fields, will see in the future if I do that.
            return JavaValues(
                save_time=latest_save_time,
                players_on=players_on, #type: ignore
                players_max=players_max, #type: ignore
                ping=ping,
                player_sample=player_sample_bytes, #type: ignore
                version_protocol=version_protocol, #type: ignore
                version_name=version_name, #type: ignore
                motd=motd_blob,
                favicon=favicon #type: ignore
            )

        except Exception as e:
            # TODO: proper error handling here as THIS IS CRITICAL.
            print(f"Error loading values: {e}")
            return None

    def update_all_changed(self, values: JavaValues, changed_fields: list[JAVA_FIELD]):
        for changed in changed_fields:
            new_value = values[changed]
            func = self.func_per_field[changed]
            func(values, new_value)

    # Used to update simple values (the ones w no ref/value things).
    def _update_simple_field(self, table_suffix: str, field_name: str, save_time: int, value: Any):
        DBQUEUES.db_queue_java.add_instuction(f"INSERT INTO {self.base_table_name}_{table_suffix} (save_time, {field_name}) VALUES (?, ?)", (save_time, value))

    def _update_value_ref_field(self):
        pass #TODO: used for values w values in a different table than the changes.

    def new_save(self, values: JavaValues, save_time: int):
        self._update_simple_field("saves", "ping", save_time, values.ping)

    def players_on_changed(self, values: JavaValues, players_on: int):
        self._update_simple_field("players_on", "players_on", values.save_time, players_on)

    def players_max_changed(self, values: JavaValues, players_max: int):
        self._update_simple_field("players_max", "players_max", values.save_time, players_max)

    def players_sample_changed(self, values: JavaValues, players_sample: bytes):
        pass

    def version_protocol_changed(self, values: JavaValues, version_protocol: int):
        self._update_simple_field("version_protocol", "version_protocol", values.save_time, version_protocol)

    def version_name_changed(self, values: JavaValues, version_name: str):
        self._update_simple_field("version_name", "version_name", values.save_time, version_name)

    def motd_changed(self, values: JavaValues, motd: bytes):
        pass

    def favicon_changed(self, values: JavaValues, favicon: bytes):
        pass


class JavaServerSv(ServerSv):
    server: JavaServer
    table_name: str
    db_updater: JavaDbUpdater # TODO: one instance per server or global instance? Doesn't really matter but yeh. 
    loading_steps: JavaLoadingSteps # TODO: Remove? Not really sure if it's really needed, could easily be moved in the init.

    values: Optional[JavaValues]

    # TODO: move the DNS loading to another func (not urgent)
    async def __init__(self, table_name: str, ip: str, port: int = 25565) -> None:
        # inheriting
        await super().__init__(table_name, ip, port)
        # steps done
        self.loading_steps = JavaLoadingSteps.new()
        # get non changing values
        self.table_name = table_name
        self.db_updater = JavaDbUpdater(table_name)

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


    async def load_db(self):
        # db init
        if not self.db_updater.dbs_exist():
            self.db_updater.create_dbs()

        self.values = self.db_updater.load_previous_values()

        self.loading_steps.db = True


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

        # In case this is the first ever status.
        if self.values is None:
            self.values, changed_fields = JavaValues.from_status(status)
        else:
            changed_fields = self.values.update_using_response_get_changed(status)

        self.db_updater.update_all_changed(self.values, changed_fields)

        # TODO (not urgent): update frontend shit.
        # FRONTEND_UPDATE_THREAD.add_update(self.table_name, data)
        logging.getLogger("root").debug(f"Done grabbing {self.ip} !")

    async def _perform_status(self):
        # logging.debug(f"Starting to grab {self.ip}.")
        try:
            async with asyncio.timeout(Timings.SERVER_TIMEOUT):
                # version = mc version for the ping.
                # Default is 47 (1.8 -> 1.8.9)
                # Set it to 764 (1.20.2, currently latest)
                # 769 is 1.21.4
                # Should still be able to ping old clients, 
                # While showing new fancy hex colors on servers that support it
                status = await self.server.async_status(version=769)
                INVALID_JAVA_SERVERS.mark_server_valid(self.ip)
                SAVED_SERVERS.value += 1
        except Exception as e:
            INVALID_JAVA_SERVERS.add_server_fail(self.ip)
            if not INVALID_JAVA_SERVERS.is_invalid(self.ip): # do not log failed servers
                if type(e) == TimeoutError:
                    return logging.warning(f"ERRORSPLIT{self.ip}: {ERRORS.get('Timeout')}")
                e = str(e)
                if "[Errno 111]" or "[Errno 113]"in e: # has dynamic data in it, can't catch w ERRORS.get()
                    formated_error = ERRORS.get("ConnectCallFailed") 
                else: 
                    formated_error = ERRORS.get(e, 'Unknown error happened ' + e)
                logging.warn(f"ERRORSPLIT{self.ip}: {formated_error}")
            return
        
        return status

    # TODO: bring back maintenance (not urgent)
    # async def perform_startup_checks(self):
    #     if Startup.SHOULD_PERFORM_STARTUP_CHECKS:
    #         run_db_checks(self.table_name)
