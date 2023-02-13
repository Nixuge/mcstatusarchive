from sqlite3 import Connection, Cursor

class ServerDb:
    name: str
    connection: Connection
    cursor: Cursor
    last_values: dict = {}
    null_if_same_as_previous: list = ["version_protocol", "version_name", "motd", "favicon"]

    def __init__(self, name: str, connection: Connection):
        self.name = name
        self.connection = connection
        self.cursor = connection.cursor()
        self.init_server_table()
        for val in self.null_if_same_as_previous:
            self.last_values[val] = self._get_last_db(val) 

    def init_server_table(self) -> None:
        self.cursor.execute(f"""CREATE TABLE IF NOT EXISTS {self.name} (
                                save_time INT NOT NULL,
                                players_on INT NOT NULL,
                                players_max INT NOT NULL,
                                ping INT NOT NULL,
                                players_sample VARCHAR(255) NOT NULL,
                                version_protocol INT,
                                version_name VARCHAR(255),
                                motd VARCHAR(255),
                                favicon BLOB(65534),
                                PRIMARY KEY (save_time)
                            );""")

    def _get_last_db(self, column: str) -> str:
        rel = self.cursor.execute(
            f"""SELECT {column} FROM {self.name} WHERE {column} IS NOT NULL ORDER BY save_time DESC LIMIT 1;""")
        result = rel.fetchone()
        if result != None and len(result) > 0:
            return result[0]


    def add_server_key(self, save_time: int, players_on: int, players_max: int, ping: int,
                       players_sample: str, null_previous: dict):

        for key in null_previous:
            if null_previous[key] == self.last_values[key]:
                null_previous[key] = None
            else:
                self.last_values[key] = null_previous[key]
        
        query = f"""INSERT INTO {self.name} VALUES (?,?,?,?,?,?,?,?,?);"""
        
        data = (save_time, players_on, players_max, ping, players_sample) + tuple(null_previous.values())

        print(data[:-1])

        self.cursor.execute(query, data)
        self.connection.commit()

