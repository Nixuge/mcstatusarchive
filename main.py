from mcstatus import BedrockServer, JavaServer
from server import ServerMgr
import time

#for some weird reason need to first instantiate and then lookup
status = BedrockServer("pe.mineplex.com").lookup("pe.mineplex.com").status()

print(status.version.brand)


hypixel = ServerMgr("hypixel", "hypixel.net", 25565)

while True:
    hypixel.add_data_db()
    time.sleep(5)