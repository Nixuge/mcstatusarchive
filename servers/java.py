from mcstatus import JavaServer
from VARS import VARS

from database.servers.JavaDb import JavaDb
from status.JavaStatus import JavaStatus

class JavaServerManager:
    name: str
    ip: str
    port: int 
    server: JavaServer
    db: JavaDb

    def __init__(self, name: str, ip: str, port: int = 25565):
        self.name = name
        self.ip = ip
        self.port = port
        self.server = JavaServer(ip, port)
        self.db = VARS.db_manager.get_server_db(name)
    

    def add_data_db(self):
        try:
            status = self.server.lookup(f"{self.ip}").status()
        except:
            print(f"Failed to grab {self.name}!")
            return # just continue another time if fail
        
        self.db.add_server_key(JavaStatus(status))
        
