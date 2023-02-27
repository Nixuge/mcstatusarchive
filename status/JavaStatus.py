from status.Status import Status

from mcstatus.pinger import PingResponse

from time import time
import base64

Player = PingResponse.Players.Player # bruh 

class JavaStatus(Status):
    def __init__(self, status: PingResponse):
        self.current_values = (
            int(time()), 
            status.players.online, 
            status.players.max, 
            int(status.latency), 
            self._get_player_sample(status.players.sample), 
            status.version.protocol, 
            status.version.name, 
            status.description, 
            self._get_favicon(status.favicon)
        )

        
    @staticmethod
    def _get_favicon(favicon: str | None) -> bytes | str:
        if favicon:
            # return "DISABLED FOR TESTING"
            return base64.decodebytes(bytes(favicon.split(',')[-1], "ascii"))
        return "None"

    @staticmethod
    def _get_player_sample(sample: list[Player] | None) -> str:
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