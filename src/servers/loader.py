import asyncio
import logging
from typing import Type

from utils.errors import ErrorHandler, ErrorKey
try:
    import pyjson5 as json
except ImportError:
    import json

from servers.base import ServerSv
from servers.bedrock import BedrockServerSv
from servers.java import JavaServerSv
from db.database import Database
from db.schema import SERVER_TYPE_JAVA, SERVER_TYPE_BEDROCK


# Technically supports ipv6 tho we dont rly care lmao
def parse_ip_port(ip_string: str, default_port: int) -> tuple[str, int]:
    if ":" in ip_string:
        parts = ip_string.rsplit(":", 1)
        try:
            port = int(parts[1])
            return parts[0], port
        except ValueError:
            pass
    return ip_string, default_port


DEFAULT_PORTS = {
    SERVER_TYPE_JAVA: 25565,
    SERVER_TYPE_BEDROCK: 19132,
}


class ServersLoader:
    def __init__(self, file_name: str, db_java: Database, db_bedrock: Database) -> None:
        self.file_name = file_name
        self.db_java = db_java
        self.db_bedrock = db_bedrock
        with open(self.file_name, 'r') as file:
            self.data = json.load(file) # pyright: ignore[reportArgumentType]

        self.java_servers: list[JavaServerSv] = []
        self.bedrock_servers: list[BedrockServerSv] = []

    
    def _load_servers_for_type(self, server_type: str, clazz: Type[ServerSv], db: Database, dict_keys: list[str], list_keys: list[str]) -> list:
        default_port = DEFAULT_PORTS[server_type]
        seen_endpoints: set[tuple[str, int]] = set()
        duplicates: set[str] = set()
        servers_list: list[ServerSv] = []

        # Process dict sections
        for key in dict_keys:
            dict_data: dict[str, str] | None = self.data.get(key)
            if not dict_data:
                continue
            for name, raw_ip in dict_data.items():
                ip, port = parse_ip_port(raw_ip, default_port)
                endpoint = (ip.lower(), port)
                if endpoint in seen_endpoints:
                    duplicates.add(raw_ip)
                else:
                    seen_endpoints.add(endpoint)
                    server_id = db.register_server(name, ip, port)
                    servers_list.append(clazz(server_id, ip, db, port))

        # Process list sections
        for key in list_keys:
            list_data: list[str] | None = self.data.get(key)
            if not list_data:
                continue
            for raw_ip in list_data:
                ip, port = parse_ip_port(raw_ip, default_port)
                endpoint = (ip.lower(), port)
                if endpoint in seen_endpoints:
                    duplicates.add(raw_ip)
                else:
                    seen_endpoints.add(endpoint)
                    server_id = db.register_server(None, ip, port)
                    servers_list.append(clazz(server_id, ip, db, port))

        if duplicates:
            ErrorHandler.add_error(
                ErrorKey.DUPLICATE_IP,
                {"server_type": server_type, "duplicates": sorted(list(duplicates))},
            )

        return servers_list

    async def _init_servers(self, server_type: str, servers: list) -> list:
        chunks = [servers[x:x+200] for x in range(0, len(servers), 200)]
        logging.info(f"Got {len(servers)} {server_type} servers. Splitting initialization tasks in {len(chunks)} chunk(s).")
        for i, chunk in enumerate(chunks):
            await asyncio.gather(*[server.async_init() for server in chunk])
            if i+1 == len(chunks):
                logging.info("Done processing all chunks!")
            else:
                logging.info(f"Done processing chunk {i+1}/{len(chunks)}. Waiting 0.1s.")
                await asyncio.sleep(0.1)

        return servers

    async def parse(self) -> list:
        self.java_servers = self._load_servers_for_type(
            SERVER_TYPE_JAVA, JavaServerSv, self.db_java, dict_keys=["java"], list_keys=["java_list"]
        )
        self.bedrock_servers = self._load_servers_for_type(
            SERVER_TYPE_BEDROCK, BedrockServerSv, self.db_bedrock, dict_keys=["bedrock", "bugrock"], list_keys=["bedrock_list"]
        )
        logging.info("Done getting the IPs and table names out of the servers.json file.")

        logging.info(f"Starting to load bedrock servers. (count: {len(self.bedrock_servers)})")
        await self._init_servers("Bedrock", self.bedrock_servers)

        logging.info(f"Starting to load dns for java servers. (count: {len(self.java_servers)})")
        await self._init_servers("Java", self.java_servers)

        logging.info("Starting to load previous database values for all servers.")
        all_servers = self.bedrock_servers + self.java_servers
        for server in all_servers:
            server.load_previous_values()

        return all_servers
