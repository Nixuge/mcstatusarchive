from sqlite3 import Connection, Cursor
from abc import abstractmethod
from typing import Any


class BaseDb:
    name: str
    connection: Connection
    cursor: Cursor
    last_values: dict = {}

    def __init__(self, name: str, connection: Connection):
        self.name = name
        self.connection = connection
        self.cursor = connection.cursor()
        self.init_server_table()

    def _get_last_db(self, column: str) -> str:
        rel = self.cursor.execute(
            f"""SELECT {column} FROM {self.name} WHERE {column} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
        result = rel.fetchone()
        if result != None and len(result) > 0:
            return result[0]

    @abstractmethod
    def init_server_table(self) -> None:
        pass

    @abstractmethod
    def add_server_key(self, status: Any):
        pass

