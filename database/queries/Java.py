def get_create_table_query(name: str) -> str:
    return f"""CREATE TABLE IF NOT EXISTS {name} (
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
                );"""

def get_insert_query(name: str) -> str:
    return f"""INSERT INTO {name} VALUES (?,?,?,?,?,?,?,?,?);"""