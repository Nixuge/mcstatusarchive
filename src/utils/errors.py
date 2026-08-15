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
    ERROR_FILE = auto()
    TRACEBACK = auto()
    TRACEBACK_FILE = auto()
    EXIT_ALL = auto()
    EXIT_THREAD = auto()
    WEBHOOK_WARN = auto()
    WEBHOOK_ERROR = auto()
    WEBHOOK_CRITICAL = auto()


class ErrorKey(Enum):
    # DB_IMPORTANT = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    DB_EXECUTE = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    DB_COMMIT = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    FRONTEND = [ErrorAction.LOG_ERROR, ErrorAction.EXIT_THREAD],
    MOTD_PARSE_TYPE = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE],
    MOTD_JSON_DUMPS = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE],
    CONFIG_BAD_JSON = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    SAVE_STATUS = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK_FILE],
    DNS_LOOKUP = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.EXIT_ALL, ErrorAction.EXIT_THREAD],
    INIT_NOT_DONE = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.EXIT_THREAD, ErrorAction.EXIT_ALL],
    LAST_VALUE_BSON_LOAD = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL],
    LAST_VALUE_BSON_SAVE = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL],
    SERVERS_INIT = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.TRACEBACK, ErrorAction.TRACEBACK_FILE, ErrorAction.EXIT_ALL],
    INVALID_IP = [ErrorAction.LOG_CRITICAL, ErrorAction.ERROR_FILE, ErrorAction.EXIT_ALL],
    DUPLICATE_IP = [ErrorAction.LOG_ERROR]
    CACHE_OVERFLOW_TEXT = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE, ErrorAction.WEBHOOK_WARN]
    CACHE_OVERFLOW_PLAYER = [ErrorAction.LOG_ERROR, ErrorAction.ERROR_FILE, ErrorAction.WEBHOOK_WARN]
    TEXT_DEDUP_BAD_TYPE = [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN]
    SAVE_VALUE_NULL = [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    DEDUPER_LASTROWID_NULL = [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    DEDUPER_GET_EXCEPTION = [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_ERROR],
    FAVICON_DECODE_FAIL = [ErrorAction.LOG_ERROR, ErrorAction.WEBHOOK_WARN]
    

class ErrorHandler:
    # _error_file_path = "/home/nix/"
    _error_file_path = "./error/"
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
        error_actions = error_key.value
        if isinstance(error_actions, tuple):
            error_actions = error_actions[0]

        if ErrorAction.LOG_CRITICAL in error_actions:
            logging.critical("Critical error happened: " + error_label)
            if data:
                logging.critical(str(data))
        if ErrorAction.LOG_ERROR in error_actions:
            logging.error("Non-critical error happened: " + error_label)
            if data:
                logging.critical(str(data))
        if ErrorAction.ERROR_FILE in error_actions:
            cls._data_to_file(error_label, data)
        if ErrorAction.TRACEBACK in error_actions:
            traceback.print_exc()
        if ErrorAction.TRACEBACK_FILE in error_actions:
            cls._traceback_to_file(error_label)
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
        cls._traceback_to_file(f"UNKNOWN_{error}")
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
    def _data_to_file(cls, error: str, data: dict | None):
        with open(cls._error_file_path + f"ERROR_{error}.txt", "a") as file:
            file.write("Error happened:" + error)
            if data:
                file.write("Additional data: " + json.dumps(data))

    @classmethod
    def _traceback_to_file(cls, error: str):
        with open(cls._error_file_path + f"ERROR_{error}.txt", "a") as file:
            file.write(traceback.format_exc())

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

        payload = json.dumps({
            "content": None,
            "embeds": [{
                "title": f"[{level.upper()}] {error}",
                "description": json.dumps(data) if data else "No additional data.",
                "color": {"warn": 0xFFA500, "error": 0xFF0000, "critical": 0x8B0000}.get(level, 0xFFFFFF),
                "fields": [{
                    "name": "Traceback",
                    "value": f"```\n{traceback.format_exc()[:1000]}\n```",
                }],
            }],
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "User-Agent": "mcstatusarchive-messager",
                "Content-Type": "application/json"
                },
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=5)
        except Exception as e:
            logging.warning(f"Failed to send webhook ({level}): {e}")

