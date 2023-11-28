from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS


class BedrockQueries:
    @staticmethod
    def get_create_table_query(name: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                    save_time INT NOT NULL,

                    players_on INT,
                    players_max INT,
                    ping INT,

                    version_protocol INT,
                    version_name VARCHAR(255),
                    version_brand VARCHAR(255),
                    motd TEXT,
                    gamemode VARCHAR(255),
                    map VARCHAR(255),
                    
                    PRIMARY KEY (save_time)
                    );"""

    @staticmethod
    def get_insert_query(name: str) -> str:
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?,?);"""


class JavaQueries:
    @staticmethod
    def get_create_table_query(name: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name} (
                    save_time INT NOT NULL,

                    players_on INT,
                    players_max INT,
                    ping INT,
                    players_sample TEXT,

                    version_protocol INT,
                    version_name VARCHAR(255),
                    motd TEXT,
                    favicon BLOB(65534),
                    
                    PRIMARY KEY (save_time)
                    );"""

    @staticmethod
    def get_insert_query(name: str) -> str:
        return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?);"""

class JavaDuplicateQueries:
    @staticmethod
    def get_create_table_query(name: str, key: str) -> str:
        return f"""CREATE TABLE IF NOT EXISTS {name}_duplicates_{key} (
                    id INT NOT NULL,
                    {key} {JAVA_EXCEPTED_KEYS[key]} NOT NULL,
                    
                    PRIMARY KEY (id)
                    );"""

    @staticmethod
    def get_insert_query(name: str, key: str) -> str:
        return f"""INSERT INTO {name}_duplicates_{key} VALUES (?,?);"""


class GlobalQueries:
    @staticmethod
    def already_exists(name: str) -> str:
        return f"SELECT count(*) FROM sqlite_master WHERE type='table' AND name='{name}';"

    @staticmethod
    def get_table_info(name: str) -> str:
        return f"SELECT name, type FROM pragma_table_info('{name}');"