from enum import Enum
from sqlite3 import Cursor
from typing import Any

# serves both as a server type enum
# and as a server args enum
class ServerType(Enum):
    JAVA = ("save_time", "players_on", "players_max", "ping", "players_sample", "version_protocol", "version_name", "motd", "favicon")
    BEDROCK = ("save_time", "players_on", "players_max", "ping", "version_protocol", "version_name", "version_brand", "motd", "gamemode", "map")


class DbUtils:
    @staticmethod
    def get_args_in_order_from_dict(args_dict: dict, server_type: ServerType):
        # Convert a dict to a list of items in order
        ordered_args: list[Any] = []
        for key in server_type.value:
            ordered_args.append(args_dict.get(key, None))
        return ordered_args

    @staticmethod
    def get_previous_values_from_db(cursor: Cursor, table_name: str, server_type: ServerType):
        last_values = {}
        for key in server_type.value:
            rel = cursor.execute(
                f"""SELECT {key} FROM {table_name} WHERE {key} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
            result = rel.fetchone() 
            # fetchone() returns a tuple w 1 element, need to get that out
            if result != None and len(result) > 0:
                last_values[key] = result[0]

        return last_values