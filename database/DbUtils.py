from enum import Enum
from sqlite3 import Cursor, OperationalError
from typing import Any

from database.LastValueSaver import LastValueSaver

# serves both as a server type enum
# and as a server args enum
class ServerType(Enum):
    JAVA = ("save_time", "players_on", "players_max", "ping", "players_sample", "version_protocol", "version_name", "motd", "favicon")
    BEDROCK = ("save_time", "players_on", "players_max", "ping", "version_protocol", "version_name", "version_brand", "motd", "gamemode", "map")


class DbUtils:
    @staticmethod
    def get_args_in_order_from_dict(args_dict: dict, server_type: ServerType) -> list:
        # Convert a dict to a list of items in order
        ordered_args: list[Any] = []
        for key in server_type.value:
            ordered_args.append(args_dict.get(key, None))
        return ordered_args

    @staticmethod
    def _table_exists(cursor: Cursor, table_name: str, column: str = "save_time"):
        # kinda dirty but needed to avoid all errors
        try:
            cursor.execute(f"""SELECT {column} FROM {table_name} ORDER BY {column} DESC LIMIT 1;""")
            return True
        except OperationalError:
            return False

    @staticmethod
    def get_previous_values_from_db(cursor: Cursor, table_name: str, server_type: ServerType, last_values_saver: LastValueSaver) -> dict[str, Any]:
        if not DbUtils._table_exists(cursor, table_name):
            return {}
        
        last_values = {}
        for key in server_type.value:
            rel = cursor.execute(
                f"""SELECT {key} FROM {table_name} WHERE {key} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
            result = rel.fetchone() 
            # fetchone() returns a tuple w 1 element, need to get that out
            if result != None and len(result) > 0:
                data = result[0]
                last_values[key] = data
                last_values_saver.set_value(table_name, key, data)

        return last_values