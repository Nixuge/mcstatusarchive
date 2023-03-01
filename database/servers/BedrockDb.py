from VARS_DBQUEUES import DBQUEUES
import database.Queries as Queries
from status.BedrockStatus import BedrockStatus
from database.servers.Base import BaseDb

class BedrockDb(BaseDb):
    db_columns_order = ("save_time", "players_on", "players_max", "ping", "version_protocol", "version_name", "version_brand", "motd", "gamemode", "map")
    
    def init_server_table(self) -> None:
        self.cursor.execute(Queries.get_create_table_query(self.name))

    def add_server_key(self, bedrock_status: BedrockStatus):
        query = Queries.get_insert_query(self.name)
        has_changed, data = bedrock_status.get_data_tuple(self.last_values)

        if has_changed:
            self.last_values = bedrock_status.current_values

        DBQUEUES.db_queue_bedrock.add_instuction(query, data)

        # self.cursor.execute(query, data)
        # self.connection.commit()
        # self.connection.serialize()
        # print(f"[Debug-BR]: Added a key successfully for {self.name}")


