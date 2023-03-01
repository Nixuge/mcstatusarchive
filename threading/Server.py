from enum import Enum

class ServerType(Enum):
    BEDROCK = None
    JAVA = None

class Server:
    server_type: ServerType
    ip: str
    port: int

    values: dict

    def __init__(self, server_type: ServerType, ip: str, port: int = 25565) -> None:
        self.server_type = server_type
        self.ip = ip
        self.port = port
        self.values = {}
    
    def update_values(self, new_values: dict):
        # this only works if new_values has all needed values in it
        for key, val in new_values.items():
            if self.values.get(key) != val:
                

    # TODO:
    # values list in here
    # func that saves values & returns only the changed ones