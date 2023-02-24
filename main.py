#!/bin/python3
import signal
import time
import json
from threading import Thread
from servers.bedrock import BedrockServerManager
from servers.java import JavaServerManager


# from https://stackoverflow.com/a/26064238
def wait_processes_timeout(procs: list[Thread]):
    TIMEOUT = 30
    start = time.time()
    while time.time() - start <= TIMEOUT:
        if not any(p.is_alive() for p in procs):
            print("    == All processes done! ==")
            break

        time.sleep(.01)  # Just to avoid hogging the CPU
    else:
        # We only enter this if we didn't 'break' above.
        print(" == Timed out, killing all ==")
        total_late = 0
        for p in procs:
            total_late += 1
            # SUBOPTIMAL (KILLING THREADS CAN CAUSE ISSUES SUCH AS MEM LEAKS)
            # NEED TO TRY AND WORK OUT ASYNC IF POSSIBLE W THIS LIB
            # OR RESTRUCTURE FOR MULTIPROCESSING
            # signal.pthread_kill(p.native_id, signal.SIGKILL) -> DOESNT WORK (KILLS EVERYTHING)
            # p.terminate() -> ONLY FOR MULTIPROCESSING
            p.join()
        print(f"{total_late} thread(s) late")
    
    while time.time() - start <= TIMEOUT:
        # Even after the check above, wait for the timeout to end (since we get maps at a fixed time)
        time.sleep(.01)



def split_list(lst, n = 2):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def load_json():
    # dirty af but working
    list_java: list[JavaServerManager] = []
    list_pe: list[BedrockServerManager] = []
    with open("servers.json", "r") as file:
        dico = json.load(file)
    
    for value in dico["java"]:
        list_java.append(JavaServerManager(value, dico["java"][value]))
    for value in dico["bugrock"]:
        list_pe.append(BedrockServerManager(value, dico["bugrock"][value]))

    return list_java, list_pe

    

def save_group(servers: list[JavaServerManager | BedrockServerManager]):
    for server in servers:
        server.add_data_db()


if __name__ == "__main__":

    java_servers, pe_servers = load_json()
    # Same start function in both so it's save to mix them in
    all_servers = java_servers + pe_servers
    
    all_servers_groups = list(split_list(all_servers))

    while True:
        processes = []
        for group in all_servers_groups:
            proc = Thread(target=save_group, args=(group, ), )
            processes.append(proc)
            proc.start()

        
        print("===== Spawned all processes =====")
        wait_processes_timeout(processes)
        print("===== Timeout done waiting ! =====")




# HOW THIS WORKS:
# - the script grabs every info about the server & saves it to db
# - next time the save runs, if all previous long standing info (motd, version, etc) 
# --- are the same, just fill those w NULLs (note that playercount still updates)
# --- However, if just 1 value is different, the whole row update (for easier queries)

#TODO:
# docker container containing everythging below
# actual website/UI to view data
# -> to avoid SQL injection, do smth like "if input not in trusted_servers" server side
# fix mem leaks (i think theres one) 
# -> BETTER METHOD TO ACTUALLY RUN THE SAVE
# -> EVENTUALLY REFACTOR
# other sources (from the internet etc) to view old data

#TODO:
# switch the names on the SQL table over to actual server ips to avoid conflicting servers
# then add a dict w like {"hypixel": "mc_hypixel_net"}

#TODO:
# save host location

#TODO:
#bedrock_nationsglory_fr & Galaxite are having issues
# See if I can PR or fix the thing or smth

#TODO:
# to save even more space, when server is down set playercount to "DOWN"
# and when the data doesn't change, don't actually save any line