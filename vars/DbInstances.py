from database.DbInstance import DbInstance


class DBINSTANCES:
    java_instance = DbInstance("z_java_servers.db")
    bedrock_instance = DbInstance("z_bedrock_servers.db")
