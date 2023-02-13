from mcstatus import BedrockServer
from mcstatus.pinger import PingResponse
from VARS import VARS
from time import time
import base64

from database.ServerDb import ServerDb

class BedrockServerManager:
    name: str
    ip: str
    port: int 
    server: BedrockServer
    db: ServerDb

    def __init__(self, name: str, ip: str, port: int = 19132):
        self.name = name
        self.ip = ip
        self.port = port
        self.server = BedrockServer(ip, port)
        self.db = VARS.db_manager_bedrock.get_server_db(name)
    

    def _build_nulldict(self, status: PingResponse):
        return {
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "motd": status.description,
            "favicon": base64.decodebytes(bytes(status.favicon.split(',')[-1], "ascii"))
        }
        

    def add_data_db(self):
        status = self.server.lookup(self.ip).status()
        nulldict = self._build_nulldict(status)
        
        

        self.db.add_server_key(
            int(time()),
            status.players.online,
            status.players.max,
            int(status.latency),
            str(status.players.sample),
            nulldict
        )
