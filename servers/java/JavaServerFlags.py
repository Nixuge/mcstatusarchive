from database.DbQueries import GlobalQueries
from vars.DbInstances import DBINSTANCES
from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS


class JavaServerFlags:
    flags_dict: dict
    def __init__(self, table_name: str) -> None:
        self.flags_dict = {}

        exists = bool(DBINSTANCES.java_instance.cursor.execute(GlobalQueries.already_exists(table_name)).fetchone()[0])
        if not exists:
            return
        for key, column_type in DBINSTANCES.java_instance.cursor.execute(GlobalQueries.get_table_info(table_name)).fetchall():
            if key not in JAVA_EXCEPTED_KEYS.keys() or column_type == JAVA_EXCEPTED_KEYS[key]: 
                continue
            self.flags_dict[key] = True