from status.Status import Status

from mcstatus.pinger import PingResponse

from time import time
import base64

Player = PingResponse.Players.Player # bruh 

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
        self.null_args_order = ("players_sample", "version_protocol", "version_name", "motd", "favicon")
        
        self.save_time = int(time())
        
        self.players_on = status.players.online
        self.players_max = status.players.max
        self.ping = int(status.latency)
        
        self.players_sample = self._get_player_sample(status.players.sample)

        self.version_protocol = status.version.protocol
        self.version_name = status.version.name
        self.motd = status.description
        if status.favicon:
            self.favicon = base64.decodebytes(bytes(status.favicon.split(',')[-1], "ascii"))
            # self.favicon = "DISABLED FOR TESTING"
        else:
            self.favicon = "None"
        
        self.current_values = {
            "players_sample": self.players_sample,
            "version_protocol": self.version_protocol,
            "version_name": self.version_name, 
            "motd": self.motd, 
            "favicon": self.favicon
        }

        self.normal_values_tuple = (self.save_time, self.players_on, self.players_max, self.ping)
        self.null_values_tuple = (self.players_sample, self.version_protocol, self.version_name, self.motd, self.favicon)

    @staticmethod
    def _get_player_sample(sample: list[Player] | None):
        if sample == None:
            return "None"
        if len(sample) == 0:
            return "[]" 

        players = []
        for player in sample:
            players.append({
                "name": player.name,
                "id": player.id
            })

        return str(players)