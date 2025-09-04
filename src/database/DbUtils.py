from sqlite3 import Cursor, OperationalError

class DbUtils:
    @staticmethod
    def table_exists(cursor: Cursor, table_name: str, column: str = "save_time"):
        # kinda dirty but needed to avoid all errors
        try:
            cursor.execute(f"""SELECT {column} FROM {table_name} ORDER BY {column} DESC LIMIT 1;""")
            return True
        except OperationalError:
            return False

    # @staticmethod
    # def get_previous_values_from_db(cursor: Cursor, table_name: str, server_type: ServerType) -> dict[str, Any]:
    #     if not DbUtils.table_exists(cursor, table_name):
    #         return {}
        
    #     last_values = {}
    #     for key in server_type.value:
    #         rel = cursor.execute(
    #             f"""SELECT {key} FROM {table_name} WHERE {key} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
    #         result = rel.fetchone() 
    #         # fetchone() returns a tuple w 1 element, need to get that out
    #         if result != None and len(result) > 0:
    #             data = result[0]
    #             last_values[key] = data

    #     return last_values