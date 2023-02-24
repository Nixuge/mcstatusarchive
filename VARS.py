from VARS_CONNECTION import CONNECTIONS
from database.DbManager import DbManager


class VARS:
    db_manager = DbManager(CONNECTIONS.java_connection)
    db_manager_bedrock = DbManager(CONNECTIONS.bedrock_connection, "bedrock")
