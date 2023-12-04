# TODO
# - cache existing values -> done
# - warn when too many caches values -> done
# - get if value exists -> done
# - save to db when new one gets added -> done
# - get id from text -> done
# etc etc...

import logging
from typing import Any
from database.DbQueries import JavaDuplicateQueries
from database.DbUtils import DbUtils
from servers.java.JavaServerFlags import JavaServerFlags
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.config import Logging


class JavaDuplicatesHelper:
    flags: JavaServerFlags
    values: dict[str, list[str]]
    def __init__(self, flags: JavaServerFlags) -> None:
        self.flags = flags
        self._load_all_values()
    
    def _load_all_values(self):
        self.values = {}
        for key, enabled in self.flags:
            if not enabled: continue
            self.values[key] = []

            table_name = JavaDuplicateQueries.get_duplicate_table_name(self.flags.parent_table_name, key)

            if not DbUtils._table_exists(DBINSTANCES.java_duplicates_instance.cursor, table_name, "id"):
                continue
            
            results = DBINSTANCES.java_duplicates_instance.cursor.execute(
                f"""SELECT * FROM {table_name} WHERE {key} IS NOT NULL ORDER BY id;""").fetchall()
            
            # last id should be equal to len(results) - 1
            # -> if not there's a missmatch & abort to avoid saving potentially wrong data.
            last_id = results[-1][0]
            lenR = len(results)
            if (lenR - 1) != last_id:
                logging.critical(f"ID MISSMATCH WHILE GRABBING DUPLICATES FOR TABLE {table_name}")
                # todo: exit critical error
            
            if lenR > 5000 and Logging.LOG_HIGH_COUNT_DUPLICATE_TABLE:
                logging.warn(f"High count of elements in duplicates list for table {table_name}")

            for result in results:
                self.values[key].append(result[1])

    # to pass int: last_data from get_previous_values_from_db.
    # This makes it so that it grabs the needed items.
    # Note: mutates the initial dict
    def get_latest_values(self, last_data_ids: dict) -> dict:
        # Partially yoinked from DbUtils
        last_data_full = last_data_ids
        for key, enabled in self.flags.flags_dict.items():
            if not enabled: continue
            duplicate_id = last_data_ids.get(key)
            if duplicate_id == None: continue

            table_name = JavaDuplicateQueries.get_duplicate_table_name(self.flags.parent_table_name, key)

            if not DbUtils._table_exists(DBINSTANCES.java_duplicates_instance.cursor, table_name, "id"):
                continue

            result = DBINSTANCES.java_duplicates_instance.cursor.execute(
                f"""SELECT {key} FROM {table_name} WHERE id = {duplicate_id};""").fetchone()
            
            if result == None or len(result) == 0:
                logging.error(f"Even tho flag is enabled, the db seems to be empty... {table_name}")
            else:
                last_data_full[key] = result[0]

        return last_data_full

    def _add_index(self, key: str, value: Any):
        self.values[key].append(value)
        DBQUEUES.db_queue_duplicates_java.add_instuction(
            JavaDuplicateQueries.get_insert_query(self.flags.parent_table_name, key),
            [len(self.values[key]) - 1, value]
        )

    # returns id if duplicate flag for key enabled
    # else returns the value itself
    def get_value_for_save(self, key: str, grabbed_value: Any):
        if grabbed_value == None: return None
        flag = self.flags.get(key)
        if not flag: return grabbed_value
        try:
            return self.values[key].index(grabbed_value)
        except ValueError:
            self._add_index(key, grabbed_value)
            return len(self.values[key]) - 1
