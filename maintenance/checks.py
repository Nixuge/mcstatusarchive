import logging
import sqlite3
from database.DbQueries import GlobalQueries
from utils.timer import CumulativeTimers
from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS, JAVA_KEYS_ORDER

# Basically columns where it's possible to do maintenance
def get_default_types_columns(table_name: str, cursor: sqlite3.Cursor):
    final = []
    columns = cursor.execute(GlobalQueries.get_table_info(table_name)).fetchall()

    for key, column_type in columns:
        if key not in JAVA_EXCEPTED_KEYS.keys() or column_type != JAVA_EXCEPTED_KEYS[key]: 
            continue
        final.append(key)

    return final

# columns_to_check:
# if None, continue w all columns
# if empty list, do nothing
# otherwise do for valus in it
def run_db_checks(table_name: str):
    conn = sqlite3.connect("z_java_servers.db", check_same_thread=False)
    cursor = conn.cursor()
    columns_to_check = get_default_types_columns(table_name, cursor)
    results = {"duplicates": [], "nonnull": []}

    if columns_to_check == []:
        return results

    
    CumulativeTimers.get_timer("Startup check").start_time(table_name)
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    for key, index in JAVA_KEYS_ORDER.items():
        if columns_to_check and key not in columns_to_check: continue
        test_query = f"SELECT * FROM {table_name} WHERE {key} IS NOT NULL;"
        test_data = [x[index] for x in cursor.execute(test_query).fetchall()]
        len_duplicates = len(test_data)
        len_nodupe = len(set(test_data))

        if len_duplicates < 100:
            continue # not enough data to process
        
        if len_duplicates == 0:
            nonnull_ratio = 0
            duplicate_ratio = 0
        else:
            nonnull_ratio = (len_duplicates / count) * 100
            duplicate_ratio = 100 - (len_nodupe / len_duplicates) * 100

        nonnull_ratio = round(nonnull_ratio, 2)
        duplicate_ratio = round(duplicate_ratio, 2)
        
        if key == "players_sample":
            if duplicate_ratio > 10:
                results["duplicates"].append(key)
                warn_high_duplicates(table_name, key, duplicate_ratio, len_duplicates)
        elif nonnull_ratio > 10:
            if duplicate_ratio > 10:
                results["duplicates"].append(key)
                warn_high_duplicates(table_name, key, duplicate_ratio, len_duplicates)
            else:
                results["nonnull"].append(key)
                warn_high_nonnull(table_name, key, nonnull_ratio, duplicate_ratio)

    conn.close()
    return results

def warn_high_nonnull(table_name: str, key: str, percentage: float, percentage_duplicate: float):
    logging.warn(f"High number of non null unique keys for {table_name} ({key}): {percentage}% ({percentage_duplicate}% duplicate)")

def warn_high_duplicates(table_name: str, key: str, percentage: float, len_total):
    logging.warn(f"Duplicate ratio high for {table_name} ({key}): {percentage}% (out of {len_total} elements)")