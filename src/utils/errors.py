import json
import logging
import traceback
import urllib.request
from enum import Enum, auto

from config import WebhookUrls


ERRORS = {
    "[Errno -5] No address associated with hostname": "No address for hostname",
    "[Errno -3] Temporary failure in name resolution": "Name Resolution Error",
    "[Errno -2] Name or service not known": "Name unknown",
    "Socket did not respond with any information!": "Socket empty",
    "[Errno 104] Connection reset by peer": "Connection reset",
    "[Errno 32] Broken pipe": "Broken pipe",
    "Timeout": "Timeout error",
    "ConnectCallFailed": "Connect call failed"
}


class ErrorAction(Enum):
    LOG_CRITICAL = auto()
    LOG_ERROR = auto()
    TRACEBACK = auto()
    EXIT_ALL = auto()
    EXIT_THREAD = auto()
    WEBHOOK_WARN = auto()
    WEBHOOK_ERROR = auto()
    WEBHOOK_CRITICAL = auto()


class ErrorKey(Enum):
    # NOTE: members use auto() and their actions live in ERROR_ACTIONS below.
    # Storing action lists as the enum values made keys with identical lists
    # alias into a single member (e.g. DNS_LOOKUP becoming MOTD_PARSE_TYPE).
    DB_EXECUTE = auto()
    DB_COMMIT = auto()
    FRONTEND = auto()
    MOTD_PARSE_TYPE = auto()
    MOTD_JSON_DUMPS = auto()
    CONFIG_BAD_JSON = auto()
    SAVE_STATUS = auto()
    DNS_LOOKUP = auto()
    DNS_LOOKUP_BATCH = auto()
    INIT_NOT_DONE = auto()
    SERVERS_INIT = auto()
    INVALID_IP = auto()
    DUPLICATE_IP = auto()
    CACHE_OVERFLOW_TEXT = auto()
    CACHE_OVERFLOW_PLAYER = auto()
    TEXT_DEDUP_BAD_TYPE = auto()
    SAVE_VALUE_NULL = auto()
    DEDUPER_LASTROWID_NULL = auto()
    DEDUPER_GET_EXCEPTION = auto()
    FAVICON_DECODE_FAIL = auto()
    SAVE_EXCEPTION = auto()


