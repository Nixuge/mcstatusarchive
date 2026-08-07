import json
import logging


class Configurator:
    _CONFIG_DICT = None

    @classmethod
    def init(cls, filename: str = "config.json") -> None:
        try:
            with open(filename, "r") as config_file:
                cls._CONFIG_DICT = json.load(config_file)
            logging.info("Loaded config.")
        except FileNotFoundError:
            logging.info("Not using any config.")
        except json.decoder.JSONDecodeError:
            logging.error("Config file contains invalid JSON.")

    @classmethod
    def get_value(cls, key: str, default_value):
        if cls._CONFIG_DICT is None:
            return default_value
        value = cls._CONFIG_DICT.get(key, None)
        if value is None:
            return default_value
        if type(value) != type(default_value):
            logging.warning(
                f"Config '{key}' has wrong type "
                f"({type(value).__name__}, expected {type(default_value).__name__})"
            )
            return default_value
        return value


Configurator.init()


class Timings:
    SERVER_TIMEOUT = Configurator.get_value("server_timeout", 25)
    SAVE_EVERY = Configurator.get_value("save_every", 120)
    DNS_TIMEOUT = Configurator.get_value("dns_timeout", 20)


class McConfig:
    JAVA_VERSION = Configurator.get_value("java_version", 776)


class LoggingConfig:
    LOG_DNS_TIMEOUT = Configurator.get_value("log_dns_timeout", False)
    LOG_DNS_ERROR = Configurator.get_value("log_dns_error", True)


class Paths:
    DB_PATH_JAVA = Configurator.get_value("db_path_java", "data/mcstatusarchive_java.db")
    DB_PATH_BEDROCK = Configurator.get_value("db_path_bedrock", "data/mcstatusarchive_bedrock.db")
    SERVERS_JSON = Configurator.get_value("servers_json", "data/servers.json")


class WebhookUrls:
    WARN = Configurator.get_value("webhook_warn_url", "")
    ERROR = Configurator.get_value("webhook_error_url", "")
    CRITICAL = Configurator.get_value("webhook_critical_url", "")


class RaterConfig:
    DOWN_THRESHOLD = Configurator.get_value("rater_down_threshold", 5)
    HISTORY_SIZE = Configurator.get_value("rater_history_size", 5)
    EMPTY_AVG_THRESHOLD = Configurator.get_value("rater_empty_avg_threshold", 1.0)
    BURST_THRESHOLD = Configurator.get_value("rater_burst_threshold", 5)
