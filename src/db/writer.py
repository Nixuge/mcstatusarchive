import hashlib
import logging
import sqlite3
from collections import OrderedDict
from threading import Thread
import threading
from time import sleep

from utils.errors import ErrorHandler, ErrorKey


class TextDeduplicator:
    CACHE_INITIAL_LOAD_MAX = 50_000
    CACHE_MAX = 500_000
    EVICT_COUNT = 10_000

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor
        self._conn = cursor.connection
        self._cache: OrderedDict[str, int] = OrderedDict()  # hash_hex -> id
        self._load_initial_cache()

    def _load_initial_cache(self):
        count = self._cursor.execute("SELECT COUNT(*) FROM text_values").fetchone()[0]
        if count <= self.CACHE_INITIAL_LOAD_MAX:
            self._cursor.execute("SELECT id, hash FROM text_values ORDER BY id;")
        else:
            self._cursor.execute(
                "SELECT id, hash FROM text_values ORDER BY id DESC LIMIT ?;",
                (self.CACHE_INITIAL_LOAD_MAX,),
            )

        # reversed() so that oldest entries end up at the front of the
        # OrderedDict and get evicted first by popitem(last=False).
        for row_id, row_hash in reversed(self._cursor.fetchall()):
            hash_hex = row_hash.hex() if isinstance(row_hash, bytes) else row_hash
            self._cache[hash_hex] = row_id

        if count <= self.CACHE_INITIAL_LOAD_MAX:
            logging.info(f"TextDeduplicator: loaded all {len(self._cache)} text values into cache.")
        else:
            logging.info(
                f"TextDeduplicator: {count} text values in DB, "
                f"loaded {len(self._cache)} most recent into cache."
            )

    def get_or_create(self, content) -> int:
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif isinstance(content, bytes):
            content_bytes = content
        else:
            ErrorHandler.add_warn(ErrorKey.TEXT_DEDUP_BAD_TYPE, {"cache": "TextDeduplicator"})
            content_bytes = str(content).encode("utf-8")

        hash_hex = hashlib.sha256(content_bytes).hexdigest()

        cached_id = self._cache.get(hash_hex)
        if cached_id is not None:
            self._cache.move_to_end(hash_hex)
            return cached_id

        try:
            hash_bytes = bytes.fromhex(hash_hex)
            row = self._cursor.execute(
                "SELECT id FROM text_values WHERE hash = ?", (hash_bytes,)
            ).fetchone()
            if row:
                self._cache[hash_hex] = row[0]
                self._evict_if_needed()
                return row[0]


            db_content = content if isinstance(content, (str, bytes)) else str(content)
            self._cursor.execute(
                "INSERT INTO text_values (hash, content) VALUES (?, ?)",
                (hash_bytes, db_content),
            )
            self._conn.commit()
            new_id = self._cursor.lastrowid
            if not new_id:
                ErrorHandler.add_error(ErrorKey.DEDUPER_LASTROWID_NULL, {"cache": "TextDeduplicator"})
                return -1
            
            self._cache[hash_hex] = new_id
            self._evict_if_needed()
            return new_id
        except Exception as e:
            ErrorHandler.add_error(ErrorKey.DEDUPER_GET_EXCEPTION, {"cache": "TextDeduplicator", "exception": str(e)})
            return -1
    
    def _evict_if_needed(self):
        if len(self._cache) > self.CACHE_MAX:
            for _ in range(self.EVICT_COUNT):
                self._cache.popitem(last=False)


class PlayerDeduplicator:
    CACHE_INITIAL_LOAD_MAX = 50_000
    CACHE_MAX = 500_000   # ~150 MB estimated
    EVICT_COUNT = 10_000

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor
        self._conn = cursor.connection
        self._cache: OrderedDict[tuple[str, str], int] = OrderedDict()
        self._load_initial_cache()

    def _load_initial_cache(self):
        count = self._cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        if count <= self.CACHE_INITIAL_LOAD_MAX:
            self._cursor.execute("SELECT id, name, uuid FROM players ORDER BY id;")
        else:
            self._cursor.execute(
                "SELECT id, name, uuid FROM players ORDER BY id DESC LIMIT ?;",
                (self.CACHE_INITIAL_LOAD_MAX,),
            )

        # reversed() so that oldest entries end up at the front of the
        # OrderedDict and get evicted first by popitem(last=False).
        for row_id, name, uuid in reversed(self._cursor.fetchall()):
            self._cache[(name, uuid)] = row_id

        if count <= self.CACHE_INITIAL_LOAD_MAX:
            logging.info(f"PlayerDeduplicator: loaded all {len(self._cache)} players into cache.")
        else:
            logging.info(
                f"PlayerDeduplicator: {count} players in DB, "
                f"loaded {len(self._cache)} most recent into cache."
            )

    def get_or_create(self, name: str, uuid: str) -> int:
        key = (name, uuid)

        cached_id = self._cache.get(key)
        if cached_id is not None:
            self._cache.move_to_end(key)
            return cached_id

        try:
            row = self._cursor.execute(
                "SELECT id FROM players WHERE name = ? AND uuid = ?", (name, uuid)
            ).fetchone()
            if row:
                self._cache[key] = row[0]
                self._evict_if_needed()
                return row[0]

            self._cursor.execute(
                "INSERT INTO players (name, uuid) VALUES (?, ?)",
                (name, uuid),
            )
            self._conn.commit()
            new_id = self._cursor.lastrowid
            if not new_id:
                ErrorHandler.add_error(ErrorKey.DEDUPER_LASTROWID_NULL, {"cache": "PlayerDeduplicator"})
                return -1
            self._cache[key] = new_id
            self._evict_if_needed()
            return new_id
        except Exception as e:
            ErrorHandler.add_error(ErrorKey.DEDUPER_GET_EXCEPTION, {"cache": "PlayerDeduplicator", "exception": str(e)})
            return -1

    def _evict_if_needed(self):
        if len(self._cache) > self.CACHE_MAX:
            for _ in range(self.EVICT_COUNT):
                self._cache.popitem(last=False)


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
        cursor.execute("PRAGMA busy_timeout=5000;")

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