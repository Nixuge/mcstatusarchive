from database.DbQueries import GlobalQueries, JavaDuplicateQueries
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS


class JavaServerFlags:
    flags_dict: dict[str, bool]
    parent_table_name: str
    def __init__(self, table_name: str) -> None:
        self.parent_table_name = table_name
        self.flags_dict = {}

        exists = bool(DBINSTANCES.java_instance.cursor.execute(GlobalQueries.already_exists(table_name)).fetchone()[0])
        if not exists:
            return
        for key, column_type in DBINSTANCES.java_instance.cursor.execute(GlobalQueries.get_table_info(table_name)).fetchall():
            if key not in JAVA_EXCEPTED_KEYS.keys() or column_type == JAVA_EXCEPTED_KEYS[key]: 
                continue
            self.flags_dict[key] = True

        self._create_dbs()
        self.flags_dict["version_name"] = False
        self.flags_dict["motd"] = False

        self.__curr = 0
        self.__term = len(self.flags_dict)

    def _create_dbs(self):
        for key, enabled in self.flags_dict.items():
            if not enabled: 
                continue
            DBQUEUES.db_queue_duplicates_java.add_important_instruction(
                JavaDuplicateQueries.get_create_table_query(self.parent_table_name, key)
            )

    def get(self, key: str):
        return self.flags_dict.get(key)

    def __iter__(self):
        return self
    
    def __next__(self):
        if self.__curr >= self.__term:
            raise StopIteration()
        data = tuple(self.flags_dict.items())[self.__curr]
        self.__curr += 1
        return data