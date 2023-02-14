from status.Status import Status

from mcstatus.pinger import PingResponse
from time import time
import base64

class JavaStatus(Status):
    save_time: int

    players_on: int
    players_max: int
    ping: int
    players_sample: str

    version_protocol: int
    version_name: str
    motd: str
    favicon: bytes

    def __init__(self, status: PingResponse):
        self.save_time = int(time())
        
        self.players_on = status.players.online
        self.players_max = status.players.max
        self.ping = int(status.latency)
        self.players_sample = str(status.players.sample)

        self.version_protocol = status.version.protocol
        self.version_name = status.version.name
        self.motd = status.description
        self.favicon = base64.decodebytes(bytes(status.favicon.split(',')[-1], "ascii"))

        self.current_values = {
            "version_protocol": self.version_protocol,
            "version_name": self.version_name, 
            "motd": self.motd, 
            "favicon": self.favicon
        }

        self.normal_values_tuple = (self.save_time, self.players_on, self.players_max, self.ping, self.players_sample)
        self.null_values_tuple = (self.version_protocol, self.version_name, self.motd, self.favicon)


    def get_data_tuple(self, previous_values: dict) -> tuple[bool, tuple]:
        if self._has_property_changed(previous_values):
            return True, self.normal_values_tuple + self.null_values_tuple
        else:
            return False, self.normal_values_tuple + (None, None, None, None)
        