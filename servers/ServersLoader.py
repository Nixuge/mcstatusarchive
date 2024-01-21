import asyncio
import pyjson5
import logging
from typing import Any, Coroutine
from servers.bedrock.BedrockServer import BedrockServerSv

from servers.java.JavaServer import JavaServerSv
from utils.timer import CumulativeTimers, Timer
from vars.Errors import ErrorHandler
from vars.config import Startup


class ServersLoader:
    file_name: str
    data: dict
    java_coroutines: list[Coroutine[Any, Any, JavaServerSv]]
    bedrock_coroutines: list[Coroutine[Any, Any, BedrockServerSv]]

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        with open(self.file_name, 'r') as file:
            self.data = pyjson5.load(file)

        self.java_coroutines = []
        self.bedrock_coroutines = []

    @classmethod
    def make_table_name_from_ip(cls, ip: str):
        ip = ip.replace("-", "_dash_").replace(":", "_colon_").replace(".", "_")
        
        if " " in ip:
            logging.error(f"ip has a space: {ip}")
            ip = ip.replace(" ", "")

        if ip[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_":
            ip = '_' + ip

        return ip # should be good

    @classmethod
    def remove_duplicates(cls, serverlist: list):
        seen = set()
        duplicates = set()
        for server in serverlist:
            if server in seen:
                duplicates.add(server)
            else:
                seen.add(server)
        return seen, duplicates

    def _parse_dict_ips_back(self, list_name: str, clazz, server_list: list):
        servers: dict | None = self.data.get(list_name)
        if not servers:
            return
            
        for table_name, server_ip in servers.items():
            server_list.append(clazz(table_name, server_ip))

    def _parse_dict_ips(self):
        self._parse_dict_ips_back("java", JavaServerSv, self.java_coroutines)
        self._parse_dict_ips_back("bugrock", BedrockServerSv, self.bedrock_coroutines)
        self._parse_dict_ips_back("bedrock", BedrockServerSv, self.bedrock_coroutines)
    
    def _parse_list_ips_back(self, list_name: str, clazz, server_list: list):
        servers: list | None = self.data.get(list_name)
        if not servers:
            return
            
        servers_noduplicates, duplicates = self.remove_duplicates(servers)
        if len(duplicates) > 0:
            logging.error("Duplicates server found in config for " + list_name)
            for duplicate in duplicates:
                logging.error(duplicate)

        for server_ip in servers_noduplicates:
            server_list.append(clazz(self.make_table_name_from_ip(server_ip), server_ip))

    def _parse_list_ips(self):
        self._parse_list_ips_back("java_list", JavaServerSv, self.java_coroutines)
        self._parse_list_ips_back("bedrock_list", BedrockServerSv, self.bedrock_coroutines)

    async def parse(self) -> list[JavaServerSv | BedrockServerSv]:
        timers = ("Lookup", "Previous value")

        self._parse_dict_ips()
        self._parse_list_ips()
        all_bedrock_servers = []
        all_java_servers = []
        try:
            bedrock_timer = Timer()
            logging.info(f"Starting to load bedrock servers. (count: {len(self.bedrock_coroutines)})")
            all_bedrock_servers = await asyncio.gather(*self.bedrock_coroutines)
            logging.info(f"Done loading bedrock servers ({bedrock_timer.end()}).")

            # for timer_key in timers:
            #     times = CumulativeTimers.get_timer(timer_key).stop()
            #     logging.info(f"{timer_key} took {times[0]}s total ({times[1]}s average)")
            CumulativeTimers.remove_timers(*timers)

            java_timer = Timer()
            logging.info(f"Starting to load dns for java servers. (count: {len(self.java_coroutines)})")
            all_java_servers = await asyncio.gather(*self.java_coroutines)
            logging.info(f"Done loading dns for java servers ({java_timer.step()}).")

            logging.info(f"Starting to init databases for java servers. (count: {len(self.java_coroutines)})")
            await asyncio.gather(*[java_server.init_db() for java_server in all_java_servers])
            logging.info(f"Done initing databases for java servers ({java_timer.step()}).")

            logging.info(f"Starting to load previous database values for java servers. (count: {len(self.java_coroutines)})")
            await asyncio.gather(*[java_server.load_previous_values_db() for java_server in all_java_servers])
            logging.info(f"Done loading previous database values for java servers ({java_timer.end()}).")

            if Startup.SHOULD_PERFORM_STARTUP_CHECKS:
                startup_timer = Timer()
                logging.info(f"Performing startup checks for java servers. (count: {len(self.java_coroutines)})")
                await asyncio.gather(*[java_server.perform_startup_checks() for java_server in all_java_servers])
                logging.info(f"Done performing startup checks for java servers ({startup_timer.end()}).")
            
        except:
            ErrorHandler.add_error("servers_init")

        return all_bedrock_servers + all_java_servers