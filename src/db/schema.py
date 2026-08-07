DB_FORMAT_VERSION = 3

# TODO: Improve this whole thing
SERVER_TYPE_JAVA = "java"
SERVER_TYPE_BEDROCK = "bedrock"

METRIC_PLAYERS_ON = 0
METRIC_PLAYERS_MAX = 1
METRIC_PING = 2
METRIC_VERSION_PROTOCOL = 3

METRIC_FIELDS = {
    "players_on": METRIC_PLAYERS_ON,
    "players_max": METRIC_PLAYERS_MAX,
    "ping": METRIC_PING,
    "version_protocol": METRIC_VERSION_PROTOCOL,
}

TEXT_MOTD = 0
TEXT_VERSION_NAME = 1
TEXT_PLAYERS_SAMPLE = 2
TEXT_FAVICON = 3
TEXT_VERSION_BRAND = 4
TEXT_GAMEMODE = 5
TEXT_MAP = 6

TEXT_FIELDS_JAVA = {
    "motd": TEXT_MOTD,
    "version_name": TEXT_VERSION_NAME,
    "players_sample": TEXT_PLAYERS_SAMPLE,
    "favicon": TEXT_FAVICON,
}

TEXT_FIELDS_BEDROCK = {
    "motd": TEXT_MOTD,
    "version_name": TEXT_VERSION_NAME,
    "version_brand": TEXT_VERSION_BRAND,
    "gamemode": TEXT_GAMEMODE,
    "map": TEXT_MAP,
}

# Reverse mappings (field_id -> column name)
METRIC_FIELD_NAMES = {v: k for k, v in METRIC_FIELDS.items()}
TEXT_FIELD_NAMES_JAVA = {v: k for k, v in TEXT_FIELDS_JAVA.items()}
TEXT_FIELD_NAMES_BEDROCK = {v: k for k, v in TEXT_FIELDS_BEDROCK.items()}

# Text field names by server type
TEXT_FIELD_NAMES = {
    SERVER_TYPE_JAVA: TEXT_FIELD_NAMES_JAVA,
    SERVER_TYPE_BEDROCK: TEXT_FIELD_NAMES_BEDROCK,
}

TEXT_FIELDS = {
    SERVER_TYPE_JAVA: TEXT_FIELDS_JAVA,
    SERVER_TYPE_BEDROCK: TEXT_FIELDS_BEDROCK,
}


CREATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS db_meta (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS servers (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT,
    ip      TEXT NOT NULL,
    port    INTEGER NOT NULL,
    UNIQUE(ip, port)
);

CREATE TABLE IF NOT EXISTS metric_changes (
    server_id   INTEGER NOT NULL,
    field_id    INTEGER NOT NULL,
    timestamp   INTEGER NOT NULL,
    value       INTEGER NOT NULL,
    PRIMARY KEY (server_id, field_id, timestamp)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS text_changes (
    server_id   INTEGER NOT NULL,
    field_id    INTEGER NOT NULL,
    timestamp   INTEGER NOT NULL,
    value_id    INTEGER NOT NULL,
    PRIMARY KEY (server_id, field_id, timestamp)
) WITHOUT ROWID;

CREATE TABLE IF NOT EXISTS text_values (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    hash    BLOB NOT NULL UNIQUE,
    content BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    uuid    TEXT NOT NULL,
    UNIQUE(name, uuid)
);

CREATE TABLE IF NOT EXISTS heartbeats (
    server_id   INTEGER NOT NULL,
    timestamp   INTEGER NOT NULL,
    PRIMARY KEY (server_id, timestamp)
) WITHOUT ROWID;
"""
