import sqlite3
from sqlite3 import Connection, Error
from database.servers.BedrockDb import BedrockDb

from database.servers.JavaDb import JavaDb

class DbManager:
    connection: Connection
    server_db_type: str

    def __init__(self, connection: Connection, server_db_type="java"):
        # see https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
        # & eventually https://ricardoanderegg.com/posts/python-sqlite-thread-safety/
        if sqlite3.threadsafety != 3:
            raise SystemError("""
============================================================
This program uses sqlite3 in a multithreaded context

This means writing to the DB is done in a multithreaded way

To avoid data corruption, this program will only launch if sqlite3 is compiled in a way that allows safe multithreaded access to the DB (sqlite.threadsafety = 3)

This is the case on Python 3.11 by default (at least for me), but not on 3.10

See https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety for more info
============================================================""")
    
        self.server_db_type = server_db_type
        self.connection = connection

    # def create_connection(self, db_file: str) -> Connection:
    #     try:
    #         # self.connection = sqlite3.connect(db_file, check_same_thread=False)
    #         print(f"Successfully connected to sqlite (v{sqlite3.version}) for {self.server_db_type}")
    #     except Error as e:
    #         print(e)

    def get_server_db(self, server_name: str) -> JavaDb | BedrockDb:
        if self.server_db_type == "java":
            return JavaDb(server_name, self.connection)
        else:
            return BedrockDb(server_name, self.connection)
