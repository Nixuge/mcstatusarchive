import logging
from datetime import datetime
import os

from vars.dirty_logging_config import LOG_FAILED_SERVER_GRABS

def get_proper_logger(logger: logging.Logger, debugConsole: bool):
    logger.setLevel(logging.DEBUG)
    logger.propagate = False #avoid having multiple outputs


    # Console output
    sh = logging.StreamHandler()
    sh.addFilter(FilterSocketExceptions())
    if debugConsole:
        sh.setLevel(logging.DEBUG)
    else:
        sh.setLevel(logging.INFO)
    sh.setFormatter(CustomFormatterConsole())
    logger.addHandler(sh)

    # File output
    if not os.path.exists("logs/"): os.mkdir("logs/")

    now = datetime.now()
    dt_string = now.strftime("%Y-%m-%d_%H.%M.%S")

    fh = logging.FileHandler(f"logs/{dt_string}.log")
    fh.addFilter(FilterSocketExceptions())
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(CustomFormatterFile())
    logger.addHandler(fh)

    return logger

class COLORS:
    pink = "\033[95m"
    blue = "\033[94m"
    cyan = "\033[96m"
    green = "\033[92m"
    grey = "\x1b[38;21m"
    yellow = "\033[93m"
    red = "\033[91m"
    bold = "\033[1m"
    underline = "\033[4m"
    reset = "\033[0m"

#using format instead of strings bc otherwise vscode removes color for everything else
format1 = "[%(levelname)s] {}%(filename)s:%(lineno)s{} ".format(COLORS.underline, COLORS.reset)
format2 = "%(message)s"

def _get_correctly(prefix: str) -> str:
    return prefix + format1 + prefix + format2 + COLORS.reset

class FilterSocketExceptions(logging.Filter):
    def filter(self, record):
        if not LOG_FAILED_SERVER_GRABS and "ERRORSPLIT" in record.getMessage():
            return False
        return not "raised exception." in record.getMessage() # This shouldn't match any other error message (I hope)


class CustomFormatterConsole(logging.Formatter):
    FORMATS = {
        logging.DEBUG: _get_correctly(COLORS.grey),
        logging.INFO: _get_correctly(COLORS.cyan),
        logging.WARNING: _get_correctly(COLORS.yellow),
        logging.ERROR: _get_correctly(COLORS.red),
        logging.CRITICAL: _get_correctly(COLORS.green) # used as a "success" print
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        result = formatter.format(record).replace(".py", "")

        # A bit dirty but makes logs look WAY better
        if "ERRORSPLIT" in result:
            return COLORS.yellow + "- " + result.split("ERRORSPLIT")[1]
        
        return result

class CustomFormatterFile(logging.Formatter):
    format_ = "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)s %(message)s"

    def format(self, record):
        formatter = logging.Formatter(self.format_)
        result = formatter.format(record).replace(".py", "")

        if "ERRORSPLIT" in result:
            return result.replace("ERRRORSPLIT", "")
        
        return result

#thanks https://stackoverflow.com/a/56944275 & https://stackoverflow.com/a/287944
# Note: special case "ERRORSPLIT is meant so that it doesn't log a full line for no reason when
# an errer fails to gets saved.