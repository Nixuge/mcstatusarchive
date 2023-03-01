from database.DbManager import DbInstance

# IMPORTANT NOTE:
# THIS COMMIT IS REALLY DIRTY BUT I JUST WANTED TO MAKE SOMETHING THAT WORKS
# FOR NOW, WILL GET TO MAKING THINGS PROPERLY NEXT WEEK

class DBMANAGERS:
    java_connection = DbInstance("z_java_servers.db")
    bedrock_connection = DbInstance("z_bedrock_servers.db")