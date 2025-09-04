from database.DbInstance import DbInstance

ALL_DB_NAMES = "_abcdefghijklmnopqrstuvwxyz"

class JavaDbInstances:
    dbs: dict[str, DbInstance]
    def __init__(self) -> None:
        self.dbs = {}
        for name in ALL_DB_NAMES:
            self.dbs[name] = DbInstance(f"z_DBs/java-{name}.sqlite3")
    
    def __getitem__(self, name: str) -> DbInstance:
        if name.startswith("mc_"):
            name = name[3:]

        if name.startswith("mcsl_"):
            name = name[5:]
        
        if name.startswith("play_"):
            name = name[5:]

        if name.startswith("cf_"):
            name = name[3:]
        
        if len(name) > 1:
            name = name[0]
        name = name.lower()

        if name in "0123456789":
            name = "_" # if we remove the prefix, the table name can start with a _
        if name not in ALL_DB_NAMES:
            raise Exception(f"Invalid DB name {name}!")
        return self.dbs[name]

JAVA_DB_INSTANCES = JavaDbInstances()



class BEDROCK_DB_INSTANCES:
    bedrock_instance = DbInstance("z_bedrock_servers.db")
