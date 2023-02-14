from status.Status import Status
from mcstatus.bedrock_status import BedrockStatusResponse

from mcstatus.pinger import PingResponse
from time import time
import base64

class BedrockStatus(Status):
    save_time: int

    players_on: int
    players_max: int
    ping: int

    version_protocol: int
    version_name: str
    version_brand: str
    motd: str
    gamemode: str
    map: str

    def __init__(self, status: BedrockStatusResponse):
        self.save_time = int(time())
        
        self.players_on = status.players_online
        self.players_max = status.players_max
        self.ping = int(status.latency)

        self.version_protocol = status.version.protocol
        self.version_name = status.version.version
        self.version_brand = status.version.brand
        self.motd = status.motd
        self.gamemode = status.gamemode
        self.map = status.map

        self.current_values = {
            "version_protocol": self.version_protocol,
            "version_name": self.version_name, 
            "version_brand": self.version_brand, 
            "motd": self.motd, 
            "gamemode": self.gamemode,
            "map": self.map
        }

        self.normal_values_tuple = (self.save_time, self.players_on, self.players_max, self.ping)
        self.null_values_tuple = (self.version_protocol, self.version_name, self.version_brand, self.motd, self.gamemode, self.map)
        self.null_null_tuple = (None, None, None, None, None, None)
