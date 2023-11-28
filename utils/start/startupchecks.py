import logging
from utils.timer import CumulativeTimers
from vars.DbInstances import DBINSTANCES

keys = {
    "favicon": 8,
    "motd": 7,
    "players_sample": 4,
    "version_name": 6
}

def run_startup_checks(table_name: str):
    cursor = DBINSTANCES.java_instance.cursor
    CumulativeTimers.get_timer("Startup check").start_time(table_name)
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

    for key, index in keys.items():
        test_query = f"SELECT * FROM {table_name} WHERE {key} IS NOT NULL;"
        test_data = [x[index] for x in cursor.execute(test_query).fetchall()]
        len_duplicates = len(test_data)
        len_nodupe = len(set(test_data))

        if len_duplicates < 100:
            return # not enough data to process
        
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
                warn_high_duplicates(table_name, key, duplicate_ratio, len_duplicates)
        elif nonnull_ratio > 10:
            if duplicate_ratio > 10:
                warn_high_duplicates(table_name, key, duplicate_ratio, len_duplicates)
            else:
                warn_high_nonnull(table_name, key, nonnull_ratio, duplicate_ratio)


def warn_high_nonnull(table_name: str, key: str, percentage: float, percentage_duplicate: float):
    logging.warn(f"High number of non null unique keys for {table_name} ({key}): {percentage}% ({percentage_duplicate}% duplicate)")

def warn_high_duplicates(table_name: str, key: str, percentage: float, len_total):
    logging.warn(f"Duplicate ratio high for {table_name} ({key}): {percentage}% (out of {len_total} elements)")