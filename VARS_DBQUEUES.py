from VARS_CONNECTION import CONNECTIONS
from database.DbQueue import DbQueue

# IMPORTANT NOTE:
# THIS COMMIT IS REALLY DIRTY BUT I JUST WANTED TO MAKE SOMETHING THAT WORKS
# FOR NOW, WILL GET TO MAKING THINGS PROPERLY NEXT WEEK

class DBQUEUES:
    db_queue_java = DbQueue(CONNECTIONS.java_connection)
    db_queue_bedrock = DbQueue(CONNECTIONS.bedrock_connection)