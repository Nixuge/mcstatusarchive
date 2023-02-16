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

def get_insert_query(name: str) -> str:
    return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?,?);"""