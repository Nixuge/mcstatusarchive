from concurrent.futures import ThreadPoolExecutor
import logging
import sqlite3
from threading import Thread
from database.DbQueries import GlobalQueries
from maintenance.checks import run_db_checks
from maintenance.migrator import process_column
from utils.timer import Timer
from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS

AUTO_RUN = True

def maintenance_main():
    print("Maintenance tool for mcstatusarchive's DB.")
    print("Running basic DB checks")
    # db_name = "Play_KingdomsMineMC_Net"
    # columns_to_check = get_default_types_columns(db_name)
    # data = run_db_checks(db_name, columns_to_check)
    # print(f"Table {db_name}, got data: {data}")

    # for column in data["duplicates"]:
    #     if AUTO_RUN or input(f"Migrate db column {column} for server {db_name}? ") in ["y", "yes", "o"]:
    #         process_column(db_name, column)
    run_all_tables()

def run_table(table_name: str, table_index: int):
    data = run_db_checks(table_name)
    if len(data["duplicates"]) == 0 and len(data["nonnull"]) == 0:
        # logging.warn(f"Skipped table {table_name}")
        return
    # logging.critical(f"Table {table_name}, got data: {data}")

    for column in data["duplicates"]:
        if AUTO_RUN or input(f"Migrate db column {column} for server {table_name}? ") in ["y", "yes", "o"]:
            # process_column(table_name, column, table_index)
            pass
    
    # logging.critical("Done with table.")

def run_all_tables():
    timer = Timer()
    # initial_size = 
    conn = sqlite3.connect("z_java_servers.db")
    tables = [x[0] for x in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    conn.close()
    # print(tables)
    lenT = len(tables)
    # tables = tables[:8]
    threads: list[Thread] = []




    for index, table in enumerate(tables):
        # logging.error(f"Table {index}/{lenT}")

        run_table(table, index)
        # thread = Thread(target = run_table, args = (table, index))
    #     # run_table(table)
    #     threads.append(thread)
    #     thread.start()
    
    # for thread in threads:
    #     thread.join()

    logging.info(timer.end())    
    
    # timer = Timer()
    # logging.info("Vacuuming...")
    # DBINSTANCES.java_instance.cursor.execute("VACUUM;")
    # DBINSTANCES.java_instance.connection.commit()
    # logging.info(f"Vacuumed. ({timer.end()})")

