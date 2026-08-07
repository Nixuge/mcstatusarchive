import hashlib
import logging
import sqlite3
from threading import Thread
import threading
from time import sleep

from utils.errors import ErrorHandler, ErrorKey


# VERY ROUGH ESTIMATION, may have been hallucinated, TO BE UPDATED IF DOESNT FIT REAL USE.
# Estimated per-entry memory cost in bytes (Python dict overhead + key + value)
_TEXT_ENTRY_BYTES = 200    # 64-char hex string key + int value + dict overhead
_PLAYER_ENTRY_BYTES = 300  # (name, uuid) tuple key + int value + dict overhead
_CACHE_WARN_BYTES = 500 * 1024 * 1024  # 500 MB


class TextDeduplicator:
    def __init__(self, cursor: sqlite3.Cursor, writer: DbWriter):
        self._cache: dict[str, int] = {}   # hash_hex -> text_value_id
        self._next_id: int = 1
        self._writer: DbWriter = writer
        self._warned: bool = False
        self._load_from_db(cursor)

    def _load_from_db(self, cursor: sqlite3.Cursor):
        cursor.execute("SELECT id, hash FROM text_values;")
        for row_id, row_hash in cursor.fetchall():
            hash_hex = row_hash.hex() if isinstance(row_hash, bytes) else row_hash
            self._cache[hash_hex] = row_id
            if row_id >= self._next_id:
                self._next_id = row_id + 1
        logging.info(f"TextDeduplicator: loaded {len(self._cache)} cached text values.")

    def get_or_create(self, content) -> int:
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            content_bytes = str(content).encode("utf-8")

        hash_hex = hashlib.sha256(content_bytes).hexdigest()

        cached_id = self._cache.get(hash_hex)
        if cached_id is not None:
            return cached_id

        new_id = self._next_id
        self._next_id += 1
        self._cache[hash_hex] = new_id

        self._check_cache_size()

        hash_bytes = bytes.fromhex(hash_hex)
        
        if isinstance(content, (str, bytes)): 
            db_content = content
        else:
            ErrorHandler.add_warn(ErrorKey.TEXT_DEDUP_BAD_TYPE, {"cache": "TextDeduplicator"})
            db_content = str(content)

        self._writer.queue(
            "INSERT OR IGNORE INTO text_values (id, hash, content) VALUES (?, ?, ?)",
            (new_id, hash_bytes, db_content),
        )
        return new_id

    def _check_cache_size(self):
        if self._warned:
            return
        
        estimated = len(self._cache) * _TEXT_ENTRY_BYTES
        if estimated >= _CACHE_WARN_BYTES:
            self._warned = True
            ErrorHandler.add_warn(
                ErrorKey.CACHE_OVERFLOW_TEXT,
                {"cache": "TextDeduplicator", "entries": len(self._cache), "estimated_mb": estimated // (1024 * 1024)},
            )


class PlayerDeduplicator:
    def __init__(self, cursor: sqlite3.Cursor, writer: "DbWriter"):
        self._cache: dict[tuple[str, str], int] = {}  # (name, uuid) -> player_id
        self._next_id: int = 1
        self._writer: DbWriter = writer
        self._warned: bool = False
        self._load_from_db(cursor)

    def _load_from_db(self, cursor: sqlite3.Cursor):
        cursor.execute("SELECT id, name, uuid FROM players;")
        for row_id, name, uuid in cursor.fetchall():
            self._cache[(name, uuid)] = row_id
            if row_id >= self._next_id:
                self._next_id = row_id + 1
        logging.info(f"PlayerDeduplicator: loaded {len(self._cache)} cached players.")

    def get_or_create(self, name: str, uuid: str) -> int:
        key = (name, uuid)
        cached_id = self._cache.get(key)
        if cached_id is not None:
            return cached_id

        new_id = self._next_id
        self._next_id += 1
        self._cache[key] = new_id

        self._check_cache_size()

        self._writer.queue(
            "INSERT OR IGNORE INTO players (id, name, uuid) VALUES (?, ?, ?)",
            (new_id, name, uuid),
        )
        
        return new_id

    def _check_cache_size(self):
        if self._warned:
            return
        estimated = len(self._cache) * _PLAYER_ENTRY_BYTES
        if estimated >= _CACHE_WARN_BYTES:
            self._warned = True
            ErrorHandler.add_error(
                ErrorKey.CACHE_OVERFLOW_PLAYER,
                {"cache": "PlayerDeduplicator", "entries": len(self._cache), "estimated_mb": estimated // (1024 * 1024)},
            )


class DbWriter(Thread):
    def __init__(self, db_path: str, should_stop_func):
        super().__init__(name="DbWriter", daemon=True)
        self.db_path = db_path
        self._should_stop = should_stop_func
        self._queue: list[tuple[str, tuple | list | None]] = []
        self._lock = threading.Lock() # unsure if really required but better safe than sorry

    def queue(self, query: str, params: tuple | list | None = None):
        with self._lock:
            self._queue.append((query, params))

    def queue_batch(self, items: list[tuple[str, tuple | list | None]]):
        with self._lock:
            self._queue.extend(items)

    def run(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")

        while not self._should_stop():
            sleep(0.5)
            if len(self._queue) > 0:
                self._process_queue(conn, cursor)

        # Final flush
        if len(self._queue) > 0:
            self._process_queue(conn, cursor)

        conn.close()
        logging.info("DbWriter thread stopped gracefully.")

    def _process_queue(self, conn, cursor):
        with self._lock:
            to_process = self._queue
            self._queue = []
        
        for query, params in to_process:
            try:
                if params is not None:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
            except Exception as e:
                ErrorHandler.add_error(ErrorKey.DB_EXECUTE, {"err": str(e), "db_path": self.db_path, "query": query, "params": params})
                # import traceback
                # traceback.print_exc()
        try:
            conn.commit()
        except Exception as e:
            ErrorHandler.add_error(ErrorKey.DB_COMMIT, {"err": str(e), "db_path": self.db_path})
            # import traceback
            # traceback.print_exc()