from sqlite3 import Connection, Cursor
from abc import abstractmethod
import sqlite3
from typing import Any


class BaseDb:
    name: str
    connection: Connection
    cursor: Cursor
    db_columns_order: tuple
    last_values: list

    def __init__(self, name: str, connection: Connection):
        self.name = name
        self.connection = connection
        # print(f"Successfully connected to sqlite (v{sqlite3.version}) for {self.name}")
        self.cursor = connection.cursor()
        self.init_server_table()

        self.last_values = []
        for key in self.db_columns_order:
            self.last_values.append(self._get_last_db(key))
        
            

    def _get_last_db(self, column: str) -> str | None:
        rel = self.cursor.execute(
            f"""SELECT {column} FROM {self.name} WHERE {column} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
        result = rel.fetchone()
        if result != None and len(result) > 0:
            return result[0]

    @abstractmethod
    def init_server_table(self) -> None:
        pass

    # @abstractmethod
    # def add_server_key(self, status: Any):
    #     pass


