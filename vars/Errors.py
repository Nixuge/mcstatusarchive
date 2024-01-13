import json
import logging
import traceback


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

class ErrorHandler:
    _error_file_path = "/home/nix/"
    _actions = {
        "dbimportant": ["log_critical", "error_file", "traceback", "traceback_file", "exit_all", "exit_thread"],
        "dbnormal": ["log_critical", "error_file", "traceback", "traceback_file", "exit_all", "exit_thread"],
        "frontend": ["log_error", "exit_thread"],
        "motd_parse_type": ["log_error", "error_file"],
        "motd_json_dumps": ["log_error", "error_file"],
        "config_badjson": ["log_error", "error_file", "traceback_file", "exit_all", "exit_thread"],
        "save_status": ["log_error", "error_file", "traceback_file"],
        "dnslookup": ["log_critical", "error_file", "exit_all", "exit_thread"],
        "init_not_done": ["log_critical", "error_file", "exit_thread", "exit_all"],
        "last_value_bson_load": ["log_critical", "error_file", "traceback", "traceback_file", "exit_all"],
        "last_value_bson_save": ["log_critical", "error_file", "traceback", "traceback_file", "exit_all"]
    }
    _errors_counts = {}
    should_stop = False

    # Returns a non-0 int if should exit
    @classmethod
    def add_error(cls, error: str, data: dict | None = None) -> int:
        # Not sure about that, basically avoid logging more info
        # if an initial error has already been detected & is already planned
        # to shutdown the whole thing.
        if cls.should_stop:
            return 0
        err_actions = cls._actions.get(error)
        if not err_actions:
            return cls._unknown_error(error)
        
        cls._up_error_count(error)

        if "log_critical" in err_actions:
            logging.critical("Critical error happened: " + error)
            if data:
                logging.critical(str(data))
        if "log_error" in err_actions:
            logging.error("Non-critical error happened: " + error)
            if data:
                logging.critical(str(data))
        if "error_file" in err_actions:
            cls._data_to_file(error, data)
        if "traceback" in err_actions:
            traceback.print_exc()
        if "traceback_file" in err_actions:
            cls._traceback_to_file(error)
        
        if "exit_all" in err_actions:
            cls.should_stop = True
        
        if "exit_thread" in err_actions:
            return cls._get_exit_code(error)
        return 0

    @classmethod
    def _unknown_error(cls, error: str) -> int:
        logging.critical("Unknown error type " + error)
        logging.critical("Exiting")
        cls._traceback_to_file(f"UNKNOWN_{error}")
        cls.should_stop = True
        return 1

    @classmethod
    def _up_error_count(cls, error: str):
        if not error in cls._errors_counts.keys():
            cls._errors_counts[error] = 1
        else:
            cls._errors_counts[error] += 1

    @classmethod
    def _get_exit_code(cls, error: str) -> int:
        index_err = list(cls._actions.keys()).index(error)
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