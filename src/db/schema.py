DB_FORMAT_VERSION = 4

SERVER_TYPE_JAVA = "java"
SERVER_TYPE_BEDROCK = "bedrock"


JAVA_METRIC_FIELDS = {
    "players_on":                0,
    "players_max":               1,
    "ping":                      2,
    "version_protocol":          3,
    "enforces_secure_chat":      4,
    "forge_fml_network_version": 5,
    "forge_truncated":           6,
}

JAVA_TEXT_FIELDS = {
    "motd":            0,
    "version_name":    1,
    "players_sample":  2,
    "favicon":         3,
    "forge_channels":  4,
    "forge_mods":      5,
}


BEDROCK_METRIC_FIELDS = {
    "players_on":        0,
    "players_max":       1,
    "ping":              2,
    "version_protocol":  3,
}

BEDROCK_TEXT_FIELDS = {
    "motd":           0,
    "version_name":   1,
    "version_brand":  2,
    "gamemode":       3,
    "map":            4,
}



METRIC_FIELDS = {
    SERVER_TYPE_JAVA: JAVA_METRIC_FIELDS,
    SERVER_TYPE_BEDROCK: BEDROCK_METRIC_FIELDS,
}

TEXT_FIELDS = {
    SERVER_TYPE_JAVA: JAVA_TEXT_FIELDS,
    SERVER_TYPE_BEDROCK: BEDROCK_TEXT_FIELDS,
}

# Reverse mappings (field_id -> column name)
JAVA_METRIC_FIELD_NAMES = {v: k for k, v in JAVA_METRIC_FIELDS.items()}
JAVA_TEXT_FIELD_NAMES = {v: k for k, v in JAVA_TEXT_FIELDS.items()}
BEDROCK_METRIC_FIELD_NAMES = {v: k for k, v in BEDROCK_METRIC_FIELDS.items()}
BEDROCK_TEXT_FIELD_NAMES = {v: k for k, v in BEDROCK_TEXT_FIELDS.items()}

METRIC_FIELD_NAMES = {
    SERVER_TYPE_JAVA: JAVA_METRIC_FIELD_NAMES,
    SERVER_TYPE_BEDROCK: BEDROCK_METRIC_FIELD_NAMES,
}

TEXT_FIELD_NAMES = {
    SERVER_TYPE_JAVA: JAVA_TEXT_FIELD_NAMES,
    SERVER_TYPE_BEDROCK: BEDROCK_TEXT_FIELD_NAMES,
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
