from vars.DbInstances import DBINSTANCES
from database.DbQueue import DbQueue


class DBQUEUES:
    db_queue_java = DbQueue(DBINSTANCES.java_instance)
    db_queue_bedrock = DbQueue(DBINSTANCES.bedrock_instance)
