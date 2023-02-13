from objects.Status import Status
from mcstatus.bedrock_status import BedrockServerStatus, BedrockStatusResponse

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

    def __init__(self, status: BedrockStatusResponse, time: int = time()):
        self.save_time = time
        self.players_on = status.players_online
        self.players_max = status.players_max
        self.ping = status.latency

        self.version_protocol = status.version.protocol
        self.version_name = status.version.version
        self.version_brand = status.version.brand
        self.motd = status.description
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
        self.null_values_tuple(self.version_protocol, self.version_name, self.version_brand, self.motd, self.gamemode, self.map)

    
    @staticmethod
    def get_query(name: str):
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?,?);"""


    def get_value_tuple(self, previous_values: dict):
        if self._has_property_changed(previous_values):
            return self.normal_values_tuple + (None, None, None, None, None, None)
        else:
            return self.normal_values_tuple + self.null_values_tuple
