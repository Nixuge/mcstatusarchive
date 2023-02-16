import database.queries.Java as Queries
from status.JavaStatus import JavaStatus
from database.servers.Base import BaseDb

class JavaDb(BaseDb):
    def __init__(self, *args):
        self.null_keys = ("players_sample", "version_protocol", "version_name", "motd", "favicon")
        super().__init__(*args)
    

    def init_server_table(self) -> None:
        self.cursor.execute(Queries.get_create_table_query(self.name))

    def add_server_key(self, java_status: JavaStatus):
        query = Queries.get_insert_query(self.name)
        has_changed, data = java_status.get_data_tuple(self.last_values)

        if has_changed:
            self.last_values = java_status.current_values

        # print(data[:-1])
        # print(query)
        # print(data)
        
        self.cursor.execute(query, data)
        self.connection.commit()
        self.connection.serialize()
        # print(f"[Debug-Java]: Added a key successfully for {self.name}")