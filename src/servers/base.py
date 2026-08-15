from abc import ABC, abstractmethod
import json
import logging
import time
from typing import Any

from mcstatus.responses import BedrockStatusResponse, JavaStatusResponse

from db.database import Database
from db.schema import METRIC_FIELDS, TEXT_FIELDS
from config import RaterConfig
from utils.errors import ErrorHandler, ErrorKey
from utils.rater import ServerRater

from enum import Enum, auto

class PollResult(Enum):
    SUCCESS = auto()
    FAIL = auto()
    SKIP = auto()
    OTHER_FAIL = auto()

class ServerSv(ABC):
    server_id: int
    ip: str
    port: int
    values: dict
    db: Database

    def __init__(self, server_id: int, ip: str, db: Database, port: int) -> None:
        self.server_id = server_id
        self.ip = ip
        self.port = port
        self.values = {}
        self.db = db
        self.rater = ServerRater(
            down_threshold=RaterConfig.DOWN_THRESHOLD,
            history_size=RaterConfig.HISTORY_SIZE,
            empty_avg_threshold=RaterConfig.EMPTY_AVG_THRESHOLD,
            burst_threshold=RaterConfig.BURST_THRESHOLD,
        )

    def update_values(self, new_values: dict[str, Any]) -> dict[str, Any]:
        changed_values = {}
        for key, val in new_values.items():
            if self.values.get(key) != val:
                self.values[key] = val
                changed_values[key] = val
        return changed_values

    def save_changes(self, timestamp: int, changed_values: dict[str, Any]):
        batch = []
        metric_fields = METRIC_FIELDS.get(self.db.server_type, {})
        text_fields = TEXT_FIELDS.get(self.db.server_type, {})

        # Always insert a heartbeat
        batch.append(("INSERT OR IGNORE INTO heartbeats (server_id, timestamp) VALUES (?, ?)", (self.server_id, timestamp)))

        for key, val in changed_values.items():
            if val is None:
                ErrorHandler.add_error(ErrorKey.SAVE_VALUE_NULL, {"data": changed_values, "key": key})
                continue
            
            if key in metric_fields:
                field_id = metric_fields[key]
                batch.append((
                    "INSERT INTO metric_changes VALUES (?, ?, ?, ?)",
                    (self.server_id, field_id, timestamp, val),
                ))
            elif key in text_fields:
                field_id = text_fields[key]
                # logging.info(f"Starting text dedup thing ({time.time_ns()})")
                value_id = self.db.text_dedup.get_or_create(val)
                # logging.info(f"Done text dedup thing ({time.time_ns()})")
                batch.append((
                    "INSERT INTO text_changes VALUES (?, ?, ?, ?)",
                    (self.server_id, field_id, timestamp, value_id),
                ))
            else:
                ErrorHandler.add_error(ErrorKey.SAVE_STATUS)

        if batch:
            self.db.writer.queue_batch(batch)
    
    def load_previous_values(self):
        self.values = self.db.load_previous_values(self.server_id)

    async def poll_and_save(self) -> PollResult:
        if not self.rater.should_poll():
            return PollResult.SKIP
        return await self.save_status()

    @staticmethod
    def _parse_motd(status: JavaStatusResponse | BedrockStatusResponse) -> str:
        raw = status.motd.raw

        if raw == None: # Should never be the case but just in case.
            return ""
        elif isinstance(raw, (dict, list)):
            return json.dumps(raw, ensure_ascii=False)
        elif isinstance(raw, str):
            return raw

        ErrorHandler.add_error(ErrorKey.MOTD_PARSE_TYPE, {"type": type(raw), "value": raw})
        return ""
    
    @abstractmethod
    async def async_init(self): pass

    @abstractmethod
    async def save_status(self) -> PollResult: pass
