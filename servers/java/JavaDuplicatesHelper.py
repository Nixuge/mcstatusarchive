# TODO
# - cache existing values
# - warn when too many caches values
# - get if value exists
# - save to db when new one gets added
# - get id from text
# etc etc...

import logging
from database.DbUtils import DbUtils
from servers.java.JavaServerFlags import JavaServerFlags
from vars.DbInstances import DBINSTANCES


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

            table_name = f"{self.flags.parent_table_name}_duplicates_{key}"

            if not DbUtils._table_exists(DBINSTANCES.java_duplicates_instance.cursor, table_name):
                continue
            
            results = DBINSTANCES.java_duplicates_instance.cursor.execute(
                f"""SELECT {key} FROM {table_name} WHERE {key} IS NOT NULL ORDER BY id DESC;""").fetchall()

            # last id should be equal to len(results) - 1
            # -> if not there's a missmatch & abort to avoid saving potentially wrong data.
            last_id = results[-1][0]
            if len(results != (last_id - 1)):
                logging.critical(f"ID MISSMATCH WHILE GRABBING DUPLICATES FOR TABLE {table_name}")

            for result in results:
                self.values[key].append(result[1])


    # to pass int: last_data from get_previous_values_from_db.
    # This makes it so that it grabs the needed items.
    def get_latest_values(self, last_data_ids: dict) -> dict:
        # Partially yoinked from DbUtils
        last_data_full = {}
        for key, enabled in self.flags.flags_dict.items():
            if not enabled: continue
            duplicate_id = last_data_ids.get(key)
            if duplicate_id == None: continue

            table_name = f"{self.flags.parent_table_name}_duplicates_{key}"

            if not DbUtils._table_exists(DBINSTANCES.java_duplicates_instance.cursor, table_name):
                continue
            
            result = DBINSTANCES.java_duplicates_instance.cursor.execute(
                f"""SELECT {key} FROM {table_name} WHERE id IS duplicate_id;""").fetchone()
            
            if result == None or len(result) == 0:
                logging.error(f"Even tho flag is enabled, the db seems to be empty... {table_name}")
            else:
                last_data_full[key] = result[1]

        return last_data_full

    