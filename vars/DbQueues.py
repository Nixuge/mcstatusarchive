from vars.DbManagers import DBMANAGERS
from database.DbQueue import DbQueue

# IMPORTANT NOTE:
# THIS COMMIT IS REALLY DIRTY BUT I JUST WANTED TO MAKE SOMETHING THAT WORKS
# FOR NOW, WILL GET TO MAKING THINGS PROPERLY NEXT WEEK

class DBQUEUES:
    db_queue_java = DbQueue(DBMANAGERS.java_connection)
    db_queue_bedrock = DbQueue(DBMANAGERS.bedrock_connection)