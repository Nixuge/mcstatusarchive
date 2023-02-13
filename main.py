from mcstatus import BedrockServer
from servers.java import JavaServerManager
import time

#for some weird reason need to first instantiate and then lookup
status = BedrockServer("pe.mineplex.com").lookup("pe.mineplex.com").status()

print(status.version.brand)
print(status.version.protocol)
print(status.version.version)
print(status.gamemode)
print(status.latency)
print(status.map)
print(status.motd)
print(status.players_max)
print(status.players_online)


hypixel = JavaServerManager("mineplex", "mineplex.com", 25565)

while True:
    hypixel.add_data_db()
    time.sleep(1)


# HOW THIS WORKS:
# - the script grabs every info about the server & saves it to db
# - next time the save runs, if all previous long standing info (motd, version, etc) 
# --- are the same, just fill those w NULLs (note that playercount still updates)
# --- However, if just 1 value is different, the whole row update (for easier queries)