from abc import ABC, abstractmethod
import json
import logging
import time
from typing import Any

from mcstatus.responses import BedrockStatusResponse, JavaStatusResponse

from dataclasses import dataclass
from db.database import Database, BatchEntry
from db.schema import METRIC_FIELDS, TEXT_FIELDS
from db.deduplicators import DedupGetType, DeduplicatorResult
from config import RaterConfig
from utils.errors import ErrorHandler, ErrorKey
from utils.rater import ServerRater

from enum import Enum, auto
from dataclasses import dataclass, field

class PollStatus(Enum):
    SUCCESS = auto()
    FAIL = auto()
    SKIP = auto()
    SAVE_FAIL = auto()
    OTHER_FAIL = auto()


@dataclass
class PollResult:
    status: PollStatus
    text_dedups: list[DedupGetType] = field(default_factory=list)
    player_dedups: list[DedupGetType] = field(default_factory=list)
    updated_properties: list[str] = field(default_factory=list)


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

    def diff_values(self, new_values: dict[str, Any]) -> dict[str, Any]:
        return {
            key: val
            for key, val in new_values.items()
            if self.values.get(key) != val
        }

    def commit_values(self, saved_values: dict[str, Any]) -> None:
        self.values.update(saved_values)

    def save_changes(self, timestamp: int, changed_values: dict[str, Any]) -> tuple[list[DedupGetType], dict[str, Any]]:
        batch: list[BatchEntry] = []
        saved: dict[str, Any] = {}
        text_dedups: list[DedupGetType] = []
        metric_fields = METRIC_FIELDS.get(self.db.server_type, {})
        text_fields = TEXT_FIELDS.get(self.db.server_type, {})

        # Always insert a heartbeat (not tied to any tracked value)
        batch.append((None, "INSERT OR IGNORE INTO heartbeats (server_id, timestamp) VALUES (?, ?)", (self.server_id, timestamp)))

        for key, val in changed_values.items():
            if val is None:
                ErrorHandler.add_error(ErrorKey.SAVE_VALUE_NULL, {"key": key})
                continue
            
            if key in metric_fields:
                field_id = metric_fields[key]
                batch.append((key,
                    "INSERT INTO metric_changes VALUES (?, ?, ?, ?)",
                    (self.server_id, field_id, timestamp, val),
                ))
                saved[key] = val
            elif key in text_fields:
                field_id = text_fields[key]
                dedup_res = self.db.text_dedup.get_or_create(val)
                if dedup_res.type == DedupGetType.ERROR:
                    # Dedup failed, no row to write: leave it out of `saved`
                    # so it gets retried on the next poll.
                    continue
                text_dedups.append(dedup_res.type)
                batch.append((key,
                    "INSERT INTO text_changes VALUES (?, ?, ?, ?)",
                    (self.server_id, field_id, timestamp, dedup_res.id),
                ))
                saved[key] = val
            else:
                ErrorHandler.add_error(ErrorKey.SAVE_STATUS)

        try:
            failed_keys = self.db.execute_batch(batch)
        except Exception as e:
            # Whole transaction failed: save nothing, retry next time
            ErrorHandler.add_error(ErrorKey.SAVE_EXCEPTION, {"ip": self.ip, "exception": str(e)})
            return text_dedups, {}

        # Statements that individually failed for one query only
        for key in failed_keys:
            saved.pop(key, None)

        self.commit_values(saved)
        return text_dedups, saved

    
    def load_previous_values(self):
        self.values = self.db.load_previous_values(self.server_id)

    async def poll_and_save(self) -> PollResult:
        if not self.rater.should_poll():
            return PollResult(status=PollStatus.SKIP)
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
    async def async_init(self) -> bool: pass

    @abstractmethod
    async def save_status(self) -> PollResult: pass
