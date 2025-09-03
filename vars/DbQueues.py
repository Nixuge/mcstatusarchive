from database.DbInstance import DbInstance
from vars.DbInstances import ALL_DB_NAMES, BEDROCK_DB_INSTANCES, JAVA_DB_INSTANCES
from database.DbQueue import DbQueue

class JavaDbQueues:
    queues: dict[DbInstance, DbQueue]
    def __init__(self) -> None:
        self.queues = {}
        for name in ALL_DB_NAMES:
            self.queues[JAVA_DB_INSTANCES[name]] = DbQueue(JAVA_DB_INSTANCES[name])
    
    def __getitem__(self, name: str) -> DbQueue:
        return self.queues[JAVA_DB_INSTANCES[name]]
    
    def start_all(self):
        for queue in self.queues.values():
            queue.start()
    
JAVA_DB_QUEUES = JavaDbQueues()

class BEDROCK_DB_QUEUES:
    db_queue_bedrock = DbQueue(BEDROCK_DB_INSTANCES.bedrock_instance)
