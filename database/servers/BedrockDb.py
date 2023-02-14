import database.queries.Bedrock as Queries
from status.BedrockStatus import BedrockStatus
from database.servers.Base import BaseDb

class BedrockDb(BaseDb):
    def init_server_table(self) -> None:
        self.cursor.execute(Queries.get_create_table_query(self.name))

    def add_server_key(self, bedrock_status: BedrockStatus):
        query = Queries.get_insert_query(self.name)
        has_changed, data = bedrock_status.get_data_tuple(self.last_values)
        if has_changed:
            self.last_values = bedrock_status.current_values

        self.cursor.execute(query, data)
        self.connection.commit()
        # print(f"Debug: Added a key successfully for {self.name}")


