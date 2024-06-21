import json
import logging

from vars.Errors import ErrorHandler
class Configurator:
    _CONFIG_DICT = None

    @classmethod
    def init(cls, filename: str = "config.json") -> None:
        try:
            with open(filename, "r") as config_file:
                cls._CONFIG_DICT = json.load(config_file)
            logging.info("Loaded config.")
        except FileNotFoundError:
            # not an error, can run without a config.
            logging.info("Not using any config.")
        except json.decoder.JSONDecodeError:
            ErrorHandler.add_error("config_badjson")

    @classmethod
    def get_value(cls, key: str, default_value):
        if cls._CONFIG_DICT == None:
            return default_value
        
        value = cls._CONFIG_DICT.get(key, None)

        if value == None:
            return default_value
        
        if type(value) != type(default_value):
            logging.warn(f"Key for config '{key}' of wrong type! ({type(value)}, excepted {type(default_value)})")
            return default_value
        
        return value

Configurator.init()


# Note:
# This checks (or at least will in the future check if ~) for 
# ~ too many duplicates in the motd/players_sample/favicon
# ~ too many changes (non duplicate) in those columns -> change to gzipped data
# ~ too many failed connections (socket, timeout, etc)
class Startup:
    SHOULD_PERFORM_STARTUP_CHECKS = Configurator.get_value("should_perform_startup_checks", False)

class Timings:
    SERVER_TIMEOUT = Configurator.get_value("server_timeout", 25)
    SAVE_EVERY = Configurator.get_value("save_every", 120)
    DNS_TIMEOUT = Configurator.get_value("dns_timeout", 20)

class Logging:
    LOG_DNS_TIMEOUT = Configurator.get_value("log_dns_timeout", False)
    LOG_DNS_ERROR = Configurator.get_value("log_dns_error", True)
    
    LOG_HIGH_COUNT_DUPLICATE_TABLE = Configurator.get_value("log_high_count_duplicate_table", True)