from status.Status import Status
from mcstatus.bedrock_status import BedrockStatusResponse

from time import time

class BedrockStatus(Status):
    def __init__(self, status: BedrockStatusResponse):
        self.current_values = (
            int(time()), 
            status.players_online, 
            status.players_max, 
            int(status.latency),
            status.version.protocol, 
            status.version.version, 
            status.version.brand, 
            status.motd, 
            status.gamemode, 
            status.map
        )

