from mcstatus import BedrockServer
from VARS import VARS

from database.servers.BedrockDb import BedrockDb
from status.BedrockStatus import BedrockStatus

class BedrockServerManager:
    name: str
    ip: str
    port: int 
    server: BedrockServer
    db: BedrockDb

    def __init__(self, name: str, ip: str, port: int = 19132):
        self.name = name
        self.ip = ip
        self.port = port
        self.server = BedrockServer(ip, port)
        self.db = VARS.db_manager_bedrock.get_server_db(name)
    

    def add_data_db(self):
        try:
            status = self.server.lookup(f"{self.ip}").status()
            # print(f"Debug: Got a lookup successfully for {self.name}")
        except:
            print("Failed to grab !")
            return # just continue another time if fail
        
        self.db.add_server_key(BedrockStatus(status))