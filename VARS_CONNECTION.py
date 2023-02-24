import sqlite3

# IMPORTANT NOTE:
# THIS COMMIT IS REALLY DIRTY BUT I JUST WANTED TO MAKE SOMETHING THAT WORKS
# FOR NOW, WILL GET TO MAKING THINGS PROPERLY NEXT WEEK

class CONNECTIONS:
    java_connection = sqlite3.connect("z_java_servers.db", check_same_thread=False)
    bedrock_connection = sqlite3.connect("z_bedrock_servers.db", check_same_thread=False)