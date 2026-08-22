import json
import logging
import sqlite3
from typing import Any

from db.schema import (
    CREATE_SCHEMA_SQL,
    DB_FORMAT_VERSION,
    METRIC_FIELD_NAMES,
    TEXT_FIELD_NAMES,
    METRIC_FIELDS,
    TEXT_FIELDS,
)
from db.deduplicators import TextDeduplicator, PlayerDeduplicator
from utils.errors import ErrorHandler, ErrorKey

BatchEntry = tuple[str | None, str, tuple | list | None]


class Database:
    def __init__(self, db_path: str, server_type: str):
        self.db_path = db_path
        self.server_type = server_type

        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA journal_mode=WAL;")
        self.cursor.execute("PRAGMA synchronous=NORMAL;")
        self.cursor.execute("PRAGMA busy_timeout=5000;")

        self.cursor.executescript(CREATE_SCHEMA_SQL)
        self.conn.commit()

        self._ensure_meta()
        logging.info(f"Database ready: {db_path} (format v{DB_FORMAT_VERSION}, {server_type})")

        self.text_dedup = TextDeduplicator(self.cursor)
        self.player_dedup = PlayerDeduplicator(self.cursor)

    def _ensure_meta(self):
        row = self.cursor.execute(
            "SELECT value FROM db_meta WHERE key = 'format_version'"
        ).fetchone()
        if row is None:
            self.cursor.execute(
                "INSERT INTO db_meta (key, value) VALUES ('format_version', ?)",
                (str(DB_FORMAT_VERSION),),
            )
        else:
            stored = int(row[0])
            if stored != DB_FORMAT_VERSION:
                raise RuntimeError(
                    f"DB format version mismatch: file has v{stored}, "
                    f"code expects v{DB_FORMAT_VERSION}"
                )

        row = self.cursor.execute(
            "SELECT value FROM db_meta WHERE key = 'server_type'"
        ).fetchone()
        if row is None:
            self.cursor.execute(
                "INSERT INTO db_meta (key, value) VALUES ('server_type', ?)",
                (self.server_type,),
            )
        else:
            if row[0] != self.server_type:
                raise RuntimeError(
                    f"DB server type mismatch: file has '{row[0]}', "
                    f"code expects '{self.server_type}'"
                )

        row = self.cursor.execute(
            "SELECT value FROM db_meta WHERE key = 'metric_fields'"
        ).fetchone()
        if row is None:
            self.cursor.execute(
                "INSERT INTO db_meta (key, value) VALUES ('metric_fields', ?)",
                (json.dumps(METRIC_FIELDS.get(self.server_type, {})),),
            )

        row = self.cursor.execute(
            "SELECT value FROM db_meta WHERE key = 'text_fields'"
        ).fetchone()
        if row is None:
            self.cursor.execute(
                "INSERT INTO db_meta (key, value) VALUES ('text_fields', ?)",
                (json.dumps(TEXT_FIELDS.get(self.server_type, {})),),
            )

        self.conn.commit()

    def execute_batch(self, batch: list[BatchEntry]) -> set[str]:
        failed_keys: set[str] = set()
        
        for value_key, query, params in batch:
            try:
                if params is not None:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
            except Exception as e:
                ErrorHandler.add_error(
                    ErrorKey.DB_EXECUTE,
                    {"err": str(e), "db_path": self.db_path, "query": query, "params": params},
                )
                if value_key is not None:
                    failed_keys.add(value_key)

        try:
            self.conn.commit()
        except Exception as e:
            ErrorHandler.add_error(ErrorKey.DB_COMMIT, {"err": str(e), "db_path": self.db_path})
            try:
                self.conn.rollback()
            except Exception:
                pass
            raise

        return failed_keys

    def register_server(self, name: str | None, ip: str, port: int) -> int:
        row = self.cursor.execute(
            "SELECT id FROM servers WHERE ip = ? AND port = ?", (ip, port)
        ).fetchone()
        if row:
            return row[0]

        self.cursor.execute(
            "INSERT INTO servers (name, ip, port) VALUES (?, ?, ?)",
            (name, ip, port),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def load_previous_values(
        self, server_id: int,
    ) -> dict[str, Any]:
        # See below for the query explanation
        values: dict[str, Any] = {}
        rows = self.cursor.execute(
            "SELECT mc.field_id, mc.value "
            "FROM metric_changes mc "
            "INNER JOIN ("
            "  SELECT field_id, MAX(timestamp) AS max_ts "
            "  FROM metric_changes WHERE server_id = ? "
            "  GROUP BY field_id"
            ") latest ON mc.field_id = latest.field_id "
            "  AND mc.timestamp = latest.max_ts "
            "WHERE mc.server_id = ?;",
            (server_id, server_id),
        ).fetchall()
        for field_id, value in rows:
            col = METRIC_FIELD_NAMES.get(self.server_type, {}).get(field_id)
            if col:
                values[col] = value

        

        # Inner query:
        # GROUP BY field_id makes differents "groups" for all entries of a certain id
        # eg, {"field 1": [<all field 1 entries>], "field 2": [<all field 2 entries>], ...}
        # THEN, the select takes the entry with the highest timestamp on all these groups, which returns like:
        # fieldid 1, max_ts 4424
        # fieldid 2, max_ts 344343
        # fieldid 3, max_ts 4234231
        # Outer query:
        # just links the entries timestamps grabbed in the inner query to the text_changes entries and then
        # to its actual value from the text_values table.
        text_names = TEXT_FIELD_NAMES.get(self.server_type, {})
        rows = self.cursor.execute(
            "SELECT tc.field_id, tv.content "
            "FROM text_changes tc "
            "JOIN text_values tv ON tv.id = tc.value_id "
            "INNER JOIN ("
            "  SELECT field_id, MAX(timestamp) AS max_ts "
            "  FROM text_changes WHERE server_id = ? "
            "  GROUP BY field_id"
            ") latest ON tc.field_id = latest.field_id "
            "  AND tc.timestamp = latest.max_ts "
            "WHERE tc.server_id = ?;",
            (server_id, server_id),
        ).fetchall()
        for field_id, content in rows:
            col = text_names.get(field_id)
            if col:
                if isinstance(content, bytes):
                    try:
                        # If is an encoded string (eg motd)
                        content = content.decode("utf-8")
                    except UnicodeDecodeError:
                        # otherwise eg if a favicon
                        pass
                values[col] = content

        return values
