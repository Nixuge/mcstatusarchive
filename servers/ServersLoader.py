import asyncio
import json
from typing import Coroutine
from servers.BedrockServer import BedrockServerSv

from servers.JavaServer import JavaServerSv


class ServersLoader:
    file_name: str
    data: dict
    all_servers_coroutines: list[Coroutine]

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        with open(self.file_name, 'r') as file:
            self.data = json.load(file)

        self.all_servers_coroutines = []

    @classmethod
    def make_table_name_from_ip(cls, ip: str):
        ip = ip.replace("-", "_dash_").replace(".", "_")
        if ip[0] not in "abcdefghijklmnopqrstuvwxyz_":
            ip = '_' + ip
        
        return ip # should be good

    def _parse_dict_ips(self):
        for key, Clazz in {"java": JavaServerSv, "bugrock": BedrockServerSv, "bedrock": BedrockServerSv}.items():
            servers: dict | None = self.data.get(key)
            if not servers:
                continue
            
            for table_name, server_ip in servers.items():
                self.all_servers_coroutines.append(Clazz(table_name, server_ip))

    def _parse_list_ips(self):
        for key, Clazz in {"java_list": JavaServerSv, "bedrock_list": BedrockServerSv}.items():
            servers: dict | None = self.data.get(key)
            if not servers:
                continue
            
            for server_ip in servers:
                self.all_servers_coroutines.append(Clazz(self.make_table_name_from_ip(server_ip), server_ip))

    async def parse(self) -> list[JavaServerSv | BedrockServerSv]:
        self._parse_dict_ips()
        self._parse_list_ips()

        all_servers = await asyncio.gather(*self.all_servers_coroutines)

        return all_servers
