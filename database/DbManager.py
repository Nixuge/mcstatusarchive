import sqlite3
from sqlite3 import Connection, Cursor, Error


class DbInstance:
    connection: Connection
    cursor: Cursor

    def __init__(self, db_file: str):
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
    
        self.connection = self.create_connection(db_file)
        self.cursor = self.connection.cursor()

    def create_connection(self, db_file: str) -> Connection:
        # try:
        connection = sqlite3.connect(db_file, check_same_thread=False)
        print(f"Successfully connected to sqlite (v{sqlite3.version}) for file \"{db_file}\"")
        return connection
        # except Error as e:
        #     print(e)
        #     raise Error(e)