ERROR_ACTIONS: dict[ErrorKey, list[ErrorAction]] = {
    ErrorKey.DB_EXECUTE:         [ErrorAction.LOG_CRITICAL, ErrorAction.TRACEBACK, ErrorAction.WEBHOOK_CRITICAL],
    ErrorKey.DB_COMMIT:          [ErrorAction.LOG_CRITICAL, ErrorAction.TRACEBACK, ErrorAction.WEBHOOK_CRITICAL],
    ErrorKey.FRONTEND:           [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR, ErrorAction.EXIT_THREAD],
    ErrorKey.MOTD_PARSE_TYPE:    [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.MOTD_JSON_DUMPS:    [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.CONFIG_BAD_JSON:    [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    ErrorKey.SAVE_STATUS:        [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.DNS_LOOKUP:         [ErrorAction.LOG_ERROR],
    ErrorKey.DNS_LOOKUP_BATCH:    [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.INIT_NOT_DONE:      [ErrorAction.LOG_CRITICAL, ErrorAction.WEBHOOK_CRITICAL, ErrorAction.EXIT_THREAD, ErrorAction.EXIT_ALL],
    ErrorKey.SERVERS_INIT:       [ErrorAction.LOG_CRITICAL, ErrorAction.TRACEBACK, ErrorAction.WEBHOOK_CRITICAL, ErrorAction.EXIT_ALL],
    ErrorKey.INVALID_IP:         [ErrorAction.LOG_CRITICAL, ErrorAction.WEBHOOK_CRITICAL, ErrorAction.EXIT_ALL],
    ErrorKey.DUPLICATE_IP:       [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.CACHE_OVERFLOW_TEXT:   [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN],
    ErrorKey.CACHE_OVERFLOW_PLAYER: [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN],
    ErrorKey.TEXT_DEDUP_BAD_TYPE:   [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN],
    ErrorKey.SAVE_VALUE_NULL:       [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.DEDUPER_LASTROWID_NULL: [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.DEDUPER_GET_EXCEPTION:  [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    ErrorKey.FAVICON_DECODE_FAIL:    [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN],
    ErrorKey.SAVE_EXCEPTION:         [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
}
    

class ErrorHandler:
    _errors_counts: dict[ErrorKey, int] = {}
    should_stop = False

    @classmethod
    def add_warn(cls, error: str | ErrorKey, data: dict | None = None) -> int:
        return cls.add_error(error, data)
    
    # Returns a non-0 int if should exit
    @classmethod
    def add_error(cls, error: str | ErrorKey, data: dict | None = None) -> int:
        # Not sure about that, basically avoid logging more info
        # if an initial error has already been detected & is already planned
        # to shutdown the whole thing.
        if cls.should_stop:
            return 0

        # Accept both string and ErrorKey
        if isinstance(error, str):
            try:
                error_key = ErrorKey(error)
            except ValueError:
                return cls._unknown_error(error)
        else:
            error_key = error
        
        cls._up_error_count(error_key)

        error_label = error_key.name
        error_actions = ERROR_ACTIONS[error_key]

        if ErrorAction.LOG_CRITICAL in error_actions:
            logging.critical("Critical error happened: " + error_label)
            if data:
                logging.critical(str(data))
        if ErrorAction.LOG_ERROR in error_actions:
            logging.error("Non-critical error happened: " + error_label)
            if data:
                logging.critical(str(data))
        if ErrorAction.TRACEBACK in error_actions:
            traceback.print_exc()
        if ErrorAction.WEBHOOK_WARN in error_actions:
            cls._send_webhook(error_label, data, level="warn")
        if ErrorAction.WEBHOOK_ERROR in error_actions:
            cls._send_webhook(error_label, data, level="error")
        if ErrorAction.WEBHOOK_CRITICAL in error_actions:
            cls._send_webhook(error_label, data, level="critical")

        if ErrorAction.EXIT_ALL in error_actions:
            cls.should_stop = True

        if ErrorAction.EXIT_THREAD in error_actions:
            return cls._get_exit_code(error_key)
        return 0

    @classmethod
    def _unknown_error(cls, error: str) -> int:
        logging.critical("Unknown error type " + error)
        logging.critical("Exiting")
        traceback.print_exc()
        cls.should_stop = True
        return 1

    @classmethod
    def _up_error_count(cls, error: ErrorKey):
        if error not in cls._errors_counts:
            cls._errors_counts[error] = 1
        else:
            cls._errors_counts[error] += 1

    @classmethod
    def _get_exit_code(cls, error: ErrorKey) -> int:
        index_err = list(ErrorKey).index(error) #TODO: Test
        return index_err + 1 # 1 is reserved for "unknown errors"

    @classmethod
    def _send_webhook(cls, error: str, data: dict | None, level: str):
        url_map = {
            "warn": WebhookUrls.WARN,
            "error": WebhookUrls.ERROR,
            "critical": WebhookUrls.CRITICAL,
        }
        url = url_map.get(level, "")
        if not url:
            return
        
        try:
            description = json.dumps(data) if data else "No additional data."
        except (TypeError, ValueError):
            description = f"Non-serializable data of type {type(data).__name__}: {data!r}"[:2000]

        payload = json.dumps({
            "content": None,
            "embeds": [{
                "title": f"[{level.upper()}] {error}",
                "description": description,
                "color": {"warn": 0xFFA500, "error": 0xFF0000, "critical": 0x8B0000}.get(level, 0xFFFFFF),
                "fields": [{
                    "name": "Traceback",
                    "value": f"```\n{traceback.format_exc()[:1000]}\n```",
                }],
            }],
        }).encode("utf-8")

        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "User-Agent": "mcstatusarchive-messager",
                    "Content-Type": "application/json"
                    },
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            logging.warning(f"Failed to send webhook: {e}")

