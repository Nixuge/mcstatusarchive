import asyncio
import logging
from typing import TypeVar

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


T = TypeVar("T", bound=ServerSv)


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

    
    def _load_servers_for_type(self, server_type: str, clazz: type[T], db: Database, dict_keys: list[str], list_keys: list[str]) -> list[T]:
        default_port = DEFAULT_PORTS[server_type]
        seen_endpoints: set[tuple[str, int]] = set()
        duplicates: set[str] = set()
        servers_list: list[T] = []

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

    async def _init_servers(self, server_type: str, servers: list[T], max_concurrent: int = 100) -> list[T]:
        total = len(servers)
        if total == 0:
            return []

        sem = asyncio.Semaphore(max_concurrent)
        done = 0

        async def init_one(server: T) -> tuple[T, bool]:
            nonlocal done
            async with sem:
                ok = await server.async_init()
            done += 1
            print(f"Initializing {server_type} servers {done}/{total}...", end="\r", flush=True)
            return server, ok

        results: list[tuple[T, bool]] = await asyncio.gather(*(init_one(s) for s in servers))
        print()

        servers_out: list[T] = []
        failed_servers: list[str] = []
        for server, ok in results:
            if ok:
                servers_out.append(server)
            else:
                failed_servers.append(f"{server.ip}:{server.port}")

        if failed_servers:
            logging.warning(f"{len(failed_servers)} {server_type} servers failed to initialize:")
            ErrorHandler.add_error(ErrorKey.DNS_LOOKUP_BATCH, {"servers": failed_servers})

        return servers_out

    async def parse(self) -> list[ServerSv]:
        java_servers = self._load_servers_for_type(
            SERVER_TYPE_JAVA, JavaServerSv, self.db_java, dict_keys=["java"], list_keys=["java_list"]
        )
        bedrock_servers = self._load_servers_for_type(
            SERVER_TYPE_BEDROCK, BedrockServerSv, self.db_bedrock, dict_keys=["bedrock", "bugrock"], list_keys=["bedrock_list"]
        )
        logging.info("Done getting the IPs and table names out of the servers.json file.")

        logging.info(f"Starting to load bedrock servers. (count: {len(bedrock_servers)})")
        self.bedrock_servers = await self._init_servers("Bedrock", bedrock_servers)

        logging.info(f"Starting to load dns for java servers. (count: {len(java_servers)})")
        self.java_servers = await self._init_servers("Java", java_servers)

        logging.info("Starting to load previous database values for all servers.")
        all_servers = self.bedrock_servers + self.java_servers
        for i, server in enumerate(all_servers):
            print(f"Loading values for server {i+1}/{len(all_servers)}...", end="\r", flush=True)
            server.load_previous_values()
        print(flush=True)
        
        logging.info("Done loading previous database values for all servers.")

        return all_servers
