from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
from VARS import VARS
from time import time
import base64

from database.ServerDb import ServerDb

class JavaServerManager:
    name: str
    ip: str
    port: int 
    server: JavaServer
    db: ServerDb

    def __init__(self, name: str, ip: str, port: int = 25565):
        self.name = name
        self.ip = ip
        self.port = port
        self.server = JavaServer(ip, port)
        self.db = VARS.db_manager.get_server_db(name)
    

    def _build_nulldict(self, status: PingResponse):
        return {
            "version_protocol": status.version.protocol,
            "version_name": status.version.name,
            "motd": status.description,
            "favicon": base64.decodebytes(bytes(status.favicon.split(',')[-1], "ascii"))
        }
        

    def add_data_db(self):
        try:
            status = self.server.lookup(self.ip).status()
        except:
            print("failed to grab !")
            return #just continue another time if fail
        nulldict = self._build_nulldict(status)
        
        

        self.db.add_server_key(
            int(time()),
            status.players.online,
            status.players.max,
            int(status.latency),
            str(status.players.sample),
            nulldict
        )
