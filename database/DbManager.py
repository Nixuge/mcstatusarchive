import sqlite3
from sqlite3 import Connection, Error
from database.servers.BedrockDb import BedrockDb

from database.servers.JavaDb import JavaDb

class DbManager:
    connection: Connection
    server_db_type: str

    def __init__(self, server_db_type="java"):
        self.server_db_type = server_db_type
        self.create_connection(f"z_{server_db_type}_servers.db")

    def create_connection(self, db_file: str) -> Connection:
        try:
            self.connection = sqlite3.connect(db_file)
            print(f"Successfully connected to sqlite (v{sqlite3.version}) for {self.server_db_type}")
        except Error as e:
            print(e)

    def get_server_db(self, server_name: str) -> JavaDb | BedrockDb:
        if self.server_db_type == "java":
            return JavaDb(server_name, self.connection)
        else:
            return BedrockDb(server_name, self.connection)
