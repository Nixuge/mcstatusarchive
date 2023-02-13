from database.DbManager import DbManager


class VARS:
    db_manager = DbManager()
    db_manager_bedrock = DbManager("bedrock")