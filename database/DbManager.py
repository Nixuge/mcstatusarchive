import sqlite3
from sqlite3 import Connection, Error

from database.ServerDb import ServerDb

class DbManager:
    connection: Connection

    def __init__(self, server_db_type="java"):
        self.create_connection(f"z_{server_db_type}_servers.db")

    def create_connection(self, db_file: str) -> Connection:
        try:
            self.connection = sqlite3.connect(db_file)
            print(f"Successfully connected to sqlite (v{sqlite3.version})")
        except Error as e:
            print(e)

    def get_server_db(self, server_name: str) -> ServerDb:
        return ServerDb(server_name, self.connection)
