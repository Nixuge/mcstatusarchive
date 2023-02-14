import database.queries.Java as Queries
from status.JavaStatus import JavaStatus
from database.servers.Base import BaseDb
import os
class JavaDb(BaseDb):
    def init_server_table(self) -> None:
        self.cursor.execute(Queries.get_create_table_query(self.name))

    def add_server_key(self, java_status: JavaStatus):
        # os.system("clear")
        query = Queries.get_insert_query(self.name)
        has_changed, data = java_status.get_data_tuple(self.last_values)
        # print(self.last_values.items())
        # print(java_status.current_values.items())
        # print(has_changed)
        # input("WAITING")
        if has_changed:
            self.last_values = java_status.current_values

        # print(data[:-1])

        self.cursor.execute(query, data)
        self.connection.commit()
