from database.DbInstance import DbInstance


class DBINSTANCES:
    java_instance = DbInstance("z_java_servers.db")
    java_duplicates_instance = DbInstance("java_duplicates.db")
    bedrock_instance = DbInstance("z_bedrock_servers.db")
