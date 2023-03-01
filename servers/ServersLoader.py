import asyncio
import json
from typing import Coroutine
from servers.BedrockServer import BedrockServerSv

from servers.JavaServer import JavaServerSv


class ServersLoader:
    file_name: str

    def __init__(self, file_name: str) -> None:
        self.file_name = file_name

    async def parse(self):
        all_servers_coroutines: list[Coroutine] = []

        with open(self.file_name, 'r') as file:
            data: dict = json.load(file)

        for key, Clazz in {"java": JavaServerSv, "bugrock": BedrockServerSv, "bedrock": BedrockServerSv}.items():
            servers: dict | None = data.get(key)
            if not servers:
                continue
            
            for table_name, server_ip in servers.items():
                all_servers_coroutines.append(Clazz(table_name, server_ip))

        all_servers: list = await asyncio.gather(*all_servers_coroutines)

        return all_servers
