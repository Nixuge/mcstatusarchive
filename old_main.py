#!/bin/python3
import signal
import time
import json
from threading import Thread
from VARS import VARS
from VARS_DBQUEUES import DBQUEUES
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
    with open("servers_alone.json", "r") as file:
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
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_bedrock.start()

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
